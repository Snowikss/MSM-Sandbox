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
  <title>MSM Sandbox Test Client</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
    body { margin:0; background:#0d1015; color:#eef3f8; }
    main { max-width:760px; margin:auto; padding:22px 16px 48px; }
    .card { background:#171c24; border:1px solid #2a3340; border-radius:18px; padding:16px; margin-top:12px; }
    .row { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
    button { border:1px solid #3a4658; background:#222a35; color:#fff; border-radius:12px; padding:10px 14px; }
    button:disabled { opacity:.5; }
    .ok { color:#8ce99a; }
    .bad { color:#ff8787; }
    .muted { color:#96a2b2; }
    code, pre { white-space:pre-wrap; word-break:break-word; }
    .monster { padding:9px 0; border-top:1px solid #28313d; }
  </style>
</head>
<body>
<main>
  <h1>MSM Sandbox Test Client</h1>
  <div class="muted">Проверяет полный путь: auth → pregame → WebSocket → профиль → Plant Island.</div>

  <section class="card">
    <div class="row">
      <button id="run" onclick="runFlow()">Запустить тест клиента</button>
      <span id="summary" class="muted">Ожидание запуска.</span>
    </div>
  </section>

  <section class="card">
    <b>Этапы</b>
    <pre id="steps" class="muted">—</pre>
  </section>

  <section class="card">
    <b>Профиль</b>
    <div id="profile" class="muted">Пока не загружен.</div>
  </section>

  <section class="card">
    <b>Монстры</b>
    <div id="monsters" class="muted">Пока не загружены.</div>
  </section>
</main>
<script>
const steps = [];
function log(text, ok=true) {
  steps.push((ok ? '✓ ' : '✗ ') + text);
  document.querySelector('#steps').textContent = steps.join('\n');
}
async function json(url, options={}) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}
function wsProbe() {
  return new Promise((resolve, reject) => {
    const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${scheme}://${location.host}/msm/socket?diagnostic=1`);
    const timer = setTimeout(() => { ws.close(); reject(new Error('WebSocket timeout')); }, 3500);
    ws.onmessage = event => {
      clearTimeout(timer);
      try { resolve(JSON.parse(event.data)); }
      catch { resolve({raw:event.data}); }
      ws.close();
    };
    ws.onerror = () => { clearTimeout(timer); reject(new Error('WebSocket error')); };
  });
}
async function runFlow() {
  const button = document.querySelector('#run');
  const summary = document.querySelector('#summary');
  button.disabled = true;
  steps.length = 0;
  document.querySelector('#profile').textContent = 'Загрузка...';
  document.querySelector('#monsters').textContent = 'Загрузка...';
  summary.className = 'muted';
  summary.textContent = 'Проверяю...';
  try {
    const auth = await json('/auth/api/token', {method:'POST'});
    if (!auth.token && !auth.access_token) throw new Error('auth не вернул token');
    log('Auth token получен');

    const pregame = await json('/pregame_setup.php', {method:'POST'});
    if (!pregame.websocket_url) throw new Error('pregame не вернул websocket_url');
    log(`Pregame получен: ${pregame.websocket_url}`);

    const hello = await wsProbe();
    log(`WebSocket отвечает: ${hello.protocol || hello.type || 'ok'}`);

    const player = await json('/api/compat/player');
    log(`Профиль загружен: ${player.display_name}`);
    log(`Остров загружен: ${player.active_island?.name || 'неизвестно'}`);

    document.querySelector('#profile').innerHTML =
      `<div><b>${player.display_name}</b></div>` +
      `<div>Остров: ${player.active_island?.name || '—'}</div>` +
      `<div>Монеты: ${player.currencies?.coins ?? 0}</div>` +
      `<div>Алмазы: ${player.currencies?.diamonds ?? 0}</div>` +
      `<div>Еда: ${player.currencies?.food ?? 0}</div>`;

    const root = document.querySelector('#monsters');
    const list = player.monsters || [];
    root.innerHTML = list.length ? '' : '<span class="muted">Монстров нет.</span>';
    for (const m of list) {
      const div = document.createElement('div');
      div.className = 'monster';
      div.textContent = `${m.species} · уровень ${m.level} · ${m.island}`;
      root.appendChild(div);
    }
    log(`Монстров загружено: ${list.length}`);
    summary.className = 'ok';
    summary.textContent = 'Полный тест пройден ✓';
  } catch (error) {
    log(error.message || String(error), false);
    summary.className = 'bad';
    summary.textContent = 'Тест остановился на ошибке.';
  } finally {
    button.disabled = false;
  }
}
</script>
</body>
</html>
"""


@router.get("/client", response_class=HTMLResponse)
def test_client() -> str:
    return CLIENT_HTML
