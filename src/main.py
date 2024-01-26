import bot
import logging
import config


if __name__ == "__main__":
    logging.basicConfig(
        filename=config.loggerPath,
        format="%(asctime)s [%(levelname)s]:%(name)s:%(message)s",
        level=logging.INFO,
    )

    bot.run()