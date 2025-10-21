from fastapi import APIRouter
from pydantic import BaseModel

from api.agents.graph import run_pipeline

router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search(body: SearchRequest) -> dict:
    result = await run_pipeline(body.query)
    return result


