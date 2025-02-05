import asyncio
import time
from asyncio import current_task
from sqlalchemy import select, or_, and_

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, async_scoped_session, AsyncSession

from core.settings import settings_db


class DataBaseHelper:
    def __init__(self, url: str, echo: bool = False, pool_size: int = 5):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            pool_size=pool_size,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    def get_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task
        )
        return session

    async def session_dependency(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session
            await session.close()

db_helper = DataBaseHelper(
    url=settings_db.get_db_url(),
    echo=settings_db.echo,
    pool_size=settings_db.pool_size
)

if __name__ == '__main__':
    from core.models.intersections import TrafficLightsObjects

    # stmt = "SELECT * FROM toolkit_trafficlightsobjects WHERE ip_adress = '10.45.154.16' OR ip_adress = '10.45.154.17'  OR ip_adress = '10.45.154.18' "
    stmt = "SELECT * FROM toolkit_trafficlightsobjects WHERE ip_adress = '10.45.154.1' OR ip_adress = '10.45.154.17'  OR ip_adress = '10.45.154.18' "
    stmt1_1 = "SELECT * FROM toolkit_trafficlightsobjects WHERE ip_adress = '10.45.154.16' "
    stmt1_2 = "SELECT * FROM toolkit_trafficlightsobjects WHERE ip_adress = '10.45.154.17' "
    stmt1_3 = "SELECT * FROM toolkit_trafficlightsobjects WHERE ip_adress = '10.45.154.18' "

    stmt__ = 'SELECT * FROM toolkit_trafficlightsobjects LIMIT 10'

    """ Один асинхронный запрос содержащий поиск нескольких хостов с сырым sql  """
    # async def get_multiple():
    #     start_time = time.time()
    #     async with db_helper.engine.connect() as conn:
    #         res = await conn.execute(text(stmt))
    #         print(f'final_time multiple: {time.time() - start_time}')
    #         for i in res:
    #
    #             print(f'i: {i}')
    # asyncio.run(get_multiple())

    """ Один асинхронный запрос содержащий поиск нескольких хостов с orm  """

    async def get_multiple():
        start_time = time.time()
        async with db_helper.engine.connect() as conn:
            stmt_ = select(TrafficLightsObjects).where(or_(
                TrafficLightsObjects.ip_adress == "10.45.154.16",
                TrafficLightsObjects.ip_adress == "10.45.154.1",
                TrafficLightsObjects.ip_adress == "10.45.154.17",
                TrafficLightsObjects.ip_adress == "10.45.154.18",

            ))

            res = await conn.execute(stmt_)
            print(type(res))
            r = res.mappings().all()

            print(f'final_time multiple: {time.time() - start_time}')
            for i in res:
                print(f'i: {i}')
            for i in r:
                print(f'i: {i}')
                print(f'i: {i.get("ip_adress")}')


    asyncio.run(get_multiple())


    """ Несколько асинхронных запросов  """
    #
    # print('-----------------------------------------')
    # time.sleep(3)

    # async def get_single():
    #     async with db_helper.engine.connect() as conn:
    #         start_time = time.time()
    #         async with asyncio.TaskGroup() as tg:
    #             res = [
    #                 tg.create_task(conn.execute(text(stmt1_1))),
    #                 tg.create_task(conn.execute(text(stmt1_2))),
    #                 tg.create_task(conn.execute(text(stmt1_3))),
    #             ]
    #         print(f'final_time single: {time.time() - start_time}')
    #         for i in res:
    #             print(f'i: {i}')
    # asyncio.run(get_single())