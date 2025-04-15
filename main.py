from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from core.models import Base, db_helper
from api_v1 import router as router_v1
from core.settings import settings
from core.drivers import AsyncClientHTTP
from core.shared import HTTP_CLIENT_SESSIONS


@asynccontextmanager
async def lifespan(app: FastAPI):
    HTTP_CLIENT_SESSIONS[0] = AsyncClientHTTP()
    async with db_helper.engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    for identification, session in HTTP_CLIENT_SESSIONS.items():
        session.close()

# routr = APIRouter(prefix=f'{settings.api_v1_prefix}{settings.traffic_lights_prefix}')

app = FastAPI(lifespan=lifespan)
app.include_router(router=router_v1, prefix=settings.api_v1_prefix)


@app.get('/')
def root():
    # print(a_sess)
    return {'Message': 'Hello from monitoring and management api'}


# app.include_router(routr)

if __name__ == '__main__':
    uvicorn.run('main:app', **settings.run_config_sdp.model_dump())
    # uvicorn.run('main:app', port=8001, reload=True)



"""

["11", "2390", "155", "2283", "2443", "2528", "2577", "2605", "2131", "214", "2470",  "2546", "218", "2202", "2424", "2448", "2461",
"259", "3061", "3271"]

["2390", "2031", "2378", "2470"]

"""