import asyncio
import argparse
import json
import struct

class ChatServer(asyncio.Protocol):
    messages_list = {'MESSAGES': []}
    transport_list = {}

    def __init__(self):
        self.user = ''
        self.data = ''
        self.length = 0
        self.saved_users = {}
        self.file_list = {'FILE_LIST': []}


    def connection_made(self, transport):
        self.transport = transport
        self.first_msg = True

    def send_message(self, data):
        for k, v in ChatServer.transport_list:
            ChatServer.v.write(data)
        # self.transport.write(data)

    def data_received(self, data):
        if self.data == '':
            self.length = struct.unpack("!I", data[0:4])[0]
            data = data[4: self.length + 4]

        self.data += data.decode('ascii')

        if len(self.data) == self.length:
            recv_data = json.loads(self.data)
            full_data = {}
            full_data['USERS_JOINED'] = []

            if 'USERNAME' in recv_data:
                result = self.username_check(recv_data['USERNAME'])
                full_data['USERNAME_ACCEPTED'] = result
                if result:
                    ChatServer.transport_list[recv_data['USERNAME']] = self.transport
                    self.user = recv_data['USERNAME']

                    full_data['USERS_JOINED'].append(self.user)
                    full_data['INFO'] = 'Welcome the CYOSP Chatroom'
                    for k in self.transport_list:
                        full_data['USER_LIST'].append(k)
                    #print(ChatServer.messages_list['MESSAGES'])
                    full_data['MESSAGES'] = ChatServer.messages_list['MESSAGES']

            if 'IP' in recv_data:
                if not recv_data['IP'][0]:
                    for k, v in self.saved_users.items():
                        if k == recv_data['IP'][1]:
                            full_data['USERNAME_ACCEPTED'] = True
                            full_data['USERNAME'] = v
                else:
                    for k, v in self.saved_users.items():
                        if k == recv_data['IP'][1]:
                            full_data['IP'] = (self.user, 'A Username is already save to this ip address')
                    if not full_data['IP']:
                        self.saved_users[recv_data['IP'][1]] = self.user
                        full_data['IP'] = (self.user, 'Username save to Server')

            if 'MESSAGES' in recv_data:
                if recv_data['MESSAGES'] == '/users':
                    for i in ChatServer.transport_list:
                        full_data['USER_LIST'].append(i)
                if recv_data['MESSAGES'] == '/file_list':
                    full_data['FILE_LIST'] = self.file_list['FILE_LIST']
                else:
                    ChatServer.messages_list['MESSAGES'].append(recv_data['MESSAGES'][-1]) # get most recent msg?
                    print(ChatServer.messages_list['MESSAGES'])
                    full_data['MESSAGES'] = ChatServer.messages_list['MESSAGES']

            if 'FILE_DOWNLOAD' in recv_data:
                if recv_data['FILE_DOWNLOAD'][0] in self.file_list['FILE_LIST']:
                    try:
                        open_file = open(recv_data['FILE_DOWNLOAD'][0], 'r')
                        data = open_file.read()
                        full_data['FILE_DOWNLOAD'] = (self.user, data, recv_data['FILE_DOWNLOAD'][0])
                    except exec as e:
                        full_data['ERROR'] += e
                else:
                    full_data['FILE_DOWNLOAD'] = (self.user, 'File not on Server', 'ERROR')

            if 'FILE_UPLOAD' in recv_data:
                if recv_data['FILE_UPLOAD'][0] in self.file_list['FILE_LIST']:
                    full_data['FILE_UPLOAD'] = (self.user, recv_data['FILE_UPLOAD'][0],
                                                'ERROR')
                else:
                    try:
                        open_file = open(recv_data['FILE_UPLOAD'][0], 'w+')
                        open_file.write(recv_data['FILE_UPLOAD'][1])
                        open_file.close()
                        full_data['FILE_UPLOAD'] = (self.user, recv_data['FILE_UPLOAD'][0], 'SUCCESS')

                    except exec as e:
                        full_data['ERROR'] += e

            if self.first_msg:
                data_json = json.dumps(full_data)
                byte_json = data_json.encode('ascii')
                byte_count = struct.pack('!I', len(byte_json))
                self.joinning_message(byte_count, self.transport)
                self.joinning_message(byte_json, self.transport)

                joined_list = {'USER_JOINED': full_data['USERS_JOINED']}
                user_json = json.dumps(joined_list)
                byte_user = user_json.encode('ascii')
                byte_count_user = struct.pack('!I', len(byte_user))
                self.send_message(byte_count_user)
                self.send_message(byte_user)
                self.first_msg = False

            else:
                data_json = json.dumps(full_data)
                byte_json = data_json.encode('ascii')
                byte_count = struct.pack('!I', len(byte_json))
                self.send_message(byte_count)
                self.send_message(byte_json)
            self.data = ''

    def connection_lost(self, exc):
        ChatServer.transport_list.remove(self.transport)
        full_data = {'USERS_LEFT': []}

        if exc:
            full_data['USERS_LEFT'].append(self.user)
            full_data['ERROR'] += '{} has left unexpectedly. Error: {}'.format(self.user, exc)
            ChatServer.user_list['USER_LIST'].remove(self.user)
        else:
            full_data['USERS_LEFT'].append(self.user)
            ChatServer.user_list['USER_LIST'].remove(self.user)
        data_json = json.dumps(full_data)
        byte_json = data_json.encode('ascii')
        byte_count = struct.pack('!I', len(byte_json))
        self.send_message(byte_count)
        self.send_message(byte_json)

    def username_check(self, name):

        if name not in ChatServer.transport_list:
            for k, v in self.saved_users.items():
                if v == name:
                    return False
            return True
        else:
            return False

    def joinning_message(self, data, new_user_transport):
        for k, v in ChatServer.transport_list:
            if v == new_user_transport:
                ChatServer.v.write(data)



def parse_command_line(description):
    """
        A function to parse the command line options given to the program
    :param description: description of the program
    :return: A tuple of args
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('host', help='IP or hostname')
    parser.add_argument('-p', metavar='port', type=int, default=9000,
                        help='TCP port (default 7000)')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address


if __name__ == '__main__':
    address = parse_command_line('asyncio server using callbacks')
    loop = asyncio.get_event_loop()
    coro = loop.create_server(ChatServer, *address)
    server = loop.run_until_complete(coro)
    print('Listening at {}'.format(address))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()