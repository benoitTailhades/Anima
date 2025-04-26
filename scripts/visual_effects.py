import pygame
import random

def generate_fog(surface, color=(220, 230, 240), opacity=40):
    fog_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    fog_surface.fill((*color, opacity))
    surface.blit(fog_surface, (0, 0))
    
def create_light_mask(radius, color=(255, 255, 255), intensity=255, edge_softness=50, flicker=False):
    """
    Generate a circular light mask with customizable properties and smooth gradient
    """
    # Apply random flicker effect if enabled
    actual_radius = radius
    if flicker and random.random() < 0.3:
        flicker_factor = 0.85 + random.random() * 0.3
        actual_radius = int(radius * flicker_factor)
        intensity = int(intensity * flicker_factor)

    # Create a fresh surface for this light
    light_mask = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    center = (radius, radius)

    # Use more steps for a smoother gradient
    steps = min(actual_radius, 100)  # Increased from 40 to 100

    # Draw from outside in with increasingly transparent circles
    for i in range(steps):
        # Calculate radius for this step - working from outside in
        r = actual_radius - (i * actual_radius / steps)

        # Calculate alpha based on distance from edge
        # This creates a smoother falloff function
        distance_factor = i / steps
        # Use a non-linear function for smoother falloff
        alpha = int(intensity * (distance_factor ** 0.8))  # Exponent < 1 creates a softer gradient

        # Apply color with calculated alpha
        light_color = color + (alpha,)
        pygame.draw.circle(light_mask, light_color, center, r)

    # Optional: Apply a small Gaussian blur if pygame has this capability
    # This would require an external library like pygame.transform.smoothscale
    # or implementing a custom blur function

    return light_mask

def apply_lighting(game, render_scroll):
    """Apply darkness effect with player and other light sources"""
    # Create a surface for darkness
    darkness = pygame.Surface(game.display.get_size(), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, game.darkness_level))  # Semi-transparent black

    # Create and apply player light
    player_props = game.player_light
    player_light = create_light_mask(
        player_props["radius"],
        player_props["color"],
        player_props["intensity"],
        player_props["edge_softness"],
        player_props["flicker"]
    )

    # Calculate player position on screen
    player_screen_x = game.player.rect().centerx - render_scroll[0]
    player_screen_y = game.player.rect().centery - render_scroll[1]

    # Position for the light mask
    light_x = player_screen_x - player_props["radius"]
    light_y = player_screen_y - player_props["radius"]

    # Apply the player light mask to the darkness surface
    darkness.blit(player_light, (light_x, light_y), special_flags=pygame.BLEND_RGBA_SUB)

    # Process light-emitting tiles
    for light_tile in game.light_emitting_tiles:
        # Get position and properties
        pos = light_tile["pos"]
        light_type = light_tile.get("type", "torch")
        properties = game.light_properties[light_type]

        # Calculate screen position
        tile_screen_x = pos[0] - render_scroll[0]
        tile_screen_y = pos[1] - render_scroll[1]

        # Check if the light is visible on screen (with buffer)
        buffer = properties["radius"] * 2
        if (-buffer <= tile_screen_x <= game.display.get_width() + buffer and
                -buffer <= tile_screen_y <= game.display.get_height() + buffer):
            # Create light mask for this tile
            tile_light = create_light_mask(
                properties["radius"],
                properties["color"],
                properties["intensity"],
                properties["edge_softness"],
                properties["flicker"]
            )

            # Apply light
            light_pos = (tile_screen_x - properties["radius"], tile_screen_y - properties["radius"])
            darkness.blit(tile_light, light_pos, special_flags=pygame.BLEND_RGBA_SUB)

    # Process light-emitting objects (enemies, items, etc.)
    for light_obj in game.light_emitting_objects:
        if hasattr(light_obj, "pos") and hasattr(light_obj, "light_properties"):
            props = light_obj.light_properties

            # Calculate screen position
            obj_screen_x = light_obj.pos[0] - render_scroll[0]
            obj_screen_y = light_obj.pos[1] - render_scroll[1]

            # Create light mask for this object
            obj_light = create_light_mask(
                props.get("radius", 80),
                props.get("color", (255, 255, 255)),
                props.get("intensity", 200),
                props.get("edge_softness", 30),
                props.get("flicker", False)
            )

            # Apply light
            light_pos = (obj_screen_x - props["radius"], obj_screen_y - props["radius"])
            darkness.blit(obj_light, light_pos, special_flags=pygame.BLEND_RGBA_SUB)

    # Apply the darkness to the display
    game.display.blit(darkness, (0, 0))

def register_light_emitting_tile(game, pos, light_type="torch"):
    """Register a new light-emitting tile at the given position"""
    if light_type in game.light_properties:
        game.light_emitting_tiles.append({
            "pos": pos,
            "type": light_type
        })

def register_light_emitting_object(game, obj, properties=None):
        """Register an object as a light source"""
        if not hasattr(obj, "light_properties") and properties:
            obj.light_properties = properties
        game.light_emitting_objects.append(obj)
        
def draw_cutscene_border(surf, color=(0, 0, 0), width=20, opacity=255):

        border_surface = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

        # Draw top border
        pygame.draw.rect(border_surface, (*color, opacity), (0, 0, surf.get_width(), width))

        # Draw bottom border
        pygame.draw.rect(border_surface, (*color, opacity),
                         (0, surf.get_height() - width, surf.get_width(), width))


        # Blit the border onto the screen
        surf.blit(border_surface, (0, 0))
