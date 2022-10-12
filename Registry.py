from concurrent import futures
import grpc
import chord_pb2_grpc as pb2_grpc
import chord_pb2 as pb2
import sys
import random


class Registry(pb2_grpc.RegistryServicer):
    def register(self, request, context):
        random.seed(0)
        node_ipaddr = request.ipaddr
        node_port = request.port

        if len(id_ipaddr_port_dict) < 2 ** m:
            new_id = random.randint(0, 2 ** m - 1)
            while new_id in id_ipaddr_port_dict.keys():
                new_id = random.randint(0, 2 ** m - 1)
            id_ipaddr_port_dict[new_id] = f'{node_ipaddr}:{node_port}'
            reply = {'id': new_id, 'm': m}
        else:
            reply = {'id': -1, 'error': 'Chord is full'}

        return pb2.RegisterReply(**reply)

    def deregister(self, request, context):
        node_id = request.id

        if node_id in id_ipaddr_port_dict.keys():
            id_ipaddr_port_dict.pop(node_id)
            reply = {'stat': True, 'msg': f'The node {node_id} deregistered successfully'}
        else:
            reply = {'stat': False, 'msg': f'The node {node_id} does not exist'}

        return pb2.DeregisterReply(**reply)

    @staticmethod
    def succ_id(node_id):
        ids = sorted(list(id_ipaddr_port_dict.keys()))
        if node_id >= ids[-1]:
            return ids[0]
        for id in ids:
            if id >= node_id:
                return id

    @staticmethod
    def pred_id(node_id):
        ids = sorted(list(id_ipaddr_port_dict.keys()), reverse=True)
        if node_id <= ids[-1]:
            return ids[0]
        for id in ids:
            if id < node_id:
                return id

    def populate_finger_table(self, request, context):
        node_id = request.id
        finger_table_ids = set(self.succ_id((node_id + 2 ** (i - 1)) % (2 ** m)) for i in range(1, m + 1))
        finger_table = [{'id': id, 'addr': id_ipaddr_port_dict[id]} for id in finger_table_ids]  # TODO correct REPEATED stuff
        reply = {'predID': self.pred_id(node_id), 'ft': finger_table}
        return pb2.PFTReply(**reply)

    def get_chord_info(self, request, context):
        chord_info = pb2.GCIReply(ci=[pb2.CI(id=key, addr=id_ipaddr_port_dict[key]) for key in id_ipaddr_port_dict.keys()])
        return chord_info

    def who_am_i(self, request, context):
        reply = {'reply': "Connected to registry"}
        return pb2.WAIResponse(**reply)


if __name__ == '__main__':
    port = sys.argv[1]
    m = int(sys.argv[2])
    id_ipaddr_port_dict = dict()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_RegistryServicer_to_server(Registry(), server)
    server.add_insecure_port('127.0.0.1:' + port)
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print('shutting down')
