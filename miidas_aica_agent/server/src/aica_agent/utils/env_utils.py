import os

DEFAULT_ENV = "local"


def get_env() -> str:
    return os.getenv("AICA_ENV", DEFAULT_ENV)


def is_local() -> bool:
    return get_env() == "local"


def is_dev() -> bool:
    return get_env() == "development"


def is_local_or_dev() -> bool:
    return is_local() or is_dev()
