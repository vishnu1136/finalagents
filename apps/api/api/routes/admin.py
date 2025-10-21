from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


