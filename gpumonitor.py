import time
import threading
import json
import socket
import gpustat


# Constants
BUFFER_SIZE = 1024
TIMEOUT = 12  # Timeout for receiving data in seconds


class GPUMonitor:
    def __init__(self, num_gpus, max_data_points=360, http_listen=False, port=None):
        self.num_gpus = num_gpus
        self.max_data_points = max_data_points
        self.gpu_usage_data = [[0] * max_data_points for _ in range(num_gpus)]
        self.gpu_temp_data = [[10] * max_data_points for _ in range(num_gpus)]
        self.http_listen = http_listen
        self.port = port

    def _get_gpu_stats_from_gpustat(self):
        """Fetch GPU usage and temperature using gpustat."""
        gpu_stats = gpustat.GPUStatCollection.new_query().gpus
        gpu_usage = [gpu.utilization for gpu in gpu_stats[:self.num_gpus]]
        gpu_temp = [gpu.temperature for gpu in gpu_stats[:self.num_gpus]]
        return gpu_usage, gpu_temp

    def _get_gpu_stats_from_socket(self):
        """Fetch GPU usage and temperature using UDP socket."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.port))
            sock.settimeout(TIMEOUT)

            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                json_dic = json.loads(data.decode())
                return json_dic["gpu_usage"], json_dic["gpu_temp"]
            except socket.timeout:
                return [-1] * self.num_gpus, [-1] * self.num_gpus
            except Exception as e:
                print(f"Error receiving message: {e}")
                return [-10] * self.num_gpus, [-10] * self.num_gpus

    def get_gpu_stats(self):
        """Get GPU stats either from gpustat or socket."""
        if self.http_listen:
            return self._get_gpu_stats_from_socket()
        return self._get_gpu_stats_from_gpustat()

    def update_gpu_stats(self):
        """Continuously update GPU stats and store the data."""
        while True:
            gpu_usage, gpu_temp = self.get_gpu_stats()
            for i in range(self.num_gpus):
                self.gpu_usage_data[i].append(gpu_usage[i])
                self.gpu_temp_data[i].append(gpu_temp[i])
                # Keep the data list within the max_data_points limit
                if len(self.gpu_usage_data[i]) > self.max_data_points:
                    self.gpu_usage_data[i].pop(0)
                    self.gpu_temp_data[i].pop(0)
            time.sleep(1)

    def start_monitoring(self):
        """Start the monitoring thread to continuously update stats."""
        monitoring_thread = threading.Thread(target=self.update_gpu_stats)
        monitoring_thread.daemon = True
        monitoring_thread.start()