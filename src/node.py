import select
import socket
import variable

from util import *


class Node(object):
    def __init__(self):
        pass

    def start_connection(self, host_ip, host_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((str(host_ip), int(host_port)))

        connection_id = len(variable.connections) + 1
        # adding connection to global connection variable to prevent ininite looping
        variable.connections[connection_id] = [sock.getpeername()[0], sock.getpeername()[1], sock]

        ############################################# INITIATING HAND SHAKE ############################################

        request = createMessage(servent_ip=sock.getsockname()[0], responder_port=sock.getsockname()[1],
                                msg_type='MSG_JOIN', ttl=1)
        sock.send(request)
        ready = select.select([sock], [], [], 10.0)
        if ready[0]:
            reply = sock.recv(4096)  # 4096
        header_message, payload_message = parseMessage(reply)
        if payload_message == 'JOIN_OK':
            return True
        else:
            # removing connection from global connection variable --> roll back
            del variable.connections[connection_id]
            return False

    def close_connection(self, connection_id, sock):
        # removing the connection data to prevent infinite close conn calls
        connection_data = variable.connections.pop(connection_id)

        request = createMessage(servent_ip=sock.getsockname()[0], responder_port=sock.getsockname()[1],
                                msg_type='MSG_CLOSE')
        sock.send(request)
        ready = select.select([sock], [], [], 10.0)

        if ready[0]:
            reply = sock.recv(4096)  # 4096
        header_message, payload_message = parseMessage(reply)
        if payload_message == 'CLOSE_OK':
            sock.close()
            return True
        else:
            # adding the connection back --> roll back
            variable[connection_id] = connection_data
            return False
