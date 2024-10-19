from enum import Enum
import time
import requests
import utils
import logging
import config

appendRowURL = "https://sheets.googleapis.com/v4/spreadsheets/{spreadSheetId}/values/{sheetName}!A1:M1:append?valueInputOption=RAW"
refreshTokenURL = "https://oauth2.googleapis.com/token?access_type=offline&refresh_token={refreshToken}&client_id={clientId}&client_secret={clientSecret}&grant_type=refresh_token"


class HttpMethod(Enum):
    GET = 0
    POST = 1
    PUT = 2
    DELETE = 3


def sendRequest(
    method: HttpMethod, url: str, values: list[list] = None, tries: int = 0
) -> requests.Response:
    token = refreshToken()

    headers = {"Authorization": f"Bearer {token}"}

    if values == None:
        data = None
    else:
        data = {"values": values}

    if method == HttpMethod.GET:
        function = requests.get
    elif method == HttpMethod.POST:
        function = requests.post
    elif method == HttpMethod.PUT:
        function = requests.put
    elif method == HttpMethod.DELETE:
        function = requests.delete

    response = function(
        url=url,
        headers=headers,
        json=data,
    )

    if response.status_code != 200 and tries < 3:
        time.sleep(1)
        response = sendRequest(method=method, url=url, values=values, tries=tries + 1)

    return response


def refreshToken() -> str | None:
    credentials = utils.read(config.googleCredentialsPath)

    response = requests.post(
        url=refreshTokenURL.format(
            refreshToken=credentials["refresh_token"],
            clientId=credentials["client_id"],
            clientSecret=credentials["client_secret"],
        )
    )

    if response.status_code == 200:
        return response.json()["access_token"]

    logging.error("Couldn't get new Google token")
    return None
