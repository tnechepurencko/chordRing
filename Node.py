import sys
import grpc
import zlib
import chord_pb2_grpc as pb2_grpc
import chord_pb2 as pb2
from concurrent import futures


class Node(pb2_grpc.NodeServicer):
    def __init__(self, port, ipaddr):
        msg = pb2.RegisterRequest(ipaddr=ipaddr, port=port)
        rsp = stub.register(msg)
        self.node_id = rsp.id
        if rsp.id == -1:
            self.quit()
        self.m = rsp.m

        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)
        self.pred = rsp.predID

        self.saved = dict()
        self.port = port
        self.ipaddr = ipaddr

    def get_finger_table(self, request, context):
        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)  # TODO must be a list of dicts
        reply = {'ft': rsp.ft}
        return pb2.GFTReply(**reply)

    def save(self, request, context):
        key = request.key
        text = request.text
        hash_value = zlib.adler32(key.encode())
        target_id = hash_value % 2 ** self.m

        if target_id == self.node_id:
            if key in self.saved.keys():
                reply = {'stat': False, 'error': f'The key \'{key}\' is already exist'}
            else:
                self.saved[key] = text
                reply = {'stat': True, 'id': self.node_id}
            return pb2.SaveReply(**reply)

        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)  # TODO must be a list of dicts
        ft = rsp.ft

        transfer_to = -1
        for node in ft:
            if node['id'] == target_id:
                transfer_to = target_id
                break

        if transfer_to == -1:
            ids = sorted(list(node['id'] for node in ft), reverse=True)
            if self.node_id < ids[-1]:
                succ_id = ids[0]
            else:
                for id in ids:
                    if id < self.node_id:
                        succ_id = id
                        break

            if self.node_id < target_id < succ_id:
                target_id = self

        if transfer_to == -1:
            ids = sorted(list(node['id'] for node in ft), reverse=True)
            if target_id < ids[-1]:
                transfer_to = ids[0]
            else:
                for id in ids:
                    if id < target_id:
                        transfer_to = id
                        break
        for node in ft:
            if node['id'] == transfer_to:
                target_ip = node['ip']
                break

        self.save_transfer(target_ip, key, text)

    def remove(self, request, context):
        key = request.key
        hash_value = zlib.adler32(key.encode())
        target_id = hash_value % 2 ** self.m

        if target_id == self.node_id:
            if key not in self.saved.keys():
                reply = {'stat': False, 'error': f'The key \'{key}\' does not exist'}
            else:
                self.saved.pop(key)
                reply = {'stat': True, 'id': self.node_id}
            return pb2.RemoveReply(**reply)

        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)  # TODO must be a list of dicts
        ft = rsp.ft

        transfer_to = -1
        for node in ft:
            if node['id'] == target_id:
                transfer_to = target_id
                break

        if transfer_to == -1:
            ids = sorted(list(node['id'] for node in ft), reverse=True)
            if self.node_id < ids[-1]:
                succ_id = ids[0]
            else:
                for id in ids:
                    if id < self.node_id:
                        succ_id = id
                        break

            if self.node_id < target_id < succ_id:
                target_id = self

        if transfer_to == -1:
            ids = sorted(list(node['id'] for node in ft), reverse=True)
            if target_id < ids[-1]:
                transfer_to = ids[0]
            else:
                for id in ids:
                    if id < target_id:
                        transfer_to = id
                        break

        self.remove_transfer(transfer_to, key)

    def find(self, request, context):
        key = request.key
        hash_value = zlib.adler32(key.encode())
        target_id = hash_value % 2 ** self.m

        if target_id == self.node_id:
            if key not in self.saved.keys():
                reply = {'stat': False, 'error': f'The key \'{key}\' does not exist'}
            else:
                self.saved.pop(key)
                reply = {'stat': True, 'id': self.node_id, 'addr': f'{self.ipaddr}:{self.port}'}
            return pb2.RemoveReply(**reply)

        msg = pb2.Empty()
        rsp = stub.get_chord_info(msg)  # TODO must be a list of dicts
        ci = rsp.ci

        ids = sorted(list(node['id'] for node in ci))
        if target_id >= ids[-1]:
            transfer_to = ids[0]
        else:
            for id in ids:
                if id >= target_id:
                    transfer_to = id
                    break

        self.find_transfer(transfer_to, key)

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
        print(response)

    @staticmethod
    def remove_transfer(target_ip, key):
        node_channel = grpc.insecure_channel(target_ip)
        node_stub = pb2_grpc.NodeStub(node_channel)
        msg = pb2.RemoveRequest(key=key)
        response = node_stub.remove(msg)
        print(response)

    @staticmethod
    def find_transfer(target_ip, key):
        node_channel = grpc.insecure_channel(target_ip)
        node_stub = pb2_grpc.NodeStub(node_channel)
        msg = pb2.FindRequest(key=key)
        response = node_stub.find(msg)
        print(response)


if __name__ == '__main__':
    registry_ipaddr = sys.argv[1].split(':')[0]
    registry_port = sys.argv[1].split(':')[1]
    ipaddr = sys.argv[2].split(':')[0]
    port = sys.argv[2].split(':')[1]

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
