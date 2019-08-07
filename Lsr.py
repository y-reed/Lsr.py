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
         self.send_time = 0
         self.revive = []
         self.dead_nodes = []

class Router:
    def __init__(self, name, port):
        #Router characteristics
        self.name = name
        self.port = int(port)
        self.neighbours = {}
        self.no_neighbours = 0
        self.paths = {}
        self.cost = {}
        self.seqnum = 0

    def add_neighbour(self, n, weight):
        if n not in self.neighbours:
            self.neighbours[n] = float(weight)
            self.no_neighbours += 1

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

    def remove_edge(self,r2):
        for r in g.routers:
            if r2 in r.neighbours:
                print("remove edge from " + r.name + r2.name)
                self.get_router(r).remove_edge(r2)

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

def establishConnection():
    global sender_sock, receiver_sock
    sender_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sender_sock.bind(('', src_router.port))

def send_broadcast():
    seq_num = 0
    while True:
        LSA_Packet = Packet("LSA_Packet", src_router, seq_num)
        LSA_Packet.neighbours_dict = src_router.neighbours
        LSA_Packet.dead_nodes = dead_nodes
        LSA_Packet.revive = revive_nodes
        for n in list(src_router.neighbours):
            sender_sock.sendto(pickle.dumps(LSA_Packet), ("localhost", n.port))
        seq_num += 1
        time.sleep(UPDATE_INTERVAL)

def send_heart_beat():
    seq_num = 0
    while True:
        heart_beat_packet = Packet("heart_beat", src_router, seq_num)
        for n in list(src_router.neighbours):
            heart_beat_packet.send_time = int(time.time())
            sender_sock.sendto(pickle.dumps(heart_beat_packet), ("localhost", n.port))
        seq_num += 1
        time.sleep(ROUTE_UPDATE_INTERVAL)

def heart_beat_timer():
    while True:
        for r in list(src_router.neighbours):
            if r.name in latest_hb:
                if int(time.time()) > (latest_hb[r.name] + 2):
                    # print(str(time.time()) + "now " + str(latest_hb[r.name]))
                    print("removed" + r.name)
                    dead_nodes.append(r.name)
                    latest_hb.clear()
                    g.remove_edge(r)


def check_seq_num(recv_packet):
    if recv_packet.original_router.name in store_LSA_packets:
        for r in store_LSA_packets[recv_packet.original_router.name]:
            if r == recv_packet.seq_num:
                return False
        return True
    store_LSA_packets[recv_packet.original_router.name] = [recv_packet.seq_num]
    return True

def receive_packets():
    store_hb = {}
    store_rv = []
    while True:
        recv_data, addr = sender_sock.recvfrom(2048)
        recv_packet = pickle.loads(recv_data)
        org_router = recv_packet.original_router
        if recv_packet.type == "LSA_Packet":

            if check_seq_num(recv_packet) == True:                                  #Checks whether or not packet has been received. Returns True if packet must be read.
                for n in recv_packet.neighbours_dict:
                    if not g.get_router(n):
                        if n.name == src_router.name:
                            continue
                        r = Router(n.name, n.port)
                        g.add_router(r)
                        g.add_edge(g.get_router(org_router), r, recv_packet.neighbours_dict[n])
                    else:
                        g.add_edge(g.get_router(org_router), g.get_router(n), recv_packet.neighbours_dict[n])

                if len(recv_packet.dead_nodes) != 0:
                    for d_node in recv_packet.dead_nodes:
                        if d_node not in dead_nodes and d_node not in src_direct_neighbours:
                            dead_nodes.append(d_node)
                            g.remove_edge(g.get_router_by_name(d_node))             ##Removes all edges connected to the failed node in the graph
                if len(recv_packet.revive) != 0:
                    for rev in recv_packet.revive:
                        if rev in dead_nodes:
                            for r in g.get_router_by_name(rev).neighbours:
                                g.add_edge(g.get_router_by_name(rev), g.get_router(r), g.get_router_by_name(rev).neighbours[r])
                            dead_nodes.remove(rev)

                for i in list(src_router.neighbours):
                    if org_router.name == i.name:
                        continue
                    sender_sock.sendto(pickle.dumps(recv_packet), ("localhost", i.port))
                store_LSA_packets[org_router.name].append(recv_packet.seq_num)

        if recv_packet.type == "heart_beat":
            if org_router.name in store_hb:
                if recv_packet.seq_num > store_hb[org_router.name]:
                    latest_hb[org_router.name] = recv_packet.send_time

            if (len(dead_nodes) != 0) and (org_router.name in dead_nodes):
                print("packet from" + org_router.name)
                dead_nodes.remove(org_router.name)
                revive_nodes.append(org_router.name)
                for n in list(recv_packet.neighbours_dict):
                    if n.name not in dead_nodes:
                        g.add_edge(g.get_router(org_router), g.get_router(n), recv_packet.neighbours_dict[n])
            store_hb[org_router.name] = recv_packet.seq_num
            print("Dead" + str(dead_nodes))
            print("revive" + str(revive_nodes))


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
        src_direct_neighbours.append(n.name)
        j += 1; i += 1
    src_direct_neighbours.append(src_router.name)
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
store_LSA_packets = {}
latest_hb = {}
dead_nodes = []
revive_nodes = []
src_direct_neighbours = []

def main():
    read_Config()
    establishConnection()
    recv_pack = threading.Thread(target = receive_packets, args=())
    recv_pack.daemon = True
    recv_pack.start()

    broadcast = threading.Thread(target = send_broadcast, args = ())
    broadcast.daemon = True
    broadcast.start()

    heartbeat = threading.Thread(target = send_heart_beat, args=())
    heartbeat.daemon = True
    heartbeat.start()

    hb_timer = threading.Thread(target = heart_beat_timer, args = ())
    hb_timer.daemon = True
    hb_timer.start()

    flag = 0
    while True:
        time.sleep(UPDATE_INTERVAL)
        print("I am Router " +  src_router.name)
        dijkstra(src_router)
        print_path(src_router)

if __name__ == '__main__':
    main()
