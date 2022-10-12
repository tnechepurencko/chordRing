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
            command, arg = instruction.split()

        if command == "connect":
            if not connected_registry:
                try:
                    channel = grpc.insecure_channel(arg)
                    stub = pb2_grpc.RegistryStub(channel)
                    connected_registry = True
                    print("Connected to registry")
                except:
                    print("wrong address")
            elif not connected_node:
                try:
                    channel = grpc.insecure_channel(arg)
                    stub = pb2_grpc.NodeStub(channel)
                    print("Connected to node")
                except:
                    print("wrong address")
            else:
                print('already connected')

        elif command == "get_info":
            if connected_registry:
                msg = pb2.Empty()
                response = stub.get_chord_info(msg)

                for ci in response.ci:
                    print(f'{ci.id}:\t{ci.addr}')
            elif connected_node:
                msg = pb2.Empty()
                response = stub.get_finger_table(msg)
                print(response)
            else:
                print("Not connected to registry/node")

        elif command == "save":
            if connected_node:
                key, text = arg.split()
                msg = pb2.SaveRequest(key=key, text=text)
                response = stub.save(msg)
                print(response)
            else:
                print("Not connected to node")

        elif command == "remove":
            if connected_node:
                msg = pb2.RemoveRequest(key=arg)
                response = stub.remove(msg)
                print(response)
            else:
                print("Not connected to node")

        elif command == "find":
            if connected_node:
                msg = pb2.FindRequest(key=arg)
                response = stub.find(msg)
                print(response)
            else:
                print("Not connected to node")

        elif command == "quit":
            break

        else:
            print("Wrong command")

    print("Terminating")
