import logging

import httpx

from AI.ChatMessage import ChatResponse
import config
from exceptions import RateLimitException
import utils


geminiApiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"


async def sendRequest(url: str, data: dict, tries: int = 0) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url,
            json=data,
            timeout=20.0,
        )

    if response.status_code == 429:
        raise RateLimitException()

    if response.status_code != 200:
        logging.error(response.text)
        raise Exception(response.text)

    return response


async def sendMessage(history: list, message: str) -> tuple[ChatResponse, int]:
    msgFormatted = {"role": "user", "parts": [{"text": message}]}
    data = {"contents": history + [msgFormatted]}

    apiKey = utils.read(config.geminiCredentialsPath)["api_key"]

    response = await sendRequest(url=geminiApiUrl.format(apiKey=apiKey), data=data)
    response = response.json()

    tokens = response['usageMetadata']['promptTokenCount']
    text = response["candidates"][0]["content"]["parts"][0]["text"]

    return ChatResponse(content=text), tokens
