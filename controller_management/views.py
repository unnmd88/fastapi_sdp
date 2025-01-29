from fastapi import APIRouter

from schemas import GetIntersectionData

router = APIRouter(prefix='/intersection', tags=['Controller-management'])

@router.post('/get-state')
def get_intersection_data(intersection: GetIntersectionData):
    return {
        'success': True,
        'ip': str(intersection.ipv4)
    }