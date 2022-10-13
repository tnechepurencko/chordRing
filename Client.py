import chord_pb2_grpc as pb2_grpc
import chord_pb2 as pb2
import grpc

if __name__ == "__main__":
    connected_registry = False
    connected_node = False

    while True:
        instruction = input()

        if len(instruction.split()) == 1:
            command = instruction
        else:
            command = instruction.split()[0]
            arg = ' '.join(instruction.split()[1:])

        if command == "connect":
            if connected_registry or connected_node:
                channel.close()
                connected_node = False
                connected_registry = False
            channel = grpc.insecure_channel(arg)
            try:
                stub = pb2_grpc.RegistryStub(channel)
                msg = pb2.Empty()
                response = stub.who_am_i(msg)
                connected_registry = True
                print(response.reply)
            except:
                stub = pb2_grpc.NodeStub(channel)
                msg = pb2.Empty()
                response = stub.who_am_i(msg)
                connected_node = True
                print(response.reply)

        elif command == "get_info":
            if connected_registry:
                msg = pb2.Empty()
                response = stub.get_chord_info(msg)
                for ci in response.ci:
                    print(f'{ci.id}:\t{ci.addr}')
            elif connected_node:
                msg = pb2.Empty()
                wai_response = stub.who_am_i(msg)
                response = stub.get_finger_table(msg)
                print('Node id:', wai_response.id, '\nFinger table:')
                for ft in response.ft:
                    print(f'{ft.id}:\t{ft.addr}')
            else:
                print("Not connected to registry/node")

        elif command == "save":
            if connected_node:
                key = arg.split()[0][1:len(arg.split()[0]) - 1]
                text = ' '.join(arg.split()[1:])
                msg = pb2.SaveRequest(key=key, text=text)
                response = stub.save(msg)
                if response.stat:
                    print(f'{response.stat}, \"{key}\" is saved in node {response.id}')
                else:
                    print(f'{response.stat}, {response.error}')
            else:
                print("Not connected to node")

        elif command == "remove":
            if connected_node:
                msg = pb2.RemoveRequest(key=arg)
                response = stub.remove(msg)
                if response.stat:
                    print(f'{response.stat}, \"{arg}\" is removed from node {response.id}')
                else:
                    print(f'{response.stat}, {response.error}')
            else:
                print("Not connected to node")

        elif command == "find":
            if connected_node:
                msg = pb2.FindRequest(key=arg)
                response = stub.find(msg)
                if response.stat:
                    print(f'{response.stat}, \"{arg}\" is saved in node {response.id}')
                else:
                    print(f'{response.stat}, {response.error}')
            else:
                print("Not connected to node")

        elif command == "quit":
            break

        else:
            print("Wrong command")

    print("Terminating")
