import pygame


class HeadlineScroller:
    def __init__(self, api, headlines, screen, subscreen_x_start, subscreen_y_start, sub_screen_width, sub_screen_height, scroll_speed=1, titlefont_size=26, body_font_size=19, subfont_size=17, title_color=(255, 255, 255), source_color=(0, 122, 204), date_color=(99, 176, 227)):
        self.api = api
        self.headlines = headlines
        self.num_headlines = len(headlines)

        self.subsurface_rect = pygame.Rect(subscreen_x_start, subscreen_y_start, sub_screen_width, sub_screen_height)
        self.subsurface = screen.subsurface(self.subsurface_rect)

        self.max_left = 0  # The length of the longest headline
        self.scroll_speed = scroll_speed

        self.x = self.subsurface_rect.width
        self.sub_screen_height = sub_screen_height

        self.headline_font = self._init_font(titlefont_size)
        self.sub_font = self._init_font(subfont_size)
        self.body_font = self._init_font(body_font_size)

        self.y_padding = sub_screen_height // len(headlines)
        self.headline_col = title_color
        self.date_col = date_color
        self.source_col = source_color

    def _init_font(self, size):
        """Initialize font with the given size."""
        return pygame.font.Font(pygame.font.match_font('ubuntusansmono'), size)

    def _render_text(self, text, font, color):
        """Render text with a given font and color."""
        return font.render(text, True, color)

    def update(self):
        """Update the scroll position and reload headlines when needed."""
        self.x -= self.scroll_speed
        if self.x <= -self.max_left:  # Reset position when pad screen
            self.headlines = self.api.get_stories()
            self.x = self.subsurface_rect.width

    def draw(self):
        """Draw all the headlines and associated data on the subsurface."""
        x = self.x
        for i, headline in enumerate(self.headlines):
            headline_text = self._render_text(headline["headline"], self.headline_font, self.headline_col)
            source_text = self._render_text(headline["source"], self.sub_font, self.source_col)
            time_text = self._render_text(headline["time"], self.sub_font, self.date_col)
            body_text = self._render_text(headline["body"], self.body_font, self.headline_col)

            self.max_left = max(body_text.get_width(), headline_text.get_width(), self.max_left)

            self._blit_texts(x, i, headline_text, body_text, source_text, time_text)

    def _blit_texts(self, x, i, headline_text, body_text, source_text, time_text):
        """Blit the texts (headline, body, source, time) to the subsurface."""
        y_position = i * self.y_padding + 15
        self.subsurface.blit(headline_text, (x, y_position))
        self.subsurface.blit(body_text, (x, y_position + 5 * (headline_text.get_height() // 4)))
        self.subsurface.blit(source_text, (x, y_position + 8 * (headline_text.get_height() // 4)))
        self.subsurface.blit(time_text, (x + 250, y_position + 8 * (headline_text.get_height() // 4)))