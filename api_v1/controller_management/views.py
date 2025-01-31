from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from core.models import db_helper
from . import crud
from .schemas import TrafficLightsObjectsRequest, TrafficLightsObjectsResponce, GetStateRequest

router = APIRouter(tags=['Controller-management'])

@router.post('/get-test')
def get_intersection_data(intersection: TrafficLightsObjectsRequest):
    return {
        'success': True,
        'ip': str(intersection.ipv4)
    }


@router.post('/get-host', response_model=TrafficLightsObjectsResponce)
# @router.post('/get-host', response_model=list[TrafficLightsObjectsResponce])
async def get_intersection(
    intersection: TrafficLightsObjectsRequest,
    session: AsyncSession = Depends(db_helper.session_dependency)
):
    print(f'intersection: {intersection}')
    res = await crud.get_intersection(session=session, ip=intersection, number=intersection)

    print(f'res from view: {res._mapping}')

    print(f'type(res): {type(res)}')
    if res is not None:
        return res

    raise HTTPException (
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Хост {intersection} не найден в базе'
    )


@router.post('/get-state')
async def get_state(data: GetStateRequest):
    return {
        'test': 1
    }