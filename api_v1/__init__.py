from fastapi import APIRouter

from core.settings import settings
from .controller_management.views import router as intersections_router

router = APIRouter()
# router.include_router(router=intersections_router, prefix='/traffic-lights')
router.include_router(router=intersections_router, prefix=settings.traffic_lights_prefix)
