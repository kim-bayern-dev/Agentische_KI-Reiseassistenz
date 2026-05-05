import os

from constants import WANDER_INTERESTS_LIST


class AppConfig:
    def __init__(self):
        pass

    @property
    def EXAMPLE_LOCATIONS(self):
        return {
            "Finsterau": (48.930035, 13.576424),
            "Riedlhütte": (48.907779, 13.381509),
            "Zwiesel": (49.013027, 13.230762),
        }

    @property
    def INTERESTS(self):
        return WANDER_INTERESTS_LIST.copy()
