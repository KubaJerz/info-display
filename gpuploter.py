import pygame
import matplotlib.pyplot as plt
import numpy as np
import threading
import os
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Constants
TIME_SERIES_LIMIT = -350
TIME_SERIES_START = 0
GPU_USAGE_LIMIT = 100
GPU_TEMP_LIMIT = 110
DEFAULT_FIGSIZE = (8, 4)
BACKGROUND_COLOR = "BLACK"
TEXT_COLOR = "WHITE"

class GPUPlot:
    def __init__(self, num_gpus, figsize=DEFAULT_FIGSIZE):
        self.num_gpus = num_gpus
        self.figsize = figsize
        self.surface = None
        self.lock = threading.Lock()
        self.colors = plt.cm.rainbow(np.linspace(0, 1, num_gpus))
        
        # Create a temporary file for saving plots
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        self.temp_file.close()
        self.temp_filename = self.temp_file.name
        
        # Flag to indicate if update is needed
        self.needs_update = False
        self.latest_data = None

    def _configure_usage_graph(self, ax):
        ax.set_ylim(0, GPU_USAGE_LIMIT)
        ax.set_xlim(TIME_SERIES_LIMIT, TIME_SERIES_START)
        ax.set_ylabel('Usage (%)', color=TEXT_COLOR)
        ax.tick_params(colors=TEXT_COLOR)
        ax.grid(color=TEXT_COLOR)
        ax.legend(facecolor=BACKGROUND_COLOR, edgecolor=TEXT_COLOR, labelcolor=TEXT_COLOR)

    def _configure_temp_graph(self, ax):
        ax.set_ylim(10, GPU_TEMP_LIMIT)
        ax.set_xlim(TIME_SERIES_LIMIT, TIME_SERIES_START)
        ax.set_ylabel('Temperature (C)', color=TEXT_COLOR)
        ax.tick_params(colors=TEXT_COLOR)
        ax.grid(color=TEXT_COLOR)
        ax.legend(facecolor=BACKGROUND_COLOR, edgecolor=TEXT_COLOR, labelcolor=TEXT_COLOR)
       

    def _update_graph(self, ax, time_series, gpu_monitor):
        for i in range(self.num_gpus):
            ax[0].plot(time_series, gpu_monitor.gpu_usage_data[i], 
                       label=f'GPU{i} Usage (%)', color=self.colors[i])
            ax[1].plot(time_series, gpu_monitor.gpu_temp_data[i], 
                       label=f'GPU{i} Temp (C)', color=self.colors[i])

    def request_update(self, gpu_monitor):
        """Request an update with new data - called from monitoring thread"""
        with self.lock:
            self.latest_data = gpu_monitor
            self.needs_update = True

    def update_if_needed(self):
        """Update the plot if needed - called from main thread only"""
        should_update = False
        gpu_monitor = None
        
        with self.lock:
            if self.needs_update and self.latest_data is not None:
                should_update = True
                gpu_monitor = self.latest_data
                self.needs_update = False
        
        if should_update:
            self._do_update(gpu_monitor)

    def _do_update(self, gpu_monitor):
        """Actually perform the matplotlib update - main thread only"""
        try:
            # Check if we have data
            if not gpu_monitor.gpu_usage_data or not gpu_monitor.gpu_usage_data[0]:
                return
                
            time_series = np.arange(-len(gpu_monitor.gpu_usage_data[0]), 0)
            
            # Create new figure each time to avoid threading issues
            fig, ax = plt.subplots(2, 1, figsize=self.figsize)
            #fig.patch.set_facecolor('blue')
            ax[0].set_facecolor(BACKGROUND_COLOR)
            ax[1].set_facecolor(BACKGROUND_COLOR)

            self._update_graph(ax, time_series, gpu_monitor)
            self._configure_usage_graph(ax[0])
            self._configure_temp_graph(ax[1])

            fig.tight_layout(pad=2.0)
            
            # Save the plot to a temporary file
            fig.savefig(self.temp_filename, dpi=100, bbox_inches='tight', 
                       facecolor=BACKGROUND_COLOR, edgecolor='white')
            
            # Close the figure to free memory
            plt.close(fig)
            
            # Load the saved image as a pygame surface
            with self.lock:
                self.surface = pygame.image.load(self.temp_filename).convert()
                
        except Exception as e:
            print(f"Error updating GPU plot: {e}")

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.temp_filename):
                os.unlink(self.temp_filename)
        except Exception as e:
            print(f"Error cleaning up temp file: {e}")

def gpu_monitoring_thread(gpu_monitor, gpu_plot, update_interval, running):
    """Monitor GPU data and request plot updates"""
    gpu_graph_update_timer = 0
    while running[0]:
        current_time = pygame.time.get_ticks()
        if current_time - gpu_graph_update_timer >= update_interval:
            gpu_graph_update_timer = current_time
            # Just request an update, don't do matplotlib operations here
            gpu_plot.request_update(gpu_monitor)
        pygame.time.wait(100)
