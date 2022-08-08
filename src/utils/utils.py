# 2DMC is a passion project to recreate the game "Minecraft" (all credit to Mojang Studios) in 2D.
# Copyright (C) 2022 Doubleface
# You can view the terms of the GPL License in LICENSE.md

# The majority of the game assets are properties of Mojang Studios,
# you can view their TOS here: https://account.mojang.com/documents/minecraft_eula

from typing import Callable, Any
import pygame

def scale_by(surf, scale):
    return pygame.transform.scale(surf, (surf.get_width() * scale, surf.get_height() * scale))

def sign(num: int | float) -> int:
    """Returns the sign of the num (+/-) as -1, 0, or 1"""
    return (num > 0) - (num < 0)

do_profile = False
def profile(callable: Callable[..., Any], *args: tuple[Any]) -> Any:
    """Profiles the given callable and saves + prints the results
    Args:
        callable (type): A callabale type (function, constructor, ect)
    Returns:
        [...]: The result of calling the callable
    """

    global do_profile
    if do_profile: # Profile_bool stops the user from being able to hold down the profile key
        do_profile = False
        with cProfile.Profile() as profile: # Profiling the contents of the with block
            returnval = callable(*args)     # Calling the callable with the args

        # Naming the profile file in the format "profile_{hour}-{minute}-{second}.prof"
        statfile = Path(os.path.join(PROFILE_DIR, str(datetime.datetime.now().strftime("profile_%H-%M-%S")) + ".prof"))
        if not (statfile_dirpath := statfile.parent).exists():
            statfile_dirpath.mkdir() # Creating the dirpath of the statfile (ex. "build/profiles") if they do not exist
        stats = pstats.Stats(profile).sort_stats(pstats.SortKey.TIME) # Sorting the stats from highest time to lowest
        stats.dump_stats(filename=str(statfile)) # Saving the stats to a profile file
        stats.print_stats()                      # Printing the stats
        print(f"\n\n Profile saved to: {str(statfile)}!\n\n")
        return returnval
    else: # Return the output of the callable
        return callable(*args)