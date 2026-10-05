from __future__ import annotations

import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response

from .sfs_codec import SFSLong, build_server_frame, parse_client_frame
from .storage import load_state


router = APIRouter(tags=["MSM compatibility"])
TRACE: deque[dict[str, Any]] = deque(maxlen=200)


LOADING_STUB_COMMANDS = {
    "db_monster",
    "db_gene",
    "db_bakery_foods",
    "db_structure",
    "db_island_v2",
    "db_scratch_offs",
    "db_attuner_gene",
    "db_store_v2",
    "db_flexeggdefs",
    "db_battle",
    "db_battle_levels",
    "db_battle_monster_training",
    "db_battle_monster_actions",
    "db_battle_monster_stats",
    "db_battle_music",
    "db_costumes",
    "gs_timed_events",
    "gs_rare_monster_data",
    "gs_epic_monster_data",
    "gs_flip_boards",
    "gs_flip_levels",
    "gs_cant_breed",
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _trace(kind: str, name: str, **details: Any) -> None:
    TRACE.appendleft(
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "name": name,
            **_json_safe(details),
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


def _wire_player_payload() -> dict[str, Any]:
    state = load_state()
    return {
        "user_id": SFSLong(1),
        "user_game_id": "sandbox-player-1",
        "display_name": state.name,
        "level": 1,
        "coins": SFSLong(state.coins),
        "diamonds": state.diamonds,
        "food": SFSLong(state.food),
        "active_island": SFSLong(1),
        "islands": [
            {
                "user_island_id": SFSLong(1),
                "island_id": 1,
                "name": state.active_island,
                "monsters": [],
                "structures": [],
            }
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
            "access_token": "sandbox-local-token",
            "user_game_id": "sandbox-player-1",
            "account_id": "sandbox-account-1",
            "username": "Sandbox",
        }
    )


async def game_config(request: Request) -> JSONResponse:
    urls = _base_urls(request)
    _trace("http", "game_config", method=request.method, path=request.url.path, host=urls["host"])
    port = int(urls["port"])
    server_ip_descriptor = f"http|websocket|{urls['host']}|{port}"
    server = {
        "host": urls["host"],
        "server_ip": urls["host"],
        "serverIp": server_ip_descriptor,
        "port": port,
        "serverPort": port,
        "websocket": True,
        "websocketPort": port,
        "websocket_url": urls["ws"],
        "websocketUrl": urls["ws"],
        "websocket_path": "/msm/socket",
        "websocketPath": "/msm/socket",
        "zone": "MySingingMonsters",
        "secure": False,
    }
    return JSONResponse(
        {
            "ok": True,
            "server": server,
            "servers": [server],
            "content_url": f"{urls['http']}/content/",
            "contentUrl": f"{urls['http']}/content/",
            "client_version": "sandbox",
        }
    )


async def pregame_setup(request: Request) -> JSONResponse:
    urls = _base_urls(request)
    data = await _request_data(request)
    _trace("http", "pregame_setup", method=request.method, path=request.url.path, keys=sorted(data.keys()))
    port = int(urls["port"])
    descriptor = f"http|websocket|{urls['host']}|{port}"
    return JSONResponse(
        {
            "ok": True,
            "server_ip": urls["host"],
            "serverIp": descriptor,
            "server_port": port,
            "serverPort": port,
            "server": f"{urls['host']}:{port}",
            "websocket_url": urls["ws"],
            "websocketUrl": urls["ws"],
            "websocket_path": "/msm/socket",
            "websocketPath": "/msm/socket",
            "content_url": f"{urls['http']}/content/",
            "contentUrl": f"{urls['http']}/content/",
            "zone": "MySingingMonsters",
        }
    )


async def legacy_auth(request: Request) -> JSONResponse:
    urls = _base_urls(request)
    data = await _request_data(request)
    _trace("http", "legacy_auth", method=request.method, path=request.url.path, keys=sorted(data.keys()))
    return JSONResponse(
        {
            "ok": True,
            "bbbId": "1",
            "sessId": "sandbox-session",
            "username": "Sandbox",
            "password": "sandbox",
            "serverIp": urls["host"],
            "contentUrl": f"{urls['http']}/content/",
            "friends": [],
            "sync": [],
        }
    )


@router.get("/api/compat/status")
def compat_status() -> dict[str, Any]:
    return {
        "status": "ready",
        "protocol": "binary-sfs-v1",
        "auth": True,
        "pregame": True,
        "websocket": "/msm/socket",
        "binary_decode": True,
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


@router.api_route("/BlueBox/BlueBox.do", methods=["GET", "POST"])
async def bluebox_probe(request: Request) -> Response:
    _trace("http", "bluebox_probe", method=request.method, path=request.url.path)
    return Response(
        '<msg t="sys"><body action="apiOK" r="0"><ver v="2.13.0"/></body></msg>\x00',
        media_type="text/xml",
    )


@router.websocket("/msm/socket")
async def msm_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    client = websocket.client.host if websocket.client else "unknown"
    diagnostic = websocket.query_params.get("diagnostic") == "1"
    _trace("websocket", "connect", client=client, path=websocket.url.path, diagnostic=diagnostic)

    try:
        if diagnostic:
            await websocket.send_json(
                {
                    "type": "server_hello",
                    "server": "MSM Sandbox",
                    "protocol": "binary-sfs-v1",
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
                try:
                    frame = parse_client_frame(binary)
                except Exception as exc:
                    _trace(
                        "websocket",
                        "binary_parse_error",
                        client=client,
                        size=len(binary),
                        hex=binary[:96].hex(),
                        error=str(exc),
                    )
                    continue

                _trace(
                    "websocket",
                    "binary_command",
                    client=client,
                    size=len(binary),
                    request_id=frame.request_id,
                    command=frame.command,
                    params=frame.params,
                )

                if frame.command == "alive":
                    continue

                if frame.command == "USER_LOGIN":
                    payload = {
                        "data": {},
                        "success": True,
                        "user": str(
                            frame.params.get("user_game_id")
                            or frame.params.get("username")
                            or "sandbox-player-1"
                        ),
                    }
                    await websocket.send_bytes(build_server_frame("USER_LOGIN", payload))
                    _trace("websocket", "binary_response", command="USER_LOGIN", payload=payload)
                    continue

                if frame.command == "client_keep_alive":
                    await websocket.send_bytes(build_server_frame("client_keep_alive", {}))
                    _trace("websocket", "binary_response", command="client_keep_alive", payload={})
                    continue

                if frame.command == "gs_player":
                    payload = {"player_object": _wire_player_payload()}
                    await websocket.send_bytes(build_server_frame("gs_player", payload))
                    _trace("websocket", "binary_response", command="gs_player", payload=payload)
                    continue

                if frame.command in LOADING_STUB_COMMANDS:
                    await websocket.send_bytes(build_server_frame(frame.command, {}))
                    _trace("websocket", "binary_stub_response", command=frame.command, payload={})
                    continue

                _trace("websocket", "binary_unhandled", command=frame.command)
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

for path in ("/auth.php", "/auth.php/"):
    router.add_api_route(path, legacy_auth, methods=["GET", "POST"])
