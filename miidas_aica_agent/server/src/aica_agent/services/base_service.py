import logging

from utils.const import LOGGER_PREFIX


class BaseService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
