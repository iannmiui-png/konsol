// Verifies the stop control actually halts a runaway grid: the alphabet file
// is a valid Aheui grid with no halt instruction.
const fs = require('fs');
const html = fs.readFileSync('aheui_console.html', 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));
let handlers = {};
function mkEl(id) {
  return { id, textContent: '', value: '', placeholder: '', disabled: false, src: '', href: '',
    download: '', scrollTop: 0, scrollHeight: 0, className: '', style: {},
    classList: { toggle() {}, add() {}, remove() {} }, appendChild() {},
    addEventListener(ev, fn) { handlers[id + ':' + ev] = fn; }, focus() {} };
}
const els = {};
global.document = { body: { style: {} }, getElementById: id => (els[id] ||= mkEl(id)),
  createElement: () => ({ textContent: '', className: '' }) };
global.location = { protocol: 'file:' };
global.Blob = class { constructor(p) { this.p = p; } };
global.URL = { createObjectURL: () => 'blob:stub' };
const api = new Function(`${script}\nreturn { load, getVM: () => vm };`)();

(async () => {
  api.load(new Uint8Array(fs.readFileSync('aheui_alphabet.txt')), 'aheui_alphabet.txt');
  await new Promise(r => setTimeout(r, 1500));
  const before = api.getVM() ? api.getVM().steps : 0;
  handlers['stop:click']();                       // the user presses 중지
  await new Promise(r => setTimeout(r, 1500));
  const vm = api.getVM();
  console.log(`ran to ${before.toLocaleString()} steps, then stop pressed`);
  console.log(`done flag        : ${vm.done}`);
  console.log(`status           : ${els.stat.textContent}`);
  console.log(`stop re-disabled : ${els.stop.disabled}`);
  process.exit(0);
})();
