import socket
import select
import errno

LENGTH = 10

ip = "127.0.0.1"
port_num = 1234
my_user_name = input("username: ")
chat_with = input("Chat with: ")

# Create a socket
# socket.AF_INET - address family, ipv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw ip packets
socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to a given ip and port_num
socket2.connect((ip, port_num))

# Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
socket2.setblocking(False)

# Prepare user_name and header and send them
# We need to encode user_name to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
user_name = my_user_name.encode('utf-8')
user_name_header = f"{len(user_name):<{LENGTH}}".encode('utf-8')
socket2.send(user_name_header + user_name)

# Prepare chatwith and header and send them
# We need to encode user_name to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
chatwith = chat_with.encode('utf-8')
chatwith_header = f"{len(chatwith):<{LENGTH}}".encode('utf-8')
socket2.send(chatwith_header + chatwith)

while True:

    # Wait for user to input a message
    message = input(f'{my_user_name} > ')

    # If message is not empty - send it
    if message:

        # Encode message to bytes, prepare header and convert to bytes, like for user_name above, then send
        message = message.encode('utf-8')
        message_header = f"{len(message):<{LENGTH}}".encode('utf-8')
        socket2.send(message_header + message)
    # Wait for user to input a message
    message = input(f'{my_user_name} > ')

    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:

            # Receive our "header" containing user_name length, it's size is defined and constant
            user_name_header = socket2.recv(LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(user_name_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert header to int value
            user_name_length = int(user_name_header.decode('utf-8').strip())

            # Receive and decode user_name
            user_name = socket2.recv(user_name_length).decode('utf-8')

            # Now do the same for message (as we received user_name, we received whole message, there's no need to check if it has any length)
            message_header = socket2.recv(LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = socket2.recv(message_length).decode('utf-8')

            # Print message
            print(f'{user_name} > {message}')

    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
        sys.exit()