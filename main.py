from time import time

from nbinput import NonBlockingInput

import saves, ui, terrain


def get_pos_delta(char, slice_, y, blocks, jump):
    # Calculate change in x pos
    if char in 'aA':
        dx = -1
    elif char in 'dD':
        dx = 1
    else:
        dx = 0

    # Jumps if up pressed, block below, no block above
    if (char in 'wW' and y > 1
        and blocks[slice_[y+1]][1]
        and not blocks[slice_[y-1]][1]):

        dy = -1
        jump = 5
    else:
        dy = 0

    return dx, dy, jump


def main():

    blocks = terrain.gen_blocks()

    # Menu loop
    while True:
        meta, map_, save = ui.main()

        x = meta['center']
        y = meta['height'] - meta['ground_height'] - 1
        width = 40
        FPS = 20
        TPS = 10

        old_edges = None
        redraw = False
        last_out = time()
        last_tick = time()
        last_inp = time()
        tick = 0
        inp = None
        jump = 0

        # Game loop
        game = True
        with NonBlockingInput() as nbi:
            while game:

                # Finds display boundaries
                edges = (x - int(width / 2), x + int(width / 2))

                # Generates new terrain
                slices = {}
                slice_list = terrain.detect_edges(map_, edges)
                for pos in slice_list:
                    slices[str(pos)] = terrain.gen_slice(pos, meta)
                    map_[str(pos)] = slices[str(pos)]
                    redraw = True

                # Save new terrain to file
                if slices:
                    saves.save_map(save, slices)

                # Moving view
                if not edges == old_edges:
                    redraw = True
                    old_edges = edges
                    view = terrain.move_map(map_, edges)

                # Draw view
                if redraw and time() >= 1/FPS + last_out:
                    redraw = False
                    last_out = time()
                    terrain.render_map(view, int(width / 2), y, blocks)

                # Increase tick
                if time() >= (1/TPS) + last_tick:
                    dt = 1
                    tick += dt
                    last_tick = time()
                else:
                    dt = 0

                # Player falls when no block below it
                if dt and not blocks[map_[str(x)][y+1]][1]:
                    if jump > 0:
                        jump -= 1
                    else:
                        y += 1
                        redraw = True

                # Take inputs and change pos accordingly
                char = str(nbi.char())

                inp = char if char in 'wWaAdD' else None

                if time() >= (1/TPS) + last_inp:
                    if inp:
                        dx, dy, jump = get_pos_delta(
                            str(inp), map_[str(x)], y, blocks, jump
                        )
                        y += dy
                        x += dx
                        if dy or dx:
                            redraw = True
                        last_inp = time()
                        inp = None

                # Pause game
                if char == ' ':
                    redraw = True
                    if ui.pause() == 'exit':
                        game = False


if __name__ == '__main__':
    main()
