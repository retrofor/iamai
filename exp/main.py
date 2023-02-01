from iamai import Bot

bot = Bot(hot_reload=True)
bot.load_adapters("iamai.adapter.cqhttp")

if __name__ == "__main__":
    bot.run()