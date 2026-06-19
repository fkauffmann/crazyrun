import pygame as pg

class Explosion:
    def __init__(self):
        self.pos = (0, 0)
        sheet = pg.image.load("assets/explosion.png")
        self.images = []
        for x in range(0, 1536, 96):
            rect = pg.Rect((x, 0, 96, 96))
            image = pg.Surface(rect.size, pg.SRCALPHA, 32)
            image = image.convert_alpha()
            image.blit(sheet, (0, 0), rect)
            # Redimensionnement (optionnel)
            image = pg.transform.smoothscale(image, (48, 48))
            self.images.append(image)

        self.image = self.images[0]
        self.index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.08  # Durée d’une image en secondes (ex: 0.08 = ~12.5 fps)
        self.explosion_sound = pg.mixer.Sound("sounds/explosion.wav")
        self.explosion_sound.set_volume(0.4)

    def update(self, delta):
        self.frame_timer += delta
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0  # ou self.index = len(self.images) - 1 pour rester figé
            self.image = self.images[self.index]
