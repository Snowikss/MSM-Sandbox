from __future__ import annotations

import asyncio

import uvicorn

from .main import app


PORTS = (8000, 5050, 8282)


async def _serve(port: int) -> None:
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    await server.serve()


async def _main() -> None:
    tasks = [asyncio.create_task(_serve(port), name=f"uvicorn-{port}") for port in PORTS]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def main() -> None:
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
