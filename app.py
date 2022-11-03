import sys
import os
import pika
import time
import json
import threading
from datetime import datetime
from zk import ZK, const

class myThread(threading.Thread):

    def __init__(self, fingertas_ip):
    # create connection to fingertas machine
        super(myThread, self).__init__()
        self.fingertas_ip=fingertas_ip
        self.conn = None
        self.pika_credentials = pika.PlainCredentials('guest', 'guest')
        self.is_run_flag = False
        # create ZK instance
        self.zk = None

    def run(self):
        while 1:
            if self.is_run_flag is False:
                try:
                    self.zk = ZK(
                        self.fingertas_ip,
                        # port=4370,
                        # timeout=5,
                        # password=0,
                        force_udp=False,
                        ommit_ping=True
                    )
                    print("Start binding to {}".format(self.fingertas_ip))
                    self.listen()
                except Exception as e:
                    print ("Process terminate : {} {}".format(e, self.fingertas_ip))
                    self.is_run_flag = False

    def listen(self):
        # create connection to message queue server
        try:
            # connect to device
            self.conn = self.zk.connect()
            print("Connected fingertas machine {0}.".format(self.fingertas_ip))
            self.is_run_flag = True
            for attendance in self.conn.live_capture():
                if attendance is None:
                    # print("none attendance event")
                    # implement here timeout logic
                    pass
                else:
                    print('[New Attendance Event] --------')
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
                    print("{} {}".format(attendance, self.fingertas_ip))
                    print('Try connecting to message queue server...')
                    connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        'rabbitmq',
                        5672,
                        '/',
                        self.pika_credentials
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
                    print('Request message queue done.')

        except Exception as e:
            print ("Process terminate : {} {}".format(e, self.fingertas_ip))
            if self.conn:
                self.conn.disconnect()
                self.is_run_flag = False
                print(
                    '{} stop all connection, waiting to restart...'.format(
                        self.fingertas_ip))

fingertas_machines_ips = [
    "10.89.10.249", # F9 Frontdoor main
    "10.89.10.250", # F9 Frontdoor side
    "10.89.10.251", # F10 Frontdoor nwvn
    "10.89.10.252", # F10 sidedoor nwvn
    "10.89.10.253", # F10 Frontdoor ndvn
    "10.89.10.254", # F10 sidedoor ndvn
]

main_app_threads = []

for ip in fingertas_machines_ips:
    main_app_threads.append(myThread(ip))
    main_app_threads[-1].start()

for thread in main_app_threads:
    thread.join()

# end
