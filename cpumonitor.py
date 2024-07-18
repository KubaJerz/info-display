import psutil
import time
import threading
import json
import socket

#code for gpu data
class CPUMonitor:
    def __init__(self, http_listen=False, port=None):
        self.top_processes = []
        self.cpu_percent = 0
        self.ram_percent = 0
        self.http_listen = http_listen
        self.port = port
        self.buffer_size=2048

    def get_cpu_stats(self):
        if not(self.http_listen):
           # Get CPU and RAM usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            ram_percent = memory_info.percent

            # Get top 5 processes by CPU usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', ]):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = processes[:5]

            return cpu_percent, ram_percent, top_processes
        
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.port))
            sock.settimeout(12)

            try:
                data, addr = sock.recvfrom(self.buffer_size)
                json_dic = json.loads(data.decode())
                return json_dic["cpu_percent"], json_dic["ram_percent"], json_dic["top_processes"]
            except socket.timeout:
                return -1, -1, []  # Return value if timeout occurs
            except Exception as e:
                print(f"Error receiving message: {e}")
                return -10, -10, []
            finally:
                sock.close()


    def update_cpu_stats(self):
        while True:
            self.cpu_percent, self.ram_percent, self.top_processes = self.get_cpu_stats()
            time.sleep(5)

    def start_monitoring(self):
        monitoring_thread = threading.Thread(target=self.update_cpu_stats)
        monitoring_thread.daemon = True
        monitoring_thread.start()