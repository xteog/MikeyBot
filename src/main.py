import logging
import config
import MikeyBot


if __name__ == "__main__":
    logging.basicConfig(
        filename=config.loggerPath,
        format="%(asctime)s [%(levelname)s]:%(name)s:%(message)s",
        level=logging.INFO,
    )

    MikeyBot.run()