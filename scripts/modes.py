
def set_default_mode(game, speed=2.5):
    # Constants for movement
        game.player.SPEED = speed
        game.player.DASH_SPEED = 6
        game.player.JUMP_VELOCITY = -6.5
        game.player.DASHTIME = 12
        game.player.JUMPTIME = 10
        game.player.DASH_COOLDOWN = 50
        game.player.WALLJUMP_COOLDOWN = 5
        game.current_mode = "default"

def set_autorun_mode(game, direction="r", speed=2.5):
    set_default_mode(game, speed)
    game.player.force_movement = direction
    game.current_mode = "autorun"

