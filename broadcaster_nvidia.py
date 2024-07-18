import socket
import psutil
import json
import time
import sys
import pynvml

def get_cpu_ram_info():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    ram_percent = memory_info.percent

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            proc_info = proc.info
            if proc_info['cpu_percent'] is not None and proc_info['memory_percent'] is not None:
                processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    top_processes = processes[:8]

    return {
        'cpu_percent': cpu_percent,
        'ram_percent': ram_percent,
        'top_processes': top_processes
    }

def get_gpu_info():
    pynvml.nvmlInit()
    num_gpus = pynvml.nvmlDeviceGetCount()
    gpu_usage = []
    gpu_temp = []
    
    for i in range(num_gpus):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        
        gpu_usage.append(util.gpu)
        gpu_temp.append(temp)
    
    pynvml.nvmlShutdown()
    
    return {
        'gpu_usage': gpu_usage,
        'gpu_temp': gpu_temp
    }

def broadcast_message(message, receiver_ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        sock.sendto(message.encode(), (receiver_ip, port))
        print(f"Sent to {receiver_ip}:{port}: {message}")
    except Exception as e:
        print(f"Error broadcasting message: {e}")
    finally:
        sock.close()

def print_usage():
    print("Usage: python broadcaster.py <receiver_ip> <cpu_port> <gpu_port>")
    print("Example: python broadcaster.py 999.999.1.999 12345 12346")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print_usage()
        sys.exit(1)

    receiver_ip = sys.argv[1]
    cpu_port = int(sys.argv[2])
    gpu_port = int(sys.argv[3])

    print(f"Broadcasting to IP: {receiver_ip}")
    print(f"CPU data port: {cpu_port}")
    print(f"GPU data port: {gpu_port}")

    while True:
        cpu_ram_message = json.dumps(get_cpu_ram_info())
        gpu_message = json.dumps(get_gpu_info())
        
        broadcast_message(cpu_ram_message, receiver_ip, cpu_port)
        broadcast_message(gpu_message, receiver_ip, gpu_port)
        
        time.sleep(5)
