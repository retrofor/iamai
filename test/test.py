from retrofor_wut import Bot

bot = Bot(hot_reload=True)
bot.load_adapters("retrofor_wut.adapter.cqhttp")

bot.run()