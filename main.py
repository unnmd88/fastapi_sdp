from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from core.models import Base, db_helper
from controller_management.views import router as router_get_state

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router_get_state)

@app.get('/')
def root():
    print(f'this:')
    return {
        'this': 'main_page'
    }

if __name__ == '__main__':
    uvicorn.run('main:app', port=8001, reload=True)