from core.config import settings
from core.gunicorn import Application, get_app_options
from main import main_app


def main():
    Application(
        application=main_app,
        options=get_app_options(
            host=settings.run.host,
            port=settings.run.port,
            workers=settings.run.workers,
            timeout=settings.run.timeout,
            log_level=settings.logging.log_level,
        ),
    ).run()


if __name__ == "__main__":
    main()
