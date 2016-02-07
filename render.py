from math import cos, sin, sqrt, modf, radians

from colours import *
from console import *

import data


world_gen = data.world_gen

sun_y = world_gen['height'] - world_gen['ground_height']
max_light = max(map(lambda b: b.get('light_radius', 0), data.blocks.values()))


def in_circle(test_x, test_y, x, y, r):
    return circle_dist(test_x, test_y, x, y, r) < 1


def circle_dist(test_x, test_y, x, y, r):
    return ( ( ((test_x - x) ** 2) /  r    ** 2) +
             ( ((test_y - y) ** 2) / (r/2) ** 2) )


lit = lambda x, y, p: min(circle_dist(x, y, p['x'], p['y'], p['radius']), 1)


def render_map(map_, objects, bk_objects, sky_colour, lights, last_frame, fancy_lights):
    """
        Prints out a frame of the game.

        Takes:
        - map_: a 2D list of blocks.
        - objects: a list of dictionaries:
            {'x': int, 'y': int, 'char': block}
        - blocks: the main dictionary describing the blocks in the game.
        - sun: (x, y) position of the sun.
        - lights: a list of light sources:
            {'x': int, 'y': int, 'radius': int}
        - time: the game time.
    """

    # Sorts the dict as a list by pos
    map_ = list(map_.items())
    map_.sort(key=lambda item: int(item[0]))

    # map_ = [[0, '##  '],
    #         [1, '### '],
    #         [2, '##  ']]

    # Separates the pos and data
    world_positions, map_ = tuple(zip(*map_))

    # Orientates the data
    map_ = zip(*map_)

    diff = ''
    this_frame = []

    for y, row in enumerate(map_):
        this_frame.append([])

        for x, pixel in enumerate(row):

            pixel_out = calc_pixel(x, y, pixel, objects, bk_objects, sky_colour, lights, fancy_lights)

            if DEBUG and y == 1 and world_positions[x] % world_gen['chunk_size'] == 0:
                pixel_out = colour_str('*', bg=RED, fg=YELLOW)

            this_frame[-1].append(pixel_out)

            try:
                if not last_frame[y][x] == pixel_out:
                    # Changed
                    diff += POS_STR(x, y, pixel_out)
            except IndexError:
                # Doesn't exist
                diff += POS_STR(x, y, pixel_out)

    return diff, this_frame


def obj_pixel(x, y, objects):

    for object_ in objects:
        if object_['x'] == x and object_['y'] == y:

            # Objects can override their block colour
            colour = object_.get('colour', blocks[object_['char']]['colours']['fg'])

            return object_['char'], colour

    return None, None


def calc_pixel(x, y, pixel_f, objects, bk_objects, sky_colour, lights, fancy_lights):

    # If the front block has a bg
    if blocks[pixel_f]['colours']['bg'] is not None:
        bg = blocks[pixel_f]['colours']['bg']
    else:
        bg = sky(x, y, bk_objects, sky_colour, lights, fancy_lights)

    # Get any object
    object_char, obj_colour = obj_pixel(x, y, objects)

    if object_char:
        char = object_char
        fg = obj_colour
    else:
        char = blocks[pixel_f]['char']
        fg = blocks[pixel_f]['colours']['fg']

    fg_colour = rgb(*fg) if fg is not None else None
    bg_colour = rgb(*bg) if bg is not None else None

    return colour_str(
        char,
        bg = bg_colour,
        fg = fg_colour,
        style = blocks[pixel_f]['colours']['style']
    )


def bk_objects(time, width, fancy_lights):
    """ Returns objects for rendering to the background """

    objects = []

    sun_r = width / 2
    time = radians(time/32)
    day = cos(time) > 0

    # Set i to +1 for night and -1 for day
    i = -2 * day + 1
    x = int(sun_r * i * sin(time) + sun_r + 1)
    y = int(sun_r * i * cos(time) + sun_y)

    # Sun/moon
    obj = {
        'x': x,
        'y': y,
        'width': 2,
        'height': 1,
        'colour': world_gen['sun_colour'] if day else world_gen['moon_colour']
    }

    if fancy_lights:
        shade = (cos(time) + 1) / 2

        sky_colour = lerp_n(rgb_to_hsv(world_gen['night_colour']), shade, rgb_to_hsv(world_gen['day_colour']))

        if day:
            light_colour = world_gen['sun_light_colour']
        else:
            light_colour = world_gen['moon_light_colour']

        obj['light_colour'] = light_colour
        obj['light_radius'] = world_gen['sun_light_radius'] * abs(cos(time))
    else:

        if day:
            sky_colour = CYAN
        else:
            sky_colour = BLUE

    objects.append(obj)

    return objects, sky_colour


def get_light_colour(x, y, lights, colour_behind, fancy_lights):
    if fancy_lights:

        # Get all lights which affect this pixel
        pixel_lights = filter(lambda l: l[1] < 1, map(lambda l: (l['colour'], lit(x, y, l)), lights))

        # Calculate light level for each light source
        light_levels = [hsv_to_rgb(lerp_n(rgb_to_hsv(l[0]), l[1], colour_behind)) for l in pixel_lights]

        # Get brightest light
        if light_levels:
            light = max(map(lambda l: round_to_palette(*l), light_levels), key=lightness)
        else:
            light = hsv_to_rgb(colour_behind)

    else:

        if any(map(lambda l: lit(x, y, l) < 1, lights)):
            light = CYAN
        else:
            light = colour_behind

    return light


def sky(x, y, bk_objects, sky_colour, lights, fancy_lights):
    """ Returns the sky colour. """

    for obj in bk_objects:
        if obj['x'] in range(x, x+obj['width']) and obj['y'] in range(y, y+obj['height']):
            return obj['colour']

    return get_light_colour(x, y, lights, sky_colour, fancy_lights)


def lerp(a, s, b):
  return a * (1 - s) + (b * s)


def lerp_n(a, s, b):
    return tuple(lerp(a[i], s, b[i]) for i in range(min(len(a), len(b))))


def rgb_to_hsv(colour):
    r, g, b = colour

    min_c = min(*colour)
    max_c = max(*colour)
    v = max_c

    delta = max_c - min_c

    if not max_c == 0:
        s = delta / max_c

        if delta == 0:
            h = 0
        elif r == max_c:
            # Between yellow & magenta
            h = (g - b) / delta
        elif g == max_c:
            # Between cyan & yellow
            h = 2 + (b - r) / delta
        else:
            # Between magenta & cyan
            h = 4 + (r - g) / delta

        h *= 60

        if h < 0:
            h += 360

    else:
        s = 0
        h = -1

    return h, s, v


def hsv_to_rgb(colour):
    h, s, v = colour

    if s == 0:
        # Grey
        return (v, v, v)

    # Sector 0 to 5
    h /= 60

    i = int(h)

    # Factorial part of h
    f = h - i

    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    return {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q)
    }[i]


def get_lights(_map, start_x, bk_objects):
    # Give background objects light
    lights = list(map(lambda obj: {
        'radius': obj['light_radius'],
        'x': obj['x'],
        'y': obj['y'],
        'colour': obj['light_colour']
    }, filter(lambda obj: obj.get('light_radius'), bk_objects)))

    # Give blocks light
    for x, slice_ in _map.items():
        # Get the lights and their y positions in this slice
        slice_lights = filter(lambda pixel: blocks[pixel[1]].get('light_radius'),
            zip(range(len(slice_)), slice_)) # [(0, ' '), (1, '~'), ...]

        # Convert light pixels to light objects
        lights.extend(map(
            lambda pixel: {
                'radius': blocks[pixel[1]]['light_radius'],
                'x': x-start_x,
                'y': pixel[0],
                'colour': blocks[pixel[1]].get('light_colour', (1,1,1))
            },
            slice_lights
        ))

    return lights


def render_grid(title, selected, grid, max_height, sel=None):
    h, v, tl, t, tr, l, m, r, bl, b, br = \
        supported_chars('─│╭┬╮├┼┤╰┴╯', '─│┌┬┐├┼┤└┴┘', '-|+++++++++')

    max_height = int((max_height-2) / 2) # -2 for title, bottom

    # Figure out offset
    if sel:
        bottom_pad = 2

        offset = sel - max(
            min(sel, max_height - bottom_pad - 1), # Beginning and middle
            sel + min(0, max_height - len(grid)) # End positions
        )
    else:
        offset = 0

    # Find maximum length of the num column.
    max_n_w = len(str(max(map(lambda s: s['num'], grid)))) if len(grid) else 1

    # Figure out number of trailing spaces to make the grid same width as the title.
    #     |   block    |         num          |
    top = tl + (h*3) + t + (h*(max_n_w+2)) + tr
    max_w = max(len(top), len(title))
    trailing = ' ' * (max_w - len(top))

    out = []
    out.append(bold(title, selected) + ' ' * (max_w - len(title)))
    out.append(top + trailing)

    for c, slot in enumerate(grid[offset:offset+max_height]):
        i = c + offset

        block_char = blocks[slot['block']]['char']
        num = slot['num']

        colour = blocks[slot['block']]['colours']
        block_char = colour_str(
            block_char,
            fg=rgb(*colour['fg']) if colour['fg'] is not None else None,
            bg=rgb(*colour['bg']) if colour['bg'] is not None else None,
            style=colour['style']
        )

        # Have to do the padding before colour because the colour
        #   messes with the char count. (The block will always be 1 char wide.)
        num = '{:{max}}'.format(num, max=max_n_w)

        out.append('{v} {b} {v} {n} {v}{trail}'.format(
            b=block_char,
            n=colour_str(num, bg=rgb(*RED)) if selected and i == sel else num,
            v=v,
            trail=trailing
        ))

        if not (c == max_height - 1 or i == len(grid) - 1):
            out.append(l + (h*3) + m + (h*(max_n_w+2)) + r + trailing)

    out.append(bl + (h*3) + b + (h*(max_n_w+2)) + br + trailing)
    return out


def render_grids(grids, x, max_height):
    """
        Prints out the grids on the right side of the game.
    """

    # Sort out grids
    # Gets row from grid if it exists, else pads with ' '
    get_row = lambda g, y: g[y] if y < len(g) else ' ' * len(uncolour_str(g[0]))

    merged_grids = []
    for row in grids:
        for y in range(max(map(len, row))):
            merged_grids.append(' '.join(map(lambda g: get_row(g, y), row)))

    merged_grids.extend('' for _ in range(max_height - len(merged_grids)))

    return ''.join(
        POS_STR(x, y, ' ' + row + CLS_END_LN)
            for y, row in enumerate(merged_grids)
    )


def gen_blocks():
    blocks = data.blocks

    for key, block in blocks.items():
        # Get supported version of block char
        blocks[key]['char'] = supported_chars(*block['char'])

    return blocks


blocks = gen_blocks()
