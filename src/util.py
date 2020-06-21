import os
import json
import struct
import variable

from PyInquirer import style_from_dict, Token

##################################################Console formater#####################################################

style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

request_operation_selection = [
    {
        'type': 'list',
        'message': 'Choose option',
        'name': 'Operation',
        'choices': ['List Open Connections', 'Connect', 'Ping', 'Find', 'Download', 'Close Connection', 'ShutDown'],
        'validate': lambda answer: 'Please choose atleast one option.' \
            if len(answer) == 0 else True
    }
]
connect_to_host = [
    {
        'type': 'input',
        'name': 'host_ip',
        'message': 'Enter host ip address',
        'default': '127.0.0.1'
    },
    {
        'type': 'input',
        'name': 'host_port',
        'message': 'Enter host port number'
    }
]
node_request = [
    {
        'type': 'input',
        'name': 'connection_id',
        'message': 'Enter connection_id',
        'default': '1'
    }
]

find_request = [
    {
        'type': 'input',
        'name': 'file_name',
        'message': 'Enter file name to search',
        'default': ''
    }
]

download_file = [
    {
        'type': 'input',
        'name': 'file_id',
        'message': 'Enter file_id to download',
        'default': '1'
    }
]

close_connection = [
    {
        'type': 'input',
        'name': 'connection_id',
        'message': 'Enter connection_id',
        'default': '1'
    }
]

continue_prompt = [
    {
        'type': 'confirm',
        'message': '',
        'name': 'continue',
        'default': True,
    }
]


################################################## HELPER METHODS ######################################################


def _json_encode(obj, encoding):
    return json.dumps(obj, ensure_ascii=False).encode(encoding)


def _json_decode(request_message, encoding):
    message = json.loads(request_message.decode(encoding))
    return message


def process_protoheader(request_message):
    hdrlen = 2
    _jsonheader_len = 0
    if len(request_message) >= hdrlen:
        _jsonheader_len = struct.unpack(
            "<H", request_message[:hdrlen]
        )[0]
        request_message = request_message[hdrlen:]
    return _jsonheader_len, request_message


def constructHeader(ttl, responder_port, servent_ip, msg_type, payload_length, payload_type):
    """

    header format
     =====================================================================================================
     0 +------------+------------+------------+-------------------+
       |                   HEADER LENGTH                          |
       +------------+------------+------------+-------------------+
       |     KEY                 |   VALUE                        |
     2 +-------------------------+--------------------------------+
       |     ttl                 |   time to live                 |
       |     msg_type            |   message type                 |
       |     servent_ip          |   servent_ip                   |
       |     responder_port      |   servent responder port number|
       |     listener_port       |   servent listener port number |
       |     payload_length      |   payload_length               |
       |     payload_type        |   payload_type                 |
     N +------------+------------+------------+-------------------+
     ====================================================================================================
    """

    jsonheader = {
        "ttl": ttl,
        "msg_type": msg_type,
        "servent_ip": servent_ip,
        "responder_port": responder_port,
        "listener_port": variable.PORT,
        "payload_length": payload_length,
        "payload_type": payload_type
    }
    jsonheader_bytes = _json_encode(jsonheader, "utf-8")
    message_hdr = struct.pack("<H", len(jsonheader_bytes))
    header_message = message_hdr + jsonheader_bytes
    return header_message


def createMessage(responder_port, servent_ip, msg_type='MSG_PING', ttl=1, payload="", payload_type=None):
    """
    message format:
     =====================================================================================================

     0 +------------+------------+------------+------------+
       |                 FIXED LENGTH HEADER               |
     2 +------------+------------+------------+------------+
       |                VARIABLE LENGTH HEADER             |
     N +------------+------------+------------+------------+
       |                                                   |
       |                      PAYLOAD                      |
       |                                                   |
     M +------------+------------+------------+------------+
     ====================================================================================================
    """

    message = constructHeader(ttl=ttl, responder_port=responder_port, servent_ip=servent_ip, msg_type=msg_type,
                              payload_length=len(payload), payload_type=payload_type)
    if payload:
        message += payload.encode('utf-8')
    return message


def parseMessage(request_message):
    header_len, request_message = process_protoheader(request_message)
    header_message = request_message[:header_len]
    request_message = request_message[header_len:]
    header_message = _json_decode(header_message, 'utf-8')
    payload_length = header_message.get('payload_length', 0)
    payload_message = ""
    if payload_length:
        payload_message = request_message[:payload_length].decode('utf-8')
        if header_message.get('payload_type') == 'application/json':
            payload_message = json.loads(payload_message)
    return header_message, payload_message


############################################          PAYLOAD DATA          ############################################


payload_data = {
    # [file_name, size]
    0: {'search': ['file_1.txt', 'file_2.txt', 'file_3.txt'],
        'specs': [['file_1.txt', os.path.getsize("data\\file_1.txt"), 512],
                  ['file_2.txt', os.path.getsize("data\\file_2.txt"), 512],
                  ['file_3.txt', os.path.getsize("data\\file_3.txt"), 512]]},
    1: {'search': ['file_4.txt', 'file_1.txt', 'file_6.txt'],
        'specs': [['file_4.txt', os.path.getsize("data\\file_4.txt"), 512],
                  ['file_1.txt', os.path.getsize("data\\file_1.txt"), 512],
                  ['file_6.txt', os.path.getsize("data\\file_6.txt"), 512]]},
    2: {'search': ['file_1.txt', 'file_8.txt', 'file_9.txt'],
        'specs': [['file_1.txt', os.path.getsize("data\\file_1.txt"), 512],
                  ['file_8.txt', os.path.getsize("data\\file_8.txt"), 512],
                  ['file_9.txt', os.path.getsize("data\\file_9.txt"), 512]]}
}

file_details = {
    'file_1.txt':os.path.getsize("data\\file_1.txt"),
    'file_2.txt':os.path.getsize("data\\file_2.txt"),
    'file_3.txt':os.path.getsize("data\\file_3.txt"),
    'file_4.txt':os.path.getsize("data\\file_4.txt"),
    'file_6.txt':os.path.getsize("data\\file_6.txt"),
    'file_8.txt':os.path.getsize("data\\file_8.txt"),
    'file_9.txt':os.path.getsize("data\\file_9.txt")
}

def return_mock_payload(port):
    payload_key = (port % 10) % 3
    return payload_data[payload_key]['specs']


def return_mock_search_idx(port):
    payload_key = (port % 10) % 3
    return payload_data[payload_key]['search']
