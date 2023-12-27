import datetime

Token = None
stewardsRole = None
devRole = None
historyPath = "data/history.json"
rulesPath = "data/rules.json"
penaltyLogPath = "data/penalty_log.xlsx"
numbersListPath = "data/numbersList.json"
defaultTimeout = 60 * 60
timeFormat = "%Y-%m-%d %H:%M"

serverId = None
reportChannelId = None
errorChannelId = None
leaguesChannelIds = None

openTime = {
    "UL": datetime.datetime(2024, 12, 30, 0, 59),
    "CL": datetime.datetime(2024, 12, 30, 0, 59),
    "JL": datetime.datetime(2024, 12, 30, 0, 59),
    "FE": datetime.datetime(2023, 12, 28, 0, 50),
}
closeTime = {
    "UL": openTime["UL"] + datetime.timedelta(days=3),
    "CL": openTime["CL"] + datetime.timedelta(days=3),
    "JL": openTime["JL"] + datetime.timedelta(days=3),
    "FE": openTime["FE"] + datetime.timedelta(days=2),
}


def TEST():
    global Token
    Token = "TOKEN"

    global serverId
    global reportChannelId
    global errorChannelId
    global leaguesChannelIds
    serverId = 881632566589915177
    reportChannelId = 1151111851170598983
    errorChannelId = 1032428103861026897
    leaguesChannelIds = {
        "UL": 1150943947812778024,
        "CL": 1150943947812778024,
        "JL": 1150943947812778024,
        "FE": 1150943947812778024,
    }

    global stewardsRole
    global devRole
    stewardsRole = 1151133613702791209
    devRole = 1144694551869673563


def RUN():
    global Token
    Token = "TOKEN"

    global serverId
    global reportChannelId
    global errorChannelId
    global leaguesChannelIds
    serverId = 449754203238301698
    reportChannelId = 1181745012971679764
    errorChannelId = 1032428103861026897
    leaguesChannelIds = {
        "UL": 903800685697593344,
        "CL": 922640901686325298,
        "JL": 1059743526088343662,
        "FE": 992504705035014314,
    }

    global stewardsRole
    global devRole
    stewardsRole = 1170840937296044163
    devRole = 1144694551869673563
