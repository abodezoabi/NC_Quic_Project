# import os
import random  # Import random module for random number generation
import struct  # Import struct module for packing and unpacking binary data
# import time
# CLOSE_MESSAGE = b'CLOSE'  # Define the close message for the connection
CONNECTION_CLOSE = b'CONNECTION_CLOSE'  # Define the connection close message


def generate_connection_id():
    return random.randint(1, 1000000)  # Generate a random connection ID


def generate_packet_number():
    return random.randint(1, 1000000)  # Generate a random packet number


def pack_long_header(connection_id, packet_number, flow_id, payload):
    # Pack the long header with connection ID, packet number, flow ID, and payload
    return struct.pack('!III', connection_id, packet_number, flow_id) + payload


def pack_short_header(packet_number, flow_id, payload):
    # Pack the short header with packet number, flow ID, and payload
    return struct.pack('!II', packet_number, flow_id) + payload


def unpack_long_header(data):
    # Unpack the first 12 bytes to extract connection ID, packet number, and flow ID
    connection_id, packet_number, flow_id = struct.unpack('!III', data[:12])
    payload = data[12:]  # Extract the payload from the remaining data (after the first 12 bytes)
    return connection_id, packet_number, flow_id, payload


def unpack_short_header(data):
    # Unpack the first 8 bytes to extract packet number and flow ID
    packet_number, flow_id = struct.unpack('!II', data[:8])
    payload = data[8:]  # Extract the payload from the remaining data (after the first 8 bytes)
    return packet_number, flow_id, payload


def generate_random_file(size):
    return bytes(random.getrandbits(8) for _ in range(size))  # Generate a random file of the specified size


def print_statistics(flows):
    total_bytes = sum(flow['total_bytes'] for flow in flows)  # Calculate the total bytes sent across all flows
    total_packets = sum(flow['total_packets'] for flow in flows)  # Calculate the total packets sent across all flows
    total_data_rate = 0  # Initialize total data rate
    total_packet_rate = 0  # Initialize total packet rate
    num_flows = len(flows)  # Get the number of flows

    print("Flow statistics:")
    for flow in flows:
        duration = flow['end_time'] - flow['start_time']  # Calculate the duration of the flow
        data_rate = flow['total_bytes'] / duration if duration > 0 else 0  # Calculate the data rate for the flow
        packet_rate = flow['total_packets'] / duration if duration > 0 else 0  # Calculate the packet rate for the flow
        total_data_rate += data_rate  # Accumulate the data rate
        total_packet_rate += packet_rate  # Accumulate the packet rate

        print(f"Flow {flow['id']}:")
        print(f"  Total bytes: {flow['total_bytes']}")
        print(f"  Total packets: {flow['total_packets']}")
        print(f" Packet Size is : {flow['packet_size']} bytes")
        print(f"  Data rate: {data_rate:.2f} bytes/second")
        print(f"  Packet rate: {packet_rate:.2f} packets/second")

    # Average the data rates and packet rates across all flows
    avg_data_rate = total_data_rate / num_flows if num_flows > 0 else 0  # Calculate average data rate
    avg_packet_rate = total_packet_rate / num_flows if num_flows > 0 else 0  # Calculate average packet rate

    print("Overall statistics:")
    print(f"  Average data rate: {avg_data_rate:.2f} bytes/second")
    print(f"  Average packet rate: {avg_packet_rate:.2f} packets/second")
