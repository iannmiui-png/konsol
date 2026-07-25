// batchpage.js — feeds each test case's Brainfuck SOURCE to the console page,
// letting the page compile it, bake a PNG and run that PNG. Two things are
// checked per case: the program's output against a reference BF interpreter,
// and the PNG the page baked against the one bf_to_png.py baked from the same
// source. The page carries its own copy of the block tables, so "the two
// compilers still agree" is the thing most worth asserting.
const fs = require('fs');

const html = fs.readFileSync('aheui_console.html', 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));

let captured = '', madeBlob = null;
function mkEl(id) {
  return {
    id, textContent: '', value: '', placeholder: '', disabled: false, src: '', href: '',
    download: '', scrollTop: 0, scrollHeight: 0, className: '', files: [], style: {},
    classList: { toggle() {}, add() {}, remove() {} },
    appendChild(n) { if (id === 'term') captured += n.textContent; },
    addEventListener() {}, focus() {},
  };
}
global.document = {
  body: { style: {} },
  getElementById: (id => { const els = {}; return i => (els[i] ||= mkEl(i)); })(),
  createElement: () => ({ textContent: '', className: '' }),
};
global.location = { protocol: 'file:' };
global.Blob = class { constructor(parts) { madeBlob = parts[0]; } };
global.URL = { createObjectURL: () => 'blob:stub' };

const mkApi = () => new Function(
  `${script}\nreturn { load, decodePNG, ALPHABET, getVM: () => vm };`)();

// Two PNGs of the same grid need not be byte-identical -- image width and
// deflate settings are free choices -- so compare what a reader recovers.
async function gridOf(api, bytes) {
  const raw = await api.decodePNG(new Uint8Array(bytes));
  let s = '';
  for (const b of raw) {
    const r = b % 40;
    if (r === 39) break;
    s += api.ALPHABET[r];
  }
  return s;
}

async function runCase(c) {
  const api = mkApi();                       // fresh closure: resets vm state
  captured = ''; madeBlob = null;
  const queue = [...(c.input || '')].map(ch => ch.charCodeAt(0));
  let primed = false, eofs = 0;
  const pump = setInterval(() => {
    const vm = api.getVM();
    if (!vm) return;
    if (!primed) { primed = true; for (const ch of queue) vm.q.push(ch); for (let i = 0; i < 8; i++) vm.q.push(0); }
    // Feed a bounded run of EOFs, then let it block: a program that loops
    // on EOF would otherwise spin until the deadline and report a step count
    // that says nothing about the program.
    if (vm.resolve && eofs < 8) { eofs++; vm.q.push(0); const r = vm.resolve; vm.resolve = null; r(); }
  }, 2);
  const deadline = setTimeout(() => { const vm = api.getVM(); if (vm) vm.done = true; }, 15000);

  await api.load(new Uint8Array(fs.readFileSync(c.bfFile)), c.bfFile);
  for (;;) { const vm = api.getVM(); if (vm && vm.done) break; await new Promise(r => setTimeout(r, 5)); }
  clearInterval(pump); clearTimeout(deadline);

  // strip the page's own compile/decode chatter; keep the program's output
  const out = captured.replace(/^[\s\S]*?개 열\n\n/, '');
  const png = madeBlob ? Buffer.from(madeBlob) : null;
  const grid = png ? await gridOf(api, png) : null;
  return { out, grid };
}

(async () => {
  const cases = JSON.parse(fs.readFileSync('jstest/cases.json', 'utf8'));
  let pass = 0, samePng = 0;
  const fails = [];
  for (const c of cases) {
    let r;
    try { r = await runCase(c); }
    catch (e) { r = { out: '<ERR ' + e.message + '>', grid: null }; }
    if (r.out === c.expect) pass++;
    else fails.push({ bf: c.bf.slice(0, 50), expect: c.expect, got: r.out });
    if (r.grid !== null) {
      const api = mkApi();
      const want = await gridOf(api, fs.readFileSync(c.png));
      if (r.grid === want) samePng++;
      else if (fails.length < 4) fails.push({ bf: c.bf.slice(0, 50), expect: '<grid>', got: '<grid differs>' });
    }
  }
  console.log(`page compiler: ${pass}/${cases.length} outputs match reference BF`);
  console.log(`page compiler: ${samePng}/${cases.length} grids identical to bf_to_png.py's`);
  for (const f of fails.slice(0, 4)) {
    console.log('  FAIL', JSON.stringify(f.bf));
    console.log('    expect', JSON.stringify(f.expect));
    console.log('    got   ', JSON.stringify(f.got));
  }
})();
