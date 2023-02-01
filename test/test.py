from retrofor_wut import Bot

bot = Bot()
bot.load_adapters("retrofor_wut.adapter.cqhttp")

bot.run()