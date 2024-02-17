FROM python:3.12.1-slim as requirements-builder

WORKDIR /build/

RUN pip --no-cache-dir install pdm

COPY pyproject.toml pdm.lock README.md /build/

RUN pdm export --without-hashes -f requirements -o requirements.txt  --prod && \
    env | sort > .docker.env


FROM python:3.12.1-slim

WORKDIR /app/

COPY --from=requirements-builder /build/requirements.txt /app/requirements.txt

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

RUN pip --no-cache-dir install -r requirements.txt

COPY food_lens /app/food_lens
COPY --from=requirements-builder /build/.docker.env /app/.docker.env

CMD ["python", "-m", "food_lens"]
