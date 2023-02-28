# app.py
import random
import re
from iamai import Plugin
from iamai.log import logger
from flask import request,Blueprint

github_bp = Blueprint('github',__name__)

class Githubs(Plugin):
    @github_bp.route('/webhook', methods=['POST'])
    def webhook():
        data = request.get_json()
        logger.info(type(data))
        return "True"

    async def handle(self) -> None:
        pass
    
    async def rule(self) -> bool:
        return False

