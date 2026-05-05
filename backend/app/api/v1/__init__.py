from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.offers import router as offers_router
from app.api.v1.requests import router as requests_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.normative_files import router as normative_files_router
from app.api.v1.plans import router as plans_router
from app.api.v1.tg import router as tg_router
from app.api.v1.ws import router as ws_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
router.include_router(requests_router, tags=["requests"])
router.include_router(offers_router, tags=["offers"])
router.include_router(ws_router, tags=["ws"])
router.include_router(tg_router, tags=["legacy-telegram"])
router.include_router(feedback_router, tags=["feedback"])
router.include_router(normative_files_router, tags=["normative_files"])
router.include_router(dashboard_router, tags=["dashboard"])
router.include_router(plans_router, tags=["plans"])
