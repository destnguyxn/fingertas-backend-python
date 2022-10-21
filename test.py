import sys
import os
sys.path.insert(1,os.path.abspath("./pyzk"))
from zk import ZK, const

from zk import ZK, const

conn = None
# create ZK instance
zk = ZK('10.89.10.254', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=True)
try:
    # connect to device
    conn = zk.connect()
    users = conn.get_users()
    for user in users:
        privilege = 'User'
        if user.privilege == const.USER_ADMIN:
            privilege = 'Admin'
        print ('+ UID #{}'.format(user.uid))
        print ('  Name       : {}'.format(user.name))
        print ('  Privilege  : {}'.format(privilege))
        print ('  Password   : {}'.format(user.password))
        print ('  Group ID   : {}'.format(user.group_id))
        print ('  User  ID   : {}'.format(user.user_id))
    # Get attendances (will return list of Attendance object)
    for attendance in conn.live_capture():
        if attendance is None:
            # implement here timeout logic
            pass
        else:
            print (attendance) # Attendance object
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
