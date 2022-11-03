from machine import MachineProcess
from logger import logger

fingertas_machines_ips = {
    # "10.89.10.249": 'F9 Frontdoor main',
    # "10.89.10.250": 'F9 Frontdoor side',
    # "10.89.10.251": 'F10 Frontdoor nwvn',
    # "10.89.10.252": 'F10 sidedoor nwvn',
    "10.89.10.253": 'F10 Frontdoor ndvn',
    "10.89.10.254":'F10 sidedoor ndvn',
}
def set_proc_name(newname):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(newname)+1)
    buff.value = newname
    libc.prctl(15, byref(buff), 0, 0, 0)

def main():
    logger.info("App start.")
    main_app_processes = []
    for key, value in fingertas_machines_ips.items():
        set_proc_name(value.encode('ascii'))
        main_app_processes.append(MachineProcess(key, value))
        main_app_processes[-1].start()

    for process in main_app_processes:
        process.join(1000)

    logger.warning("App stop.")

if __name__ == '__main__':
    while True:
        logger.info("App initialize.")
        main()
        logger.warning("App retry.")


