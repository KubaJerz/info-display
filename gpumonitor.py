import gpustat
import time
import threading
import json
import socket

#code for gpu data

class GPUMonitor:
    def __init__(self, num_gpus, max_data_points=360, http_listen=False, port=None):
        self.num_gpus = num_gpus
        self.max_data_points = max_data_points
        self.gpu_usage_data = [[0] * max_data_points for _ in range(num_gpus)]
        self.gpu_temp_data = [[10] * max_data_points for _ in range(num_gpus)]
        self.http_listen = http_listen
        self.port = port
        self.buffer_size = 1024

    def get_gpu_stats(self):
        if not self.http_listen:
            gpu_stats = gpustat.GPUStatCollection.new_query().gpus
            gpu_usage = [gpu.utilization for gpu in gpu_stats[:self.num_gpus]]
            gpu_temp = [gpu.temperature for gpu in gpu_stats[:self.num_gpus]]
            return gpu_usage, gpu_temp
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.port))
            sock.settimeout(12)  # Set a timeout of 12 seconds
            try:
                data, addr = sock.recvfrom(self.buffer_size)
                json_dic = json.loads(data.decode())
                return json_dic["gpu_usage"], json_dic["gpu_temp"]
            except socket.timeout:
                return [-1] * self.num_gpus, [-1] * self.num_gpus
            except Exception as e:
                print(f"Error receiving message: {e}")
                return [-10] * self.num_gpus, [-10] * self.num_gpus
            finally:
                sock.close()

    def update_gpu_stats(self):
        while True:
            gpu_usage, gpu_temp = self.get_gpu_stats()
            for i in range(self.num_gpus):
                self.gpu_usage_data[i].append(gpu_usage[i])
                self.gpu_temp_data[i].append(gpu_temp[i])
                if len(self.gpu_usage_data[i]) > self.max_data_points:
                    self.gpu_usage_data[i].pop(0)
                    self.gpu_temp_data[i].pop(0)
            time.sleep(1)

    def start_monitoring(self):
        monitoring_thread = threading.Thread(target=self.update_gpu_stats)
        monitoring_thread.daemon = True
        monitoring_thread.start()