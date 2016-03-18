import unittest
import subprocess
import pykafka
from pykafka.cli import kafka_tools
import elasticsearch
import time
import socket
import os.path

def isolate(*names):
    subprocess.check_call(('vagga', '_network', 'isolate') + names)

def restore():
    subprocess.check_call(('vagga', '_network', 'fullmesh'))

def wait_for_logstash():
    logstash_stdout_file = "/work/logstash.out"
    while not os.path.isfile(logstash_stdout_file):
        time.sleep(2)
        pass
    
    while True:
        num_lines = 0
        with open(logstash_stdout_file) as f:
            for l in f:
                num_lines += 1
        if num_lines > 50:
            break




def wait_for_kafka():
    while True:
        try:
            socket.create_connection(("kafka", 9092)).close()
            break
        except ConnectionRefusedError:
            pass

class TestKafka(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wait_for_kafka()
        wait_for_logstash()

    def test_offsets(self):
        # check consumer offsets
        client = pykafka.KafkaClient(hosts="kafka:9092")
        avro_test_topic = client.topics[b'avro_meet_kafka']
        print(kafka_tools.fetch_consumer_lag(client, avro_test_topic, b'logstash'))


if __name__ == '__main__':
    unittest.main()

