import socket
import select

HEADER_LENGTH = 10

ip = " 192.168.179.9"
port_num = 1234

# Create a socket
# socket.AF_INET - address family, ipv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw ip packets
socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given ip and port_num
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface ip
socket1.bind((ip, port_num))

# This makes server listen to new connections
socket1.listen()

# List of sockets for select.select()
sockets_list = [socket1]

# List of connected clients - socket as a key, user header and name as data
clients = {}

# List of connected clients - socket as a key, user header and name as data
chatclients = {}

print(f'Listening for connections on {ip}:{port_num}...')

# Handles message receiving
def receive_message(socket2):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = socket2.recv(HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': socket2.recv(message_length)}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

while True:

    # Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == socket1:

            # Accept new connection
            # That gives us new socket - client socket, connected to this given client only, it's unique for that client
            # The other returned object is ip/port_num set
            socket2, client_address = socket1.accept()

            # Client should send his name right away, receive it
            user = receive_message(socket2)

            # If False - client disconnected before he sent his name
            if user is False:
                continue

            # Client should send his name right away, receive it
            chatuser = receive_message(socket2)

            # If False - client disconnected before he sent his chatuser name
            if chatuser is False:
                continue

            # Add accepted socket to select.select() list
            sockets_list.append(socket2)

            # Also save username and username header
            clients[socket2] = user

            # Also save chat username and chat username header
            chatclients[socket2] = chatuser
            
            print('Accepted new connection from {}:{}, username: {}, chatusername: {}'.format(*client_address, user['data'].decode('utf-8'), chatuser['data'].decode('utf-8')))

        # Else existing socket is sending a message
        else:

            # Receive message
            message = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)

                # Remove from our list of users
                del clients[notified_socket]

                continue

            # Get userv by notified socket, so we will know who sent the message
            user = clients[notified_socket]
                   
            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            # Iterate over connected clients and broadcast message
            for socket2 in clients:
            
                # Get chat user by client socket
                receiver_chatuser = chatclients[socket2]
                
                # Get user by notified socket, so we will know who sent the message
                receiver = clients[socket2]
                
                # Get userv by notified socket, so we will know who sent the message
                notified_user = clients[notified_socket]
            
                # Get chat user by notified socket
                notified_chatuser = chatclients[notified_socket]            

                # But don't sent it to sender
                if socket2 != notified_socket:                

                    # Send message all chat users
                    if notified_chatuser["data"].decode("utf-8") == "all":

                        # Send user and message (both with their headers)
                        # We are reusing here message header sent by sender, and saved username header send by user when he connected
                        socket2.send(notified_user['header'] + notified_user['data'] + message['header'] + message['data'])
                
                    # Send message to chat user
                    if receiver["data"].decode("utf-8") == notified_chatuser["data"].decode("utf-8"):

                        # Send user and message (both with their headers)
                        # We are reusing here message header sent by sender, and saved username header send by user when he connected
                        socket2.send(notified_user['header'] + notified_user['data'] + message['header'] + message['data'])

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]