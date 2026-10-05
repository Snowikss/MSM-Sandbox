from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .models import (
    CurrencyPatch,
    Monster,
    MonsterCreate,
    MonsterLevelPatch,
    PlayerState,
    TimerPatch,
)
from .storage import load_state, save_state


app = FastAPI(title="MSM Sandbox", version="0.1.0")
state: PlayerState = load_state()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/state", response_model=PlayerState)
def get_state() -> PlayerState:
    return state


@app.patch("/api/currencies", response_model=PlayerState)
def patch_currencies(payload: CurrencyPatch) -> PlayerState:
    updates = payload.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(state, key, value)
    save_state(state)
    return state


@app.patch("/api/timer", response_model=PlayerState)
def patch_timer(payload: TimerPatch) -> PlayerState:
    state.timer_mode = payload.mode
    save_state(state)
    return state


@app.post("/api/monsters", response_model=Monster, status_code=201)
def create_monster(payload: MonsterCreate) -> Monster:
    monster = Monster(
        species=payload.species.strip(),
        level=payload.level,
        island=payload.island.strip(),
    )
    state.monsters.append(monster)
    save_state(state)
    return monster


@app.patch("/api/monsters/{monster_id}/level", response_model=Monster)
def patch_monster_level(monster_id: str, payload: MonsterLevelPatch) -> Monster:
    for monster in state.monsters:
        if monster.id == monster_id:
            monster.level = payload.level
            save_state(state)
            return monster
    raise HTTPException(status_code=404, detail="Monster not found")


@app.delete("/api/monsters/{monster_id}", status_code=204)
def delete_monster(monster_id: str) -> None:
    for index, monster in enumerate(state.monsters):
        if monster.id == monster_id:
            state.monsters.pop(index)
            save_state(state)
            return None
    raise HTTPException(status_code=404, detail="Monster not found")


@app.post("/api/reset", response_model=PlayerState)
def reset_state() -> PlayerState:
    global state
    state = PlayerState()
    save_state(state)
    return state


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


DASHBOARD_HTML = r"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>MSM Sandbox</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
    body { margin: 0; background: #111318; color: #edf1f7; }
    main { max-width: 980px; margin: 0 auto; padding: 28px 18px 60px; }
    h1 { margin: 0 0 6px; }
    .muted { color: #9ba7b7; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(210px,1fr)); gap: 12px; margin: 22px 0; }
    .card { background: #1a1e26; border: 1px solid #2a303b; border-radius: 16px; padding: 16px; }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    input, select, button { border-radius: 10px; border: 1px solid #394151; background: #11151c; color: #edf1f7; padding: 9px 11px; }
    input { min-width: 0; flex: 1; }
    button { cursor: pointer; }
    button:hover { background: #232a35; }
    .danger { border-color: #7e3c48; }
    .monster { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center; padding: 10px 0; border-top: 1px solid #2a303b; }
    .monster:first-child { border-top: 0; }
    code { color: #b8c7ff; }
  </style>
</head>
<body>
<main>
  <h1>MSM Sandbox</h1>
  <div class="muted">Локальная тестовая панель. Никаких официальных аккаунтов и серверов.</div>

  <section class="grid">
    <div class="card"><b>Монеты</b><div class="row"><input id="coins" type="number" min="0"><button onclick="saveCurrencies()">Сохранить</button></div></div>
    <div class="card"><b>Алмазы</b><div class="row"><input id="diamonds" type="number" min="0"><button onclick="saveCurrencies()">Сохранить</button></div></div>
    <div class="card"><b>Еда</b><div class="row"><input id="food" type="number" min="0"><button onclick="saveCurrencies()">Сохранить</button></div></div>
  </section>

  <section class="card">
    <h2>Таймеры</h2>
    <div class="row">
      <select id="timer" onchange="saveTimer()">
        <option value="x1">Обычные x1</option>
        <option value="x10">Ускоренные x10</option>
        <option value="instant">Мгновенно</option>
      </select>
      <span class="muted">Сейчас это серверная настройка для будущей логики действий.</span>
    </div>
  </section>

  <section class="card" style="margin-top:12px">
    <h2>Монстры</h2>
    <div class="row">
      <input id="species" placeholder="Например, Entbrat">
      <input id="level" type="number" min="1" max="20" value="1" style="max-width:100px">
      <button onclick="addMonster()">Добавить</button>
    </div>
    <div id="monsterList" style="margin-top:14px"></div>
  </section>

  <section class="card" style="margin-top:12px">
    <div class="row">
      <button class="danger" onclick="resetState()">Сбросить тестовый мир</button>
      <span class="muted">API: <code>/docs</code></span>
    </div>
  </section>
</main>
<script>
let current = null;

async function request(url, options={}) {
  const response = await fetch(url, {headers: {'Content-Type': 'application/json'}, ...options});
  if (!response.ok && response.status !== 204) {
    throw new Error(await response.text());
  }
  return response.status === 204 ? null : response.json();
}

async function loadState() {
  current = await request('/api/state');
  document.querySelector('#coins').value = current.coins;
  document.querySelector('#diamonds').value = current.diamonds;
  document.querySelector('#food').value = current.food;
  document.querySelector('#timer').value = current.timer_mode;
  renderMonsters();
}

function renderMonsters() {
  const root = document.querySelector('#monsterList');
  root.innerHTML = '';
  for (const monster of current.monsters) {
    const row = document.createElement('div');
    row.className = 'monster';
    row.innerHTML = `
      <div><b>${escapeHtml(monster.species)}</b><div class="muted">${escapeHtml(monster.island)}</div></div>
      <input type="number" min="1" max="20" value="${monster.level}" style="width:75px" aria-label="Уровень">
      <button class="danger">Удалить</button>`;
    const levelInput = row.querySelector('input');
    levelInput.addEventListener('change', () => setMonsterLevel(monster.id, levelInput.value));
    row.querySelector('button').addEventListener('click', () => removeMonster(monster.id));
    root.appendChild(row);
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}

async function saveCurrencies() {
  current = await request('/api/currencies', {
    method: 'PATCH',
    body: JSON.stringify({
      coins: Number(document.querySelector('#coins').value),
      diamonds: Number(document.querySelector('#diamonds').value),
      food: Number(document.querySelector('#food').value)
    })
  });
  renderMonsters();
}

async function saveTimer() {
  current = await request('/api/timer', {
    method: 'PATCH',
    body: JSON.stringify({mode: document.querySelector('#timer').value})
  });
}

async function addMonster() {
  const species = document.querySelector('#species').value.trim();
  if (!species) return;
  await request('/api/monsters', {
    method: 'POST',
    body: JSON.stringify({species, level: Number(document.querySelector('#level').value), island: 'Plant Island'})
  });
  document.querySelector('#species').value = '';
  await loadState();
}

async function setMonsterLevel(id, level) {
  await request(`/api/monsters/${id}/level`, {
    method: 'PATCH',
    body: JSON.stringify({level: Number(level)})
  });
  await loadState();
}

async function removeMonster(id) {
  await request(`/api/monsters/${id}`, {method: 'DELETE'});
  await loadState();
}

async function resetState() {
  if (!confirm('Сбросить тестовый мир?')) return;
  current = await request('/api/reset', {method: 'POST'});
  await loadState();
}

loadState().catch(error => {
  document.body.innerHTML += `<pre>${escapeHtml(error.message)}</pre>`;
});
</script>
</body>
</html>
"""
