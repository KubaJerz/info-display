import pygame

# Welcome text scroller class
class WelcomeScroller:
    def __init__(self, welcome_text, screen_info, x_start, y=0, scrollspeed=2, padding=15, fontsize=74, textcolor=(255, 255, 255)):
        self.text = pygame.font.Font(pygame.font.match_font('ubuntumono'), fontsize).render(welcome_text, True, textcolor)
        self.text_rect = self.text.get_rect(left=x_start, top=y)
        self.screen_width = screen_info.current_w
        self.scrollspeed = scrollspeed
        self.padding = padding

    def update(self):
        self.text_rect.x -= self.scrollspeed
        if self.text_rect.right < 0:  # Reset once off screen
            self.text_rect.left = self.screen_width

    def draw(self, screen):
        screen.blit(self.text, self.text_rect)
