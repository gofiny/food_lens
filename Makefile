SERVICE := food_lens

setup:
	@pdm install

lint:
	@printf "=========================== black ==============================\n"
	@pdm run black $(SERVICE)/ tests/
	@printf "=========================== MYPY ==============================\n"
	@pdm run mypy $(SERVICE)/
	@printf "=========================== RUFF ==============================\n"
	@pdm run ruff check --fix --exit-non-zero-on-fix .

test:
	@pdm run pytest tests --cov $(SERVICE) -vv

start_docker:
	docker-compose  down && docker-compose up --build -d && docker-compose logs -f

stop_docker:
	docker-compose  down

start:
	@pdm run python -m granian --interface asgi $(SERVICE).app:app
