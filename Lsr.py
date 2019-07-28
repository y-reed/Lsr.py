# By Yuki Reed z5159982

import sys
import os
import time
import socket
import pickle
import threading

UPDATE_INTERVAL = 1
ROUTE_UPDATE_INTERVAL = 0.5


class Packet:
     def __init__(self, type, o_router, seq_num):
         self.type = type
         self.original_router = o_router
         self.neighbours_dict = {}
         self.seq_num = seq_num
         # self.router_state = router_state
         self.send_time = 0
class Router:
    def __init__(self, name, port):
        #Router characteristics
        self.name = name
        self.port = int(port)
        self.neighbours = {}
        self.no_neighbours = 0
        self.paths = {}
        self.cost = {}
        self.ftable = {}
        self.seqnum = 0


    def add_neighbour(self, n, weight):
        if n not in self.neighbours:
            self.neighbours[n] = float(weight)
            self.no_neighbours += 1

    def get_neightbour_port(n):
        # TO DO
        return

    def append_ft(self, dest, next):
        self.ftable[dest] = next[0][0]

    def append_path(self, dest, path, cost):
        self.paths[dest.name] = path
        self.cost[dest.name] = cost

    def get_neighbours(self):
        return self.neighbours.keys()

    def remove_edge(self, dest):
        self.no_neighbours -= 1
        self.neighbours.pop(dest)

class Graph:
    def __init__(self):
        self.routers = []

    def add_router(self, router):
        if router not in self.routers:
            self.routers.append(router)

    def get_router(self, r):
        for n in self.routers:
            if (n.name == r.name):
                return n

    def get_router_by_name(self, r):
        for n in self.routers:
            if (n.name == r):
                return n

    def add_edge(self, r1, r2, w):
        if r1 in self.routers and r2 in self.routers:
            self.get_router(r1).add_neighbour(r2, w)
            self.get_router(r2).add_neighbour(r1, w)

    def adjacent(self, r1, r2):
        if r1 in get_router(self,r).neighbours:
            return True
        return False

    def remove_router(self,r):
        for r1 in self.get_router(r).neighbours:
            g.remove_edge(r1, r)
        self.routers.remove(r)
        del r

    def remove_edge(self,r1,r2):
        self.get_router(r1).remove_edge(r2)
        # self.get_router(r2).remove_edge(r1)
        # g.get_router(r2) = self.get_router(r1).remove_edge(r2)
        # g.get_router(r1) = self.get_router(r2).remove_edge(r1)

def store_path(src, dest, prev, dist):
    path = []
    d = dest
    while(d != src):
        path.append(d.name)
        d = prev[d]
    path.append(src.name)
    path.reverse()
    src.append_path(dest, path, dist[dest])

def dijkstra(src):
    dist = {}
    prev = {}
    unvisited = []
    unvisited.append(src)

    for r in g.routers:
        dist[r] = sys.maxint
        prev[r] = None
        if (src != r):
            unvisited.append(r)

    dist[src] = 0

    while unvisited:
        curr = unvisited.pop(0)
        for next in curr.neighbours:
            new_dist = dist[curr] + curr.neighbours[next]
            if new_dist < dist[next]:
                dist[next] = new_dist
                prev[next] = curr

    src.paths.clear()
    src.cost.clear()
    for router in g.routers:
        if (router != src and dist[router] != sys.maxint):
            store_path(src, router, prev, dist)

def creat_ft():
    for src in g.routers:
        for dest in src.paths.keys():
            if src == dest:
                continue
            src.append_ft(dest, src.paths.values())

def print_cost_path():
    # TO DO
    return

def establishConnection():
    global sender_sock, receiver_sock
    sender_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sender_sock.bind(('', src_router.port))

def send_broadcast():
    seq_num = 0
    while True:
        LSA_Packet = Packet("LSA_Packet", src_router, seq_num)
        LSA_Packet.neighbours_dict = src_router.neighbours
        for n in src_router.neighbours:
            sender_sock.sendto(pickle.dumps(LSA_Packet), ("localhost", n.port))
        seq_num += 1
        time.sleep(UPDATE_INTERVAL)

def heart_beat():
    seq_num = 0
    while True:
        heart_beat_packet = Packet("heart_beat", src_router, seq_num)
        heart_beat_packet.send_time = time.time()
        for n in src_router.neighbours:
            sender_sock.sendto(pickle.dumps(heart_beat_packet), ("localhost", n.port))
        seq_num += 1
        time.sleep(ROUTE_UPDATE_INTERVAL)
    return

def receive_packets():
    recved_packet = []
    while True:
        recv_data, addr = sender_sock.recvfrom(4048)
        recv_packet = pickle.loads(recv_data)
        # if recv_packet.original_router not in recved_packet:
        if recv_packet.type == "LSA_Packet":
            for n in recv_packet.neighbours_dict:
                if n.name == src_router.name:
                    continue
                if not g.get_router(n):
                    r = Router(n.name, n.port)
                    g.add_router(r)
                    g.add_edge(g.get_router(recv_packet.original_router), r, recv_packet.neighbours_dict[n])
                else:
                    g.add_edge(g.get_router(recv_packet.original_router), g.get_router(n), recv_packet.neighbours_dict[n])
            for i in src_router.neighbours:
                if recv_packet.original_router.name == i.name:
                    continue
                sender_sock.sendto(pickle.dumps(recv_packet), ("localhost", i.port))
            # recved_packet.append(recv_packet.original_router)
        if recv_packet.type == "heart_beat":

            continue

def read_Config():
    configFile = open(sys.argv[1], "r")
    x = [];
    for data in configFile:
        x.append(data.split())
    global src_router
    src_router = Router(x[0][0], x[0][1])
    g.add_router(src_router)
    nNeighbours = int(x[1][0])
    i = 1; j = 2
    while i <= nNeighbours:
        n = Router(x[j][0],x[j][2])
        g.add_router(n); g.add_edge(src_router, n, x[j][1])
        j += 1; i += 1
    configFile.close()

def print_path(src_router):
    b = src_router
    for j in g.routers:
        if j == b:
            continue
        if j.name not in b.paths:
            print("no path " + j.name)
        else:
            print("Least cost path to router " + j.name + ":" + ' '.join(b.paths[j.name]).replace(" ","") + " and the cost is " + str(b.cost[j.name]))

g = Graph()

def main():
    read_Config()
    establishConnection()
    recv_pack = threading.Thread(target = receive_packets, args=())
    recv_pack.daemon = True
    recv_pack.start()

    broadcast = threading.Thread(target = send_broadcast, args = ())
    broadcast.daemon = True
    broadcast.start()

    heartbeat = threading.Thread(target = heart_beat, args=())
    heartbeat.daemon = True
    heartbeat.start()

    flag = 0
    while True:
        time.sleep(UPDATE_INTERVAL)
        print("I am Router " +  src_router.name)
        dijkstra(src_router)
        print_path(src_router)







if __name__ == '__main__':
    main()
