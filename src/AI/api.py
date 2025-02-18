import asyncio
import logging
import time
import requests

import config
import utils


geminiApiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"


async def sendRequest(url: str, data: dict, tries: int = 0) -> requests.Response:

    response = requests.post(
        url=url,
        json=data,
    )

    if response.status_code != 200 and tries <= 5:
        print(data)
        await asyncio.sleep(pow(2, tries)) #TODO forse meglio far gestire il retry dal bot così può avvisare l'utente di rate limited
        response = await sendRequest(url=url, data=data, tries=tries + 1)
        if response.status_code != 200:
            raise Exception(response.text)

    return response


async def sendMessage(history: list, message: str) -> str:
    msgFormatted = {"role": "user", "parts": [{"text": message}]}
    data = {"contents": history + [msgFormatted]}

    apiKey = utils.read(config.geminiCredentialsPath)["api_key"]

    response = await sendRequest(url=geminiApiUrl.format(apiKey=apiKey), data=data)
    response = response.json()

    logging.info(response)

    return response["candidates"][0]["content"]["parts"][0]["text"]
