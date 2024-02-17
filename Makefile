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

test-ci:
	@printf "${TXT_BOLD}${TXT_MAGENTA}=========================== TEST ==============================${TXT_RESET}\n"
	pdm run pytest --force-sugar --color=yes -ra --cov=. --cov-report=xml:pytest-cobertura.xml --cov-report=term --junitxml=pytest-junit.xml tests/
	@printf "${TXT_BOLD}${TXT_MAGENTA}========================= END TEST ============================${TXT_RESET}\n"

ruff-ci:
	@printf "${TXT_BOLD}${TXT_MAGENTA}=========================== RUFF ==============================${TXT_RESET}\n"
	pdm run ruff check  . > ruff.xml
	@printf "${TXT_BOLD}${TXT_MAGENTA}========================= END RUFF ============================${TXT_RESET}\n"

mypy-ci:
	@printf "${TXT_BOLD}${TXT_MAGENTA}=========================== MYPY ==============================${TXT_RESET}\n"
	pdm run mypy --scripts-are-modules $(SERVICE_DIR)/ | pdm run mypy2junit > mypy.xml
	@printf "${TXT_BOLD}${TXT_MAGENTA}========================= END MYPY ============================${TXT_RESET}\n"

start_docker:
	docker-compose  down && docker-compose up --build -d && docker-compose logs -f

stop_docker:
	docker-compose  down

start:
	@pdm run python -m $(SERVICE)
