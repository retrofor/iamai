import os
import typing
import websockets
from os import path
from iamai.logger import logger
from iamai.middleware import MiddleWare
from iamai._core import *


class Bot:
    def __init__(self, config: str):
        self.config = None
