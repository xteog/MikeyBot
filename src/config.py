import json

import utils

Token = None

stewardsRole = None
devRole = None
URARole = None
connectedRole = None
ccOfficialRole = None

databaseUser = None
databasePassword = None
databaseHost = None

loggerPath = "../data/logging.log"
numbersListPath = "../data/numbersList.json"
numbersSheetPath = "../data/AvailableNumbers.xlsx"
reportWindowNoticePath = "../data/report_window_notice.json"
schedulePath = "../data/schedule.json"
discordCredentialsPath= "../data/discord_credentials.json"
googleCredentialsPath = "../data/google_credentials.json"
geminiCredentialsPath = "../data/gemini_credentials.json"
welcomeMessagePath = "../data/welcome_message.md"
connectionTipsPath = "../data/connection_tips.md"
geminiDescPath = "../data/gemini_description.txt"

spreadSheetId = "1Hvruu_KB-dVkpy9V_sC6ZMx9C-Nlge-y8oAk9uSs2gs"
attendanceUsersRange = "A9:C"
attendanceRaceRange = "B3:B5"
attendanceStatusRange = "B2"
penLogRange = "A1:M1"

defaultTimeout = 60 * 60
timeFormat = "%Y-%m-%d %H:%M"

stewardsNumber = 8

botId = None
serverId = None
reportChannelId = None
errorChannelId = None
leaguesChannelIds = None
ccChannelId = None
lobbiesChannelId = None
nummbersChannelId = None

reportWindowDelta = 5

summaryRequest = "Summarize all the previous messages in no more than 4000 characters. Make sure to include the important stuff. Your response will be used as long term memory, so make sure to not mess it up and include only the summary, no other messages."

summaryPartition = 0.75
maxTokens = 16000
maxCharsText = 4000

def TEST():
    global Token

    Token = utils.read(discordCredentialsPath)["test"]

    global botId
    global serverId
    global reportChannelId
    global errorChannelId
    global leaguesChannelIds
    global ccChannelId
    global lobbiesChannelId
    global numbersChannelId
    botId = 881632829547642972
    serverId = 881632566589915177
    reportChannelId = 1151111851170598983
    errorChannelId = 1032428103861026897
    leaguesChannelIds = {
        "UL": 1150943947812778024,
        "CL": 1150943947812778024,
        "JL": 1150943947812778024,
        "FE": 1150943947812778024,
    }
    ccChannelId = 1150943947812778024
    lobbiesChannelId = 1150943947812778024
    numbersChannelId = 1150943947812778024

    global stewardsRole
    global devRole
    global URARole
    global connectedRole
    global ccOfficialRole
    stewardsRole = 1151133613702791209
    devRole = 1150883871936745545
    URARole = 749351036745023551
    connectedRole = 1150883871936745545
    ccOfficialRole = None

    global databaseUser
    global databasePassword
    global databaseHost
    databaseUser = "root"
    databasePassword = "peppinomarco"
    databaseHost = "localhost"


def RUN():
    global Token
    Token = utils.read(discordCredentialsPath)["run"]

    global botId
    global serverId
    global reportChannelId
    global errorChannelId
    global leaguesChannelIds
    global ccChannelId
    global lobbiesChannelId
    global numbersChannelId
    botId = 1150936522263101461
    serverId = 449754203238301698
    reportChannelId = 1181745012971679764
    errorChannelId = 1032428103861026897
    leaguesChannelIds = {
        "UL": 903800685697593344,
        "CL": 922640901686325298,
        "JL": 1059743526088343662,
        "AL": 1204493092271689798,
        "FE": 992504705035014314,
    }
    ccChannelId = 930047083510132746
    lobbiesChannelId = 903892486399868978
    numbersChannelId = 990229907479076914

    global stewardsRole
    global devRole
    global URARole
    global connectedRole
    global ccOfficialRole
    stewardsRole = 1170840937296044163
    devRole = 1189920883003887628
    URARole = 749351036745023551
    connectedRole = 967141781353431091
    ccOfficialRole = 943384660908593182

    global databaseUser
    global databasePassword
    global databaseHost
    databaseUser = "root"
    databasePassword = "7ClsWHSf6?a52v6#[?4T"
    databaseHost = "localhost"
