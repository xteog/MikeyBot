import config
from database.beans import Race
from google_sheets.api import HttpMethod, sendRequest

valuesURL = "https://sheets.googleapis.com/v4/spreadsheets/{spreadSheetId}/values/{sheetName}!{range}"

setOptions = "?valueInputOption=RAW"
getOptions = "?majorDimension=ROWS"
appendOptions = ":append" + setOptions


def loadAttendance() -> tuple[Race, list[list]]:
    response = sendRequest(
        method=HttpMethod.GET,
        url=valuesURL.format(
            spreadSheetId=config.spreadSheetId,
            sheetName="ATTENDANCE",
            range=config.attendanceRaceRange,
        )
        + getOptions,
    )
    if response.status_code != 200:
        statusAttendance("Error: Cannot read round")
        return None, None

    values = response.json()["values"]
    try:
        race = Race(league=values[0][0], season=values[1][0], round=values[2][0])
    except Exception as e:
        statusAttendance(str(e))
        return None, None

    response = sendRequest(
        method=HttpMethod.GET,
        url=valuesURL.format(
            spreadSheetId=config.spreadSheetId,
            sheetName="ATTENDANCE",
            range=config.attendanceUsersRange,
        )
        + getOptions,
    )
    if response.status_code != 200:
        statusAttendance("Error: Cannot read users")
        return None, None

    return race, response.json()["values"]


def resetAttendance(users: tuple[tuple[int, str]]) -> None:
    data = []
    for user in users:
        data.append([user[0], user[1], False])

    sendRequest(
        method=HttpMethod.PUT,
        url=valuesURL.format(
            spreadSheetId=config.spreadSheetId,
            sheetName="ATTENDANCE",
            range=config.attendanceUsersRange,
        )
        + setOptions,
        values=data,
    )

    statusAttendance("Ready")


def statusAttendance(str: str) -> None:
    sendRequest(
        method=HttpMethod.PUT,
        url=valuesURL.format(
            spreadSheetId=config.spreadSheetId,
            sheetName="ATTENDANCE",
            range=config.attendanceStatusRange,
        )
        + setOptions,
        values=[[str]],
    )


def appendRow(row: list[str], sheetName: str) -> None:
    sendRequest(
        method=HttpMethod.POST,
        url=valuesURL.format(
            spreadSheetId=config.spreadSheetId,
            sheetName=sheetName,
            range=config.penLogRange,
        )
        + appendOptions,
        values=[row],
    )
