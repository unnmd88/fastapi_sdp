from fastapi import APIRouter

from .controller_management.views import router as intersections_router

router = APIRouter()
router.include_router(router=intersections_router, prefix='/intersection')
