# Anima  
Project Group - Projet Transverse EFREI 2025  
By François-Xavier Sabatier, Benoit Tailhades, Raphaël Cayeux, Aymeric Danlos and Loïc Giannini  

[![Watch the video](https://img.youtube.com/vi/jJIcrVEib6A/maxresdefault.jpg)](https://youtu.be/jJIcrVEib6A)

### [Watch this video on YouTube](https://youtu.be/jJIcrVEib6A)

## Concept  
“What if the last millisecond of your life was your only chance for redemption?”
Anima is a narrative-driven platformer set in the final moment of a man's life — a criminal seeking redemption just before his death. The player dives into the dying mind of this man, navigating a surreal and decaying landscape shaped by guilt, denial, and past sins.  

## Gameplay Summary  
The game begins with a brief and implicit execution scene — a gunshot, a flash...  
The player then enters the Main caracter’s mind, experiencing a fast-paced platformer reflecting his psychological descent that he has lived throuhought his all life.  
Each level goes deeper, becoming darker and more chaotic, showing how he ignored his conscience throughout his life.  
At the end, the player confronts the Main caracter’s soul — an unwinnable boss fight.  
The journey ends with the inevitable death, underlining the game’s core moral: "It is never too late to beg pardon until it is" .  

This game isn't just a platformer — it's a philosophical journey. The goal: show that waiting until your last breath to change your ways is often too late. We want players to feel the weight of choices, even in retrospect, and question the illusion of last-minute redemption. 

## Technical tools  
**Game engine**: Pygame   
**Language**: Python 100%  
**Assets**: Entirely hand drawn(on a tablet)   
**Sound design**: Made up from pieces all over internet  
**Version Control**: Github (I think you figured that out)   

## Code's structure 
```
└── benoittailhades-anima/
    ├── Readme.md
    ├── editor.py
    ├── main.py
    ├── assets/
    │   ├── images/
    │   │   ├── activators/
    │   │   │   ├── buttons/
    │   │   │   │   └── blue_cave/
    │   │   │   ├── levers/
    │   │   │   │   ├── blue_cave/
    │   │   │   │   └── green_cave/
    │   │   │   ├── progressive_teleporters/
    │   │   │   │   └── blue_cave/
    │   │   │   └── teleporters/
    │   │   │       └── blue_cave/
    │   │   ├── backgrounds/
    │   │   │   ├── blue_cave/
    │   │   │   └── green_cave/
    │   │   ├── clouds/
    │   │   ├── doors/
    │   │   │   ├── blue_cave/
    │   │   │   │   ├── blue_vine_door_h/
    │   │   │   │   │   ├── closed/
    │   │   │   │   │   ├── closing/
    │   │   │   │   │   ├── opened/
    │   │   │   │   │   └── opening/
    │   │   │   │   ├── blue_vine_door_v/
    │   │   │   │   │   ├── closed/
    │   │   │   │   │   ├── closing/
    │   │   │   │   │   ├── opened/
    │   │   │   │   │   └── opening/
    │   │   │   │   └── breakable_stalactite/
    │   │   │   │       ├── closed/
    │   │   │   │       ├── opened/
    │   │   │   │       └── opening/
    │   │   │   └── green_cave/
    │   │   │       ├── vines_door_h/
    │   │   │       │   ├── closed/
    │   │   │       │   ├── closing/
    │   │   │       │   ├── opened/
    │   │   │       │   └── opening/
    │   │   │       └── vines_door_v/
    │   │   │           ├── closed/
    │   │   │           ├── closing/
    │   │   │           ├── opened/
    │   │   │           └── opening/
    │   │   ├── entities/
    │   │   │   ├── bosses/
    │   │   │   │   ├── ego/
    │   │   │   │   │   ├── appear/
    │   │   │   │   │   ├── idle/
    │   │   │   │   │   ├── laser_charge/
    │   │   │   │   │   ├── laser_fire/
    │   │   │   │   │   ├── missile_charge/
    │   │   │   │   │   ├── missile_fire/
    │   │   │   │   │   └── teleport/
    │   │   │   │   └── wrath/
    │   │   │   │       ├── charge/
    │   │   │   │       ├── death/
    │   │   │   │       ├── hit/
    │   │   │   │       ├── idle/
    │   │   │   │       ├── jump/
    │   │   │   │       └── run/
    │   │   │   │           ├── left/
    │   │   │   │           └── right/
    │   │   │   ├── elements/
    │   │   │   │   ├── blue_rock/
    │   │   │   │   │   ├── breaking/
    │   │   │   │   │   └── intact/
    │   │   │   │   └── vine/
    │   │   │   │       ├── attack/
    │   │   │   │       ├── retreat/
    │   │   │   │       └── warning/
    │   │   │   ├── enemies/
    │   │   │   │   ├── glorbo/
    │   │   │   │   │   ├── attack/
    │   │   │   │   │   ├── death/
    │   │   │   │   │   ├── hit/
    │   │   │   │   │   ├── idle/
    │   │   │   │   │   └── run/
    │   │   │   │   └── picko/
    │   │   │   │       ├── attack/
    │   │   │   │       ├── death/
    │   │   │   │       ├── hit/
    │   │   │   │       ├── idle/
    │   │   │   │       └── run/
    │   │   │   │           ├── left/
    │   │   │   │           └── right/
    │   │   │   └── player/
    │   │   │       ├── attack/
    │   │   │       │   ├── left/
    │   │   │       │   └── right/
    │   │   │       ├── dash/
    │   │   │       │   ├── left/
    │   │   │       │   ├── right/
    │   │   │       │   └── top/
    │   │   │       ├── falling/
    │   │   │       │   ├── left/
    │   │   │       │   ├── right/
    │   │   │       │   └── vertical/
    │   │   │       ├── idle/
    │   │   │       ├── jump/
    │   │   │       │   ├── left/
    │   │   │       │   ├── right/
    │   │   │       │   └── top/
    │   │   │       ├── run/
    │   │   │       │   ├── left/
    │   │   │       │   └── right/
    │   │   │       └── wall_slide/
    │   │   │           ├── left/
    │   │   │           └── right/
    │   │   ├── particles/
    │   │   │   ├── crystal/
    │   │   │   ├── crystal_fragment/
    │   │   │   ├── leaf/
    │   │   │   └── particle/
    │   │   ├── projectiles/
    │   │   ├── spawners/
    │   │   ├── tiles/
    │   │   │   ├── blue_cave/
    │   │   │   │   ├── big_bloody_spikes/
    │   │   │   │   ├── big_spikes/
    │   │   │   │   ├── bloody_spikes/
    │   │   │   │   ├── blue_decor/
    │   │   │   │   ├── blue_grass/
    │   │   │   │   ├── blue_large_decor/
    │   │   │   │   └── spikes/
    │   │   │   └── green_cave/
    │   │   │       ├── dark_vine/
    │   │   │       ├── gray_mossy_stone/
    │   │   │       ├── hanging_vine/
    │   │   │       ├── mossy_stone/
    │   │   │       ├── mossy_stone_decor/
    │   │   │       ├── vine/
    │   │   │       ├── vine_decor/
    │   │   │       ├── vine_transp/
    │   │   │       └── vine_transp_back/
    │   │   └── transition/
    │   └── sounds/
    │       ├── effects
    │       ├── musics
    │       └── player/
    ├── data/
    │   ├── activators.json
    │   ├── texts.json
    │   └── maps/
    │       ├── 0.json
    │       ├── 1.json
    │       ├── 2.json
    │       ├── 3.json
    │       └── 4.json
    ├── scripts/
    │   ├── activators.py
    │   ├── boss.py
    │   ├── display.py
    │   ├── doors.py
    │   ├── entities.py
    │   ├── particle.py
    │   ├── physics.py
    │   ├── saving.py
    │   ├── sound.py
    │   ├── spark.py
    │   ├── text.py
    │   ├── tilemap.py
    │   ├── user_interface.py
    │   └── utils.py
    └── utilities/
        ├── animations
        └── helpers
```



## Getting started 
To play **Anima** on it's early state(right now state...) You will have to do:   
**Whatch this explaining video I made**  

[![Regarder la vidéo](https://img.youtube.com/vi/vT6RiCA_D9Q/maxresdefault.jpg)](https://www.youtube.com/watch?v=vT6RiCA_D9Q)


**Or** (if you hate me and don't want to watch my video)  
 
>Open pycharm **last version**.   
>Create a new project  
>Paste this URL: https://github.com/benoitTailhades/Anima.git when copying repo.

Then make sure to install These libraries in the Pycharm console.   
**Install** :
```sh
pip install pygame
```
**Make sure Json python is installed** 
```sh
pip install json
```
**Enjoy !!**
 
 ## Features  
 One millisecond of gameplay stretched into hours of intense gameplay, symbolic action.  
 Descending level design to reflect the journey into one's deep nibble(yes I used google traduction for this word) conscience.  
 Psychological storytelling through sound, color, and game mechanics.  
 Implicit narrative — very little amount of dialogues, most emotions and visuals.  
 Dynamic audio assets representing thoughts, memories, regrets.  
 Unwinnable final confrontation, emphasizing the tragic ending.  
  
## Team Roles  
**Loïc Giannini** – [Project Director, Art realisation/ Designer, Major dev, Game designer]  
  
**Benoit Tailhades** – [Story Teller, Major dev, Documentation writer, Game designer]  

**Raphaël Cayeux** – [Level designer]  

**Aymeric Danlos** – [Physic Dev]  

**François-Xavier Sabatier** – [Sound designer]  
  
## Acknoledgements/Inspirations  
Graphic Inspiration from games like Inside, Celeste, Hollow knight    
Unconsiously inspired by Dante's Inferno painting   

## Sources   
**Pygame**: documentation https://www.pygame.org/docs/  
**youtube**: https://www.youtube.com/  
**Chat GPT**: https://www.chatgpt.com/
**Claude AI**: https://www.claude.ai/  
**Internet documentation** : google (I guess)   
**This video**: https://youtu.be/2gABYM5M0ww  



