import socket
import codecs


def getLobbyInfo(data: str) -> str:
    
    start, end = 0, 0
    for i in range(len(data)):
        if data[i] == '#':
            start = i + 1
        if data[i] == '|':
            end = i
            break
    lobbyName = data[start:end]

    start, end, cont = 0, 0, 0
    for i in range(len(data)):
        if data[i] == '|':
            if start == 0:
                cont += 1
            else:
                end = i
                break
        
        if data[i] == '|' and cont == 3:
            start = i + 1
    dim = data[start:end]

    start, end, cont = 0, 0, 0
    for i in range(len(data)):
        if data[i] == '|':
            if start == 0:
                cont += 1
            else:
                end = i
                break
        
        if data[i] == '|' and cont == 9:
            start = i + 1
    players = data[start:end]

    start, end, cont = 0, 0, 0
    for i in range(len(data)):
        if data[i] == '|':
            if start == 0:
                cont += 1
            else:
                end = i
                break
        
        if data[i] == '|' and cont == 10:
            start = i + 1
    password = data[start:end]
    
    if password != "":
        return f"- {lobbyName} {players}/{dim} :lock:\n"
    else:
        return f"- {lobbyName} {players}/{dim}\n"


def getLobbiesList():
    lobbies = []
    IP = "46.101.147.176"
    PORT= 6510
    payload=f"39300a00"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", PORT))

    data = codecs.decode(payload, "hex_codec")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (IP, PORT))

    run = True
    sock.settimeout(2)
    while run:
        try:
            data, addr = sock.recvfrom(1024)
            data = data.decode()
            
            lobbies.append(getLobbyInfo(data))
        except:
            run = False

    sock.close()

    return lobbies
