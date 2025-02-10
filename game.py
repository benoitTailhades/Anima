import pygame

import sys 

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Anima") #Nom de la fenêtre
        self.screen = pygame.display.set_mode((800, 600))

        self.clock = pygame.time.Clock()

        self.img = pygame.image.load("Data\data\images\clouds\cloud_1.png") #Chargement de l'image
        self.img.set_colorkey((0,0,0)) #Couleur de transparence

        self.img_pos = [160, 260]
        self.movement = [False, False]

        self.collision_area = pygame.Rect(50, 50, 300, 50) #Zone de collision

    def run(self):
        running = True

        while running: #Boucle qui sert à actualiser le jeu
            self.screen.fill((14, 219, 248)) #Couleur de fond et clear de l'écran
            
            img_r = pygame.Rect(self.img_pos[0],self.img_pos[1],self.img.get_width(),self.img.get_height()) 
            if img_r.colliderect(self.collision_area): #Vérifie si la zone de collision de l'image touche celle de l'objet
                pygame.draw.rect(self.screen,(0, 100, 255),self.collision_area)
            else:
                pygame.draw.rect(self.screen,(0, 50, 155),self.collision_area)

            self.img_pos[1] += (self.movement[1] - self.movement[0]) * 5 #Déplacement de l'image
            self.screen.blit(self.img,self.img_pos) #Affiche l'image à la position donnée
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:   #Quitte le jeu si la touche en question est appuyée
                    running = False 
                    sys.exit()  #Quitte le programme
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.movement[0] = True
                    if event.key == pygame.K_DOWN:
                        self.movement[1] = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        self.movement[0] = False
                    if event.key == pygame.K_DOWN:
                        self.movement[1] = False
            pygame.display.update()
            self.clock.tick(60) #Actualise le jeu 60 fois par seconde

Game().run()
