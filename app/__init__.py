from .compat import router as compat_router
from .test_client import router as test_client_router

# Keep the standalone browser test client on the same compatibility router.
# app.main already mounts compat_router, so /client becomes available without
# coupling the test UI to the admin dashboard.
compat_router.include_router(test_client_router)
