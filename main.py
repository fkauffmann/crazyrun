#    __________  ___ _______  __   ____  __  ___   __
#   / ____/ __ \/   /__  /\ \/ /  / __ \/ / / / | / /
#  / /   / /_/ / /| | / /  \  /  / /_/ / / / /  |/ / 
# / /___/ _, _/ ___ |/ /__ / /  / _, _/ /_/ / /|  /  
# \____/_/ |_/_/  |_/____//_/  /_/ |_|\____/_/ |_/   
#                                                    
# History:
# 2025.04.10 : Initial version (FK)
#
# Based on this gamedev tutorial by FinFET
# https://www.youtube.com/watch?v=xTyURl8qjZw
#
# Game Music by edwardszakal -- https://freesound.org/s/514154/ -- License: Attribution NonCommercial 4.0
#
import asyncio
import pygame as pg
import sys, platform, math, random

from explosion import Explosion

# --- Constantes ---
SCREEN_WIDTH, SCREEN_HEIGHT = 320, 180
ROAD_DEPTH = 120
Z_BUFFER_DEFAULT = 999
COLORKEY = (255, 0, 255)

# --- Variables globales
damage_anim_duration = 0                # durée de l'animation d'explision
game_level = 0                          # 0 = intro

# --- Fonctions de rendu du terrain ---
def calc_y(x):
    """Calcul de l'altitude horizontale de la route"""
    return 200 * math.sin(x / 17) + 170 * math.sin(x / 8)

def calc_z(x):
    """Calcul du relief vertical (profondeur)"""
    return 200 + 80 * math.sin(x / 13) - 120 * math.sin(x / 7)

def render_element(screen, sprite, width, height, scale, x, car, y_offset, z_buffer, detect_collision):
    global damage_anim_duration
    y = calc_y(x) - y_offset
    z = calc_z(x) - car.z
    vertical = int(60 + 160 * scale + z * scale)

    if 1 <= vertical < SCREEN_HEIGHT and z_buffer[vertical - 1] > 1 / scale - 10:
        horizontal = 160 - (160 - y) * scale + car.angle * (vertical - 150)
        scaled_sprite = pg.transform.scale(sprite, (int(width), int(height)))
        screen.blit(scaled_sprite, (horizontal, vertical - height + 1))

        if detect_collision:
            # Collision avec la voiture du joueur (toujours à x=120, y=100)
            sprite_rect = pg.Rect(horizontal, vertical - height + 1, 40, 40)
            player_rect = pg.Rect(120, 100, 40, 40)  # Taille fixe du sprite joueur

            if sprite_rect.colliderect(player_rect) and scale > 0.5:
                car.velocity *= 0.7
                car.acceleration *= 0.5
                damage_anim_duration = 4


# --- Classes objets du jeu ---
class Tree:
    def __init__(self, distance):
        self.x = distance + random.randint(10, 20) + 0.5
        self.y = random.randint(500, 1500) * random.choice([-1, 1])

class Car:
    def __init__(self, distance):
        self.x = distance + random.randint(90, 110)

class Player:
    def __init__(self):
        self.x = 0
        self.y = 300
        self.z = 0
        self.angle = 0
        self.velocity = 0
        self.acceleration = 0

    def controls(self, delta):
        keys = pg.key.get_pressed()
        self.acceleration += -0.5 * self.acceleration * delta
        self.velocity += -0.5 * self.velocity * delta

        if keys[pg.K_w] or keys[pg.K_UP]:
            if self.velocity > -1:
                self.acceleration += 4 * delta
            else:
                self.acceleration = 0
                self.velocity += -self.velocity * delta
        elif keys[pg.K_s] or keys[pg.K_DOWN]:
            if self.velocity < 1:
                self.acceleration -= delta
            else:
                self.acceleration = 0
                self.velocity += -self.velocity * delta

        self.going_left = False
        self.going_right = False

        if keys[pg.K_a] or keys[pg.K_LEFT]:
            self.angle -= delta * self.velocity / 10
            self.going_left = True
        elif keys[pg.K_d] or keys[pg.K_RIGHT]:
            self.angle += delta * self.velocity / 10
            self.going_right = True

        # Clamp angle et vitesse
        self.velocity = max(-10, min(self.velocity, 20))
        self.angle = max(-0.8, min(self.angle, 0.8))
        self.velocity += self.acceleration * delta
        self.x += self.velocity * delta * math.cos(self.angle)
        self.y += self.velocity * math.sin(self.angle) * delta * 100

# --- Boucle principale du jeu ---
async def main():
    global damage_anim_duration
    global game_level

    # Initialisation de l’écran
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SCALED | pg.RESIZABLE)

    clock = pg.time.Clock()
    clock.tick(); pg.time.wait(16)

    # Chargement des textures
    def load_sprite(path):
        sprite = pg.image.load(path).convert()
        sprite.set_colorkey(COLORKEY)
        return sprite

    intro_texture = pg.image.load("assets/intro.png").convert()
    road_texture = pg.image.load("assets/road.png").convert()
    sky_texture = pg.image.load("assets/sky.png").convert()

    car_back_sprite = load_sprite("assets/f40_back.png")
    car_left_sprite = load_sprite("assets/f40_left.png")
    car_right_sprite = load_sprite("assets/f40_right.png")

    traffic_sprite = load_sprite("assets/traffic.png")
    tree_sprite = load_sprite("assets/palmtree.png")

    # Chargement de la police
    game_font_small = pg.freetype.Font("fonts/lcd.ttf", 16)
    game_font_medium = pg.freetype.Font("fonts/lcd.ttf", 20)

    # Création des objets
    car = Player()
    cars = [Car(-50), Car(-23), Car(7)]
    trees = [Tree(x) for x in [-67, -55, -43, -33, -25, -13, -3]]
    explosion = Explosion()

    # Get some music
    if pg.mixer.get_init():
        pg.mixer.music.load("sounds/soundtrack.mp3")
        pg.mixer.music.set_volume(0.8)

    running = True
    total_time = 0

    while running:
        delta = clock.tick() / 1000 + 1e-5
        total_time += delta
        car.controls(delta)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE]:
            game_level = 1
            pg.mixer.music.play(-1)


        if game_level==1:

            # Affichage du fond nuageux
            screen.blit(sky_texture, (-65 - car.angle * 82, 0))

            # Rendu de la route et buffer Z
            vertical, draw_distance = SCREEN_HEIGHT, 1
            car.z = calc_z(car.x)
            z_buffer = [Z_BUFFER_DEFAULT] * SCREEN_HEIGHT

            while draw_distance < ROAD_DEPTH:
                last_vertical = vertical
                while vertical >= last_vertical and draw_distance < ROAD_DEPTH:
                    draw_distance += draw_distance / 150
                    x = car.x + draw_distance
                    scale = 1 / draw_distance
                    z = calc_z(x) - car.z
                    vertical = int(60 + 160 * scale + z * scale)

                if draw_distance < ROAD_DEPTH:
                    z_buffer[min(SCREEN_HEIGHT - 1, vertical)] = draw_distance
                    road_slice = road_texture.subsurface((0, int(10 * x) % 360, SCREEN_WIDTH, 1))
                    color = (
                        int(150 - draw_distance / 3),
                        int(130 - draw_distance),
                        int(50 - z / 20 + 30 * math.sin(x))
                    )
                    pg.draw.rect(screen, color, (0, vertical, SCREEN_WIDTH, 1))
                    render_element(screen, road_slice, 500 * scale, 1, scale, x, car, car.y, z_buffer, False)

            # Rendu des arbres
            for tree in reversed(trees[:-1]):
                scale = max(1e-4, 1 / (tree.x - car.x))
                render_element(screen, tree_sprite, 320 * scale, 320 * scale, scale, tree.x, car, tree.y + car.y, z_buffer, False)

            if trees[0].x < car.x + 1:
                trees.pop(0)
                trees.append(Tree(trees[-1].x))

            # Rendu des voitures adverses
            for other_car in reversed(cars[:-1]):
                scale = max(1e-4, 1 / (other_car.x - car.x))
                render_element(screen, traffic_sprite, 80 * scale, 80 * scale, scale, other_car.x, car, -220 + car.y, z_buffer, True)
                other_car.x -= 10 * delta          

            if cars[0].x < car.x + 1:
                cars.pop(0)
                cars.append(Car(car.x))

            # Rendu et animation de la voiture du joueur
            if car.going_left:
                screen.blit(car_left_sprite, (120, 100))
            if car.going_right:
                screen.blit(car_right_sprite, (120, 100))
            if not car.going_left and not car.going_right:
                screen.blit(car_back_sprite, (120, 100))

            # Rendu des dégats
            if damage_anim_duration > 0:
                screen.blit(explosion.image, (SCREEN_WIDTH / 2 - 24, 110))
                voice = pg.mixer.Channel(5)
                if not voice.get_busy():
                    voice.play(explosion.explosion_sound) 
                damage_anim_duration = damage_anim_duration - (delta*10)                  

            # Rendu de la vitesse
            game_font_medium.render_to(screen, (251, 11), str(int(car.velocity*20)).zfill(3), (0,0,0))        
            game_font_medium.render_to(screen, (250, 10), str(int(car.velocity*20)).zfill(3), (255,255,255))        
            game_font_small.render_to(screen, (284, 14), "KMH", (0,255,255))        

            # Crash si trop de différence de hauteur
            if abs(car.y - calc_y(car.x + 2) - 100) > 280 and car.velocity > 5:
                car.velocity *= (1 - delta)
                car.acceleration *= (1 - delta)
                pg.draw.circle(screen, (255, 0, 0), (300, 170), 3)

            # Avance l'animation de l'explosion
            explosion.update(delta)

        if game_level==0:
            # Affichage de l'image d'intro
            screen.blit(intro_texture, (0, 0))
            game_font_medium.render_to(screen, (110, 76), "PRESS SPACE", (255,255,255))        


        pg.display.update()
        await asyncio.sleep(0)

# --- Lancement du jeu ---
if __name__ == "__main__":
    pg.init()
    pg.mixer.init()

    pg.display.set_caption("Crazy Run")
    icon = pg.image.load("assets/icon.png")
    pg.display.set_icon(icon)

    asyncio.run(main())

    pg.quit()
