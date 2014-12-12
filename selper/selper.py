#!/usr/bin/python
#coding = utf-8
"""
这是一个非常简单的进程管理工具，用来对服务进程进行管理。
可以通过参数对文件进行操作。
"""

import sys,os
import logging
import subprocess
import signal
import socket
import time

selper_name = "selper"
run_dir = "/var/run/"
loc_dir = "/var/lock"
selper_log = "/var/log/%s/selper.log" %selper_name
selper_conf = "/etc/%s/selper.conf" %selper_name

port = 5002

"""
数据传递，结束标志
"""
end_ = ";;"

'''
根据行为分为两类。
启动selper
对服务进行管理
'''
behaviors = ["START_SELPER","CONTROL_SERVICE"]

"""
对服务管理参数
"""

manage_method = ["start", "stop", "restart", "reload", "status"]

"""
启动程序分为两类。
一类为普通程序，一类为系统服务
普通程序只是启动，不对其进行管理。如果需要
"""

logger = logging.getLogger(selper_name)
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(selper_log)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

signals = []

#最早使用方法，通过pid文件进行通信
class service_handler(object):
    operator_signal = {"restart":12,"reload":1,"stop":3}
    @staticmethod
    def create_pidfile(name, pid):
        pid_locate = "%s%s/%s" %(run_dir, selper_name, name)
        pid_file = open(pid_locate , "w")
        pid_file.write(str(pid))
        pid_file.close()

    @staticmethod
    def post_signal(name, signum):
        pid_locate = "%s%s/%s" %(run_dir, selper_name, name)
        pid_file = open(pid_locate , "r")
        pid  = pid_file.read()
        pid_file.close()
        os.kill(pid, signum)

    @staticmethod
    def service_operator(name, operator):
        pid_locate = "%s%s/%s" %(run_dir, selper_name, name)
        if not os.path.exists(pid_locate):
            print(" service %s is not exist" %name)
        if operator in service_handler.operator_signal.keys():
            signum = service_handler.operator_signal['operator']
            service_handler.post_signal(name, signum)
        else:
            print("operator  is not supported!")

    @staticmethod
    def clear_all():
        dir = "%s%s" %(run_dir, selper_name)
        files = os.listdir(dir)
        for file in files:
            os.remove("%s/%s" %(dir, file))

    @staticmethod
    def clear_one(name):
        file = "%s%s/%s" %(run_dir, selper_name,name)
        os.remove(file)


class service_holder(object):
    def __init__(self, name, command, type='service', need_result = True):
        self.service_name = name
        self.command = command
        self.program_type = type
        self.need_result = need_result

    @property
    def get_name(self):
        return self.service_name

    def stop(self):
        self.proc.send_signal(signal.SIGINT)
        self.proc.wait()
        
    def start(self):
        array = self.command.split(' ')
        cmd_params = [i for i in array if i != '']
        self.proc = subprocess.Popen(cmd_params)
        if self.program_type != "service" and self.need_result:
            self.proc.wait()

    @property
    def is_service(self):
        return self.program_type == "service"

    def status(self):
        if self.proc.poll() == None:
            return True
        return False

    def restart(self):
        self.stop()
        self.start()

    def reload(self):
        self.proc.send_signal(signal.SIGHUP)


class selper(object):
    def __init__(self, config_file = None):
        if not config_file:
            config_file = selper_conf

        self.config_file = config_file
        self.service_holders = self.get_services(config_file)
        self.start_all()

    def reload(self, signum, frame):
        self.stop_all()
        self.service_holders = []
        self.service_holders = self.get_services(self.config_file)

        
    def start(self):
        self._build_server()
        self.loop()

    def loop(self):
        while True:
            conn, addr = self.handle_connect()
            if conn == None:
                time.sleep(1)
                continue

            buffer = ""
            while True:
                buffer += conn.recv(1024)
                if len(buffer) == 0:
                    time.sleep(1)
                if buffer.strip().endswith(end_):
                    command = buffer.strip()[:-2]
                    ret, msg = self.handle_command(command)
                    send_prompt  = "%s%s%s%s" %(str(ret), end_, msg, end_)
                    conn.send(send_prompt)
                    buffer = ""
                    break

    def handle_command(self, command):
        s = command.split(" ")
        ss = [i for i in s if i != ""]
        name = ss[0]
        oper = ss[1]
        for service in self.service_holders:
            if service.get_name == name and service.is_service:
                try:
                    call = getattr(service, oper)
                except:
                    log.error("no %s operation" %oper)
                    return False, "no %s operation" %oper
                call()
                return True, ""
        return False, "no service named %s" %name

    def _build_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(1)
        self.sock.setblocking(0)

    def handle_connect(self):
        conn, addr = None, None
        try:
            conn, addr = self.sock.accept()
            conn.setblocking(0)
        except:
            pass
        return conn, addr
        

    def get_services(self, config_file):
        """
        读取配置文件
        """
        import ConfigParser
        service_holders = []
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.read(config_file)
        secs = conf_parser.sections()
        for sec in secs:
            try:
                command = conf_parser.get(sec,'command')
            except ConfigParser.NoOptionError:
                command = None
            if not command:
                continue

            try:
                program_type = conf_parser.get(sec,'program_type')
            except ConfigParser.NoOptionError:
                program_type = None

            try:
                need_result = conf_parser.get(sec,'need_result')
            except ConfigParser.NoOptionError:
                need_result = None
            p = service_holder(sec, command, program_type, need_result)
            service_holders.append(p)

        return service_holders
    
    def start_all(self):
        for p in self.service_holders:
            p.start()

    def stop_all(self):
        for p in self.service_holders:
            p.stop()



def daemonize():
    try:   
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
    except OSError, e:
        #print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            sys.exit(0)
    except OSError, e:
        
        sys.exit(1)


def sys_exit(signum, frame):
    sys.exit(1)

#start services
def main():
    args = sys.argv
    if len(args) == 1:
        config_file = "/etc/selper/selper.ini"
    else:
        config_file = args[1]
    if not os.path.exists(config_file):
        sys.exit(1)

    instance = selper(config_file)
    signal.signal(signal.SIGHUP, instance.reload)
    signal.signal(signal.SIGINT, sys_exit)

    instance.start()


#print help
#TODO:
def controller_help():
    pass


#control services
class controller(object):

    def __init__(self):
        #self.check_service()
        self.execute()

    def connect_selper(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect_ex(("127.0.0.1", port))
        except Exception as e:
            print("cannt connect to 127.0.0.1:%s, please check the selper start" %port)
            sys.exit(1)

    def execute(self):
        self.connect_selper()
        name = sys.argv[1]
        operator = sys.argv[2]
        self.sock.send("%s %s%s" %(name, operator, end_))
        buf = self.sock.recv(1024)
        rets = buf.split(end_)
        if (rets[0] == "True"):
            print("%s service %s [OK]" %(operator, name))
        elif (rets[0] == "False"):
            print("%s service %s Fail: [OK]" %(operator, name, rets[1]))            
        self.sock.close()


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        daemonize()
        if not os.path.exists(os.path.dirname(selper_log)):
            try:
                os.makedirs(os.path.dirname(selper_log))
            except Exception as e:
                pass
        main()
    else : #manage the services
        controller()
