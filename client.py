import socket
import random
import time
from api import generate_connection_id, generate_packet_number, pack_long_header, pack_short_header, \
    unpack_short_header, print_statistics


def start_quic_client():
    server_address = ('localhost', 4433)
    buffer_size = 2048

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        connection_id = generate_connection_id()
        packet_number = generate_packet_number()
        message = b"Hello, QUIC server!"

        # Pack the long header with the initial connection ID and packet number
        packet = pack_long_header(connection_id, packet_number, 0, message)
        print(f"Sending initial packet with connection ID {connection_id} and packet number {packet_number}")
        client_socket.sendto(packet, server_address)

        # Receive files from the server
        flows = []
        num_flows = 3
        received_bytes = {i: 0 for i in range(num_flows+1)}

        while True:
            data, server = client_socket.recvfrom(buffer_size)
            packet_number, flow_id, payload = unpack_short_header(data)
           #print(f"Received packet number {packet_number} with {len(payload)} bytes from {server}")

            # Find or initialize flow
            flow = next((f for f in flows if f['id'] == flow_id), None)
            if not flow:
                packet_size = random.randint(1000, 2000)
                flow = {
                    'id': flow_id,
                    'packet_size': packet_size,
                    'file_size': 2 * 1024 * 1024,  # 2MB
                    'total_bytes': 0,
                    'total_packets': 0,
                    'start_time': time.time(),
                    'end_time': 0
                }
                flows.append(flow)

            # Update flow statistics
            flow['total_bytes'] += len(payload)
            flow['total_packets'] += 1
            flow['end_time'] = time.time()
            received_bytes[flow_id] += len(payload)

            # Send ACK
            ack_packet = pack_short_header(packet_number, flow_id, b'ACK')
            client_socket.sendto(ack_packet, server_address)
          #  print(f"Sent ACK for packet number {packet_number} with flow ID {flow_id}")

            # Check if the flow is complete
            if received_bytes[flow_id] >= flow['file_size']:
                print(f"Flow {flow_id} is complete")
                # Check if all flows are complete

            if all(received_bytes[i] >= 2 * 1024 * 1024 for i in range(1, num_flows + 1)):
                break

        # Print statistics
        print_statistics(flows)


if __name__ == '__main__':
    start_quic_client()
