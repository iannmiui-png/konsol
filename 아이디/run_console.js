// run_console.js <image.png> [input-string] [--html page.html] [--timeout ms]
//
// Runs a PNG through the JS actually embedded in aheui_console.html, under a
// stub DOM. Same decoder, same grid builder, same VM the browser uses -- so a
// pass here means the page will play it.
const fs = require('fs');

const argv = process.argv.slice(2);
let png = null, input = null, htmlPath = 'aheui_console.html', timeout = 60000;
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--html') htmlPath = argv[++i];
  else if (argv[i] === '--timeout') timeout = +argv[++i];
  else if (png === null) png = argv[i];
  else input = argv[i];
}

const html = fs.readFileSync(htmlPath, 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));

let captured = '';
function mkEl(id) {
  return {
    id, textContent: '', value: '', placeholder: '', disabled: false,
    scrollTop: 0, scrollHeight: 0, className: '', files: [], style: {},
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

const api = new Function(`${script}\nreturn { decodePNG, buildGrid, buildSkip, AheuiVM };`)();

(async () => {
  const raw = await api.decodePNG(new Uint8Array(fs.readFileSync(png)));
  const g = api.buildGrid(raw);
  const skip = api.buildSkip(g);
  process.stderr.write(`grid ${g.rows.toLocaleString()} rows x ${g.W} cols, ` +
                       `skip tables ${skip.filter(Boolean).length}/${g.W}\n`);
  captured = '';
  const vm = new api.AheuiVM(g, skip);
  for (const ch of (input || '')) vm.q.push(ch.charCodeAt(0));
  for (let i = 0; i < 8; i++) vm.q.push(0);      // EOF = 0, as the reference does
  // A program that outruns its input would await getChar() forever and the
  // process would exit silently with no verdict. Unblock, then stop.
  const t = setTimeout(() => {
    vm.done = true;
    if (vm.resolve) { vm.q.push(0); const r = vm.resolve; vm.resolve = null; r(); }
  }, timeout);
  await vm.run();
  clearTimeout(t);
  process.stderr.write(`steps ${vm.steps.toLocaleString()}\n`);
  process.stdout.write(captured);
})();
