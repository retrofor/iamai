import sys
sys.path.insert(0, '../IamAI')

from IamAI import Bot

bot = Bot(hot_reload=True)
bot.load_adapters("IamAI.adapter.cqhttp")

bot.run()
