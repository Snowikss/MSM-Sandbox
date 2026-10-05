from .compat import router as compat_router
from .nps_compat import router as nps_router
from .test_client import router as test_client_router

# NPS duplicates a few HTTP paths that the generic compatibility layer also
# exposes. Put its stricter launcher-shaped responses first while keeping the
# existing generic endpoints and developer test client available afterwards.
compat_router.routes = [*nps_router.routes, *compat_router.routes]
compat_router.include_router(test_client_router)
