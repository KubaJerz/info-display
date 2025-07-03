import pygame
import sys

#init the game
pygame.init()

#get the dims
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

screen = pygame.display.set_mode((screen_width, screen_height),pygame.FULLSCREEN)
pygame.display.set_caption('I ani\'t noting yet but we working! {Esc} to exit')

pygame.mouse.set_visible(False)

background_color = (0,0,0)

#lets insert some text
font = pygame.font.Font(None, 174)
text = font.render('Welcome to Valafar Lab',True, (255, 255, 255))
text_rect = text.get_rect()

#positon stuff
text_x = screen_width
text_y = screen_height // 2 - text_rect.height // 2

speed = 2


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False


    text_x -= speed
    if text_x < -text_rect.width:
        text_x = screen_width

    screen.fill(background_color)

    #draw the text
    screen.blit(text, (text_x, text_y))

    pygame.display.flip()
    pygame.time.Clock().tick(60) #frame rate = 60

pygame.quit()
sys.exit()
