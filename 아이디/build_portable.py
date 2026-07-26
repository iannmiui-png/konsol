#!/usr/bin/env python3
"""
build_portable.py [source.png] [out.html]

Produces a single self-contained page: the PNG is embedded once as base64
and used twice -- decoded into the Aheui program that runs, and rendered
as the page background. The bytes you are looking at are the bytes being
executed.

Defaults: lost_kingdom_pure_aheui.png -> lost_kingdom_portable.html
"""
import base64
import sys

TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{background:#0d0d10 top center/1067px auto repeat-y fixed;
     font:13px/1.5 'D2Coding',Consolas,monospace;color:#e8e8e8;
     display:flex;align-items:center;justify-content:center;padding:16px}
#panel{width:min(860px,100%);max-height:94vh;display:flex;flex-direction:column;
       background:rgba(12,12,16,.90);border:1px solid #6b6b5c;
       box-shadow:0 0 0 1px rgba(0,0,0,.6),0 8px 40px rgba(0,0,0,.7);backdrop-filter:blur(2px)}
#top{background:linear-gradient(#2b2b25,#1c1c18);border-bottom:1px solid #6b6b5c;
     padding:7px 11px;display:flex;justify-content:space-between;align-items:baseline;gap:10px}
#top b{color:#e6d9a8;font-size:14px;letter-spacing:.3px}
#top i{color:#8e8e7e;font-style:normal;font-size:11px}
#term{flex:1;overflow-y:auto;padding:11px 13px;white-space:pre-wrap;word-wrap:break-word;min-height:340px}
#term .e{color:#7fc4ff}
#term .m{color:#8e8e7e}
#bot{display:flex;border-top:1px solid #6b6b5c;background:rgba(20,20,24,.9)}
#bot span{padding:7px 4px 7px 11px;color:#e6d9a8;font-weight:bold}
#cmd{flex:1;background:transparent;border:0;outline:0;color:#7fc4ff;
     font:13px/1.5 'D2Coding',Consolas,monospace;padding:7px 11px 7px 4px}
#bar{display:flex;justify-content:space-between;padding:3px 11px;font-size:10.5px;
     color:#8e8e7e;background:rgba(8,8,10,.9);border-top:1px solid #3a3a33}
</style>
</head>
<body>
<div id="panel">
  <div id="top"><b>__TITLE__</b><i id="stat">시작하는 중…</i></div>
  <div id="term"></div>
  <div id="bot"><span>&gt;</span><input id="cmd" autocomplete="off" disabled placeholder="로딩 중…"></div>
  <div id="bar"><span id="steps">걸음: 0</span><span>(C) Jon Ripley 2004, 2005 — Aheui edition</span></div>
</div>
<script>
// The page background and the running program are the same bytes.
const PNG_B64="__B64__";
const ALPHABET="__ALPHA__";
const TERM_DIGIT=39,BASE=40,HBASE=0xAC00;
const STROKES=[0,2,4,4,2,5,5,3,5,7,9,9,7,9,9,8,4,4,6,2,4,0,3,4,3,4,4,0];

const termEl=document.getElementById('term'),cmdEl=document.getElementById('cmd'),
      statEl=document.getElementById('stat'),stepEl=document.getElementById('steps');
function say(t,c){const s=document.createElement('span');if(c)s.className=c;s.textContent=t;
  termEl.appendChild(s);termEl.scrollTop=termEl.scrollHeight;}
const status=t=>statEl.textContent=t;
const yieldUI=()=>new Promise(r=>setTimeout(r,0));
function b64bytes(b64){const s=atob(b64),a=new Uint8Array(s.length);
  for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a;}

// PNG decoded by hand: canvas would premultiply alpha and destroy the residues.
async function decodePNG(bytes){
  let off=8,W=0,H=0,ch=4;const idat=[];
  while(off<bytes.length){
    const dv=new DataView(bytes.buffer,bytes.byteOffset+off,8),len=dv.getUint32(0);
    const type=String.fromCharCode(bytes[off+4],bytes[off+5],bytes[off+6],bytes[off+7]);
    const data=bytes.subarray(off+8,off+8+len);
    if(type==='IHDR'){const h=new DataView(data.buffer,data.byteOffset,data.length);
      W=h.getUint32(0);H=h.getUint32(4);const ct=data[9];
      ch=ct===6?4:ct===2?3:ct===4?2:1;}
    else if(type==='IDAT')idat.push(data);
    else if(type==='IEND')break;
    off+=12+len;
  }
  let n=0;for(const c of idat)n+=c.length;
  const comp=new Uint8Array(n);let p=0;for(const c of idat){comp.set(c,p);p+=c.length;}
  const ds=new DecompressionStream('deflate'),wr=ds.writable.getWriter();
  wr.write(comp);wr.close();
  const rd=ds.readable.getReader(),parts=[];let tot=0;
  for(;;){const{done,value}=await rd.read();if(done)break;parts.push(value);tot+=value.length;}
  const dec=new Uint8Array(tot);p=0;for(const c of parts){dec.set(c,p);p+=c.length;}
  const stride=W*ch,raw=new Uint8Array(W*H*ch);let s=0;
  for(let y=0;y<H;y++){
    const f=dec[s++],o=y*stride;
    for(let x=0;x<stride;x++){
      const cur=dec[s++],a=x>=ch?raw[o+x-ch]:0,b=y>0?raw[o-stride+x]:0,
            c2=(x>=ch&&y>0)?raw[o-stride+x-ch]:0;let v;
      switch(f){
        case 0:v=cur;break;
        case 1:v=(cur+a)&255;break;
        case 2:v=(cur+b)&255;break;
        case 3:v=(cur+((a+b)>>1))&255;break;
        case 4:{const pp=a+b-c2,pa=Math.abs(pp-a),pb=Math.abs(pp-b),pc=Math.abs(pp-c2);
          v=(cur+((pa<=pb&&pa<=pc)?a:(pb<=pc)?b:c2))&255;break;}
        default:v=cur;
      }
      raw[o+x]=v;
    }
  }
  return raw;
}

// Rows are stored right-stripped; a cell past a row's end reads blank, which
// is equivalent to padding the grid without paying for it.
function buildGrid(raw){
  const NL=0;let end=raw.length;
  for(let i=0;i<raw.length;i++)if(raw[i]%BASE===TERM_DIGIT){end=i;break;}
  let rows=0;for(let i=0;i<end;i++)if(raw[i]%BASE===NL)rows++;
  const rowStart=new Int32Array(rows),rowLen=new Uint16Array(rows),data=new Uint8Array(end-rows);
  let r=0,w=0,st=0,W=0;
  for(let i=0;i<end;i++){
    const d=raw[i]%BASE;
    if(d===NL){rowStart[r]=st;rowLen[r]=w-st;if(w-st>W)W=w-st;st=w;r++;}
    else data[w++]=d;
  }
  const cho=new Int8Array(ALPHABET.length).fill(-1),
        ju=new Uint8Array(ALPHABET.length),jo=new Uint8Array(ALPHABET.length);
  for(let i=0;i<ALPHABET.length;i++){
    const o=ALPHABET.charCodeAt(i)-HBASE;
    if(o>=0&&o<19*21*28){cho[i]=(o/588)|0;ju[i]=((o%588)/28)|0;jo[i]=o%28;}
  }
  return{data,rowStart,rowLen,rows,W,cho,ju,jo};
}

// Blank cells are no-ops, so a run of them can be jumped in one hop.
// Only sparse columns get a table; dense ones glide a cell or two anyway.
function buildSkip(g){
  const{rows,W,cho,data,rowStart,rowLen}=g;
  const cell=(x,y)=>x<rowLen[y]?data[rowStart[y]+x]:1;
  const tab=new Array(W).fill(null);
  for(let x=0;x<W;x++){
    let n=0;for(let y=0;y<rows;y++)if(cho[cell(x,y)]>=0)n++;
    if(n>rows*0.3||n===0)continue;
    const a=new Int32Array(n);let k=0;
    for(let y=0;y<rows;y++)if(cho[cell(x,y)]>=0)a[k++]=y;
    tab[x]=a;
  }
  return tab;
}

class AheuiVM{
  constructor(g,skip){
    this.g=g;this.skip=skip;this.st=[];for(let i=0;i<28;i++)this.st.push([]);
    this.cur=0;this.x=0;this.y=0;this.dx=1;this.dy=0;
    this.steps=0;this.out='';this.q=[];this.resolve=null;this.done=false;
  }
  cell(x,y){const g=this.g;return x<g.rowLen[y]?g.data[g.rowStart[y]+x]:1;}
  feed(l){for(const c of l)this.q.push(c.charCodeAt(0));this.q.push(10);
    if(this.resolve){const r=this.resolve;this.resolve=null;r();}}
  async getChar(){
    if(this.q.length)return this.q.shift();
    if(this.out){say(this.out);this.out='';}
    cmdEl.disabled=false;cmdEl.placeholder='명령어 입력…';cmdEl.focus();status('입력 대기');
    await new Promise(r=>this.resolve=r);
    return this.q.shift();
  }
  advance(){const g=this.g;this.x+=this.dx;this.y+=this.dy;
    if(this.y<0)this.y=g.rows-1;else if(this.y>=g.rows)this.y=0;
    if(this.x<0)this.x=g.W-1;else if(this.x>=g.W)this.x=0;}
  async run(){
    const g=this.g,cho=g.cho,ju=g.ju,jo=g.jo,BATCH=3000000;
    while(!this.done){
      let left=BATCH;
      while(left-->0){
        const s=this.cell(this.x,this.y),c=cho[s];
        this.steps++;
        if(c<0){
          let n=4,moved=false;
          while(n-->0){this.advance();if(cho[this.cell(this.x,this.y)]>=0){moved=true;break;}}
          if(moved)continue;
          const t=(this.dx===0&&this.dy!==0)?this.skip[this.x]:null;
          if(t&&Math.abs(this.dy)===1){
            let lo=0,hi=t.length-1,res=-1;
            if(this.dy>0){
              while(lo<=hi){const m=(lo+hi)>>1;if(t[m]>this.y){res=t[m];hi=m-1;}else lo=m+1;}
              this.y=res>=0?res:t[0];
            }else{
              while(lo<=hi){const m=(lo+hi)>>1;if(t[m]<this.y){res=t[m];lo=m+1;}else hi=m-1;}
              this.y=res>=0?res:t[t.length-1];
            }
          }else this.advance();
          continue;
        }
        const v=ju[s],j=jo[s];
        if(v===0){this.dx=1;this.dy=0;}
        else if(v===2){this.dx=2;this.dy=0;}
        else if(v===4){this.dx=-1;this.dy=0;}
        else if(v===6){this.dx=-2;this.dy=0;}
        else if(v===8){this.dx=0;this.dy=-1;}
        else if(v===12){this.dx=0;this.dy=-2;}
        else if(v===13){this.dx=0;this.dy=1;}
        else if(v===17){this.dx=0;this.dy=2;}
        else if(v===18)this.dy=-this.dy;
        else if(v===19){this.dx=-this.dx;this.dy=-this.dy;}
        else if(v===20)this.dx=-this.dx;
        let ok=true;const S=this.st[this.cur];
        switch(c){
          case 2:if(S.length<2)ok=false;else{const a=S.pop(),b=S.pop();S.push(a===0?0:Math.trunc(b/a));}break;
          case 3:if(S.length<2)ok=false;else{const a=S.pop();S[S.length-1]+=a;}break;
          case 4:if(S.length<2)ok=false;else{const a=S.pop();S[S.length-1]*=a;}break;
          case 5:if(S.length<2)ok=false;else{const a=S.pop(),b=S.pop();S.push(a===0?0:((b%a)+a)%a);}break;
          case 6:if(!S.length)ok=false;else{const n=this.cur===21?S.shift():S.pop();
            if(j===21)this.out+=String(n);else if(j===27)this.out+=String.fromCharCode(n);}break;
          case 7:if(j===27){if(this.out){say(this.out);this.out='';}S.push(await this.getChar());
              cmdEl.disabled=true;cmdEl.placeholder='실행 중…';status('실행 중');}
            else if(j!==21)S.push(STROKES[j]);break;
          case 8:if(!S.length)ok=false;else S.push(this.cur===21?S[0]:S[S.length-1]);break;
          case 9:this.cur=j;break;
          case 10:if(!S.length)ok=false;else{const n=this.cur===21?S.shift():S.pop();
            if(j!==27)this.st[j].push(n);}break;
          case 12:if(S.length<2)ok=false;else{const a=S.pop(),b=S.pop();S.push(b>=a?1:0);}break;
          case 14:if(!S.length)ok=false;else{const n=this.cur===21?S.shift():S.pop();
            if(n===0){this.dx=-this.dx;this.dy=-this.dy;}}break;
          case 15:if(S.length<2)ok=false;else{const t=S[S.length-1];S[S.length-1]=S[S.length-2];S[S.length-2]=t;}break;
          case 16:if(S.length<2)ok=false;else{const a=S.pop();S[S.length-1]-=a;}break;
          case 17:if(!S.length)ok=false;else{const n=this.cur===21?S[0]:S[S.length-1];
            if(j!==27)this.st[j].push(n);}break;
          case 18:this.done=true;break;
        }
        if(this.done)break;
        if(!ok){this.dx=-this.dx;this.dy=-this.dy;}
        this.advance();
      }
      if(this.out){say(this.out);this.out='';}
      stepEl.textContent='걸음: '+this.steps.toLocaleString();
      await yieldUI();
    }
    if(this.out){say(this.out);this.out='';}
    status('프로그램 종료');cmdEl.placeholder='종료됨';cmdEl.disabled=true;
  }
}

let vm=null;
cmdEl.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&vm&&!vm.done){
    const v=cmdEl.value;cmdEl.value='';
    say(v+'\n','e');cmdEl.disabled=true;cmdEl.placeholder='실행 중…';vm.feed(v);
  }
});

async function boot(){
  // one blob, two jobs: the wallpaper is the program
  document.body.style.backgroundImage='url(data:image/png;base64,'+PNG_B64+')';
  status('배경 이미지 디코딩 중…');await yieldUI();
  const raw=await decodePNG(b64bytes(PNG_B64));
  status('아희 격자 복원 중…');await yieldUI();
  const g=buildGrid(raw);
  say(`배경 이미지에서 아희 격자 ${g.rows.toLocaleString()}행 × ${g.W}열 복원\n`,'m');
  status('스킵 테이블 생성 중…');await yieldUI();
  const skip=buildSkip(g);
  say(`스킵 테이블 ${skip.filter(Boolean).length}/${g.W}개 열\n\n`,'m');
  status('실행 중');await yieldUI();
  vm=new AheuiVM(g,skip);
  vm.run();
}
boot();
</script>
</body>
</html>
"""


def build(src='lost_kingdom_pure_aheui.png',
          out='lost_kingdom_portable.html',
          title='잃어버린 왕국 · 아희',
          alphabet='aheui_alphabet.txt'):
    b64 = base64.b64encode(open(src, 'rb').read()).decode('ascii')
    # The alphabet MUST come from the build that produced this PNG. It was
    # hardcoded once; then a change to the compiler's input block swapped two
    # syllables, every index past 9 shifted, and the page silently decoded
    # garbage. Inject it instead.
    alpha = open(alphabet, encoding='utf-8').read()
    alpha_js = ''.join('\\n' if c == '\n' else c if c == ' ' else
                       '\\u%04X' % ord(c) for c in alpha)
    html = (TEMPLATE
            .replace('__B64__', b64)
            .replace('__ALPHA__', alpha_js)
            .replace('__TITLE__', title))
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    return len(b64), len(html)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'lost_kingdom_pure_aheui.png'
    out = sys.argv[2] if len(sys.argv) > 2 else 'lost_kingdom_portable.html'
    nb, nh = build(src, out)
    print(f'{src} -> {out}')
    print(f'  base64 {nb:,} chars, page {nh:,} bytes ({nh/1e6:.2f} MB)')
