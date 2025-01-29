import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

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

db_helper = DataBaseHelper(
    url=settings_db.get_db_url(),
    echo=settings_db.echo,
    pool_size=settings_db.pool_size
)

if __name__ == '__main__':

    async def get():
        async with db_helper.engine.connect() as conn:
            res = await conn.execute(text('SELECT * FROM toolkit_trafficlightsobjects LIMIT 10'))
            for i in res:

                print(f'i: {i}')
    asyncio.run(get())
