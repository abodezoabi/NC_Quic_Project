import socket
import random
import time
from api import unpack_long_header, pack_short_header, unpack_short_header, generate_random_file, print_statistics

connections = {}


def start_quic_server():
    server_address = ('localhost', 4433)
    buffer_size = 2048

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(server_address)
        print("QUIC server is running...")

        while True:
            data, client_address = server_socket.recvfrom(buffer_size)
            print(f"Received {len(data)} bytes from {client_address}")

            if client_address not in connections:
                connection_id, packet_number, flow_id, payload = unpack_long_header(data)
                print(f"Initial connection ID: {connection_id}, Packet number: {packet_number}, Flow ID: {flow_id}, Payload: {payload}")
                connections[client_address] = {
                    'connection_id': connection_id,
                    'flows': [],
                    'last_packet_number': packet_number,
                    'acks': set()
                }

                # Initialize flows
                num_flows = 3
                for i in range(1, num_flows+1):
                    packet_size = random.randint(1000, 2000)
                    file_size = 2 * 1024 * 1024  # 2MB
                    flow = {
                        'id': i,
                        'packet_size': packet_size,
                        'file_size': file_size,
                        'total_bytes': 0,
                        'total_packets': 0,
                        'start_time': time.time(),
                        'end_time': 0,
                        'remaining_data': generate_random_file(file_size),
                        'packet_number': 0
                    }
                    connections[client_address]['flows'].append(flow)

                # Start sending files to the client one flow at a time
                for flow in connections[client_address]['flows']:
                    while flow['total_bytes'] < flow['file_size']:
                        send_next_packet(server_socket, client_address, flow)
                        time.sleep(0.0004)

            else:
                packet_number, flow_id, payload = unpack_short_header(data)
                print(f"Packet number: {packet_number}, Flow ID: {flow_id}, Payload: {payload}")

                if payload == b'ACK':
                    print(f"Received ACK for packet number {packet_number} from {client_address}")
                    connections[client_address]['acks'].add((flow_id, packet_number))


def send_next_packet(server_socket, client_address, flow):
    if flow['total_bytes'] < flow['file_size']:
        flow['packet_number'] += 1
        chunk_size = min(flow['packet_size'], len(flow['remaining_data']))
        message = flow['remaining_data'][:chunk_size]
        flow['remaining_data'] = flow['remaining_data'][chunk_size:]
        packet = pack_short_header(flow['packet_number'], flow['id'], message)
        server_socket.sendto(packet, client_address)
        print(f"Sent packet number {flow['packet_number']} with {len(message)} bytes to {client_address}")
        flow['total_bytes'] += len(message)
        flow['total_packets'] += 1
        if flow['total_bytes'] >= flow['file_size']:
            flow['end_time'] = time.time()


if __name__ == '__main__':
    start_quic_server()
