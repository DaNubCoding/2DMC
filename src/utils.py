from pygame.draw import rect as drawrect
from pygame.locals import SRCALPHA
from pygame.surface import Surface
from pygame.math import Vector2
from pathlib import Path
from pygame import Rect
from typing import Any
import cProfile
import datetime
import cProfile
import pstats
import os

from src.constants import *

def pathof(file: str) -> str:
    """Gets the path to the given file that will work with exes.

    Args:
        file (str): The original path to go to

    Returns:
        str: The bundled - exe compatible file path
    """

    abspath = os.path.abspath(os.path.join(BUNDLE_DIR, file))
    if not os.path.exists(abspath):
        abspath = file
    return abspath

def intv(vector: Vector2) -> Vector2:
    """Returns vector where x and y are integers"""
    return VEC(int(vector.x), int(vector.y))

def inttup(tup: tuple) -> tuple:
    """Returns a tuple where both elements are integers"""
    return (int(tup[0]), int(tup[1]))

def text(text: str, color: tuple=(0, 0, 0)) -> Surface:
    """Returns a surface which has the given text argument rendered using font 24 in the given colour (default black)"""
    return FONT24.render(text, True, color)

def smol_text(text: str, color: tuple=(255, 255, 255)) -> Surface:
    """Returns a surface which has the given text argument rendered using font 20 in the given colour (default white)"""
    return FONT20.render(text, True, color)

def create_text_box(text: Surface, pos: tuple, opacity: int) -> tuple[Surface, tuple]:
    """Creats a text box at the position given with the supplied text and opacity

    Args:
        text (Surface): A rendered surface of the text (most often generated by text())
        pos (tuple): The position to draw at
        opacity (int): The opacity of the text box

    Returns:
        tuple[Surface, tuple]: Returns a surface containing the text box and the position to draw at
    """
    # Creating a surface slightly larger than the text and changing opacity
    text_rect = text.get_rect()
    blit_pos = pos
    surface = Surface((text_rect.width+16, text_rect.height+8), SRCALPHA)
    surface.set_alpha(opacity)

    # Drawing a bunch of rects the make the minecraft-y style purple border
    drawrect(surface, (0, 0, 0), (2, 0, text_rect.width + 12, text_rect.height + 8))
    drawrect(surface, (0, 0, 0), (0, 2, text_rect.width + 16, text_rect.height + 4))
    drawrect(surface, (44, 8, 99), (2, 2, text_rect.width + 12, 2))
    drawrect(surface, (44, 8, 99), (2, 4 + text_rect.height, text_rect.width + 12, 2))
    drawrect(surface, (44, 8, 99), (2, 2, 2, text_rect.height + 4))
    drawrect(surface, (44, 8, 99), (12 + text_rect.width, 2, 2, text_rect.height + 4))

    # Blitting the text onto the surface and returning it and the pos
    surface.blit(text, (8, 4))
    return surface, blit_pos

def block_collide(playerx: int, playery: int, width: float, height: float, detecting: list, block) -> tuple[bool, str]:
    """Checks collision between the player and the given block object.

    Args:
        playerx (int): The x position of the player.
        playery (int): The y position of the player.
        width (float): The width of the player.
        height (float): The height of the player.
        detecting (list): The detecting_rects lists used by the player (player.detecting_rects)
        block (Block, type not specified due to circular imports): The block object to check collision with.

    Returns:
        bool: True if the player is colliding with the block else False
        list: The detetcing_rects list with the new rect appended to it
    """

    player_rect = Rect(playerx, playery, width, height) # Rect that represents the player
    block_rect = Rect(block.pos.x, block.pos.y, BLOCK_SIZE, BLOCK_SIZE) # Rect that represents the block
    if not block.rect in detecting:
        detecting.append(block.rect) # Adding the block rect to player.detecting_rects
    if player_rect.colliderect(block_rect): # Checking if the player is colliding with the block
        return True, detecting
    return False, detecting

def canter_pairing(tup: tuple) -> int:
    """Uses the Canter Pairing function to get a unique integer from a unique interger pair"""
    # Deal with negative numbers by turning positives into positive evens and negatives into positive odds
    a = 2 * tup[0] if tup[0] >= 0 else -2 * tup[0] - 1
    b = 2 * tup[1] if tup[1] >= 0 else -2 * tup[1] - 1
    return (a + b) * (a + b + 1) + b

def ascii_str_sum(string: str) -> int:
    """Gets the sum of the ASCII values of all the letters in a string"""
    return sum([ord(letter) for letter in string])

profile_bool = False
def profile(callable: type, *args: tuple):
    global profile_bool
    if profile_bool:
        profile_bool = False
        with cProfile.Profile() as profile:
            returnval = callable(*args)

        statfile = Path(os.path.join(PROFILE_DIR, str(datetime.datetime.now().strftime("profile_%H-%M-%S"))))
        stats = pstats.Stats(profile).sort_stats(pstats.SortKey.TIME)
        if not (statfile_dirpath := statfile.parent).exists():
            statfile_dirpath.mkdir()
        stats.dump_stats(filename=str(statfile))
        stats.print_stats()
        return returnval
    else:
        return callable(*args)