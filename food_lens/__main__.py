from .app import create_app
from .settings import Settings
from .uvicorn import run_server

if __name__ == "__main__":
    settings = Settings()

    app = create_app(settings)
    run_server(app, settings)
