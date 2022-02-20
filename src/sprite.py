from __future__ import annotations

from enum import Enum, auto
from pygame import Surface
from typing import Any

class LayersEnum(Enum):
    BACKGROUND = auto()
    ENV_PARTICLES = auto()
    BLOCKS = auto()
    REG_PARTICLES = auto()
    BLOCK_SELECTION = auto()
    DEBUG = auto()
    PLAYER = auto()
    INVENTORY = auto()
    CROSSHAIR = auto()

class Sprite:
    """A common baseclass for all sprites."""

    def __init__(self, layer: int | LayersEnum, debug_layer: int | LayersEnum | None = None) -> None:
        # Setting the layer attribute. This defines where in the draw order the sprite will be drawn.
        # See SpriteHandler.draw()
        # In theory try except is faster as layer will almost always be an enum, so may as well
        try:
            self._layer = layer.value
        except AttributeError:
            if isinstance(layer, int):
                self._layer = layer
            else:
                raise TypeError("Argument 'layer' must be of type 'int' or 'Enum item'")

        if not debug_layer:
            self._debug_layer = self._layer
        else:
            try:
                self._debug_layer = debug_layer.value
            except AttributeError:
                if isinstance(debug_layer, int):
                    self._debug_layer = debug_layer
                else:
                    raise TypeError("Argument 'debug_layer' must be of type 'int' or 'Enum item'")

    def update(self, dt: float, **kwargs: dict[Any]) -> None:
        """Update the classes attributes and variables or handle class logic related to the class.

        Args:
            dt (float): Delta time
            **kwargs (dict[Any]): Class specific arguments
        """

    def draw(self, screen: Surface, **kwargs: dict[Any]) -> None:
        """Draw the sprite to the screen

        Args:
            screen (Surface): The screen to draw to
            **kwargs (dict[Any]): Class specific arguments
        """

    def debug(self, screen: Surface, **kwargs: dict[Any]) -> None:
        """Draw the sprite's debug information to the given screen

        Args:
            screen (Surface): The screen to draw to
            **kwargs (dict[Any]): Class specific arguments
        """

    def kill(self) -> None:
        """Kill the sprite and handle any cleanup logic"""

class NoLayerAttributeException(Exception):
    """If the sprite does not have a layer attribute"""

    def __init__(self, sprite: Sprite) -> None:
        self.sprite = sprite

    def __str__(self) -> str:
        return f"Class {self.sprite.__class__} does not have a _layer / _debug_layer attribute!"

class LayerNotFoundException(Exception):
    """If the sprites layer did not exist in the layer dict"""

    def __init__(self, arg: int | Sprite) -> None:
        if isinstance(arg, Sprite):
            arg = arg._layer
        self._layer = arg

    def __str__(self) -> str:
        return f"Layer {LayersEnum(self._layer).name} does not exist in the layer list!"

class SpriteNotFoundException(Exception):
    """If the sprite did not exist inside the layer"""

    def __init__(self, sprite: Sprite) -> None:
        self.sprite = sprite

    def __str__(self) -> str:
        return f"Sprite object {self.sprite} does not exist in the sprite list!"

class SpriteHandler:
    """A class to simplify and better how sprites are drawn and managed"""

    def __init__(self, *args: tuple[Sprite]) -> None:
        self.layers = {}
        if args: # You can create a spritehandler without specifying any args
            self.add(*args)

    def __iter__(self) -> SpriteHandler:
        # Sorting the layer dict so that the lowest layer (layer that should be drawn first)
        # is first, and the highest is drawn last
        self.layers = dict(sorted(self.layers.items()))
        self.layeriter = self.spriteiter = 0 # Iteration variables
        return self

    def __next__(self) -> tuple[list, Sprite]:
        # If the current layer is greater than the number of layers, stop the iteration (this exits a for loop)
        if self.layeriter >= len(self.layers):
            raise StopIteration

        # The layers dict is keyed by the layer, but we need it to be keyed by its index
        # Ideally this would be in __iter__ but fsr it crashes so.. ¯\_(ツ)_/¯
        layer = list(self.layers.values())[self.layeriter]
        self.spriteiter += 1 # Increase the iter variable
        # Then check if it is greater than the max.
        if self.spriteiter >= len(layer):
            self.layeriter += 1 # Next iteration, loop through the next layer
            self.spriteiter = 0 # Reset the sprite iter variable

        return list(self.layers)[self.layeriter - 1 if self.layeriter > 1 else 0], layer[self.spriteiter] # Return the sprite

    def __contains__(self, sprite: Sprite) -> bool:
        try:
            return sprite in self.layers[sprite._layer]
        except AttributeError: # No layer attribute
            raise NoLayerAttributeException(sprite)
        except KeyError: # Layer not found
            # We dont want it to throw an error, but may as well have a warning
            print(str(LayerNotFoundException(sprite)))
            return False

    def add(self, *args: tuple[Sprite]) -> None:
        """Add any number of sprites to the list of sprites

        Args:
            *args (tuple of Sprites): The sprites to add (can be of arbitary length)

        Raises:
            NoLayerAttributeException: If any given sprite does not have a layer attribute
        """

        for sprite in args:
            try:
                if sprite._layer != sprite._debug_layer: # If the debug layer is specified (not default)
                    if sprite._debug_layer not in self.layers: # Make a new debug layer
                        self.layers[sprite._debug_layer] = [sprite]
                    else: # Add to an existing debug layer
                        self.layers[sprite._debug_layer].append(sprite)

                if sprite._layer not in self.layers: # Make a new layer
                    self.layers[sprite._layer] = [sprite]
                else: # Add the sprite to a pre-existing layer
                    self.layers[sprite._layer].append(sprite)
            # Try / Except is faster
            # Raised if the sprite does not have a layer / debug layer attribute
            except AttributeError:
                raise NoLayerAttributeException(sprite)

    def remove(self, sprite: Sprite) -> None:
        try: # Remove the sprite
            self.layers[sprite._layer].remove(sprite)
        except ValueError: # If the sprite was not in its corresponding layer list
            raise SpriteNotFoundException(sprite)
        except KeyError: # If the sprite's layer was not in the layer dict
            raise LayerNotFoundException(sprite._layer)

        # If the layer list is empty, delete it
        # (Having an empty list breaks iteration)
        if not self.layers[sprite._layer]:
            del self.layers[sprite._layer]

    def draw(self, screen: Surface, debug: bool, **kwargs) -> None:
        for layer in self.layers:
            # If the layer is a debug layer and debug is active, debug every sprite in the layer
            if LayersEnum(layer).name.endswith("_DEBUG"):
                if debug:
                    for sprite in self.layers[layer]:
                        sprite.debug(screen, **kwargs)
            # If its not a debug layer just draw every sprite
            else:
                for sprite in self.layers[layer]:
                    sprite.draw(screen, **kwargs)

    def update(self, dt: float, **kwargs) -> None:
        for layer, sprite in self:
            if not LayersEnum(layer).name.endswith("_DEBUG"): # Dont update debug layers (would be repetition)
                sprite.update(dt, **kwargs)