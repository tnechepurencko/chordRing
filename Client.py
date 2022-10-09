import chord_pb2_grpc as pb2_grpc
import chord_pb2 as pb2
import grpc

if __name__ == "__main__":
    connected_registry = False
    connected_node = False

    while True:
        instruction = input()
        command, arg = instruction.split()
        if command == "connect":
            try:
                if not connected_registry:
                    channel = grpc.insecure_channel("arg")
                    stub = pb2_grpc.RegistryStub(channel)
                    connected_registry = True
                    print("Connected to registry")
            except:
                if not connected_node:
                    try:
                        channel = grpc.insecure_channel("arg")
                        stub = pb2_grpc.NodeStub(channel)
                        connected_node = True
                        print("Connected to node")
                    except:
                        print("there is no registry/node on this address")
        elif command == "get_info":
            if connected_registry:
                msg = pb2.Empty()
                response = stub.get_chord_info(msg)
                print(response)
            elif connected_node:
                msg = pb2.Empty()
                response = stub.get_finger_table(msg)
                print(response)
            else:
                print("Not connected to registry/node")
        elif command == "save":
            if connected_node:
                key, text = arg.split()
                msg = pb2.SaveRequest(key = key, text = text)
                response = stub.save(msg)
            else:
                print("Not connected to node")
        elif command == "remove":
            if connected_node:
                msg = pb2.RemoveRequest(key = arg)
                response = stub.remove(msg)
            else:
                print("Not connected to node")
        elif command == "find":
            if connected_node:
                msg = pb2.FindRequest(key = arg)
                response = stub.find(msg)
            else:
                print("Not connected to node")
        elif command == "quit":
            break
        else:
            print("Wrong command")

    print("Terminating")
