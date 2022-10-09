# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import chord_pb2 as chord__pb2


class RegistryStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.register = channel.unary_unary(
                '/Registry/register',
                request_serializer=chord__pb2.RegisterRequest.SerializeToString,
                response_deserializer=chord__pb2.RegisterReply.FromString,
                )
        self.deregister = channel.unary_unary(
                '/Registry/deregister',
                request_serializer=chord__pb2.DeregisterRequest.SerializeToString,
                response_deserializer=chord__pb2.DeregisterReply.FromString,
                )
        self.populate_finger_table = channel.unary_unary(
                '/Registry/populate_finger_table',
                request_serializer=chord__pb2.PFTRequest.SerializeToString,
                response_deserializer=chord__pb2.PFTReply.FromString,
                )
        self.get_chord_info = channel.unary_unary(
                '/Registry/get_chord_info',
                request_serializer=chord__pb2.Empty.SerializeToString,
                response_deserializer=chord__pb2.GCIReply.FromString,
                )


class RegistryServicer(object):
    """Missing associated documentation comment in .proto file."""

    def register(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def deregister(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def populate_finger_table(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_chord_info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RegistryServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'register': grpc.unary_unary_rpc_method_handler(
                    servicer.register,
                    request_deserializer=chord__pb2.RegisterRequest.FromString,
                    response_serializer=chord__pb2.RegisterReply.SerializeToString,
            ),
            'deregister': grpc.unary_unary_rpc_method_handler(
                    servicer.deregister,
                    request_deserializer=chord__pb2.DeregisterRequest.FromString,
                    response_serializer=chord__pb2.DeregisterReply.SerializeToString,
            ),
            'populate_finger_table': grpc.unary_unary_rpc_method_handler(
                    servicer.populate_finger_table,
                    request_deserializer=chord__pb2.PFTRequest.FromString,
                    response_serializer=chord__pb2.PFTReply.SerializeToString,
            ),
            'get_chord_info': grpc.unary_unary_rpc_method_handler(
                    servicer.get_chord_info,
                    request_deserializer=chord__pb2.Empty.FromString,
                    response_serializer=chord__pb2.GCIReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Registry', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Registry(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def register(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Registry/register',
            chord__pb2.RegisterRequest.SerializeToString,
            chord__pb2.RegisterReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def deregister(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Registry/deregister',
            chord__pb2.DeregisterRequest.SerializeToString,
            chord__pb2.DeregisterReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def populate_finger_table(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Registry/populate_finger_table',
            chord__pb2.PFTRequest.SerializeToString,
            chord__pb2.PFTReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def get_chord_info(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Registry/get_chord_info',
            chord__pb2.Empty.SerializeToString,
            chord__pb2.GCIReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
