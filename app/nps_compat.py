from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response


router = APIRouter(tags=["NPS launcher compatibility"])

HTTP_PORT = 5050
WEBSOCKET_PORT = 8282
TCP_PORT = 9933
ZONE = "MySingingMonsters"
TOKEN = "sandbox-local-token"
ACCOUNT_ID = "1"
USER_GAME_ID = "sandbox-player-1"
USERNAME = "Sandbox"
EMAIL = "sandbox@local.invalid"
GAME_VERSION = "5.4.2"
ASSETS_VERSION = "494"


def _host(request: Request) -> str:
    value = request.headers.get("host", "127.0.0.1")
    if value.startswith("["):
        return value.split("]", 1)[0] + "]"
    return value.split(":", 1)[0] or "127.0.0.1"


def _connection_info(request: Request) -> dict[str, Any]:
    host = _host(request)
    descriptor = f"http|websocket|{host}|{WEBSOCKET_PORT}"
    websocket_url = f"ws://{host}:{WEBSOCKET_PORT}/msm/socket"
    bluebox_url = f"http://{host}:{WEBSOCKET_PORT}/BlueBox/BlueBox.do"

    return {
        "host": host,
        "ip": host,
        "address": host,
        "hostname": host,
        "serverAddress": host,
        "serverId": 1,
        "server_id": 1,
        "serverIp": descriptor,
        "serverIP": descriptor,
        "server_ip": descriptor,
        "serverHost": host,
        "server_host": host,
        "port": TCP_PORT,
        "serverPort": TCP_PORT,
        "server_port": TCP_PORT,
        "socketPort": TCP_PORT,
        "socket_port": TCP_PORT,
        "tcpPort": TCP_PORT,
        "tcp_port": TCP_PORT,
        "sfsHost": host,
        "sfs_host": host,
        "sfsIp": host,
        "sfs_ip": host,
        "sfsPort": TCP_PORT,
        "sfs_port": TCP_PORT,
        "zone": ZONE,
        "zoneName": ZONE,
        "zone_name": ZONE,
        "protocol": "websocket",
        "transport": "websocket",
        "connection": "websocket",
        "connectionType": "websocket",
        "connection_type": "websocket",
        "websocket": True,
        "webSocket": True,
        "use_websocket": True,
        "useWebSocket": True,
        "secure": False,
        "ssl": False,
        "tls": False,
        "websocketHost": host,
        "websocket_host": host,
        "wsHost": host,
        "ws_host": host,
        "websocketPort": WEBSOCKET_PORT,
        "websocket_port": WEBSOCKET_PORT,
        "wsPort": WEBSOCKET_PORT,
        "ws_port": WEBSOCKET_PORT,
        "websocketPath": "/msm/socket",
        "websocket_path": "/msm/socket",
        "websocketUrl": websocket_url,
        "websocket_url": websocket_url,
        "wsUrl": websocket_url,
        "ws_url": websocket_url,
        "bluebox": False,
        "blueBox": False,
        "useBlueBox": False,
        "blueboxHost": host,
        "bluebox_host": host,
        "blueboxPort": WEBSOCKET_PORT,
        "bluebox_port": WEBSOCKET_PORT,
        "httpPort": WEBSOCKET_PORT,
        "http_port": WEBSOCKET_PORT,
        "blueboxUrl": bluebox_url,
        "bluebox_url": bluebox_url,
    }


def _content_root(request: Request) -> str:
    return f"http://{_host(request)}:{HTTP_PORT}/MSM/GameAssets/"


def _login_types() -> list[dict[str, Any]]:
    return [
        {
            "type": "email",
            "login_type": "email",
            "auth_type": "email",
            "auto_create": False,
            "can_bind_to": True,
            "can_create": True,
            "enabled": True,
        }
    ]


def _account_entry() -> dict[str, Any]:
    return {
        "type": "email",
        "username": USERNAME,
        "userName": USERNAME,
        "email": EMAIL,
        "can_bind_to": True,
        "can_create": True,
        "auto_create": False,
    }


def _game_config(request: Request) -> dict[str, Any]:
    connection = _connection_info(request)
    content = _content_root(request)
    login_types = _login_types()
    return {
        "login_types": login_types,
        "loginConfigs": login_types,
        "login_configs": login_types,
        "type": "android",
        "platform": "android",
        "store": "android",
        "package": "com.bigbluebubble.singingmonsters.full",
        "game_version": GAME_VERSION,
        "client_version": GAME_VERSION,
        "assets_version": ASSETS_VERSION,
        "build": ASSETS_VERSION,
        "contentUrl": content,
        "content_url": content,
        "update_url": content,
        "download_url": content,
        "precheck": True,
        "precheck_required": True,
        "precheck_db": "db_precheck",
        "precheckDb": "db_precheck",
        "precheck_databases": ["db_precheck"],
        "precheckDatabases": ["db_precheck"],
        "startup_databases": ["db_precheck"],
        "startupDatabases": ["db_precheck"],
        "server": connection,
        "sfs": connection,
        "game_server": connection,
        "gameServer": connection,
        "smartfox": connection,
        "smartFox": connection,
        "connectionInfo": connection,
        "connection_info": connection,
        "socket": connection,
        "socketServer": connection,
        "socket_server": connection,
        "servers": [connection],
        "server_list": [connection],
        "serverList": [connection],
        "sfs_servers": [connection],
        "sfsServers": [connection],
        **connection,
    }


def _auth_payload(request: Request) -> dict[str, Any]:
    config = _game_config(request)
    account = _account_entry()
    payload = {
        "ok": True,
        "success": True,
        "status": "ok",
        "result": "ok",
        "verified": True,
        "allow": True,
        "connectionError": False,
        "access_token": TOKEN,
        "accessToken": TOKEN,
        "token": TOKEN,
        "token_type": "bearer",
        "sessId": "sandbox-session",
        "session_id": "sandbox-session",
        "account_id": ACCOUNT_ID,
        "userId": ACCOUNT_ID,
        "user_id": ACCOUNT_ID,
        "bbbId": ACCOUNT_ID,
        "bbbID": ACCOUNT_ID,
        "username": USERNAME,
        "userName": USERNAME,
        "email": EMAIL,
        "userEmail": EMAIL,
        "email_name": EMAIL,
        "type": "email",
        "login_type": "email",
        "auth_type": "email",
        "authType": "email",
        "loginMethod": "email",
        "platform": "android",
        "platform_type": "android",
        "anon": False,
        "guest": False,
        "found": True,
        "registered": True,
        "existing_account": True,
        "account_exists": True,
        "create_account": False,
        "needs_registration": False,
        "needs_password_reset": False,
        "auth_types": ["email"],
        "userGameId": USER_GAME_ID,
        "user_game_id": USER_GAME_ID,
        "existing_accounts": [account],
        "accounts": [account],
        "config": config,
        "game_config": config,
        "gameConfig": config,
        **config,
    }
    return payload


async def _request_data(request: Request) -> dict[str, Any]:
    data: dict[str, Any] = dict(request.query_params)
    try:
        form = await request.form()
        data.update({str(k): v for k, v in form.items()})
    except Exception:
        pass
    if data:
        return data
    try:
        raw = await request.body()
    except Exception:
        return data
    if not raw:
        return data
    text = raw.decode("utf-8", "replace")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            data.update(parsed)
    except Exception:
        pass
    return data


async def auth(request: Request) -> JSONResponse:
    await _request_data(request)
    response = JSONResponse(_auth_payload(request))
    response.headers["Authorization"] = f"Bearer {TOKEN}"
    return response


async def existing_accounts(request: Request) -> JSONResponse:
    await _request_data(request)
    account = _account_entry()
    return JSONResponse(
        {
            "ok": True,
            "success": True,
            "status": "ok",
            "found": True,
            "existing_account": True,
            "account_exists": True,
            "create_account": False,
            "connectionError": False,
            "can_create": True,
            "auto_create": False,
            "can_bind_to": ["email"],
            "isAvailable": True,
            "existing_accounts": [account],
            "accounts": [account],
            "login_types": ["email"],
        }
    )


async def game_config(request: Request) -> JSONResponse:
    await _request_data(request)
    return JSONResponse(_auth_payload(request))


async def pregame(request: Request) -> JSONResponse:
    await _request_data(request)
    payload = _auth_payload(request)
    content = _content_root(request)
    payload.update(
        {
            "contentUrl": content,
            "content_url": content,
            "update_url": content,
            "download_url": content,
            "contentServer": content,
            "force_update": False,
            "maintenance": False,
            "min_version": "1.0.0",
        }
    )
    return JSONResponse(payload)


async def waf(request: Request) -> JSONResponse:
    await _request_data(request)
    return JSONResponse(
        {
            "ok": True,
            "success": True,
            "status": "ok",
            "challenge": {"type": "none", "required": False},
            "challengeRequired": False,
            "captcha": False,
            "token": TOKEN,
            "aws-waf-token": TOKEN,
            "wafToken": TOKEN,
        }
    )


async def bluebox_probe(request: Request) -> Response:
    return Response(
        '<msg t="sys"><body action="apiOK" r="0"><ver v="2.13.0"/></body></msg>\x00',
        media_type="text/xml",
    )


@router.get("/api/compat/nps")
def nps_status(request: Request) -> dict[str, Any]:
    host = _host(request)
    return {
        "status": "ready",
        "mode": "nps-custom-server",
        "custom_host": host,
        "auth_url": f"http://{host}:{HTTP_PORT}",
        "websocket_url": f"ws://{host}:{WEBSOCKET_PORT}/msm/socket",
        "http_port": HTTP_PORT,
        "websocket_port": WEBSOCKET_PORT,
        "game_port": TCP_PORT,
    }


@router.api_route("/content/files.json", methods=["GET", "POST"])
@router.api_route("/MSM/GameAssets/files.json", methods=["GET", "POST"])
async def empty_files_manifest() -> JSONResponse:
    return JSONResponse([])


@router.api_route("/content/downloads.xml", methods=["GET", "POST"])
@router.api_route("/MSM/GameAssets/downloads.xml", methods=["GET", "POST"])
async def empty_downloads_manifest() -> Response:
    xml = f'<?xml version="1.0"?><Downloads version="{GAME_VERSION}" build="{ASSETS_VERSION}"></Downloads>'
    return Response(xml, media_type="application/xml")


for path in (
    "/auth/api/token",
    "/auth/api/token/",
    "/auth/api/anon_account",
    "/auth/api/anon_account/",
    "/auth/api/steam_account",
    "/auth/api/steam_account/",
):
    router.add_api_route(path, auth, methods=["GET", "POST"])

for path in ("/auth/api/login", "/auth/api/login/"):
    router.add_api_route(path, auth, methods=["GET", "POST"])

for path in ("/auth/api/existing_accounts", "/auth/api/existing_accounts/"):
    router.add_api_route(path, existing_accounts, methods=["GET", "POST"])

for path in (
    "/auth/api/find_account",
    "/auth/api/find_account/",
):
    router.add_api_route(path, auth, methods=["GET", "POST"])

for path in ("/auth/api/game_config", "/auth/api/game_config/"):
    router.add_api_route(path, game_config, methods=["GET", "POST"])

for path in ("/pregame_setup.php", "/pregame_setup", "/auth/pregame_setup.php"):
    router.add_api_route(path, pregame, methods=["GET", "POST"])

for path in ("/waf", "/waf/", "/challenge", "/challenge/", "/token", "/token/"):
    router.add_api_route(path, waf, methods=["GET", "POST", "PUT"])

for path in ("/BlueBox/BlueBox.do", "/msm/socket"):
    router.add_api_route(path, bluebox_probe, methods=["GET", "POST"])
