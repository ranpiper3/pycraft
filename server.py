from time import time

from math import radians

import terrain, saves, render


chunk_size = terrain.world_gen['chunk_size']
blocks = render.gen_blocks()

SUN_TICK = radians(1/32)
TPS = 10 # Ticks


class Server:
    def __init__(self, save):
        self.save = save
        self.meta = saves.load_meta(save)
        self.last_tick = time()

    def load_chunks(self, slice_list):
        new_slices = {}
        gen_slices = {}

        # Generates new terrain
        for chunk_num in set(i // chunk_size for i in slice_list):
            chunk = saves.load_chunk(self.save, chunk_num)
            for i in range(chunk_size):
                pos = i + chunk_num * chunk_size
                if not str(pos) in chunk:
                    slice_ = terrain.gen_slice(pos, self.meta, blocks)
                    chunk[str(pos)] = slice_
                    gen_slices[str(pos)] = slice_
            new_slices.update(chunk)
    
        # Save generated terrain to file
        if gen_slices:
            saves.save_map(self.save, gen_slices)
    
        return new_slices

    def tick(self):
        # Increase tick
        if time() >= (1/TPS) + self.last_tick:
            dt = 1
            self.meta['tick'] += SUN_TICK
            self.last_tick = time()
        else:
            dt = 0
        
        return dt