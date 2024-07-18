import pygame
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import threading
import time

from gpumonitor import GPUMonitor
from gpuploter import GPUPlot, gpu_monitoring_thread
from welcome_scroller import WelcomeScroller
from cpumonitor import CPUMonitor

pygame.init()

# Get dims
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('Welcome to Valfar Lab - {Esc} to exit')
pygame.mouse.set_visible(False)

background_color = (0, 0, 0)

#scroller code
welcome_scroller = WelcomeScroller('Welcome to Valafar Lab', screen_info, screen_width, scrollspeed=2)

#gpu graph code
plt.style.use('dark_background')

num_gpus=2
gpu_plot00 = GPUPlot(num_gpus)
gpu_plot01 = GPUPlot(num_gpus)

gpu_monitor00 = GPUMonitor(http_listen=True, port=12345, num_gpus=num_gpus)
gpu_monitor00.start_monitoring()
gpu_monitor01 = GPUMonitor(http_listen=True, port=12346, num_gpus=num_gpus)
gpu_monitor01.start_monitoring()

def render_cpu_info(screen, cpu_monitor, x, y):
    fontbig = pygame.font.Font(pygame.font.match_font('ubuntusansmono'), 30)
    font = pygame.font.Font(pygame.font.match_font('ubuntusansmono'), 20)
    
    cpu_text = fontbig.render(f"CPU: {cpu_monitor.cpu_percent:.1f}%", True, (99,176,227))
    ram_text = fontbig.render(f"RAM: {cpu_monitor.ram_percent:.1f}%", True, (99,176,227))
    
    screen.blit(cpu_text, (x, y))
    screen.blit(ram_text, (x+250, y))
    
    y_offset = 50
    for proc in cpu_monitor.top_processes:
        proc_text = font.render(
            f"/{proc['username'][:10]:<11}"
            f"cpu:{proc['cpu_percent']:>6.2f}%   mem:{proc['memory_percent']:>6.2f}%"
            f"  pid:{proc['pid']:>6}"
            f" {proc['name'][:25]:<25}",
            True, (255, 255, 255))
        screen.blit(proc_text, (x, y + y_offset))
        y_offset += 30

cpu_monitor = CPUMonitor(http_listen=True, port=12347)
cpu_monitor.start_monitoring()

beast = pygame.font.Font(None, 55).render('Beast', True, (99,176,227))
beauty = pygame.font.Font(None, 55).render('Beauty', True, (99,176,227))


# main loop
clock = pygame.time.Clock()
update_interval = 5000  # 5 sec
running = True

gpu_thread00 = threading.Thread(target=gpu_monitoring_thread, args=(gpu_monitor00, gpu_plot00, update_interval, running))
gpu_thread00.start()

gpu_thread01 = threading.Thread(target=gpu_monitoring_thread, args=(gpu_monitor01, gpu_plot01, update_interval, running))
gpu_thread01.start()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    screen.fill(background_color)

    #welcome scroller
    welcome_scroller.update()
    welcome_scroller.draw(screen)

    #create outline of the 4 quadrants
    height_of_welcome_text = welcome_scroller.text_rect.height
    pygame.draw.line(screen, (255,255,255), (0, height_of_welcome_text), (screen_width, height_of_welcome_text), 1)
    pygame.draw.line(screen, (255,255,255), (screen_width//2, height_of_welcome_text), (screen_width//2, screen_height), 1)

    with gpu_plot00.lock:
        if gpu_plot00.surface:
            screen.blit(gpu_plot00.surface, (20, screen_height//2 + 10))

    with gpu_plot01.lock:
        if gpu_plot01.surface:
            screen.blit(gpu_plot01.surface, (screen_width // 2 + 20, screen_height//2 + 10))

    screen.blit(beast, (screen_width//5, welcome_scroller.text_rect.height + 10))
    render_cpu_info(screen, cpu_monitor, 0 + 20, height_of_welcome_text + 75)

    screen.blit(beauty, (screen_width // 2 + screen_width//5, welcome_scroller.text_rect.height + 10))
    render_cpu_info(screen, cpu_monitor, screen_width // 2 + 20, height_of_welcome_text + 75)

    pygame.display.flip()
    clock.tick(60)  # frame rate = 60

running = False
gpu_thread00.join()
gpu_thread01.join()
pygame.quit()
sys.exit()