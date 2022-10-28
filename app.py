import sys
import os
import pika
import time
import json
from datetime import datetime
from zk import ZK, const

# create connection to fingertas machine
conn = None
# create ZK instance
zk = ZK('10.89.10.254', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=True)

pika_credentials = pika.PlainCredentials('guest', 'guest')

is_run_flag = False
def listenEvent():
    # create connection to message queue server
    try:
        # connect to device
        conn = zk.connect()
        print("Start listening event from fingertas machine.")
        is_run_flag = True
        for attendance in conn.live_capture():
            if attendance is None:
                # implement here timeout logic
                pass
            else:
                data = {
                    'fingerId': attendance.user_id,
                    'timestamp': attendance.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                }

                # old method send rest request
                # # defining the api-endpoint
                # # data to be sent to api
                # # sending post request and saving response as response object
                # # API_ENDPOINT = "http://localhost:3001/attendances"
                # # r = requests.post(url = API_ENDPOINT, data = data)

                # new method send a message to message queue
                print(attendance)
                connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    'localhost',
                    5672,
                    '/',
                    pika_credentials
                ))
                channel = connection.channel()
                # declare a queue for our service
                channel.queue_declare(queue='fingertas_machine', durable=True)
                channel.basic_publish(
                    exchange='',
                    routing_key='fingertas_machine',
                    body=json.dumps({
                        'pattern': 'fingertas_machine',
                        'data': json.dumps(data)
                    }),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                    ),
                )
                connection.close()

    except Exception as e:
        print ("Process terminate : {}".format(e))
    finally:
        if conn:
            is_run_flag = False
            conn.disconnect()
            connection.close()

while 1:
    if (is_run_flag == False):
        listenEvent()

