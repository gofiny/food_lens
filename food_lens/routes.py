from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/health_check")
async def healthcheck() -> Response:
    return Response()
