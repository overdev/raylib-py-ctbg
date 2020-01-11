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
rlctbg.wrap_header(import_module=False)
import rlctbg.raylib as rl


__all__ = [
    'main',
]

# region MAIN


def main():
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

# endregion (functions)
# ---------------------------------------------------------


if __name__ == '__main__':
    main()
