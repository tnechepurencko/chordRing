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
            if not connected_registry or not connected_node:
                channel = grpc.insecure_channel(arg)
                stub = pb2_grpc.RegistryStub(channel)
                msg = pb2.Empty()
                response = stub.who_am_i(msg)
                if response.reply == "Connected to registry":
                    connected_registry = True
                    print(response.reply)
                elif response.reply == "Connected to node":
                    connected_node = True
                    print(response.reply)
                else:
                    print("wrong address")
            else:
                print('already connected')
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
