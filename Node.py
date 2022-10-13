import sys
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

        # msg = pb2.Empty()
        # rsp = stub.get_chord_info(msg)
        # info = rsp.ci
        if len(self.chord_info()) > 1:
            self.get_saved_keys_from_successor()

        # msg = pb2.PFTRequest(id=self.node_id)
        # rsp = stub.populate_finger_table(msg)
        # self.pred = rsp.predID

    def finger_table(self):
        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)
        return rsp.ft

    @staticmethod
    def chord_info():
        msg = pb2.Empty()
        rsp = stub.get_chord_info(msg)
        return rsp.ci

    def get_saved_keys_from_successor(self):
        # msg = pb2.Empty()
        # rsp = stub.get_chord_info(msg)
        info = self.chord_info()

        for node in info:
            if node.id == self.get_successor_id(info, self.node_id + 1):
                succ_ip = node.addr
                break

        msg = pb2.GSKRequest(id=self.node_id)
        channel = grpc.insecure_channel(succ_ip)
        node_stub = pb2_grpc.NodeStub(channel)
        response = node_stub.get_saved_keys(msg)
        print(response.keysExist)
        if response.keysExist:
            for kv in response.kv:
                self.saved[kv.key] = kv.value

    def get_saved_keys(self, request, context):
        node_id = request.id
        kv = []
        for key in self.saved.keys():
            # hash_value = zlib.adler32(key.encode())
            # target_id = hash_value % 2 ** self.m
            if self.get_target_id(key) <= node_id:
                kv.append(pb2.KeyValue(key=key, value=self.saved[key]))
                self.saved.pop(key)

        if len(kv) > 0:
            keys_to_transfer = pb2.GSKReply(keysExist=True, kv=kv)
        else:
            keys_to_transfer = pb2.GSKReply(keysExist=False, kv=[pb2.KeyValue(key='-1', value='-1')])
        # print(keys_to_transfer.keysExist)
        print(keys_to_transfer)
        return keys_to_transfer

    def get_finger_table(self, request, context):
        # msg = pb2.PFTRequest(id=self.node_id)
        # rsp = stub.populate_finger_table(msg)
        reply = {'ft': self.finger_table()}
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

        # msg = pb2.Empty()
        # rsp = stub.get_chord_info(msg)
        chord_info = self.chord_info()

        # msg = pb2.PFTRequest(id=self.node_id)
        # rsp = stub.populate_finger_table(msg)
        ft = self.finger_table()

        if self.node_id == self.get_successor_id(chord_info, target_id):
            if key in self.saved.keys():
                reply = {'stat': False, 'error': f'\"{key}\" is already exist in node {self.node_id}'}
            else:
                self.saved[key] = text
                reply = {'stat': True, 'id': self.node_id}
            return pb2.SaveReply(**reply)

        transfer_to = -1
        # for node in ft:
        #     if node.id == target_id:
        #         transfer_to = target_id
        #         break

        # if transfer_to == -1:
        succ_id = self.get_successor_id(chord_info, self.node_id)
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

        # msg = pb2.Empty()
        # rsp = stub.get_chord_info(msg)
        chord_info = self.chord_info()

        # msg = pb2.PFTRequest(id=self.node_id)
        # rsp = stub.populate_finger_table(msg)
        ft = self.finger_table()

        if self.node_id == self.get_successor_id(chord_info, target_id):
            if key not in self.saved.keys():
                reply = {'stat': False, 'error': f'\"{key}\" does not exist in node {self.node_id}'}
            else:
                self.saved.pop(key)
                reply = {'stat': True, 'id': self.node_id}
            return pb2.RemoveReply(**reply)

        transfer_to = -1
        # for node in chord_info:
        #     if node.id == target_id:
        #         transfer_to = target_id
        #         break

        # if transfer_to == -1:
        succ_id = self.get_successor_id(chord_info, self.node_id)
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

        # msg = pb2.Empty()
        # rsp = stub.get_chord_info(msg)
        chord_info = self.chord_info()

        # msg = pb2.PFTRequest(id=self.node_id)
        # rsp = stub.populate_finger_table(msg)
        ft = self.finger_table()

        if self.node_id == self.get_successor_id(chord_info, target_id):
            if key not in self.saved.keys():
                reply = {'stat': False, 'error': f'\'{key}\' does not exist in node {self.node_id}'}
            else:
                reply = {'stat': True, 'id': self.node_id, 'addr': f'{self.ipaddr}:{self.port}'}
            return pb2.FindReply(**reply)

        transfer_to = -1
        # for node in info:
        #     if node.id == target_id:
        #         transfer_to = target_id
        #         break

        # if transfer_to == -1:
        succ_id = self.get_successor_id(chord_info, self.node_id)
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
    # registry_ipaddr = '127.0.0.1'
    # registry_port = '5000'
    # ipaddr = '127.0.0.1'
    # port = '5001'

    channel = grpc.insecure_channel(f'{registry_ipaddr}:{registry_port}')
    stub = pb2_grpc.RegistryStub(channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_NodeServicer_to_server(Node(port, ipaddr), server)
    server.add_insecure_port(f'{ipaddr}:{port}')
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print('shutting down')
