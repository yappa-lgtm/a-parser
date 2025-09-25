from .logger import GunicornLogger


def get_app_options(
    host: str,
    port: int,
    timeout: int,
    workers: int,
    log_level: str,
) -> dict:
    return {
        "accesslog": "-",
        "errorlog": "-",
        "bind": f"{host}:{port}",
        "timeout": timeout,
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "loglevel": log_level,
        "logger_class": GunicornLogger,
    }
