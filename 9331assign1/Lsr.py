import threading
import pickle
import socket
import time
import sys

UPDATE_INTERVAL = 1
ROUTE_UPDATE_INTERVAL = 30
MAX = 999
neighbourDic = {}
nodeVisited = []
information = {}#message
heartbeat = {}
graph = {} #global view of the network topology
portNo = 0 #the cuurent router port number

sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ipv4 and UDP

"""
To broadcaste its information
"""
def ThreadBoardc():
    global nodeVisited
    packet = pickle.dumps(information)
    while True:
        for key, values in information['neighbour'].items():
            sender.sendto(packet, ("localhost", int(values[1])))
        information["path"] = nodeVisited
        time.sleep(UPDATE_INTERVAL)


"""
    To Transfer the message to the current router’s
    neighbors when necessary.
"""
def Retransfer(message):
    packet = pickle.dumps(message)
    transNodes = []
    for key, values in information['neighbour'].items():
        if key not in message['path']:
            transNodes.append(key)
            message['path'].append(key)
    for node in transNodes:
        sender.sendto(packet, ("localhost", int(information['neighbour'][node][1])))


"""
    To listen link-state message from other nodes.
"""
def ThreadListen():
    global graph
    global heartbeat
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ipv4 and UDP
    receiver.bind(("localhost", int(portNo)))
    while True:
        try:
            message, senderPort = receiver.recvfrom(2048)
            message = pickle.loads(message)
            message['path'].append(router)
            graph[message['source']] = message['neighbour']
            #Restricts excessive link-state broadcast(heartbeat approach)
            heartbeat[message['source']] = time.time()
            for keys, values in heartbeat.items():
                if (time.time() - values) > 3 * UPDATE_INTERVAL:
                    if keys not in graph.keys():
                        continue
                    else:
                        del graph[keys]
            Retransfer(message)
        except Exception:
            print("Listen error!")
            break


"""
    To calculate the least cost and the shortest path
"""
def ThreadDijkstra():
    global graph
    while True:
        time.sleep(ROUTE_UPDATE_INTERVAL)
        #to make sure every node's status again
        for keys, values in heartbeat.items():
            if (time.time() - values) > 3 * UPDATE_INTERVAL:
                if keys not in graph.keys():
                    continue
                else:
                    del graph[keys]
        
        if len(graph.keys())>1:              
            unvisited = {node: MAX for node in graph.keys()}
            visited = dict()
            previous = dict()
            current = router
            currentDistance = 0.0
            unvisited[current] = currentDistance
            while True:
                for neighbour, distance in graph[current].items():
                    if neighbour not in unvisited.keys():
                        continue
                    newDistance = float(currentDistance) + float(distance[0])
                    if unvisited[neighbour] is MAX or unvisited[neighbour] > newDistance:
                        unvisited[neighbour] = newDistance
                        previous[neighbour] = current
                visited[current] = float(currentDistance)
                del unvisited[current]
                if not unvisited:
                    break
                candidates = [node for node in unvisited.items() if node[1] != MAX]
                current, currentDistance = sorted(candidates, key=lambda x: x[1])[0]
                currentDistance = round(currentDistance, 2)

            print(f'I am Router {router}')
            S = set(node for node in graph.keys())
            S.remove(router)
            S = sorted(S)
            for node in S:
                path = []
                path.append(node)
                while True:
                    path.append(previous[node])
                    if router in path:
                        break
                    previous[node] = previous[previous[node]]
                path_string = ''.join([i for i in reversed(path)])
                print(f'Least cost path to router {node}:{path_string} and the cost is {round(visited[node], 1)}')
        else:
            print(f'I am Router {router}')
            print("There is no path.")

"""
    To process each instance of the routing protocol’s data
"""
def ProcessFile():
    global portNo
    global neighbourDic
    global information
    global router
    f = open(sys.argv[1])
    data = f.readline().strip()
    data = data.split(' ')
    router = data[0]
    portNo = int(data[1])
    neighbourNum = f.readline().strip() 
    items = f.readlines()
    for i in range(len(items)):
        neighbourDic[items[i].split()[0]] = [items[i].split()[1], items[i].split()[2]]
    nodeVisited.append(router)
    for key in neighbourDic.keys():
        nodeVisited.append(key)
    graph[router] = neighbourDic
    information['source'] = router
    information['neighbour'] = neighbourDic
    information['path'] = nodeVisited


ProcessFile()
t1 = threading.Thread(target=ThreadBoardc)
t1.start()
t2 = threading.Thread(target=ThreadListen)
t2.start()
t3 = threading.Thread(target=ThreadDijkstra)
t3.start()
