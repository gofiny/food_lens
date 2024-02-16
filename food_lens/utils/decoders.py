import orjson
from typing import Any, Protocol


class JsonDecoderProtocol(Protocol):
    def __call__(self, body: bytes) -> dict[str, Any]:
        raise NotImplementedError


def decode_json(body: bytes) -> dict[str, Any]:
    return orjson.loads(body)
