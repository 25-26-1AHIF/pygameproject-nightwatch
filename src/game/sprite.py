import pygame

class Sprite:
    def __init__(self, filepath: str, image_count: int,
                 image_rect: pygame.Rect, animation_speed: int):
        self.filepath        = filepath
        self.image_count     = image_count
        self.image_rect      = image_rect
        self.animation_speed = animation_speed
        self.images: list[pygame.Surface] = []

    def load_spritesheet(self) -> None:
        sprite_sheet = pygame.image.load(self.filepath).convert_alpha()
        for i in range(self.image_count):
            # SRCALPHA damit Transparenz erhalten bleibt
            frame = pygame.Surface(self.image_rect.size, pygame.SRCALPHA).convert_alpha()
            frame.blit(sprite_sheet, dest=(0, 0),
                       area=pygame.Rect(i * self.image_rect.width,
                                        self.image_rect.y,
                                        self.image_rect.width,
                                        self.image_rect.height))
            self.images.append(frame)

    def draw(self, screen: pygame.Surface, xpos: float, ypos: float,
             frame_counter: int, scale: tuple = None):
        img = self.images[(frame_counter // self.animation_speed) % self.image_count]
        if scale:
            img = pygame.transform.scale(img, scale)
        screen.blit(img, dest=(xpos, ypos))
