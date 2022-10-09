import sys
import random

port = sys.argv[1]
m = int(sys.argv[2])

id_ipaddr_port_dict = dict()


def register(ipaddr, port):
    random.seed(0)
    if len(id_ipaddr_port_dict) < 2 ** m:
        new_id = random.randint(0, 2 ** m - 1)
        while new_id in id_ipaddr_port_dict.keys():
            new_id = random.randint(0, 2 ** m - 1)
        id_ipaddr_port_dict[new_id] = f'{ipaddr}:{port}'
        return new_id, m
    return -1, 'Chord is full'


def deregister(node_id):
    if node_id in id_ipaddr_port_dict.keys():
        id_ipaddr_port_dict.pop(node_id)
        return True, f'The node {node_id} deregistered successfully'
    return False, f'The node {node_id} does not exist'


def succ_id(node_id):
    ids = sorted(list(id_ipaddr_port_dict.keys()))
    if node_id == ids[-1]:
        return ids[0]
    for id in ids:
        if id > node_id:
            return id


def pred_id(node_id):
    ids = sorted(list(id_ipaddr_port_dict.keys()), reverse=True)
    if node_id == ids[0]:
        return ids[-1]
    for id in ids:
        if id < node_id:
            return id


def populate_finger_table(node_id):
    finger_table_ids = set(succ_id((node_id + 2 ** (i - 1)) % (2 ** m)) for i in range(1, m + 1))
    finger_table = [(id, id_ipaddr_port_dict[id]) for id in finger_table_ids]
    return pred_id(node_id), finger_table


def get_chord_info():
    return [(key, id_ipaddr_port_dict[key]) for key in id_ipaddr_port_dict.keys()]




