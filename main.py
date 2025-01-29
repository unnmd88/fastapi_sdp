from dotenv import load_dotenv

from fastapi import FastAPI
import uvicorn

from controller_management.views import router as router_get_state

load_dotenv()

app = FastAPI()
app.include_router(router_get_state)

@app.get('/')
def root():
    print(f'this:')
    return {
        'this': 'main_page'
    }

if __name__ == '__main__':
    uvicorn.run('main:app', port=8001, reload=True)