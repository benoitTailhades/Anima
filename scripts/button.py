import pygame

class Button:

    def __init__(self, left, top, width, height, clicking):
        self.x = left
        self.y = top
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.clicking = clicking
        self.activated = True

    def pressed(self, mpos):
        if self.clicking and self.rect.collidepoint(mpos):
            return True
        return False

    def draw(self, surf, color, mpos):
        if self.rect.collidepoint(mpos) and not self.pressed(mpos) and self.activated:
            color = (0, 0, 0)
        pygame.draw.rect(surf, color, self.rect)