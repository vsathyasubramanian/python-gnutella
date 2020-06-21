import logging
import select
import socket
import sys
import threading

from node import Node
from util import *


class ResponseOperation(object):
    def __init__(self):
        self.ip_address = None
        self.port_no = None
        self.socket = None

    def __pong_response(self, conn_socket):
        logging.info(
            "PING message from client --> ip address :: {0} and port no :: {1}".format(conn_socket.getpeername()[0],
                                                                                       conn_socket.getpeername()[
                                                                                           1]))
        logging.info(" Responding with a PONG message")
        payload_message = {'servent_ip': conn_socket.getsockname()[0],
                           'servent_port': conn_socket.getsockname()[1],
                           'Public data': return_mock_search_idx(conn_socket.getsockname()[1])}
        payload_message = json.dumps(payload_message)
        message = createMessage(servent_ip=conn_socket.getsockname()[0], responder_port=conn_socket.getsockname()[1],
                                msg_type='MSG_PONG', ttl=1,
                                payload=payload_message, payload_type='application/json')
        conn_socket.send(message)
        logging.info("Responded to PING request")

    def __join_response(self, conn_socket):
        logging.info(
            "JOIN message from client --> ip address :: {0} and port no :: {1}".format(
                conn_socket.getpeername()[0],
                conn_socket.getpeername()[
                    1]))

        message = createMessage(servent_ip=conn_socket.getsockname()[0], responder_port=conn_socket.getsockname()[1],
                                msg_type='MSG_JOIN',
                                payload="JOIN_OK")
        conn_socket.send(message)
        logging.info("Responded to JOIN request")

    def __create_duplex_connection(self, header_message):
        # check if connection exists
        for key, value in variable.connections.items():
            if value[0] == header_message['servent_ip'] and value[1] == header_message['listener_port']:
                # connection already exists.
                return
        Node().start_connection(header_message['servent_ip'], header_message['listener_port'])

    def __remove_duplex_connection(self, header_message):
        # check if connection exists
        for key, value in variable.connections.items():
            if value[0] == header_message['servent_ip'] and value[1] == header_message['listener_port']:
                # connection exists.
                Node().close_connection(key, value[2])
                return

    def __qhit_response(self, payload_message, conn_socket):
        logging.info(
            "QHIT response to client --> ip address :: {0} and port no :: {1}".format(conn_socket.getpeername()[0],
                                                                                      conn_socket.getpeername()[
                                                                                          1]))
        payload_message = {'data': payload_message}
        payload_message = json.dumps(payload_message)
        message = createMessage(servent_ip=conn_socket.getsockname()[0], responder_port=conn_socket.getsockname()[1],
                                msg_type='MSG_QHIT', ttl=1,
                                payload=payload_message, payload_type='application/json')
        conn_socket.send(message)
        logging.info("QHit Sent")

    def __forward_request(self, header_message, request_message):
        payload_message = {'data': []}
        for key, value in variable.connections.items():
            if not (value[0] == header_message['servent_ip'] and value[1] == header_message['listener_port']):
                payload_message = request_message
                sock = value[2]
                request = createMessage(servent_ip=sock.getsockname()[0], responder_port=sock.getsockname()[1],
                                        msg_type='MSG_QUERY', ttl=header_message['ttl'],
                                        payload=payload_message)
                sock.send(request)
                ready = select.select([sock], [], [], 10.0)
                if ready[0]:
                    find_response = sock.recv(4096)  # 4096
                header_message, payload_message = parseMessage(find_response)
        return payload_message

    def __find_resource(self, header_message, request_message, conn_socket):
        response_payload = []
        available_resources = return_mock_search_idx(conn_socket.getsockname()[1])
        if request_message in available_resources:
            # hit found!! add to response payload
            response_payload.append({
                'ip_addr': variable.HOST,
                'port': variable.PORT,
                'file_path': request_message,
                'file_size': file_details[request_message]
            })
        if header_message['ttl'] > 1:
            header_message['ttl'] -= 1
            forward_response = self.__forward_request(header_message, request_message)
            response_payload.extend(forward_response['data'])
        return response_payload

    def __send_file(self,payload_data,conn_socket):
        file_location = "data/" + str(payload_data['file_path'])
        with open(file_location, "rb") as f:
            # read the bytes from the file
            bytes_read = f.read()
            # we use sendall to assure transimission in
            # busy networks
            conn_socket.sendall(bytes_read)

    def __close_response(self, conn_socket):
        logging.info("CLOSE message from client --> ip address :: {0} and port no :: {1}".format(
            conn_socket.getpeername()[0],
            conn_socket.getpeername()[1]))
        message = createMessage(servent_ip=conn_socket.getsockname()[0], responder_port=conn_socket.getsockname()[1],
                                msg_type='MSG_CLOSE', ttl=1,
                                payload="CLOSE_OK")
        conn_socket.send(message)
        logging.info("Responded to CLOSE request")

    def start_server_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip_address, self.port))
        print("Can be reached at " + str(self.socket.getsockname()))
        self.socket.listen(5)

    def process_request(self, conn_socket):
        try:
            connected = True
            while connected:
                message = conn_socket.recv(1024)
                if not message:
                    break
                header_message, payload_message = parseMessage(message)
                # Disconnect after CLOSE
                if header_message['msg_type'] == 'MSG_CLOSE':
                    connected = False
                self.process_message(header_message, payload_message, conn_socket)
            conn_socket.close()
        except KeyboardInterrupt:
            return

    def process_message(self, header_message, payload_message, conn_socket):
        if header_message['msg_type'] == 'MSG_PING':
            self.__pong_response(conn_socket)
        elif header_message['msg_type'] == 'MSG_JOIN':
            self.__create_duplex_connection(header_message)
            self.__join_response(conn_socket)
        elif header_message['msg_type'] == 'MSG_QUERY':
            payload = self.__find_resource(header_message, payload_message, conn_socket)
            self.__qhit_response(payload, conn_socket)
        elif header_message['msg_type'] == 'MSG_DOWNLOAD':
            self.__send_file(payload_message, conn_socket)
        elif header_message['msg_type'] == 'MSG_CLOSE':
            self.__remove_duplex_connection(header_message)
            self.__close_response(conn_socket)


def server_process(port):
    response_obj = ResponseOperation()
    response_obj.ip_address = variable.HOST
    response_obj.port = port
    response_obj.start_server_socket()
    while True:
        (sock_conn, address) = response_obj.socket.accept()
        logging.info("Connection accepted!!")
        ct = threading.Thread(target=response_obj.process_request, args=[sock_conn])
        ct.daemon = True
        ct.start()
    sock.close()


########################################################################################################################

#
# if __name__ == "__main__":
#     port = int(sys.argv[1])
#     # preparing logging setup for server
#     for handler in logging.root.handlers[:]:
#         logging.root.removeHandler(handler)
#     log_file_name = 'server_log_' + str(port) + '.log'
#     logging.basicConfig(filename=log_file_name, filemode='w', format='%(message)s', level=logging.DEBUG)
#     try:
#         server_process(port)
#     except KeyboardInterrupt:
#         print("Terminating run.......")
