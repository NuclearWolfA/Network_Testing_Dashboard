from fastapi import APIRouter


router = APIRouter()


@router.get("/dummy")
def dummy_api() -> dict[str, str]:
    return {"message": "dummy backend api"}