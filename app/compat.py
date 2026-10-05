from __future__ import annotations

import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .storage import load_state


router = APIRouter(tags=["MSM compatibility"])
TRACE: deque[dict[str, Any]] = deque(maxlen=200)


def _trace(kind: str, name: str, **details: Any) -> None:
    TRACE.appendleft(
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "name": name,
            **details,
        }
    )


def _host_from_request(request: Request) -> str:
    host = request.headers.get("host", "127.0.0.1:8000")
    return host.split(":", 1)[0] or "127.0.0.1"


def _base_urls(request: Request) -> dict[str, str]:
    host = _host_from_request(request)
    port = request.url.port or 8000
    return {
        "host": host,
        "port": str(port),
        "http": f"http://{host}:{port}",
        "ws": f"ws://{host}:{port}/msm/socket",
    }


def _player_payload() -> dict[str, Any]:
    state = load_state()
    return {
        "id": "sandbox-player-1",
        "user_game_id": "sandbox-player-1",
        "display_name": state.name,
        "level": 1,
        "currencies": {
            "coins": state.coins,
            "diamonds": state.diamonds,
            "food": state.food,
        },
        "active_island": {
            "id": 1,
            "name": state.active_island,
        },
        "timer_mode": state.timer_mode,
        "monsters": [
            {
                "id": monster.id,
                "species": monster.species,
                "level": monster.level,
                "island": monster.island,
            }
            for monster in state.monsters
        ],
    }


async def _request_data(request: Request) -> dict[str, Any]:
    data: dict[str, Any] = dict(request.query_params)
    try:
        body = await request.body()
    except Exception:
        body = b""

    if body:
        text = body.decode("utf-8", "replace")
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                data.update(parsed)
            else:
                data["body"] = parsed
        except Exception:
            data["body"] = text[:2000]
    return data


async def auth_token(request: Request) -> JSONResponse:
    data = await _request_data(request)
    _trace("http", "auth_token", method=request.method, path=request.url.path, keys=sorted(data.keys()))
    now = int(time.time())
    payload = {
        "ok": True,
        "token": "sandbox-local-token",
        "access_token": "sandbox-local-token",
        "token_type": "bearer",
        "account_id": "sandbox-account-1",
        "user_game_id": "sandbox-player-1",
        "username": "Sandbox",
        "time_created": now,
        "expires_at": now + 86400,
    }
    response = JSONResponse(payload)
    response.headers["Authorization"] = "Bearer sandbox-local-token"
    return response


async def auth_login(request: Request) -> JSONResponse:
    data = await _request_data(request)
    _trace("http", "auth_login", method=request.method, path=request.url.path, keys=sorted(data.keys()))
    return JSONResponse(
        {
            "ok": True,
            "token": "sandbox-local-token",
            "user_game_id": "sandbox-player-1",
            "account_id": "sandbox-account-1",
            "username": "Sandbox",
        }
    )


async def game_config(request: Request) -> JSONResponse:
    urls = _base_urls(request)
    _trace("http", "game_config", method=request.method, path=request.url.path, host=urls["host"])
    port = int(urls["port"])
    server = {
        "host": urls["host"],
        "server_ip": urls["host"],
        "port": port,
        "websocket": True,
        "websocket_url": urls["ws"],
        "websocket_path": "/msm/socket",
        "zone": "MySingingMonsters",
        "secure": False,
    }
    return JSONResponse(
        {
            "ok": True,
            "server": server,
            "servers": [server],
            "content_url": f"{urls['http']}/content/",
            "client_version": "sandbox",
        }
    )


async def pregame_setup(request: Request) -> JSONResponse:
    urls = _base_urls(request)
    data = await _request_data(request)
    _trace("http", "pregame_setup", method=request.method, path=request.url.path, keys=sorted(data.keys()))
    port = int(urls["port"])
    return JSONResponse(
        {
            "ok": True,
            "server_ip": urls["host"],
            "server_port": port,
            "server": f"{urls['host']}:{port}",
            "websocket_url": urls["ws"],
            "websocket_path": "/msm/socket",
            "content_url": f"{urls['http']}/content/",
            "zone": "MySingingMonsters",
        }
    )


@router.get("/api/compat/status")
def compat_status() -> dict[str, Any]:
    return {
        "status": "ready",
        "protocol": "diagnostic-v1",
        "auth": True,
        "pregame": True,
        "websocket": "/msm/socket",
        "captured_events": len(TRACE),
    }


@router.get("/api/compat/logs")
def compat_logs(limit: int = 50) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    return {"events": list(TRACE)[:limit]}


@router.delete("/api/compat/logs")
def clear_compat_logs() -> dict[str, Any]:
    TRACE.clear()
    return {"status": "cleared"}


@router.get("/api/compat/player")
def compat_player() -> dict[str, Any]:
    return _player_payload()


@router.websocket("/msm/socket")
async def msm_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    client = websocket.client.host if websocket.client else "unknown"
    _trace("websocket", "connect", client=client, path=websocket.url.path)

    # This hello is for our diagnostic client. A real MSM binary client can ignore it.
    try:
        await websocket.send_json(
            {
                "type": "server_hello",
                "server": "MSM Sandbox",
                "protocol": "diagnostic-v1",
            }
        )

        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            text = message.get("text")
            binary = message.get("bytes")

            if text is not None:
                _trace("websocket", "text", client=client, payload=text[:2000])
                try:
                    payload = json.loads(text)
                except Exception:
                    payload = {"command": text}

                command = str(payload.get("command") or payload.get("request") or "").strip()
                if command in {"ping", "alive"}:
                    await websocket.send_json({"type": "pong", "time": int(time.time() * 1000)})
                elif command in {"playerSync", "player_sync", "gs_player"}:
                    await websocket.send_json({"type": "playerSync", "player": _player_payload()})
                elif command in {"gameConfig", "game_config"}:
                    await websocket.send_json(
                        {
                            "type": "gameConfig",
                            "websocket_path": "/msm/socket",
                            "zone": "MySingingMonsters",
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "unhandled",
                            "command": command or None,
                            "captured": True,
                        }
                    )

            elif binary is not None:
                # Do not invent a binary reply. Capture the frame so we can implement
                # the real wire format once we know exactly what the test client sent.
                _trace(
                    "websocket",
                    "binary",
                    client=client,
                    size=len(binary),
                    hex=binary[:96].hex(),
                )
    except WebSocketDisconnect:
        pass
    finally:
        _trace("websocket", "disconnect", client=client)


for path in (
    "/auth/api/token",
    "/auth/api/token/",
    "/auth/api/anon_account",
    "/auth/api/anon_account/",
):
    router.add_api_route(path, auth_token, methods=["GET", "POST"])

for path in ("/auth/api/login", "/auth/api/login/"):
    router.add_api_route(path, auth_login, methods=["GET", "POST"])

for path in ("/auth/api/game_config", "/auth/api/game_config/"):
    router.add_api_route(path, game_config, methods=["GET", "POST"])

for path in (
    "/pregame_setup.php",
    "/pregame_setup",
    "/auth/pregame_setup.php",
):
    router.add_api_route(path, pregame_setup, methods=["GET", "POST"])
