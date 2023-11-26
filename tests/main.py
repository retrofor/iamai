from iamai import Bot
import iamai

bot = Bot(hot_reload=True)

if __name__ == "__main__":
    print(iamai.__version__)
    bot.run()
