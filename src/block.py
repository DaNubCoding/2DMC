# 2DMC is a passion project to recreate the game "Minecraft" (all credit to Mojang Studios) in 2D.
# Copyright (C) 2022 Doubleface
# You can view the terms of the GPL License in LICENSE.md

# The majority of the game assets are properties of Mojang Studios,
# you can view their TOS here: https://account.mojang.com/documents/minecraft_eula

import pygame

from src.constants import VEC, MIN_BLOCK_SIZE, BLOCK_SIZE, CHUNK_SIZE, BLOCK_DATA, WorldSlices
from src.particle import BlockParticle
from src.images import BLOCK_TEXTURES
from src.utils import inttup

class BlockData(dict):
    def __missing__(self, key):
        return ""

class Block:
    """Class that handles the managaing, updating and drawing of blocks."""
    instances = {}

    def __init__(self, chunk, pos: tuple, name: str):
        __class__.instances[tuple(pos)] = self
        self.name = name
        self.data = BLOCK_DATA[self.name]
        self.chunk = chunk
        self.coords = VEC(pos)
        self.pos = self.coords * BLOCK_SIZE
        self.neighbors = {
            "0 -1": inttup((self.coords.x, self.coords.y-1)),
            "0 1": inttup((self.coords.x, self.coords.y+1)),
            "-1 0": inttup((self.coords.x-1, self.coords.y)),
            "1 0": inttup((self.coords.x+1, self.coords.y))
        }
        self.image = BLOCK_TEXTURES[self.name]

        # Different hitbox types (currently only two)
        if self.data["collision_box"] == "full":
            self.rect = pygame.Rect(self.pos, (BLOCK_SIZE, BLOCK_SIZE))
        elif self.data["collision_box"] == "none":
            self.rect = pygame.Rect(self.pos, (0, 0))

    def update(self, chunks):
        # Check if the block is supported, if not then remove the block
        if not is_supported(self.data, self.neighbors):
            remove_block(chunks, self.coords, self.data, self.neighbors)

    def draw(self, screen):
        on_chunk_pos = self.pos.x / BLOCK_SIZE % CHUNK_SIZE * MIN_BLOCK_SIZE, self.pos.y / BLOCK_SIZE % CHUNK_SIZE * MIN_BLOCK_SIZE
        screen.blit(self.image, on_chunk_pos)

    def kill(self) -> None:
        if inttup(self.coords) in __class__.instances:
            del __class__.instances[inttup(self.coords)]
            del self

    def calc_pos(self, camera) -> None:
        self.rect.topleft = self.pos - camera.pos

class Location:
    instances: dict[tuple[int, int], Block] = {}

    def __init__(self, pos, **kwargs: dict[str, str]) -> None:
        self.pos = pos
        for worldslice, block in kwargs.items():
            self[worldslice] = block

    def __setitem__(self, key: WorldSlices, value: Block):
        setattr(self, key.name.lower(), value)

    def __getitem__(self, key: WorldSlices):
        getattr(self, key.name.lower(), "")

    def __contains__(self, key: WorldSlices):
        return getattr(self, key.name.lower(), False)

    def __delitem__(self, key: WorldSlices):
        delattr(self, key.name.lower())

    def get_if_in(self, key):
        if key in self:
            return self[key]

    def __bool__(self):
        return any([worldslice.name in self for worldslice in WorldSlices])

    # TODO: use tag system for transparency
    def draw(self, screen):
        get = self.get_if_in # Makes it a tad cleaner
        for block in {get(WorldSlices.FOREGROUND), get(WorldSlices.MIDDLEGROUND), get(WorldSlices.BACKGROUND)}:
            block.draw(screen)

            if block.name != "glass": # <- use tags here :P
                break

    def update(self, chunks):
        get = self.get_if_in # Makes it a tad cleaner
        for block in {get(WorldSlices.FOREGROUND), get(WorldSlices.MIDDLEGROUND), get(WorldSlices.BACKGROUND)}:
            block.update(chunks)

def remove_block(chunks: dict, pos: tuple, data: dict, neighbors: dict, worldslice: WorldSlices) -> None:
    """Remove the block at the position given

    Args:
        chunks (dict): A dictionary containing all the chunks
        pos (tuple): The position which has a block to remove
        data (dict): Dictionary of block data
        neighbors (dict): The neighbours of the block to remove
    """

    pos = inttup(pos)
    # Create a random number of particles
    BlockParticle.spawn(pos, Block.instances)
    chunk = (pos[0] // CHUNK_SIZE, pos[1] // CHUNK_SIZE)
    # TODO: Remove next layers and use worldslices instead :D
    # If the block is layered, instead of removing the block completely, change that block to the next layer
    if "next_layer" in data:
        Location.instances[pos][worldslice] = Block(chunk, pos, data["next_layer"])
        # chunks[chunk].block_data[pos][worldslice] = data["next_layer"] <- shouldnt be necessary
    else:
        # Remove the block from both the blocks dictionary AND the chunk information
        del Location.instances[pos][worldslice]
        del chunks[chunk].block_data[pos][worldslice]
        if not chunks[chunk].block_data[pos]: # check __bool__
            del Location.instances[pos]

    # After the block breaks, update its neighbors
    for neighbor in neighbors:
        if neighbors[neighbor] in Block.instances:
            Location.instances[pos][worldslice].update(chunks)

def set_block(chunks: dict, block_pos: tuple, block_name: str, worldslice: WorldSlices):
    block_pos = inttup(block_pos)
    # Calculates the position of the chunk the block is in.
    chunk = (block_pos[0] // CHUNK_SIZE, block_pos[1] // CHUNK_SIZE)
    if chunk in chunks:
        # Create an entry in the block dictionary that contains a new Block object
        Block.instances[block_pos] = Block(chunks[chunk], block_pos, block_name)
        if block_pos in chunks[chunk].block_data:
            chunks[chunk].block_data[block_pos][worldslice] = block_name
        else:
            chunks[chunk].block_data[block_pos] = Location(block_pos, **{worldslice.value: block_name})

def updated_set_block(chunks: dict, pos: tuple, name: str, neighbors: dict, worldslice: WorldSlices) -> None:
    """Set the block at the position given to the block given

    Args:
        chunks (dict): Dictionary containing all the chunks
        pos (tuple): The position of the block to set
        name (str): The name of the block to set
        neighbors (dict): THe neighbours of the block
    """

    set_block(chunks, pos, name, worldslice)
    for neighbor in neighbors:
        # Update the neighboring blocks
        if neighbors[neighbor] in Block.instances:
            Block.instances[neighbors[neighbor]].update(chunks)

def is_occupied(player, pos: tuple, worldslice: WorldSlices) -> bool:
    """Check if a block or the player overlaps with the position given

    Args:
        player (Player): The player
        pos (tuple): The position of the block that is being placed

    Returns:
        bool: Whether the given position is occupied or not
    """

    pos = inttup(pos)
    # Check if the player's rect is overlapping with the position of the block that is trying to be placed
    if not pygame.Rect(VEC(pos) * BLOCK_SIZE, (BLOCK_SIZE, BLOCK_SIZE)).colliderect(pygame.Rect(player.pos, player.size)):
        if pos in Location.instances: # If there is already a block there:
            if worldslice in Location.instances[pos]:
                # If the "replaceable" key is in the block's data, meaning that the block is directly replaceable (i.e. grass)
                return "replaceable" not in Location.instances[pos][worldslice].data # This will return False if the block is replaceable and vice versa
            else:
                return False
        else:
            return False
    return True

def is_supported(data: dict, neighbors: dict[str, tuple[int, int]], ignored_block_offset: None | VEC = None) -> bool:
    """Checks if the given block data (data) of the block can be supported at the given position

    Args:
        data (dict): The data information of the block
        neighbors (dict): The block's neighbours
        ignored_block_offset (None or VEC): The offset of the supporting block to be ignored (used for counterpart/multi-block placing)

    Returns:
        bool: Whether the block will be supported at the given position
    """

    if "support" in data and data["support"]: # If the block requires support
        for support in data["support"]: # Check every required supporting block
            if neighbors[support] in Block.instances: # If the required support position has a block there
                # If the block is not the required supporting block
                if Block.instances[neighbors[support]].name not in data["support"][support]:
                    return False
            else: # If the required support position doesn't have a block there
                if ignored_block_offset: # If there's a required support position to be ignored
                    support_vec = VEC(inttup(support.split()))
                    # If the ignored offset refers to the same block pos as the required support block pos, then it is placeable
                    if inttup(-support_vec) == inttup(ignored_block_offset):
                        return True
                return False # If there are no ignored blocks, it is not placeable
    return True # If it doesn't require support, then it is placeable

def is_placeable(player, pos: tuple, data: dict, neighbors: dict, counterpart_offset: None | VEC = None) -> bool:
    """Evaluates if a block is placeable at a given position

    Args:
        player (Player): The player
        pos (tuple): The position to check
        data (dict): The block data
        neighbors (dict): The block's neighbours
        second_block_pos (tuple, optional): Passed into is_supported for some unknown magical reason. Defaults to False.

    Returns:
        bool: If you can place the block or not
    """

    # Checking if the position occupied and supported.
    return not is_occupied(player, pos) and is_supported(data, neighbors, counterpart_offset)
