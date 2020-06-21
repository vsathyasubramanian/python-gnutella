import select
import sys
import tabulate
import variable
import socket

from util import *


class RequestOperation(object):
    def __init__(self):
        pass

    def __print_payload_data(self, payload_data):
        header = ['SERVENT LISTENER IP ADDR', 'SERVENT LISTENER PORT NO', 'FILE_NAME']
        values = list(payload_data.values())
        row = [values]
        sys.stdout.write("\n")
        sys.stdout.write(tabulate.tabulate(row, header))
        sys.stdout.write("\n")

    def __print_qhit_data(self, payload_data):
        if payload_data:
            header = payload_data[0].keys()
            rows = []
            for record in payload_data:
                rows.append(list(record.values()))
            sys.stdout.write("\n")
            sys.stdout.write(tabulate.tabulate(rows, header))
            sys.stdout.write("\n")
        else:
            sys.stdout.write("\nFile not available!!\n")

    def __add_file_descriptors(self, payload_data):
        for file_data in payload_data:
            file_id = len(variable.file_descriptor) + 1
            variable.file_descriptor[file_id] = file_data

    def get_available_files(self):
        if variable.file_descriptor:
            header = ['FILE_ID', 'SERVENT_LISTENER IP ADDR', 'SERVENT LISTENER PORT NO', 'FILE_PATH', 'FILE_SIZE']
            rows = []
            for key, values in variable.file_descriptor.items():
                row_data = [key]
                row_data.extend(list(values.values()))
                rows.append(row_data)
            sys.stdout.write("\n")
            sys.stdout.write(tabulate.tabulate(rows, header))
            sys.stdout.write("\n")
        else:
            sys.stdout.write("\nNo File available for download!!\n")

    def get_connected_hosts(self):
        if variable.connections:
            header = ['CONNECTION_ID', 'SERVENT_LISTENER IP ADDR', 'SERVENT LISTENER PORT NO']
            rows = []
            for key, values in variable.connections.items():
                row_entry = [key]
                row_entry.extend(values)
                rows.append(row_entry[:-1])  # skipping socket object
            sys.stdout.write("\n")
            sys.stdout.write(tabulate.tabulate(rows, header))
            sys.stdout.write("\n")
        else:
            sys.stdout.write("\nNo Open Connections!!\n")

    def send_ping_request(self, sock):
        request = createMessage(servent_ip=sock.getsockname()[0], responder_port=sock.getsockname()[1],
                                msg_type='MSG_PING', ttl=1)
        sock.send(request)
        ready = select.select([sock], [], [], 10.0)
        if ready[0]:
            pong_response = sock.recv(4096)  # 4096
        header_message, payload_message = parseMessage(pong_response)
        self.__print_payload_data(payload_message)

    def send_query_request(self, sock, search_query):
        payload_message = search_query
        request = createMessage(servent_ip=sock.getsockname()[0], responder_port=sock.getsockname()[1],
                                msg_type='MSG_QUERY', ttl=2, payload=payload_message)
        sock.send(request)
        ready = select.select([sock], [], [], 10.0)
        if ready[0]:
            query_hit_response = sock.recv(4096)  # 4096
        header_message, payload_message = parseMessage(query_hit_response)
        self.__add_file_descriptors(payload_message['data'])
        self.__print_qhit_data(payload_message['data'])

    def download_file(self, file_descriptor):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((str(file_descriptor['ip_addr']), int(file_descriptor['port'])))
        payload_message = json.dumps({'file_path': file_descriptor['file_path'],
                                      'file_size': file_descriptor['file_size']})
        request = createMessage(servent_ip=sock.getsockname()[0], responder_port=sock.getsockname()[1],
                                msg_type='MSG_DOWNLOAD', ttl=1, payload=payload_message,
                                payload_type='application/json')
        sock.send(request)
        ready = select.select([sock], [], [], 10.0)
        if ready[0]:
            file_obj = open('downloaded_' + file_descriptor['file_path'], "wb")
            download_response = sock.recv(4096)  # 4096
            file_obj.write(download_response)
            file_obj.close()
        variable.file_descriptor.clear()
        sock.close()
        sys.stdout.write("\nDownload Complete!!\n")


########################################################################################################################

#
# if __name__ == "__main__":
#     try:
#         client_process()
#     except KeyboardInterrupt:
#         print("Terminating run.......")
