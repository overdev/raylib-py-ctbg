# raylib-ctbg-2.6
A Python ctypes binding generator for the great C library raylib (ver. 2.6).

### Description

`raylib-py-ctbg` generates the binding code required to load and use the API
exposed in the raylib header file. The output python file contains all
constants, structures, enumerations and functions. 


### Usage

* Add the source folder `rlctbg` to your project folder;
* Drop in this folder the `raylib.h` you want to generate the bind for, and
  the binaries for the corresponding python architecture (32bit or 64bit) and platform
  (Windows, Mac or Linux) to be loaded. The loader will select the binary acording
  to the platform, but the architecture must match the intepreter's.
* In the initialization of your main module, import the `rlctbg` module:

```python
import rlctbg
```
* Call it, passing optionaly the C header file path and the output python file:
 
```python
rlctbg.wrap_header()
``` 
* Import the output module:
```python
import rlctbg.raylib as rl
```

* Have fun!
```python
# -*- encoding: utf-8 -*-

import rlctbg
rlctbg.wrap_header()
import rlctbg.raylib as rl


__all__ = ['main']

# ------------------------------------------------------------------------------
# region MAIN


def main():
    screen_width: int = 800
    screen_height: int = 450

    rl.init_window(screen_width, screen_height, b"raylib [core] example - basic window")

    rl.set_target_fps(60)

    while not rl.window_should_close():

        # Logic and input handling goes here.

        # Render is done between begin_drawing and end_drawing functions.
        rl.begin_drawing()

        rl.clear_background(rl.RAYWHITE)
        rl.draw_text(b"Congrats! You created your first window!", 190, 200, 20, rl.LIGHTGRAY)

        rl.end_drawing()

    rl.close_window()

    return 0

# endregion (main)
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    main()

```

### TO-DO

- Extend some structure classes to allow more flexible handling of ctype objects.
- Include some header comments as docstring for functions and classes.
- Add automatic conversion between `bytes` (`c_char_p`) and `str` (utf8) inside wrappers.
- Refactor the code generation function.
- generate a `CHEATSHEET.md` along with the binding code


### Additional Information

raylib-ctbg does not include the raylib binaries. Those are available in the
C raylib [repository](https://github.com/raysan5/raylib), in the
[releases tab](https://github.com/raysan5/raylib/releases).
