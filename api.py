import random
import struct
import time
# extra functionality check:
# starting connection headers
# get flows number in client
# updated GUI for graph visualization
# code comments
# closing connection headers


def generate_connection_id():
    return random.randint(1, 1000000)


def generate_packet_number():
    return random.randint(1, 1000000)


def pack_long_header(connection_id, packet_number, flow_id, payload):
    return struct.pack('!III', connection_id, packet_number, flow_id) + payload


def pack_short_header(packet_number, flow_id, payload):
    return struct.pack('!II', packet_number, flow_id) + payload


def unpack_long_header(data):
    connection_id, packet_number, flow_id = struct.unpack('!III', data[:12])
    payload = data[12:]
    return connection_id, packet_number, flow_id, payload


def unpack_short_header(data):
    packet_number, flow_id = struct.unpack('!II', data[:8])
    payload = data[8:]
    return packet_number, flow_id, payload


def generate_random_file(size):
    return bytes(random.getrandbits(8) for _ in range(size))


def print_statistics(flows):
    total_bytes = sum(flow['total_bytes'] for flow in flows)
    total_packets = sum(flow['total_packets'] for flow in flows)
    duration = max(flow['end_time'] - flow['start_time'] for flow in flows if flow['end_time'] > 0)

    print("Flow statistics:")
    for flow in flows:
        duration = flow['end_time'] - flow['start_time']
        print(f"Flow {flow['id']}:")
        print(f"  Total bytes: {flow['total_bytes']}")
        print(f"  Total packets: {flow['total_packets']}")
        print(f"  Data rate: {flow['total_bytes'] / duration if duration > 0 else 0:.2f} bytes/second")
        print(f"  Packet rate: {flow['total_packets'] / duration if duration > 0 else 0:.2f} packets/second")

    print("Overall statistics:")
    print(f"  Total data rate: {total_bytes / duration if duration > 0 else 0:.2f} bytes/second")
    print(f"  Total packet rate: {total_packets / duration if duration > 0 else 0:.2f} packets/second")
