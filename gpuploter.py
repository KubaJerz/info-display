import pygame
import matplotlib.pyplot as plt
import numpy as np
import threading
from matplotlib.backends.backend_agg import FigureCanvasAgg


class GPUPlot:
    def __init__(self, figsize=(9, 4)):
        self.fig, self.ax = plt.subplots(2, 1, figsize=figsize)
        self.canvas = FigureCanvasAgg(self.fig)
        self.surface = None
        self.lock = threading.Lock()

    def update(self, gpu_monitor):
        time_series = np.arange(-len(gpu_monitor.gpu_usage_data), 0)

        self.ax[0].clear()
        self.ax[0].plot(time_series, gpu_monitor.gpu_usage_data, label='GPU Usage (%)', color='white')
        self.ax[0].set_ylim(0, 100)
        self.ax[0].set_ylabel('Usage (%)')
        self.ax[0].grid()
        self.ax[0].legend()

        self.ax[1].clear()
        self.ax[1].plot(time_series, gpu_monitor.gpu_temp_data, label='GPU Temperature (C)', color='red')
        self.ax[1].set_ylim(0, 100)
        self.ax[1].set_ylabel('Temperature (C)')
        self.ax[1].grid()
        self.ax[1].legend()

        self.fig.tight_layout(pad=2.0)
        
        self.canvas.draw()
        raw_data = self.canvas.buffer_rgba()
        size = self.canvas.get_width_height()
        with self.lock:
            self.surface = pygame.image.frombuffer(raw_data, size, "RGBA").convert()

def gpu_monitoring_thread(gpu_monitor, gpu_plot, update_interval, running):
    gpu_graph_update_timer = 0
    while running:
        current_time = pygame.time.get_ticks()
        if current_time - gpu_graph_update_timer >= update_interval:
            gpu_graph_update_timer = current_time
            gpu_plot.update(gpu_monitor)
        pygame.time.wait(100)