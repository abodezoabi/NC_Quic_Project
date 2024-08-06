import threading
import unittest
from unittest.mock import patch

from api import generate_connection_id, generate_packet_number, pack_long_header, unpack_long_header, pack_short_header, unpack_short_header, generate_random_file, print_statistics
from client import start_quic_client
from server import start_quic_server
import random
import time
import io
import sys

class TestAPI(unittest.TestCase):

    def test_generate_connection_id(self):
        for _ in range(50):
            connection_id = generate_connection_id()
            self.assertGreaterEqual(connection_id, 1)
            self.assertLessEqual(connection_id, 1000000)

    def test_generate_packet_number(self):
        for _ in range(50):
            packet_number = generate_packet_number()
            self.assertGreaterEqual(packet_number, 1)
            self.assertLessEqual(packet_number, 1000000)

    def test_pack_and_unpack_long_header(self):
        for _ in range(50):
            connection_id = generate_connection_id()
            packet_number = generate_packet_number()
            flow_id = random.randint(1, 100)
            payload_size = random.randint(1, 1024)
            payload = generate_random_file(payload_size)
            packed_data = pack_long_header(connection_id, packet_number, flow_id, payload)
            unpacked_connection_id, unpacked_packet_number, unpacked_flow_id, unpacked_payload = unpack_long_header(packed_data)
            self.assertEqual(connection_id, unpacked_connection_id)
            self.assertEqual(packet_number, unpacked_packet_number)
            self.assertEqual(flow_id, unpacked_flow_id)
            self.assertEqual(payload, unpacked_payload)

    def test_pack_and_unpack_short_header(self):
        for _ in range(50):
            packet_number = generate_packet_number()
            flow_id = random.randint(1, 100)
            payload_size = random.randint(1, 1024)
            payload = generate_random_file(payload_size)
            packed_data = pack_short_header(packet_number, flow_id, payload)
            unpacked_packet_number, unpacked_flow_id, unpacked_payload = unpack_short_header(packed_data)
            self.assertEqual(packet_number, unpacked_packet_number)
            self.assertEqual(flow_id, unpacked_flow_id)
            self.assertEqual(payload, unpacked_payload)

    def test_generate_random_file(self):
        for _ in range(50):
            size = random.randint(1, 1024)
            random_file = generate_random_file(size)
            self.assertEqual(len(random_file), size)
            self.assertIsInstance(random_file, bytes)

    def test_print_statistics(self):
        for _ in range(50):
            flows = []
            for i in range(random.randint(1, 10)):
                total_bytes = random.randint(1000, 100000)
                total_packets = random.randint(10, 1000)
                packet_size = random.randint(64, 1500)  # Assuming packet sizes range between 64 and 1500 bytes
                start_time = time.time()
                end_time = start_time + random.uniform(0.1, 10.0)
                flow = {
                    'id': i,
                    'total_bytes': total_bytes,
                    'total_packets': total_packets,
                    'packet_size': packet_size,
                    'start_time': start_time,
                    'end_time': end_time
                }
                flows.append(flow)

            # Capture the printed output
            with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                print_statistics(flows)
                printed_output = fake_stdout.getvalue()

                # Manually construct the expected output
                expected_output = "Flow statistics:\n"
                for flow in flows:
                    duration = flow['end_time'] - flow['start_time']
                    data_rate = flow['total_bytes'] / duration if duration > 0 else 0
                    packet_rate = flow['total_packets'] / duration if duration > 0 else 0
                    expected_output += (
                        f"Flow {flow['id']}:\n"
                        f"  Total bytes: {flow['total_bytes']}\n"
                        f"  Total packets: {flow['total_packets']}\n"
                        f" Packet Size is : {flow['packet_size']} bytes\n"
                        f"  Data rate: {data_rate:.2f} bytes/second\n"
                        f"  Packet rate: {packet_rate:.2f} packets/second\n"
                    )

                # Calculate overall statistics
                num_flows = len(flows)
                total_data_rate = sum(flow['total_bytes'] / (flow['end_time'] - flow['start_time']) for flow in flows if flow['end_time'] - flow['start_time'] > 0)
                total_packet_rate = sum(flow['total_packets'] / (flow['end_time'] - flow['start_time']) for flow in flows if flow['end_time'] - flow['start_time'] > 0)
                avg_data_rate = total_data_rate / num_flows if num_flows > 0 else 0
                avg_packet_rate = total_packet_rate / num_flows if num_flows > 0 else 0

                expected_output += (
                    "Overall statistics:\n"
                    f"  Average data rate: {avg_data_rate:.2f} bytes/second\n"
                    f"  Average packet rate: {avg_packet_rate:.2f} packets/second\n"
                )

                # Compare the captured output with the expected output
                self.assertEqual(printed_output, expected_output)

class TestClientServer(unittest.TestCase):

    def start_quic_server_thread(self):
        self.server_thread = threading.Thread(target=start_quic_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(2)  # Wait for the server to start

    def test_quic_client_server_comm(self):
        self.start_quic_server_thread()

        client_thread = threading.Thread(target=start_quic_client)
        client_thread.daemon = True
        client_thread.start()
        client_thread.join()

        # Closes the server after client test is done
        self.server_thread.join(timeout=0.1)

if __name__ == '__main__':
    unittest.main()