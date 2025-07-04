import pygame
import sys
import threading
import time
from matplotlib.backends.backend_agg import FigureCanvasAgg

from gpumonitor import GPUMonitor
from gpuploter import GPUPlot, gpu_monitoring_thread
from welcome_scroller import WelcomeScroller
from headline_scroller import HeadlineScroller
from newsapi import NEWSAPI
from cpumonitor import CPUMonitor

# Constants
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
UPDATE_INTERVAL = 5000  # in milliseconds
NEWS_UPDATE_INTERVAL = 900000  # 15 minutes
CPU_PORT = 12347
GPU_PORTS = [12345, 12346]
NUM_GPUS = 2

# Initialize pygame
pygame.init()
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('Welcome to Valfar Lab - {Esc} to exit')
pygame.mouse.set_visible(False)

# Initialize components
newsapi = NEWSAPI()
headlines = newsapi.get_stories()

welcome_scroller = WelcomeScroller('Welcome to Valafar Lab', screen_info, screen_width, scrollspeed=2)
headlines_scroller = HeadlineScroller(newsapi, headlines, screen, 0, screen_height - screen_height // 2, screen_width // 2, screen_height // 2)

# GPU monitors and plots
gpu_monitors = [GPUMonitor(http_listen=True, port=port, num_gpus=NUM_GPUS) for port in GPU_PORTS]
for monitor in gpu_monitors:
    monitor.start_monitoring()

gpu_plots = [GPUPlot(NUM_GPUS) for _ in range(len(GPU_PORTS))]

# CPU monitor
cpu_monitor = CPUMonitor(http_listen=True, port=CPU_PORT)
cpu_monitor.start_monitoring()

# Fonts
font_large = pygame.font.Font(pygame.font.match_font('ubuntumono'), 30)
font_small = pygame.font.Font(pygame.font.match_font('ubuntumono'), 20)
font_title = pygame.font.Font(None, 55)
beast_cpu_text = font_title.render('Beast CPU', True, (99, 176, 227))

# Threads - Use mutable running flag
running_flag = [True]  # Using list to make it mutable for thread access
gpu_threads = []
for monitor, plot in zip(gpu_monitors, gpu_plots):
    thread = threading.Thread(target=gpu_monitoring_thread, args=(monitor, plot, UPDATE_INTERVAL, running_flag))
    gpu_threads.append(thread)
    thread.start()

# Functions
def handle_events():
    """Handle Pygame events."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return False
    return True

def render_cpu_info(x, y):
    """Render CPU and RAM information on the screen."""
    cpu_text = font_large.render(f"CPU: {cpu_monitor.cpu_percent:.1f}%", True, TEXT_COLOR)
    ram_text = font_large.render(f"RAM: {cpu_monitor.ram_percent:.1f}%", True, TEXT_COLOR)

    screen.blit(cpu_text, (x, y))
    screen.blit(ram_text, (x, y + 30))

    y_offset = 85
    for proc in cpu_monitor.top_processes:
        proc_text = font_small.render(
            f"/{proc['username'][:10]:<11}"
            f"cpu:{proc['cpu_percent']:>6.2f}%   mem:{proc['memory_percent']:>6.2f}%"
            f"  pid:{proc['pid']:>6}"
            f" {proc['name'][:25]:<25}",
            True, TEXT_COLOR)
        screen.blit(proc_text, (x, y + y_offset))
        y_offset += 30

def render_gpu_plots():
    """Render GPU plots on the screen."""
    plot_positions = [
        (screen_width // 2 + 20, welcome_scroller.text_rect.height + 10),
        (screen_width // 2 + 20, screen_height // 2 + 10)
    ]

    # Update plots if needed (main thread only)
    for plot in gpu_plots:
        plot.update_if_needed()

    for plot, (x, y) in zip(gpu_plots, plot_positions):
        with plot.lock:
            if plot.surface:
                screen.blit(plot.surface, (x, y))

def render_layout():
    """Draw layout and scrollers."""
    height_of_welcome_text = welcome_scroller.text_rect.height

    # Welcome scroller
    welcome_scroller.update()
    welcome_scroller.draw(screen)

    # Headlines scroller
    headlines_scroller.update()
    headlines_scroller.draw()

    # Quadrant outlines
    pygame.draw.rect(screen, TEXT_COLOR, (0, height_of_welcome_text, screen_width // 2, screen_height // 2 - height_of_welcome_text), 1)
    pygame.draw.rect(screen, TEXT_COLOR, (0, screen_height // 2, screen_width // 2, screen_height // 2), 1)
    pygame.draw.rect(screen, TEXT_COLOR, (screen_width // 2, screen_height // 2, screen_width // 2, screen_height // 2), 1)
    pygame.draw.rect(screen, TEXT_COLOR, (screen_width // 2, height_of_welcome_text, screen_width // 2, screen_height // 2 - height_of_welcome_text), 1)

# Main loop
clock = pygame.time.Clock()
running = True

try:
    while running:
        screen.fill(BACKGROUND_COLOR)

        running = handle_events()
        render_layout()
        render_gpu_plots()
        render_cpu_info(screen_width // 16, welcome_scroller.text_rect.height + 55)

        screen.blit(beast_cpu_text, (screen_width // 5, welcome_scroller.text_rect.height + 10))
        pygame.display.flip()
        clock.tick(60)

finally:
    # Cleanup
    running_flag[0] = False  # Signal threads to stop
    
    for thread in gpu_threads:
        thread.join()
    
    # Clean up temporary files
    for plot in gpu_plots:
        plot.cleanup()

pygame.quit()
sys.exit()
