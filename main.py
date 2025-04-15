import time
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI, APIRouter
import uvicorn

from api_v1.controller_management import services
from api_v1.controller_management.crud.crud import HostPropertiesProcessors
from api_v1.controller_management.schemas import NumbersOrIpv4, ResponseSearchinDb, ResponseGetState
from core.models import Base, db_helper
from api_v1 import router as router_v1
from core.settings import settings


a_sess = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global a_sess
    a_sess =  aiohttp.ClientSession()
    async with db_helper.engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

routr = APIRouter(prefix=f'{settings.api_v1_prefix}{settings.traffic_lights_prefix}')

app = FastAPI(lifespan=lifespan)
app.include_router(router=router_v1, prefix=settings.api_v1_prefix)



@app.get('/')
def root():
    print(a_sess)

    return {
        'Message': 'Hello from monitoring and management api'
    }


@routr.get('/nu-i-nu')
def root():
    print(a_sess)

    return {
        'Message': 'Hello from monitoring and management api'
    }

app.include_router(routr)


if __name__ == '__main__':
    uvicorn.run('main:app', **settings.run_config_sdp.model_dump())
    # uvicorn.run('main:app', port=8001, reload=True)



"""

["11", "2390", "155", "2283", "2443", "2528", "2577", "2605", "2131", "214", "2470",  "2546", "218", "2202", "2424", "2448", "2461",
"259", "3061", "3271"]

["2390", "2031", "2378", "2470"]

"""