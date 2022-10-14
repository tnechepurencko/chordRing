import sys
from threading import Thread
from time import sleep
import grpc
import zlib
import chord_pb2_grpc as pb2_grpc
import chord_pb2 as pb2
from concurrent import futures


class Node(pb2_grpc.NodeServicer):
    def __init__(self, port, ipaddr):
        self.saved = dict()
        self.port = port
        self.ipaddr = ipaddr

        msg = pb2.RegisterRequest(ipaddr=ipaddr, port=port)
        rsp = stub.register(msg)
        self.node_id = rsp.id

        if rsp.id == -1:
            self.quit()

        self.m = rsp.m
        self.ft = self.finger_table()

        if len(self.chord_info()) > 1:
            self.get_saved_keys_from_successor()

        self.upd_ft = Thread(self.update_finger_table())
        self.upd_ft.start()

    def update_finger_table(self):
        try:
            while True:
                self.ft = self.finger_table()
                sleep(1)
        except:
            print('Node is not registered')

    def get_saved_keys_from_successor(self):
        info = self.chord_info()

        for node in info:
            if node.id == self.get_successor_id(info, self.node_id + 1):
                succ_ip = node.addr
                break

        msg = pb2.GSKRequest(id=self.node_id)
        channel = grpc.insecure_channel(succ_ip)
        node_stub = pb2_grpc.NodeStub(channel)
        response = node_stub.get_saved_keys(msg)
        channel.close()
        if response.keysExist:
            for kv in response.kv:
                self.saved[kv.key] = kv.value

    def transfer_keys_to_successor(self):
        info = self.chord_info()

        for node in info:
            if node.id == self.get_successor_id(info, self.node_id + 1):
                succ_ip = node.addr
                break

        kv = []

        for key in self.saved.keys():
            kv.append(pb2.KeyValue(key=key, value=self.saved[key]))
        if len(kv) > 0:
            keys_to_transfer = pb2.TSKRequest(keysExist=True, kv=kv)
        else:
            keys_to_transfer = pb2.TSKRequest(keysExist=False, kv=[pb2.KeyValue(key='-1', value='-1')])

        msg = keys_to_transfer

        channel = grpc.insecure_channel(succ_ip)
        node_stub = pb2_grpc.NodeStub(channel)
        node_stub.transfer_saved_keys(msg)
        channel.close()

    def transfer_saved_keys(self, request, context):
        if request.keysExist:
            for kv in request.kv:
                self.saved[kv.key] = kv.value

        return pb2.Empty()

    def get_saved_keys(self, request, context):
        node_id = request.id
        kv = []
        for key in self.saved.keys():
            if self.get_target_id(key) <= node_id:
                kv.append(pb2.KeyValue(key=key, value=self.saved[key]))
        for key in kv:
            self.saved.pop(key.key)

        if len(kv) > 0:
            keys_to_transfer = pb2.GSKReply(keysExist=True, kv=kv)
        else:
            keys_to_transfer = pb2.GSKReply(keysExist=False, kv=[pb2.KeyValue(key='-1', value='-1')])
        return keys_to_transfer

    def finger_table(self):
        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)
        return rsp.ft

    @staticmethod
    def chord_info():
        msg = pb2.Empty()
        rsp = stub.get_chord_info(msg)
        return rsp.ci

    def get_finger_table(self, request, context):
        reply = {'ft': self.ft}
        return pb2.GFTReply(**reply)

    @staticmethod
    def get_successor_id(chord_info_table, node_id):
        ids = sorted(list(node.id for node in chord_info_table))
        if node_id > ids[-1]:
            return ids[0]
        for id in ids:
            if id >= node_id:
                return id

    @staticmethod
    def closest_to_target(finger_table, target_id):
        ids = sorted(list(node.id for node in finger_table), reverse=True)
        if target_id < ids[-1]:
            return ids[0]
        for id in ids:
            if id <= target_id:
                return id

    def get_target_id(self, key):
        hash_value = zlib.adler32(key.encode())
        return hash_value % 2 ** self.m

    def save(self, request, context):
        key, text = request.key, request.text
        target_id = self.get_target_id(key)

        chord_info = self.chord_info()
        ft = self.finger_table()

        if self.node_id == self.get_successor_id(chord_info, target_id):
            if key in self.saved.keys():
                reply = {'stat': False, 'error': f'\"{key}\" is already exist in node {self.node_id}'}
            else:
                self.saved[key] = text
                reply = {'stat': True, 'id': self.node_id}
            return pb2.SaveReply(**reply)

        transfer_to = -1
        succ_id = self.get_successor_id(chord_info, self.node_id + 1)
        if self.node_id < target_id < succ_id:
            transfer_to = succ_id

        if transfer_to == -1:
            transfer_to = self.closest_to_target(ft, target_id)

        for node in chord_info:
            if node.id == transfer_to:
                target_ip = node.addr
                break

        return self.save_transfer(target_ip, key, text)

    def remove(self, request, context):
        key = request.key
        target_id = self.get_target_id(key)

        chord_info = self.chord_info()
        ft = self.finger_table()

        if self.node_id == self.get_successor_id(chord_info, target_id):
            if key not in self.saved.keys():
                reply = {'stat': False, 'error': f'\"{key}\" does not exist in node {self.node_id}'}
            else:
                self.saved.pop(key)
                reply = {'stat': True, 'id': self.node_id}
            return pb2.RemoveReply(**reply)

        transfer_to = -1
        succ_id = self.get_successor_id(chord_info, self.node_id + 1)
        if self.node_id < target_id < succ_id:
            transfer_to = succ_id

        if transfer_to == -1:
            transfer_to = self.closest_to_target(ft, target_id)

        for node in chord_info:
            if node.id == transfer_to:
                target_ip = node.addr
                break

        return self.remove_transfer(target_ip, key)

    def find(self, request, context):
        key = request.key
        target_id = self.get_target_id(key)

        chord_info = self.chord_info()
        ft = self.finger_table()

        if self.node_id == self.get_successor_id(chord_info, target_id):
            if key not in self.saved.keys():
                reply = {'stat': False, 'error': f'\'{key}\' does not exist in node {self.node_id}'}
            else:
                reply = {'stat': True, 'id': self.node_id, 'addr': f'{self.ipaddr}:{self.port}'}
            return pb2.FindReply(**reply)

        transfer_to = -1
        succ_id = self.get_successor_id(chord_info, self.node_id + 1)
        if self.node_id < target_id < succ_id:
            transfer_to = succ_id

        if transfer_to == -1:
            transfer_to = self.closest_to_target(ft, target_id)

        for node in chord_info:
            if node.id == transfer_to:
                target_ip = node.addr
                break

        return self.find_transfer(target_ip, key)

    def quit(self):
        msg = pb2.DeregisterRequest(id=self.node_id)
        self.transfer_keys_to_successor()
        rsp = stub.deregister(msg)
        if not rsp.stat:
            print('The node did not pass registration')
        print('Quitting')
        sys.exit(0)

    def who_am_i(self, request, context):
        reply = {'reply': "Connected to node", 'id': self.node_id}
        return pb2.WAIResponse(**reply)

    @staticmethod
    def save_transfer(target_ip, key, text):
        node_channel = grpc.insecure_channel(target_ip)
        node_stub = pb2_grpc.NodeStub(node_channel)
        msg = pb2.SaveRequest(key=key, text=text)
        response = node_stub.save(msg)
        return response

    @staticmethod
    def remove_transfer(target_ip, key):
        node_channel = grpc.insecure_channel(target_ip)
        node_stub = pb2_grpc.NodeStub(node_channel)
        msg = pb2.RemoveRequest(key=key)
        response = node_stub.remove(msg)
        return response

    @staticmethod
    def find_transfer(target_ip, key):
        node_channel = grpc.insecure_channel(target_ip)
        node_stub = pb2_grpc.NodeStub(node_channel)
        msg = pb2.FindRequest(key=key)
        response = node_stub.find(msg)
        return response


if __name__ == '__main__':
    registry_ipaddr = sys.argv[1].split(':')[0]
    registry_port = sys.argv[1].split(':')[1]
    ipaddr = sys.argv[2].split(':')[0]
    port = sys.argv[2].split(':')[1]

    channel = grpc.insecure_channel(f'{registry_ipaddr}:{registry_port}')
    stub = pb2_grpc.RegistryStub(channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node = Node(port, ipaddr)
    pb2_grpc.add_NodeServicer_to_server(node, server)
    server.add_insecure_port(f'{ipaddr}:{port}')
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        node.quit()
        print('shutting down')
