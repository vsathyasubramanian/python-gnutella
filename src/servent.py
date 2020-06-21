import sys
import time
import variable
import logging

from request_operation import *
from response_operation import *
from PyInquirer import prompt
from pyfiglet import Figlet


def cli_prompt():
    request_object = RequestOperation()
    while True:
        Operation = prompt(request_operation_selection, style=style)['Operation']
        if Operation == 'List Open Connections':
            request_object.get_connected_hosts()
        elif Operation == 'Connect':
            input_data = prompt(connect_to_host, style=style)
            servent_ip = input_data['host_ip']
            listener_port = input_data['host_port']
            Node().start_connection(servent_ip, listener_port)
            sys.stdout.write("Connected to servent!!\n")
        elif Operation == 'Ping':
            if variable.connections:
                request_object.get_connected_hosts()
                connection_id = int(prompt(node_request, style=style)['connection_id'])
                request_object.send_ping_request(
                    variable.connections[connection_id][2])  # 3rd value is the socket object
            else:
                sys.stdout.write("\nNo connected hosts to ping!!")
        elif Operation == 'Find':
            if variable.connections:
                request_object.get_connected_hosts()
                connection_id = int(prompt(node_request, style=style)['connection_id'])
                file_name = prompt(find_request, style=style)['file_name']
                request_object.send_query_request(variable.connections[connection_id][2],
                                                  file_name)  # 3rd value is the socket object
            else:
                sys.stdout.write("\nNo connected hosts to fire search!!")

        elif Operation == 'Download':
            if variable.file_descriptor:
                request_object.get_available_files()
                file_id = int(prompt(download_file, style=style)['file_id'])
                request_object.download_file(variable.file_descriptor[file_id])
            else:
                sys.stdout.write("\nNo file available for download!!")

        elif Operation == 'Close Connection':
            if variable.connections:
                request_object.get_connected_hosts()
                connection_id = int(prompt(close_connection, style=style)['connection_id'])
                Node().close_connection(connection_id,
                                        variable.connections[connection_id][2])  # 3rd value is the socket object
            else:
                sys.stdout.write("\nNo connected hosts to ping!!")
        elif Operation == 'ShutDown':
            if variable.connections:
                sys.stdout.write("\nOpen Connections found....closing all connections!!")
                connection_list = list(variable.connections.keys())
                for connection_id in connection_list:
                    Node().close_connection(connection_id,
                                            variable.connections[connection_id][2])  # 3rd value is the socket object
                sys.stdout.write("\n Shutting Down....!!")
            break
        sys.stdout.write("\n")
        # prompt(continue_prompt, style=style)
        # os.system('cls')
        # sys.stdout.flush()


def initiate_logging():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    log_file_name = 'server_log_' + str(variable.PORT) + '.log'
    logging.basicConfig(filename=log_file_name, filemode='w', format='%(message)s', level=logging.DEBUG)


if __name__ == "__main__":
    variable.PORT = int(sys.argv[1])
    # preparing logging setup for server
    initiate_logging()
    f = Figlet(font='slant')
    print(f.renderText('Peer to Peer Network'))

    try:
        server_thread = threading.Thread(target=server_process, args=[variable.PORT])
        server_thread.daemon = True
        print("triggering server thread.......")
        server_thread.start()
        for i in range(101):
            time.sleep(0.005)  # arbitrary wait
            sys.stdout.write("\r%d%%" % i)
            sys.stdout.flush()
        print("\ntriggering cli prompt.......\n")
        cli_prompt()

    except KeyboardInterrupt:
        print("Terminating run.......")
