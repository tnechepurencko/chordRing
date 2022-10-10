import sys
import grpc
import zlib
import chord_pb2_grpc as pb2_grpc
import chord_pb2 as pb2

registry_ipaddr = sys.argv[1].split(':')[0]
registry_port = sys.argv[1].split(':')[1]
ipaddr = sys.argv[2].split(':')[0]
port = sys.argv[2].split(':')[1]

channel = grpc.insecure_channel(f'{registry_ipaddr}:{registry_port}')
stub = pb2_grpc.RegistryStub(channel)


class Node(pb2_grpc.NodeServicer):
    def __init__(self):
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

    def get_finger_table(self, request, context):
        msg = pb2.PFTRequest(id=self.node_id)
        rsp = stub.populate_finger_table(msg)  # TODO must be a list if dicts
        reply = {'ft': rsp.ft}
        return pb2.GFTReply(**reply)

    def save(self, request, context):
        key = request.key
        text = request.text
        hash_value = zlib.adler32(key.encode())
        target_id = hash_value % 2 ** self.m

        if target_id == self.node_id:
            if key in self.saved.keys():
                reply = {'stat': False, 'error': f'The key {key} is already exist'}
            else:
                self.saved[key] = text
                reply = {'stat': True, 'id': self.node_id}
        else:
            msg = pb2.PFTRequest(id=self.node_id)
            rsp = stub.populate_finger_table(msg)  # TODO must be a list if dicts
            ft = rsp.ft

            transfer_to = -1
            for node in ft:
                if node['id'] == target_id:
                    transfer_to = target_id
                    break

            if transfer_to == -1:
                ids = sorted(list(node['id'] for node in ft))
                if self.node_id == ids[-1]:
                    transfer_to = ids[0]
                else:
                    for id in ids:
                        if id > self.node_id:
                            transfer_to = id

            self.transfer(transfer_to, target_id, text)  # TODO make transfer




    def remove(self, request, context):
        pass

    def find(self, request, context):
        pass

    def quit(self):
        msg = pb2.DeregisterRequest(id=self.node_id)
        rsp = stub.deregister(msg)
        if not rsp.stat:
            print('The node did not pass registration')
        print('Quitting')
        sys.exit(0)










