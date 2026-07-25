// run_page.js <file.b|file.aheui|file.png> [input] [--save out.png] [--html page]
//
// Drives aheui_console.html's own load() under a stub DOM: a source file goes
// in, the page compiles it, bakes a PNG, decodes that PNG back and runs it.
// --save writes out the PNG the page produced, so it can be diffed against the
// one bf_to_png.py produces from the same source.
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
let file = null, input = null, save = null, htmlPath = 'aheui_console.html', timeout = 120000;
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--save') save = argv[++i];
  else if (argv[i] === '--html') htmlPath = argv[++i];
  else if (argv[i] === '--timeout') timeout = +argv[++i];
  else if (file === null) file = argv[i];
  else input = argv[i];
}

const html = fs.readFileSync(htmlPath, 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));

let captured = '';
function mkEl(id) {
  return {
    id, textContent: '', value: '', placeholder: '', disabled: false, src: '', href: '',
    download: '', scrollTop: 0, scrollHeight: 0, className: '', files: [], style: {},
    classList: { toggle() {}, add() {}, remove() {} },
    appendChild(n) { if (id === 'term') captured += n.textContent; },
    addEventListener() {}, focus() {},
  };
}
const els = {};
global.document = {
  body: { style: {} },
  getElementById: id => (els[id] ||= mkEl(id)),
  createElement: () => ({ textContent: '', className: '' }),
};
global.location = { protocol: 'file:' };

// Capture the blob the page hands to the download link, so the exact bytes it
// offers the user are the bytes this harness checks.
let madeBlob = null;
global.Blob = class { constructor(parts) { madeBlob = parts[0]; } };
global.URL = { createObjectURL: () => 'blob:stub' };

const api = new Function(
  `${script}\nreturn { load, compileBF, gridToBytes, encodePNG, getVM: () => vm };`)();

(async () => {
  const bytes = new Uint8Array(fs.readFileSync(file));
  const queue = [...(input || '')].map(c => c.charCodeAt(0));
  let primed = false, eofs = 0;

  const pump = setInterval(() => {
    const vm = api.getVM();
    if (!vm) return;
    if (!primed) { primed = true; for (const c of queue) vm.q.push(c); for (let i = 0; i < 8; i++) vm.q.push(0); }
    // Feed a bounded run of EOFs, then let it block: a program that loops
    // on EOF would otherwise spin until the deadline and report a step count
    // that says nothing about the program.
    if (vm.resolve && eofs < 8) { eofs++; vm.q.push(0); const r = vm.resolve; vm.resolve = null; r(); }
  }, 5);

  const deadline = setTimeout(() => { const vm = api.getVM(); if (vm) vm.done = true; }, timeout);
  await api.load(bytes, path.basename(file));
  // load() can bail before starting anything (bad brackets, no ops, no
  // alphabet match). Nothing will ever set vm, so do not wait for it.
  if (api.getVM()) {
    for (;;) {
      const vm = api.getVM();
      if (vm && vm.done) break;
      await new Promise(r => setTimeout(r, 20));
    }
  }
  clearInterval(pump); clearTimeout(deadline);

  if (save && madeBlob) fs.writeFileSync(save, Buffer.from(madeBlob));
  const vm = api.getVM();
  if (vm) process.stderr.write(`steps ${vm.steps.toLocaleString()}\n`);
  process.stdout.write(captured);
})();
