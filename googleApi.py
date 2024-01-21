import requests
import utils
import logging
import config

appendRowURL = "https://sheets.googleapis.com/v4/spreadsheets/{spreadSheetId}/values/{sheetName}!A1:M1:append?valueInputOption=RAW"
refreshTokenURL = "https://oauth2.googleapis.com/token?access_type=offline&refresh_token={refreshToken}&client_id={clientId}&client_secret={clientSecret}&grant_type=refresh_token"


def appendRow(row: list) -> bool:
    token = refreshToken()

    headers = {"Authorization": f"Bearer {token}"}
    data = {"values": [row]}

    response = requests.post(
        url=appendRowURL.format(
            spreadSheetId=config.spreadSheetId, sheetName=config.sheetName
        ),
        headers=headers,
        json=data,
    )

    if response.status_code == 200:
        return True

    return False


def refreshToken() -> str | None:
    credentials = utils.read("data/google_credentials.json")

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
