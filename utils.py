import json
import random


def lev_dist(s, t):
    v0 = [i for i in range(len(t) + 1)]
    v1 = [0] * (len(t) + 1)

    for i in range(len(s)):
        v1[0] = i + 1
        for j in range(len(t)):
            deletionCost = v0[j + 1] + 1
            insertionCost = v1[j] + 1
            if s[i] == t[j]:
                substitutionCost = v0[j]
            else:
                substitutionCost = v0[j] + 1

            v1[j + 1] = min(deletionCost, insertionCost, substitutionCost)

        temp = v0
        v0 = v1
        v1 = temp
    return v0[-1]


def loading(i, len):
    j = 0
    str = "|"
    perc = round(i / len * 20, 1)
    while j < 20:
        if perc > j:
            str += "█"
        else:
            str += "   "
        j += 1
    str += f"| {round(i/len*100, 1)}%"
    return str


def write(path: str, data) -> None:
    data = json.dumps(data, indent=2)
    with open(path, "w+") as f:
        f.write(data)


def read(path: str) -> list | None:
    try:
        with open(path, "r") as f:
            file = f.read()
        return json.loads(file)
    except: #TODO catch
        return None
    

def randomString(len:int) -> str:
    alphabet = "0123456789"

    return random.choices(alphabet[1:])[0] + "".join(random.choices(alphabet, k=len - 1))

def isLink(str: str) -> bool:
    return len(str) > 5 and str[0:5] == "https"
