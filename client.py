import socket  # Import socket module for network communication
import time  # Import time module for timing purposes
from api import generate_connection_id, generate_packet_number, pack_long_header, pack_short_header, unpack_short_header, unpack_long_header, print_statistics, CONNECTION_CLOSE  # Import various functions from the api module
from server import get_num_flows  # Import get_num_flows function from the server module
import matplotlib.pyplot as plt  # Import matplotlib for plotting graphs


def start_quic_client():
    server_address = ('localhost', 4433)  # Define the server address & port
    buffer_size = 2048  # Define the buffer size for receiving data

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:  # Create a UDP socket
        connection_id = generate_connection_id()  # Generate a unique connection ID
        packet_number = generate_packet_number()  # Generate a packet number
        message = b"Hello, QUIC server!(Long header)"  # Define the initial message

        # Pack the long header with the initial connection ID and packet number
        packet = pack_long_header(connection_id, packet_number, 0, message)
        print(f"Sending initial packet with connection ID {connection_id} and packet number {packet_number}")
        client_socket.sendto(packet, server_address)  # Send the initial packet to the server

        # Receive files from the server
        flows = []  # Initialize an empty list to store flow information
        num_flows = get_num_flows()  # Get the number of flows from the server
        received_bytes = {i: 0 for i in range(1, num_flows + 1)}  # Initialize received bytes for each flow

        while True:
            data, server = client_socket.recvfrom(buffer_size)  # Receive data from the server
            packet_number, flow_id, payload = unpack_short_header(data)  # Unpack the received data

            if payload == CONNECTION_CLOSE:  # Check if the received payload is a CONNECTION_CLOSE signal
                print(f"Received CONNECTION_CLOSE from {server}")
                send_connection_close(client_socket, server)  # Send a CONNECTION_CLOSE signal back to the server
                time.sleep(0.5)  # Wait for a short period before closing
                break
            elif payload.startswith(b'Hello, QUIC client!'):  # Check if the received payload is a client hello message
                print(f"Received client hello from {server}")
                continue

            # Ensure the flow_id is within the expected range and handles unexpected packets
            if flow_id not in received_bytes:
                print(f"Unexpected flow_id {flow_id} received. Ignoring packet.")
                continue

            # Find or initialize flow
            flow = next((f for f in flows if f['id'] == flow_id), None)
            if not flow:  # Check if a flow exists before making a new flow created
                flow = {
                    'id': flow_id,
                    'packet_size': 0,  # Initialize with zero, will be set on first packet reception
                    'file_size': 2 * 1024 * 1024,  # 2MB
                    'total_bytes': 0,
                    'total_packets': 0,
                    'start_time': time.time(),
                    'end_time': 0
                }
                flows.append(flow)  # Append the new flow to the flows list
                print(f"Initialized flow {flow_id}")

            # Update flow statistics
            flow['total_bytes'] += len(payload)
            flow['total_packets'] += 1
            flow['end_time'] = time.time() # stop timer
            received_bytes[flow_id] += len(payload)

            # Set packet size based on the first packet received
            if flow['packet_size'] == 0:
                flow['packet_size'] = len(payload)
                print(f"Set packet size for flow {flow_id} to {flow['packet_size']} bytes.")

            # print(f"Received packet number {packet_number} of size {len(payload)} bytes for flow {flow_id}")

            # Send ACK
            ack_packet = pack_short_header(packet_number, flow_id, b'ACK')
            client_socket.sendto(ack_packet, server_address)
            # print(f"Sent ACK for packet number {packet_number} for flow {flow_id}")

            # Check if the flow is complete
            if received_bytes[flow_id] >= flow['file_size']:
                print(f"Flow {flow_id} is complete")

            # Check if all flows are complete
            if all(received_bytes[i] >= 2 * 1024 * 1024 for i in range(1, num_flows + 1)):
                break

        # Print statistics
        print_statistics(flows)
        # Graph statistics
        show_graph(flows)


def send_connection_close(client_socket, server_address):
    packet = pack_short_header(0, 0, CONNECTION_CLOSE)  # Pack a CONNECTION_CLOSE signal
    client_socket.sendto(packet, server_address)  # Send the CONNECTION_CLOSE signal to the server
    print(f"Sent CONNECTION_CLOSE to {server_address}")


def show_graph(flows):
    num_flows = len(flows)  # Get the number of flows
    flow_ids = [flow['id'] for flow in flows]  # Get the flow IDs
    # Calculate data rates for each flow
    data_rates = [flow['total_bytes'] / (flow['end_time'] - flow['start_time']) for flow in flows]
    # Calculate packet rates for each flow
    packet_rates = [flow['total_packets'] / (flow['end_time'] - flow['start_time']) for flow in flows]

    # Plot average data rate vs number of streams
    plt.figure()
    plt.plot(flow_ids, data_rates, marker='o')
    plt.xlabel('Number of Streams')
    plt.ylabel('Average Data Rate (bytes/second)')
    plt.title('Average Data Rate vs Number of Streams')
    plt.grid(True)
    plt.savefig('average_data_rate_vs_streams.png')
    plt.show()

    # Plot average packet rate vs number of streams
    plt.figure()
    plt.plot(flow_ids, packet_rates, marker='o')
    plt.xlabel('Number of Streams')
    plt.ylabel('Average Packet Rate (packets/second)')
    plt.title('Average Packet Rate vs Number of Streams')
    plt.grid(True)
    plt.savefig('average_packet_rate_vs_streams.png')
    plt.show()


if __name__ == '__main__':
    start_quic_client()  # Start the QUIC client
