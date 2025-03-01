#Heavily upgraded basic godot physics code that i then converted to Python --Aymeric
import pygame as pg

import sys

import pygame
class Physics :
    #Overall physics and movement handler
    def __init__(self):
        self.vel_x = 0
        self.vel_y = 0
        self.y = 0
        self.x = -100
        self.stage = []

        self.SPEED = 2.5
        self.DASH_SPEED = 6
        self.JUMP_VELOCITY = -6.0
        self.DASHTIME = 12
        self.JUMPTIME = 10

        self.dashtime_cur = 0  # Immune to gravity during dashtime
        self.dash_amt = 1
        self.jumptime_cur = 0

        self.direction = 0
        self.last_direction = 1

        self.dash_direction_x = 0
        self.dash_direction_y = 0

        self.tech_momentum_mult = 0
        self.dict_kb = {"key_right":0, "key_left":0, "key_up":0, "key_down":0, "key_jump":0, "key_dash":0}
        self.anti_dash_buffer = False

    def physics_process(self,framerate,dict_kb,stage):
        """Input :
        framerate (int) : current framerate. Used for gravity
        dict_kb (dict) : (for each key in dict) whether this key is currently pressed. 1 if true, 0 if false."""
        # Player movement and gravity handler.

        #Turn dict.kb provided as arg into a class variable
        self.dict_kb = dict_kb
        self.stage = stage



        # Get the input direction and handle the movement.
        # Prevents being stuck when holding 2 directions.
        self.direction = self.get_direction("x")
        if self.direction != 0:
            self.last_direction = self.direction



        if not self.dashtime_cur > 0:
            if self.vel_x != 0 and abs(self.vel_x) / self.vel_x != self.direction:
                self.vel_x += self.direction * self.SPEED / 2
            elif abs(self.vel_x) <= abs(self.direction * self.SPEED):
                self.vel_x = self.direction * self.SPEED

        self.gravity()

        # Jump & Tech logic
        self.jump()

        # Dash logic
        self.dash()
        self.dash_momentum()

        self.collision_check()


        return self.apply_momentum()


    def gravity(self):
        # Gravity (ignored during dashtime to not be annoying)
        if not self.is_on_floor() and not self.dashtime_cur > 0:
            self.vel_y = min(5, self.vel_y+0.5)

        elif self.is_on_floor():
            if self.is_on_floor(self.y - 1):
                self.y -= 1
            if self.vel_y > 0:
                self.vel_y = 0
            if self.dashtime_cur < 10 and self.dash_amt == 0:
                self.dash_amt = 1



    def jump(self):

        if self.dict_kb["key_jump"] == 1 and self.is_on_floor():
            self.vel_y = self.JUMP_VELOCITY

            # Wavedash/Superdash. X Velocity is set to sqrt(2)*DASH_SPEED*20 if wavedash (diagonal into jump), DASH_SPEED*20 if superdash (parallel into dash)
            # Cancels any dash time remaining.
            if self.dashtime_cur != 0:
                self.dashtime_cur = 0
                self.tech_momentum_mult = pow(abs(self.dash_direction_x) + abs(self.dash_direction_y), 0.5)
                self.vel_x = self.get_direction("x") * self.DASH_SPEED * (self.tech_momentum_mult)
                self.vel_y /= self.tech_momentum_mult

    def dash(self):
        if not self.anti_dash_buffer:
            if self.dict_kb["key_dash"]== 1:
                if self.dash_amt > 0:
                    self.dash_direction_x = self.get_direction("x")
                    self.dash_direction_y = self.get_direction("y")

                    if self.dash_direction_x == 0 and self.dash_direction_y == 0:  # Have a default dash direction to not get stuck in the air.
                        self.dash_direction_x = self.last_direction
                    self.dashtime_cur = self.DASHTIME

                    self.dash_amt -= 1
                self.anti_dash_buffer = True
        else:
            if self.dict_kb["key_dash"] == 0:
                self.anti_dash_buffer = False


    def dash_momentum(self):
        if self.dashtime_cur > 0:
            self.dashtime_cur -= 1
            self.vel_x = self.dash_direction_x * self.DASH_SPEED
            self.vel_y = -1 * self.dash_direction_y * self.DASH_SPEED
            if self.is_on_floor(self.y+self.vel_y):
                self.vel_y = 0
            if self.dashtime_cur == 0:
                self.vel_x = 0
                self.vel_y = 0

    def apply_momentum(self):
        #Basic physics : add vel to position
        self.x += self.vel_x
        self.y += self.vel_y

        #Ground/Air friction. Stop significantly faster on the ground than in the air
        if self.is_on_floor():
            self.vel_x *= 0.2
        elif self.get_direction("x") == 0:
            self.vel_x *= 0.8


        return (-self.x,self.y)

    def is_on_floor(self, cur_y="undef"):
        if cur_y == "undef":
            cur_y = self.y
        if cur_y > 50:
            return True
        #TODO : CHANGE THIS

    def get_direction(self,axis):
        if axis == "x":
            return self.dict_kb["key_left"] - self.dict_kb["key_right"]
        elif axis == "y":
            return self.dict_kb["key_up"] - self.dict_kb["key_down"]
        else:
            print("Error encountered : get_direction() received an axis that is neither x nor y")
            return 0

    def collision_check(self):
        pass


class Game:
    #USED FOR DEBUGGING. DO NOT REUSE IT SUCKS.
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('TEST')
        self.screen = pygame.display.set_mode((1640, 980))

        self.clock = pygame.time.Clock()

        self.img = pygame.image.load('../assets/images/debugasset.png')
        self.img.set_colorkey((0, 0, 0))
        self.img = pygame.transform.scale(self.img, (50,50))

        self.img_pos = [160, 260]

        self.collision_area = pygame.Rect(50, 50, 300, 50)

    def run(self):
        phys = Physics()
        dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0}
        while True:
            self.screen.fill((14, 219, 248))

            img_r = pygame.Rect(self.img_pos[0], self.img_pos[1], self.img.get_width(), self.img.get_height())
            if img_r.colliderect(self.collision_area):
                pygame.draw.rect(self.screen, (0, 100, 255), self.collision_area)
            else:
                pygame.draw.rect(self.screen, (0, 50, 155), self.collision_area)





            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        dict_kb["key_up"] = 1
                    if event.key == pygame.K_s:
                        dict_kb["key_down"] = 1
                    if event.key == pygame.K_q:
                        dict_kb["key_left"] = 1
                    if event.key == pygame.K_d:
                        dict_kb["key_right"] = 1
                    if event.key == pygame.K_q:
                        dict_kb["key_left"] = 1
                    if event.key == pygame.K_g:
                        dict_kb["key_dash"] = 1
                    if event.key == pygame.K_h:
                        dict_kb["key_attack"] = 1
                    if event.key == pygame.K_SPACE:
                        dict_kb["key_jump"] = 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_z:
                        dict_kb["key_up"] = 0
                    if event.key == pygame.K_s:
                        dict_kb["key_down"] = 0
                    if event.key == pygame.K_q:
                        dict_kb["key_left"] = 0
                    if event.key == pygame.K_d:
                        dict_kb["key_right"] = 0
                    if event.key == pygame.K_q:
                        dict_kb["key_left"] = 0
                    if event.key == pygame.K_g:
                        dict_kb["key_dash"] = 0
                    if event.key == pygame.K_h:
                        dict_kb["key_attack"] = 0
                    if event.key == pygame.K_SPACE:
                        dict_kb["key_jump"] = 0

            coords = phys.physics_process(1,dict_kb,list_stage)
            self.img_pos[0],self.img_pos[1] = coords
            self.screen.blit(self.img, self.img_pos)

            pygame.display.update()
            self.clock.tick(60)

if __name__ == "__main__":
    Game().run()

