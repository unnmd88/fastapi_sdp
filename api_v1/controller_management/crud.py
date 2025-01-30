from sqlalchemy import select, text
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import TrafficLightsObjects


async def get_intersections(session: AsyncSession):
    stmt = select(TrafficLightsObjects)
    result: Result = await session.execute(stmt)
    intersections = result.scalars().all()
    return intersections

async def get_intersection(session: AsyncSession, ip, number):
    # if ip:
        # res = await session.get(TrafficLightsObjects, 150)
    #     res = await session.execute(select(TrafficLightsObjects).filter(TrafficLightsObjects.ip_adress == ip))
    #
    #     print(f'res: {res.scalars().first()}')
    #     # res = await session.get(TrafficLightsObjects, ip)
    # else:
    #     res = await session.execute(select(TrafficLightsObjects).filter(TrafficLightsObjects.number == number))
    #     print(f'res: {res}')
    # res = await session.execute(select(TrafficLightsObjects).order_by(TrafficLightsObjects.id).limit(2))
    res = await session.execute(text("SELECT * FROM toolkit_trafficlightsobjects WHERE number = '11' "))



    # res = await session.get(TrafficLightsObjects, 37)
    # print(f'type(res): {type(res)}')
    # print(f'(res): {res}')


    return res.first()