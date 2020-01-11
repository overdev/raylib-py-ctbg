# -*- encoding: utf-8 -*-


"""SUGESTED FOLDER STRUCTURE:

project_root
    +-- rlctbg
    |       +-- __init__.py
    |       +-- raylib.h    <--------- the header file
    |       +-- raylib.py   <--------- the generated binding
    |       +-- raylib.dll  <--------- the binary loaded by the binding provided by you
    +-- example.py  <----------------- this example file

"""


import rlctbg
rlctbg.wrap_header()
import rlctbg.raylib as rl


__all__ = ['main']

# region MAIN


def main():
    basic_window()
    camera()


def basic_window():
    screen_width: int = 800
    screen_height: int = 450

    rl.init_window(screen_width, screen_height, b"raylib [core] example - basic window")

    rl.set_target_fps(60)

    while not rl.window_should_close():

        rl.begin_drawing()

        rl.clear_background(rl.RAYWHITE)
        rl.draw_text(b"Congrats! You created your first window!", 190, 200, 20, rl.LIGHTGRAY)

        rl.end_drawing()

    rl.close_window()

    return 0


def camera():
    # include "raylib.h"
    MAX_BUILDINGS = 100

    # Initialization
    # --------------------------------------------------------------------------------------
    screen_width: int = 800
    screen_height: int = 450

    rl.init_window(screen_width, screen_height, b"raylib [core] example - 2d camera")

    player = rl.Rectangle(400, 280, 40, 40)
    buildings = [rl.Rectangle() for _ in range(MAX_BUILDINGS)]
    build_colors = [rl.Color() for _ in range(MAX_BUILDINGS)]

    spacing: int = 0

    for i in range(MAX_BUILDINGS):
        buildings[i].width = rl.get_random_value(50, 200)
        buildings[i].height = rl.get_random_value(100, 800)
        buildings[i].y = screen_height - 130 - buildings[i].height
        buildings[i].x = -6000 + spacing

        spacing += buildings[i].width

        build_colors[i] = rl.Color(rl.get_random_value(200, 240), rl.get_random_value(200, 240), rl.get_random_value(200, 250), 255)

    camera: rl.Camera2D = rl.Camera2D()
    camera.target = rl.Vector2(player.x + 20, player.y + 20)
    camera.offset = rl.Vector2(screen_width / 2, screen_height / 2)
    camera.rotation = 0.0
    camera.zoom = 1.0

    rl.set_target_fps(60) # Set our game to run at 60 frames-per-second
    # --------------------------------------------------------------------------------------

    # Main game loop
    while not rl.window_should_close(): # Detect window close button or ESC key
        # Update
        # ----------------------------------------------------------------------------------
    
        # Player movement
        if rl.is_key_down(rl.KEY_RIGHT):
            player.x += 2
        elif rl.is_key_down(rl.KEY_LEFT):
            player.x -= 2
    
        # Camera target follows player
        camera.target = rl.Vector2(player.x + 20, player.y + 20)
    
        # Camera rotation controls
        if rl.is_key_down(rl.KEY_A):
            camera.rotation -= 1.0
        elif rl.is_key_down(rl.KEY_S):
            camera.rotation += 1.0
    
        # Limit camera rotation to 80 degrees (-40 to 40)
        if camera.rotation > 40:
            camera.rotation = 40
        elif camera.rotation < -40:
            camera.rotation = -40
    
        # Camera zoom controls
        camera.zoom += rl.get_mouse_wheel_move() * 0.05
    
        if camera.zoom > 3.0:
            camera.zoom = 3.0
        elif camera.zoom < 0.1:
            camera.zoom = 0.1
    
        # Camera reset (zoom and rotation)
        if rl.is_key_pressed(rl.KEY_R):
            camera.zoom = 1.0
            camera.rotation = 0.0
        # ----------------------------------------------------------------------------------
    
        # Draw
        # ----------------------------------------------------------------------------------
        rl.begin_drawing()
    
        rl.clear_background(rl.RAYWHITE)
    
        rl.begin_mode2_d(camera)
    
        rl.draw_rectangle(-6000, 320, 13000, 8000, rl.DARKGRAY)
    
        for i in range(MAX_BUILDINGS):
            rl.draw_rectangle_rec(buildings[i], build_colors[i])
    
        rl.draw_rectangle_rec(player, rl.RED)
    
        rl.draw_line(int(camera.target.x), -screen_height * 10, int(camera.target.x), screen_height * 10, rl.GREEN)
        rl.draw_line(-screen_width * 10, int(camera.target.y), screen_width * 10, int(camera.target.y), rl.GREEN)
    
        rl.end_mode2_d()
    
        rl.draw_text(b"SCREEN AREA", 640, 10, 20, rl.RED)
    
        rl.draw_rectangle(0, 0, screen_width, 5, rl.RED)
        rl.draw_rectangle(0, 5, 5, screen_height - 10, rl.RED)
        rl.draw_rectangle(screen_width - 5, 5, 5, screen_height - 10, rl.RED)
        rl.draw_rectangle(0, screen_height - 5, screen_width, 5, rl.RED)
    
        rl.draw_rectangle(10, 10, 250, 113, rl.fade(rl.SKYBLUE, 0.5))
        rl.draw_rectangle_lines(10, 10, 250, 113, rl.BLUE)
    
        rl.draw_text(b"Free 2d camera controls:", 20, 20, 10, rl.BLACK)
        rl.draw_text(b"- Right/Left to move Offset", 40, 40, 10, rl.DARKGRAY)
        rl.draw_text(b"- Mouse Wheel to Zoom in-out", 40, 60, 10, rl.DARKGRAY)
        rl.draw_text(b"- A / S to Rotate", 40, 80, 10, rl.DARKGRAY)
        rl.draw_text(b"- R to reset Zoom and Rotation", 40, 100, 10, rl.DARKGRAY)
    
        rl.end_drawing()
    # ----------------------------------------------------------------------------------

    # De-Initialization
    # --------------------------------------------------------------------------------------
    rl.close_window()    # Close window and OpenGL context
    # --------------------------------------------------------------------------------------

    return 0


# endregion (functions)
# ---------------------------------------------------------


if __name__ == '__main__':
    main()
