from fastapi import APIRouter, Response

router = APIRouter()


@router.route("/health_check")
async def healthcheck() -> Response:
    return Response()
