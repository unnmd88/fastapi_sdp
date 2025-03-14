from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI
import uvicorn
from pysnmp.entity.engine import SnmpEngine

from core.models import Base, db_helper
from api_v1 import router as router_v1
from core.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router=router_v1, prefix=settings.api_v1_prefix)


@app.get('/')
def root():
    print(f'this:')
    return {
        'this': 'main_page'
    }

if __name__ == '__main__':
    uvicorn.run('main:app', port=8002, reload=True)