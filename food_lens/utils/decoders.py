from typing import Any, Protocol, cast

import orjson


class JsonDecoderProtocol(Protocol):
    def __call__(self, body: bytes) -> dict[str, Any]:
        raise NotImplementedError


def decode_json(body: bytes) -> dict[str, Any]:
    return cast(dict[str, Any], orjson.loads(body))
