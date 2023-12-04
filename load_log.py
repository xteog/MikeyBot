import csv
from moderation import moderation
import utils
import config


def addToHistory(data: moderation.ReportData, nick) -> None:
    history = utils.read(config.historyPath)

    if history == None:
        history = {}

    if str(data.offender) in history.keys():
        history[str(data.offender)]["name"] = nick
    else:
        history[str(data.offender)] = {"name": nick, "violations": {}}

    history[str(data.offender)]["violations"][data.id] = {
        "creator": data.creator,
        "league": data.league,
        "round": data.round,
        "rule": data.rule.code,
        "proof": data.proof,
        "description": data.desc,
        "penalty": data.penalty,
        "severity": data.severity,
        "notes": data.notes,
        "active": False,
        "timestamp": "2001-11-09 8:09",
    }

    utils.write(config.historyPath, history)


file = open("pen_log.csv")

csvreader = csv.reader(file)

for row in csvreader:
    if row[0] != "" and row[0] != "DISCORD ID":
        report = moderation.ReportData(
            creator=1150936522263101461,
            offender=row[0],
            round=row[2],
            league="",
            proof=row[7],
            penalty=row[3],
            severity=row[4],
            notes=row[6],
            desc=""
        )

        addToHistory(report, row[1])
