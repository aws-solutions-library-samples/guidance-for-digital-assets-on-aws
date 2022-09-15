import asyncio
import json
import os
import signal
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import boto3
import zmq
import zmq.asyncio

app = os.environ['COPILOT_APPLICATION_NAME']
envName = os.environ['COPILOT_ENVIRONMENT_NAME']

btc_endpoint = os.environ['BTC_LISTENER'].split(':')
host = btc_endpoint[0]
port = int(btc_endpoint[1])

print("host=%s,port=%s" % (host, port))

rpc_user = os.environ['RPC_USER']
rpc_password = os.environ['RPC_PASSWORD']

region = os.environ['AWS_REGION']

TOPIC_ARNS = json.loads(os.getenv("COPILOT_SNS_TOPIC_ARNS"))
print("TOPIC_ARNS=%s" % TOPIC_ARNS)
client = boto3.client('sns', region_name=region)


class MyHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        healthy = True
        if healthy:
            DATA = {'healthy': healthy}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(DATA).encode())
        else:
            self.send_response(501)
        return


def start_server():
    print('start http 8080')
    httpd = HTTPServer(('', 8080), MyHttpHandler)
    httpd.serve_forever()


class ZMQHandler():
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.zmqContext = zmq.asyncio.Context()
        self.zmqSubSocket = self.zmqContext.socket(zmq.SUB)
        self.zmqSubSocket.setsockopt(zmq.RCVHWM, 0)
        self.zmqSubSocket.setsockopt_string(zmq.SUBSCRIBE, "hashblock")
        self.zmqSubSocket.connect("tcp://"+host+":%i" % port)

    async def handle(self):
        print("wait for message")
        topic, body, seq = await self.zmqSubSocket.recv_multipart()
        sequence = "Unknown"
        if len(seq) == 4:
            sequence = str(struct.unpack('<I', seq)[-1])
        if topic == b"hashblock":
            print('- HASH BLOCK ('+sequence+') -')
            hash = body.hex()
            print("importByHash:%s" % hash)
            msg = {"method": "importBlockByHash", "hash": hash}
            data = json.dumps(msg)
            response = client.publish(
                TopicArn=TOPIC_ARNS["btcTopic"],
                Message=data
            )
            print("res=%s" % response)

        # schedule ourselves to receive the next message
        asyncio.ensure_future(self.handle())

    def start(self):
        self.loop.add_signal_handler(signal.SIGINT, self.stop)
        self.loop.create_task(self.handle())
        self.loop.run_forever()

    def stop(self):
        self.loop.stop()
        self.zmqContext.destroy()


if __name__ == "__main__":
    daemon = threading.Thread(name='http_server', target=start_server, daemon=True)
    daemon.start()

    listener = ZMQHandler()
    listener.start()
