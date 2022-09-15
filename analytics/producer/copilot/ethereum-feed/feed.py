import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import boto3
from websockets import connect

region = os.environ['AWS_REGION']

TOPIC_ARNS = json.loads(os.getenv("COPILOT_SNS_TOPIC_ARNS"))
print("TOPIC_ARNS=%s" % TOPIC_ARNS)
client = boto3.client('sns', region_name=region)

eth_endpoint = os.environ['ETH_LISTENER'].split(':')
ETH_HOST = eth_endpoint[0]
ETH_PORT = int(eth_endpoint[1])


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


async def get_event():
    serverURL = 'ws://' + str(ETH_HOST)+":" + str(ETH_PORT)
    print(serverURL)
    async with connect(serverURL) as ws:
        await ws.send(json.dumps({"id": 1, "method": "eth_subscribe", "params": ["newHeads"]}))
        subscription_response = await ws.recv()
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60)
                print(message)
                data = json.loads(message)
                blockNumber = int(data['params']['result']['number'], 16)
                msg = {"method": "importBlockByNumber", "number": blockNumber}
                data = json.dumps(msg)
                response = client.publish(
                    TopicArn=TOPIC_ARNS["ethTopic"],
                    Message=data
                )
                print("res = %s" % response)
                pass
            except Exception as e:
                pass

if __name__ == "__main__":
    daemon = threading.Thread(name='http_server', target=start_server, daemon=True)
    daemon.start()

    loop = asyncio.get_event_loop()
    while True:
        loop.run_until_complete(get_event())
