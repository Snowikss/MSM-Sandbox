from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Test client"])

CLIENT_HTML = r"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>MSM Sandbox Client</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
    * { box-sizing:border-box; }
    body { margin:0; background:#0b0f14; color:#eef3f8; }
    main { max-width:820px; margin:auto; padding:20px 14px 48px; }
    h1 { margin:0 0 4px; }
    .muted { color:#96a2b2; }
    .ok { color:#8ce99a; }
    .bad { color:#ff8787; }
    .card { background:#161c24; border:1px solid #2a3442; border-radius:18px; padding:15px; margin-top:12px; }
    .row { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
    button { border:1px solid #435168; background:#222b37; color:#fff; border-radius:12px; padding:11px 15px; font-weight:650; }
    button:disabled { opacity:.5; }
    code, pre { white-space:pre-wrap; word-break:break-word; }
    .stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
    .stat { background:#10151c; border-radius:12px; padding:10px; text-align:center; }
    .island { position:relative; overflow:hidden; min-height:300px; margin-top:12px; border-radius:20px; background:linear-gradient(#172939 0 48%,#193728 48% 100%); border:1px solid #334353; touch-action:none; }
    .ground { position:absolute; width:115%; height:68%; left:-7%; bottom:-30%; border-radius:50%; background:#294a31; border:1px solid #3e6848; pointer-events:none; }
    .island-title { position:absolute; left:14px; top:12px; z-index:3; padding:7px 10px; border-radius:10px; background:#10151ccc; pointer-events:none; }
    .move-status { position:absolute; right:14px; top:15px; z-index:3; font-size:12px; pointer-events:none; }
    .monster-dot { position:absolute; z-index:4; min-width:72px; padding:8px 10px; text-align:center; border-radius:14px; background:#202936ee; border:1px solid #526078; transform:translate(-50%,-50%); font-size:12px; cursor:grab; user-select:none; touch-action:none; box-shadow:0 6px 18px #0006; }
    .monster-dot b { display:block; font-size:13px; }
    .monster-dot.dragging { cursor:grabbing; border-color:#9ab2d4; transform:translate(-50%,-50%) scale(1.05); }
    .monster { padding:9px 0; border-top:1px solid #28313d; }
    @media (max-width:520px) { .stats { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<main>
  <h1>MSM Sandbox Client</h1>
  <div class="muted">Наш локальный мобильный клиент. Бинарный SFS загружает мир, а позиции монстров сохраняются на сервере.</div>

  <section class="card">
    <div class="row">
      <button id="run" onclick="runFlow()">Подключиться к миру</button>
      <span id="summary" class="muted">Ожидание подключения.</span>
    </div>
  </section>

  <section class="card">
    <b>Этапы подключения</b>
    <pre id="steps" class="muted">—</pre>
  </section>

  <section class="card" id="world" hidden>
    <div class="row">
      <b id="playerName">Sandbox</b>
      <span class="muted" id="protocolBadge"></span>
      <span class="muted">Перетаскивай монстров пальцем или мышкой.</span>
    </div>
    <div class="stats">
      <div class="stat"><div class="muted">Монеты</div><b id="coins">0</b></div>
      <div class="stat"><div class="muted">Алмазы</div><b id="diamonds">0</b></div>
      <div class="stat"><div class="muted">Еда</div><b id="food">0</b></div>
    </div>
    <div class="island" id="island">
      <div class="ground"></div>
      <div class="island-title" id="islandName">Plant Island</div>
      <div class="move-status muted" id="moveStatus"></div>
    </div>
  </section>

  <section class="card" id="monsterCard" hidden>
    <b>Монстры</b>
    <div id="monsters"></div>
  </section>
</main>
<script>
const steps = [];
const enc = new TextEncoder();
const dec = new TextDecoder();
let requestId = 1n;
let currentPlayer = null;

function log(text, ok=true) {
  steps.push((ok ? '✓ ' : '✗ ') + text);
  document.querySelector('#steps').textContent = steps.join('\n');
}

async function json(url, options={}) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

function concat(parts) {
  const size = parts.reduce((n,p)=>n+p.length,0);
  const out = new Uint8Array(size);
  let pos=0;
  for (const p of parts) { out.set(p,pos); pos += p.length; }
  return out;
}
function u8(v){ return Uint8Array.of(v & 255); }
function u16(v){ const b=new Uint8Array(2); new DataView(b.buffer).setUint16(0,v,false); return b; }
function i32(v){ const b=new Uint8Array(4); new DataView(b.buffer).setInt32(0,v,false); return b; }
function i64(v){ const b=new Uint8Array(8); new DataView(b.buffer).setBigInt64(0,BigInt(v),false); return b; }
function utf(s){ const r=enc.encode(String(s)); return concat([u16(r.length),r]); }

function encodeValue(type, value) {
  if (type===0) return new Uint8Array();
  if (type===1) return u8(value?1:0);
  if (type===4) return i32(value);
  if (type===5) return i64(value);
  if (type===8) return utf(value);
  if (type===17) {
    const parts=[u16(value.length)];
    for (const item of value) { const t=inferType(item); parts.push(u8(t),encodeValue(t,item)); }
    return concat(parts);
  }
  if (type===18) return encodeObjectBody(value);
  throw new Error('encode SFS type '+type+' пока не нужен');
}
function inferType(v) {
  if (v===null || v===undefined) return 0;
  if (typeof v==='boolean') return 1;
  if (typeof v==='bigint') return 5;
  if (Number.isInteger(v)) return 4;
  if (typeof v==='string') return 8;
  if (Array.isArray(v)) return 17;
  if (typeof v==='object') return 18;
  throw new Error('Неизвестный тип SFS');
}
function encodeObjectBody(obj) {
  const keys=Object.keys(obj); const parts=[u16(keys.length)];
  for (const key of keys) { const t=inferType(obj[key]); parts.push(utf(key),u8(t),encodeValue(t,obj[key])); }
  return concat(parts);
}
function encodeObject(obj) { return concat([u8(18),encodeObjectBody(obj)]); }
function buildClientFrame(command, params={}) {
  const cmd=enc.encode(command);
  const head=new Uint8Array(10);
  head[0]=0;
  new DataView(head.buffer).setBigInt64(1,requestId++,false);
  head[9]=cmd.length;
  return concat([head,cmd,encodeObject({data:params})]);
}

class Reader {
  constructor(bytes){ this.b=bytes; this.p=0; }
  take(n){ const x=this.b.slice(this.p,this.p+n); if(x.length!==n) throw new Error('Обрезанный SFS пакет'); this.p+=n; return x; }
  u8(){ return this.take(1)[0]; }
  u16(){ const x=this.take(2); return new DataView(x.buffer,x.byteOffset,2).getUint16(0,false); }
  i16(){ const x=this.take(2); return new DataView(x.buffer,x.byteOffset,2).getInt16(0,false); }
  i32(){ const x=this.take(4); return new DataView(x.buffer,x.byteOffset,4).getInt32(0,false); }
  i64(){ const x=this.take(8); return new DataView(x.buffer,x.byteOffset,8).getBigInt64(0,false); }
  f32(){ const x=this.take(4); return new DataView(x.buffer,x.byteOffset,4).getFloat32(0,false); }
  f64(){ const x=this.take(8); return new DataView(x.buffer,x.byteOffset,8).getFloat64(0,false); }
  utf(){ return dec.decode(this.take(this.u16())); }
}
function decodeValue(r,t) {
  if(t===0) return null;
  if(t===1) return r.u8()!==0;
  if(t===2) return (r.u8()<<24)>>24;
  if(t===3) return r.i16();
  if(t===4) return r.i32();
  if(t===5) return Number(r.i64());
  if(t===6) return r.f32();
  if(t===7) return r.f64();
  if(t===8) return r.utf();
  if(t===9) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(r.u8()!==0); return a; }
  if(t===10) return r.take(r.i32());
  if(t===11) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(r.i16()); return a; }
  if(t===12) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(r.i32()); return a; }
  if(t===13) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(Number(r.i64())); return a; }
  if(t===14) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(r.f32()); return a; }
  if(t===15) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(r.f64()); return a; }
  if(t===16) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(r.utf()); return a; }
  if(t===17) { const a=[]; for(let i=0,n=r.u16();i<n;i++) a.push(decodeValue(r,r.u8())); return a; }
  if(t===18) return decodeObjectBody(r);
  if(t===20) return dec.decode(r.take(r.i32()));
  throw new Error('Неизвестный SFS type '+t);
}
function decodeObjectBody(r) {
  const o={};
  for(let i=0,n=r.u16();i<n;i++){ const k=r.utf(); o[k]=decodeValue(r,r.u8()); }
  return o;
}
function decodeObject(bytes) {
  const r=new Reader(bytes); const root=r.u8(); if(root!==18) throw new Error('Корень не SFSObject'); return decodeObjectBody(r);
}
function parseServerFrame(buf) {
  const bytes=new Uint8Array(buf); const r=new Reader(bytes); const len=r.u16(); const cmd=dec.decode(r.take(len));
  const payload=r.p<bytes.length ? decodeObject(bytes.slice(r.p)) : {};
  return {command:cmd,payload};
}

function binarySession() {
  return new Promise((resolve,reject)=>{
    const scheme=location.protocol==='https:'?'wss':'ws';
    const ws=new WebSocket(`${scheme}://${location.host}/msm/socket`);
    ws.binaryType='arraybuffer';
    let stage='login';
    const timer=setTimeout(()=>{ ws.close(); reject(new Error('Binary WebSocket timeout')); },5000);
    ws.onopen=()=> ws.send(buildClientFrame('USER_LOGIN',{user_game_id:'sandbox-player-1',username:'Sandbox'}));
    ws.onmessage=e=>{
      try {
        if (!(e.data instanceof ArrayBuffer)) return;
        const frame=parseServerFrame(e.data);
        if(stage==='login' && frame.command==='USER_LOGIN') {
          log('Бинарный USER_LOGIN подтверждён');
          stage='player';
          ws.send(buildClientFrame('gs_player',{}));
          return;
        }
        if(stage==='player' && frame.command==='gs_player') {
          clearTimeout(timer); ws.close(); resolve(frame.payload.player_object || frame.payload);
        }
      } catch(err) { clearTimeout(timer); ws.close(); reject(err); }
    };
    ws.onerror=()=>{ clearTimeout(timer); reject(new Error('Binary WebSocket error')); };
  });
}

function clamp(v,min,max){ return Math.max(min,Math.min(max,v)); }

async function savePosition(monster, x, y) {
  const status=document.querySelector('#moveStatus');
  status.textContent='Сохраняю...';
  try {
    const result=await json(`/api/compat/monsters/${encodeURIComponent(monster.id)}/position`,{
      method:'PATCH',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({x,y})
    });
    monster.x=result.monster.x;
    monster.y=result.monster.y;
    status.className='move-status ok';
    status.textContent='Позиция сохранена ✓';
    setTimeout(()=>{ status.textContent=''; status.className='move-status muted'; },1200);
  } catch(error) {
    status.className='move-status bad';
    status.textContent='Не сохранилось';
  }
}

function attachDrag(dot, monster) {
  const island=document.querySelector('#island');
  let dragging=false;

  function moveFromEvent(event) {
    const rect=island.getBoundingClientRect();
    const x=clamp(((event.clientX-rect.left)/rect.width)*100,5,95);
    const y=clamp(((event.clientY-rect.top)/rect.height)*100,25,90);
    dot.style.left=x+'%';
    dot.style.top=y+'%';
    monster.x=x;
    monster.y=y;
  }

  dot.addEventListener('pointerdown',event=>{
    dragging=true;
    dot.classList.add('dragging');
    dot.setPointerCapture(event.pointerId);
    moveFromEvent(event);
  });
  dot.addEventListener('pointermove',event=>{
    if(dragging) moveFromEvent(event);
  });
  dot.addEventListener('pointerup',async event=>{
    if(!dragging) return;
    dragging=false;
    dot.classList.remove('dragging');
    moveFromEvent(event);
    await savePosition(monster,monster.x,monster.y);
    renderMonsterList(currentPlayer?.monsters || []);
  });
  dot.addEventListener('pointercancel',()=>{
    dragging=false;
    dot.classList.remove('dragging');
  });
}

function renderMonsterList(list) {
  const root=document.querySelector('#monsters');
  root.innerHTML='';
  if(!list.length) root.innerHTML='<span class="muted">Монстров нет.</span>';
  for(const m of list){
    const d=document.createElement('div');
    d.className='monster';
    d.textContent=`${m.species} · уровень ${m.level} · ${m.island} · ${m.x.toFixed(1)}%, ${m.y.toFixed(1)}%`;
    root.appendChild(d);
  }
}

function renderWorld(player, wirePlayer) {
  currentPlayer=player;
  document.querySelector('#world').hidden=false;
  document.querySelector('#monsterCard').hidden=false;
  document.querySelector('#playerName').textContent=player.display_name || 'Sandbox';
  document.querySelector('#protocolBadge').textContent='binary-sfs-v2';
  document.querySelector('#coins').textContent=wirePlayer?.coins ?? player.currencies?.coins ?? 0;
  document.querySelector('#diamonds').textContent=wirePlayer?.diamonds ?? player.currencies?.diamonds ?? 0;
  document.querySelector('#food').textContent=wirePlayer?.food ?? player.currencies?.food ?? 0;
  document.querySelector('#islandName').textContent=player.active_island?.name || 'Plant Island';

  const island=document.querySelector('#island');
  island.querySelectorAll('.monster-dot').forEach(x=>x.remove());
  const list=player.monsters || [];
  list.forEach((m,i)=>{
    if(typeof m.x!=='number') m.x=20+((i*31)%65);
    if(typeof m.y!=='number') m.y=56+((i*17)%24);
    const dot=document.createElement('div');
    dot.className='monster-dot';
    dot.style.left=m.x+'%';
    dot.style.top=m.y+'%';
    dot.innerHTML=`<b>${escapeHtml(m.species)}</b>ур. ${m.level}`;
    attachDrag(dot,m);
    island.appendChild(dot);
  });
  renderMonsterList(list);
}
function escapeHtml(v){ return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

async function runFlow() {
  const button=document.querySelector('#run'); const summary=document.querySelector('#summary');
  button.disabled=true; steps.length=0; document.querySelector('#steps').textContent='—';
  summary.className='muted'; summary.textContent='Подключаюсь...';
  try {
    const auth=await json('/auth/api/token',{method:'POST'});
    if(!auth.token && !auth.access_token) throw new Error('auth не вернул token');
    log('Auth token получен');

    const pregame=await json('/pregame_setup.php',{method:'POST'});
    if(!pregame.websocket_url) throw new Error('pregame не вернул websocket_url');
    log(`Pregame получен: ${pregame.websocket_url}`);

    const wirePlayer=await binarySession();
    log('gs_player получен и распарсен из бинарного SFSObject');
    const wireMonsters=wirePlayer?.islands?.[0]?.monsters || [];
    log(`Бинарный gs_player содержит монстров: ${wireMonsters.length}`);

    const player=await json('/api/compat/player');
    log(`Plant Island загружен: ${player.active_island?.name || '—'}`);
    log(`Монстров загружено: ${(player.monsters||[]).length}`);
    renderWorld(player,wirePlayer);

    summary.className='ok'; summary.textContent='Интерактивный клиент подключён ✓';
  } catch(error) {
    log(error.message || String(error),false);
    summary.className='bad'; summary.textContent='Подключение остановилось на ошибке.';
  } finally { button.disabled=false; }
}
</script>
</body>
</html>
"""


@router.get("/client", response_class=HTMLResponse)
def test_client() -> str:
    return CLIENT_HTML
