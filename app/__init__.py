from .compat import LOADING_STUB_COMMANDS, router as compat_router
from .nps_compat import router as nps_router
from .test_client import router as test_client_router

# NPS duplicates a few HTTP paths that the generic compatibility layer also
# exposes. Put its stricter launcher-shaped responses first while keeping the
# existing generic endpoints and developer test client available afterwards.
compat_router.routes = [*nps_router.routes, *compat_router.routes]
compat_router.include_router(test_client_router)

# The launcher advertises a precheck database during startup. We intentionally
# answer these with empty SFS payloads until the client tells us which fields it
# truly needs. This keeps the sandbox independent from extracted game data.
LOADING_STUB_COMMANDS.update({"db_precheck", "game_settings", "gs_initialized"})
