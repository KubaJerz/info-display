import gpustat
import time
import threading
import json
import socket

#code for gpu data
class GPUMonitor:
    def __init__(self, max_data_points=360, http_listen=False, port=None):
        self.max_data_points = max_data_points
        self.gpu_usage_data = [0] * max_data_points
        self.gpu_temp_data = [0] * max_data_points
        self.http_listen = http_listen
        self.port = port
        self.buffer_size=1024

    def get_gpu_stats(self):
        if not(self.http_listen):
          gpu_stats = gpustat.GPUStatCollection.new_query().gpus[0]
          gpu_usage = gpu_stats.utilization
          gpu_temp = gpu_stats.temperature
          return gpu_usage, gpu_temp
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.port))
            sock.settimeout(12)  # Set a timeout of 5 seconds

            try:
                data, addr = sock.recvfrom(self.buffer_size)
                json_dic = json.loads(data.decode())
                return json_dic["gpu_usage"], json_dic["gpu_temp"]
            except socket.timeout:
                return -1, -1  # Return a specific value if timeout occurs
            except Exception as e:
                print(f"Error receiving message: {e}")
                return -10, -10
            finally:
                sock.close()



        

    def update_gpu_stats(self):
        while True:
            gpu_usage, gpu_temp = self.get_gpu_stats()
            self.gpu_usage_data.append(gpu_usage)
            self.gpu_temp_data.append(gpu_temp)
            if len(self.gpu_usage_data) > self.max_data_points:
                self.gpu_usage_data.pop(0)
                self.gpu_temp_data.pop(0)
            time.sleep(5)

    def start_monitoring(self):
        monitoring_thread = threading.Thread(target=self.update_gpu_stats)
        monitoring_thread.daemon = True
        monitoring_thread.start()