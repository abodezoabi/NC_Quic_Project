import socket  # Import socket module for network communication
import random  # Import random module for random number generation
import math  # Import math module for mathematical operations
import time  # Import time module for timing purposes
from api import (unpack_long_header, pack_long_header, pack_short_header, unpack_short_header, generate_random_file,
                 CONNECTION_CLOSE, generate_packet_number)  # Import various functions from the api module

CLIENT_HELLO = b'Hello, QUIC client!(Long header)'  # Define the client hello message

connections = {}  # Initialize a dictionary to store connections

# number of flows/streams
num_flows = 3  # Define the number of flows


def get_num_flows():
    return num_flows  # Return the number of flows


def start_quic_server():
    server_address = ('localhost', 4433)  # Define the server address and port
    buffer_size = 2048  # Define the buffer size for receiving data

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:  # Create a UDP socket
        server_socket.bind(server_address)  # Bind the socket to the server address
        print("QUIC server is running...")

        while True:
            data, client_address = server_socket.recvfrom(buffer_size)  # Receive data from a client
            print(f"Received {len(data)} bytes from {client_address}")

            if client_address not in connections:
                connection_id, packet_number, flow_id, payload = unpack_long_header(data)  # Unpack the received data
                print(f"Initial connection ID: {connection_id}, Packet number: {packet_number}, Flow ID: {flow_id}, Payload: {payload}")
                connections[client_address] = {
                    'connection_id': connection_id,
                    'flows': [],
                    'last_packet_number': packet_number,
                    'acks': set()
                }

                # Send client hello message
                send_client_hello(server_socket, client_address, connection_id)

                # Initialize flows
                for i in range(1, num_flows + 1):
                    packet_size = random.randint(1000, 2000)  # Randomize packet size between 1000 and 2000 bytes
                    file_size = 2 * 1024 * 1024  # 2MB
                    num_packets = math.ceil(file_size / packet_size)  # Calculate the number of packets needed
                    flow = {
                        'id': i,
                        'packet_size': packet_size,
                        'file_size': file_size,
                        'total_bytes': 0,
                        'total_packets': 0,
                        'start_time': time.time(),  # start timer
                        'end_time': 0,
                        'remaining_data': generate_random_file(file_size),  # Generate random file data
                        'packet_number': 0,
                        'num_packets': num_packets
                    }
                    connections[client_address]['flows'].append(flow)  # Append the flow to the client's flow list
                    print(f"Initialized flow {i} with packet size {packet_size} bytes.")

                # Start sending files to the client one flow at a time
                send_files_to_client(server_socket, client_address)

                # Send CONNECTION_CLOSE frame to the client
                send_connection_close(server_socket, client_address)

            else:
                packet_number, flow_id, payload = unpack_short_header(data)  # Unpack the received data

                if payload == b'ACK':
                    connections[client_address]['acks'].add((flow_id, packet_number))  # Add ACK to the client's ack set
                elif payload == CONNECTION_CLOSE:
                    print(f"Received CONNECTION_CLOSE from {client_address}")
                    break


def send_client_hello(server_socket, client_address, connection_id):
    packet_number = generate_packet_number()  # Generate a packet number
    flow_id = 0  # Assuming flow_id 0 for the initial handshake
    # Pack the long header with client hello message
    packet = pack_long_header(connection_id, packet_number, flow_id, CLIENT_HELLO)
    server_socket.sendto(packet, client_address)  # Send the client hello packet to the client
    print(f"Sent client hello to {client_address}")


def send_files_to_client(server_socket, client_address):
    flows = connections[client_address]['flows']  # Get the client's flows
    for flow in flows:
        print(f"Sending data for flow {flow['id']} with packet size {flow['packet_size']} bytes.")
        for _ in range(flow['num_packets']):
            send_next_packet(server_socket, client_address, flow)  # Send the next packet in the flow
            time.sleep(0.0002)  # Briefly sleep to simulate network delay


def send_next_packet(server_socket, client_address, flow):
    if flow['total_bytes'] < flow['file_size']:
        flow['packet_number'] += 1
        chunk_size = min(flow['packet_size'], len(flow['remaining_data']))  # Determine the chunk size
        message = flow['remaining_data'][:chunk_size]  # Get the chunk of data to send
        flow['remaining_data'] = flow['remaining_data'][chunk_size:]  # Update remaining data
        packet = pack_short_header(flow['packet_number'], flow['id'], message)  # Pack the short header with the data
        server_socket.sendto(packet, client_address)  # Send the packet to the client
        flow['total_bytes'] += len(message)  # Update total bytes sent
        flow['total_packets'] += 1  # Update total packets sent
        if flow['total_bytes'] >= flow['file_size']:
            flow['end_time'] = time.time()  # End timer for the flow


def send_connection_close(server_socket, client_address):
    packet = pack_short_header(0, 0, CONNECTION_CLOSE)  # Pack a CONNECTION_CLOSE signal
    server_socket.sendto(packet, client_address)  # Send the CONNECTION_CLOSE signal to the client
    print(f"Sent CONNECTION_CLOSE to {client_address}")
    time.sleep(0.5)  # Wait for a short period before closing
    print("Server is closing the connection.")
    exit(0)  # Ensure the server exits

if __name__ == '__main__':
    start_quic_server()  # Start the QUIC server
