from multiprocessing import Process
import json
import time
import pika
from zk import ZK, const
from logger import logger

MAX_TRY_TIME = 10
TIME_INTERVAL_RETRY = 3

class MachineProcess(Process):

    def __init__(self, fingertas_machine_ip, fingertas_machine_name):
    # create connection to fingertas machine
        super().__init__()
        self.fingertas_ip=fingertas_machine_ip
        self.fingertas_name=fingertas_machine_name
        self.conn = None
        self.pika_credentials = pika.PlainCredentials('guest', 'guest')
        self.is_run_flag = False
        # create ZK instance
        self.zk = None
        self.tryTime = 0

    def run(self):
        while True:
            if self.is_run_flag is False:
                try:
                    self.zk = ZK(
                        self.fingertas_ip,
                        # port=4370,
                        # timeout=TIME_INTERVAL_RETRY,
                        # password=0,
                        force_udp=False,
                        ommit_ping=True
                    )
                    logger.info(f"Start binding to {self.fingertas_name} at {self.fingertas_ip}")
                    self.__listen()
                finally:
                    time.sleep(TIME_INTERVAL_RETRY)
                    if self.tryTime > MAX_TRY_TIME:
                        logger.critical(
                            f"Max try time reach for machine\
                            {self.fingertas_name} at {self.fingertas_ip}.\
                            Connection failed."
                        )
                        break

    def __listen(self):
        self.tryTime = self.tryTime + 1
        # create connection to message queue server
        try:
            # connect to device
            self.conn = self.zk.connect()
            logger.info(f"Connected fingertas machine {self.fingertas_name} at {self.fingertas_ip}.")
            self.is_run_flag = True
            for attendance in self.conn.live_capture():
                if attendance is None:
                    # print("none attendance event")
                    # implement here timeout logic
                    pass
                else:
                    data = {
                        'fingerId': attendance.user_id,
                        'timestamp': attendance.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    }

                    # old method send rest request
                    # # defining the api-endpoint
                    # # data to be sent to api
                    # # sending post request and saving response as response object
                    # # API_ENDPOINT = "http://localhost:3001/attendances"
                    # # r = requests.post(url = API_ENDPOINT, data = data)

                    # new method send a message to message queue
                    logger.debug(
                        f"{attendance} from machine {self.fingertas_name} at {self.fingertas_ip}"
                    )
                    logger.debug('Try connecting and send message to message queue server...')
                    connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        '13.215.225.1',
                        5672,
                        '/',
                        self.pika_credentials
                    ))
                    channel = connection.channel()
                    channel.basic_qos(prefetch_count=1)
                    # declare a queue for our service
                    channel.queue_declare(queue='fingertas_machine', durable=False)
                    channel.basic_publish(
                        exchange='',
                        routing_key='fingertas_machine',
                        body=json.dumps({
                            'pattern': 'fingertas_machine',
                            'data': json.dumps(data)
                        }),
                        properties=pika.BasicProperties(
                            delivery_mode=pika.spec.TRANSIENT_DELIVERY_MODE
                        ),
                    )
                    connection.close()

        except Exception as error:
            if self.conn:
                self.conn.disconnect()
            logger.warning(f'{self.fingertas_ip}\
                           is run equal {self.is_run_flag},\
                           waiting to restart...')
            logger.error(f"Connection terminated : {error} at {self.fingertas_ip}\
                            retrying in {TIME_INTERVAL_RETRY} seconds ...\
                            for {self.tryTime} time(s)")
            self.is_run_flag = False

# end
