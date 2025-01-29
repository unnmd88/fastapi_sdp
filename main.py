from dotenv import load_dotenv


from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel, IPvAnyAddress


load_dotenv()

class GetIntersectionData(BaseModel):
    ipv4: IPvAnyAddress | None
    num: str | None


app = FastAPI()


@app.get('/')
def root():
    print(f'this:')
    return {
        'this': 'main_page'
    }


@app.post('/intersection')
def get_intersection_data(intersection: GetIntersectionData):
    print(f'intersection: {intersection}')
    return {
        'success': True
    }

if __name__ == '__main__':
    uvicorn.run('main:app', port=8001, reload=True)