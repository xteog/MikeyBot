import time
import mysql.connector
import logging

import config


class Database:
    def __init__(self) -> None:
        self.database = None
        self.cursor = None

    def connect(self) -> None:
        done = False

        while not done:
            try:
                self.database = mysql.connector.connect(
                    user=config.databaseUser,
                    password=config.databasePassword,
                    host=config.databaseHost,
                    database="MikeyBot",
                )
                self.cursor = self.database.cursor()

                print("Connessione al database riuscita!")
                logging.info("Connessione al database riuscita!")

                done = True
            except mysql.connector.Error as err:
                logging.error(f"Errore durante la connessione al database: {err}")
                print(f"Errore durante la connessione al database: {err}")
                time.sleep(5)

    def close(self) -> None:
        self.database.close()
        logging.info("Connessione chiusa.")
        print("Connessione chiusa.")
