# -*- coding: utf-8 -*-
#Copyright (c) 2010,11 Walter Bender
#Copyright (c) 2010, Tuukka Hastrup
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

BEAD_WIDTH = 40
BEAD_HEIGHT = 30
BEAD_OFFSET = 10
FRAME_STROKE_WIDTH = 45
FRAME_LAYER = 100
ROD_LAYER = 101
BEAD_LAYER = 102
BAR_LAYER = 103
DOT_LAYER = 104
MARK_LAYER = 105
MAX_FADE_LEVEL = 3
CURSOR = '█'

ROD_COLORS = ['#282828', '#A0A0A0', '#282828', '#A0A0A0', '#282828',
              '#A0A0A0', '#282828', '#A0A0A0', '#282828', '#A0A0A0',
              '#282828', '#A0A0A0', '#282828', '#A0A0A0', '#282828']
COLORS = ('#FFFFFF', '#FF0000', '#88FF00', '#FF00FF', '#FFFF00',
          '#00CC00', '#000000', '#AA6600', '#00CCFF', '#FF8800')
LABELS = ('#000000', '#FFFFFF', '#000000', '#FFFFFF', '#000000',
          '#000000', '#FFFFFF', '#FFFFFF', '#000000', '#000000')

import gi
from gi.repository import Gtk, Gdk, GdkPixbuf
from math import floor, ceil

import locale

import traceback
import logging
_logger = logging.getLogger('abacus-activity')

try:
    from sugar3.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except ImportError:
    GRID_CELL_SIZE = 0

from sprites import Sprites, Sprite


def dec2frac(d):
    ''' Convert float to its approximate fractional representation. '''

    '''
    This code was translated to Python from the answers at
    http://stackoverflow.com/questions/95727/how-to-convert-floats-to-human-\
readable-fractions/681534#681534

    For example:
    >>> 3./5
    0.59999999999999998

    >>> dec2frac(3./5)
    "3/5"

    '''

    if d > 1:
        return '%s' % d
    df = 1.0
    top = 1
    bot = 1

    while abs(df - d) > 0.00000001:
        if df < d:
            top += 1
        else:
            bot += 1
            top = int(d * bot)
        df = float(top) / bot

    if bot == 1:
        return '%s' % top
    elif top == 0:
        return ''
    return '%s/%s' % (top, bot)

#
# Utilities for generating artwork as SVG
#


def _svg_str_to_pixbuf(svg_string):
    ''' Load pixbuf from SVG string '''
    pl = GdkPixbuf.PixbufLoader.new_with_type('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf


def _svg_circle(r, cx, cy, fill, stroke):
    ''' Returns an SVG circle '''
    svg_string = '       <circle\n'
    svg_string += '          r="%f"\n' % (r)
    svg_string += '          cx="%f"\n' % (cx)
    svg_string += '          cy="%f"\n' % (cy)
    svg_string += _svg_style('fill:%s;stroke:%s;' % (fill, stroke))
    return svg_string


def _svg_rect(w, h, rx, ry, x, y, fill, stroke):
    ''' Returns an SVG rectangle '''
    svg_string = '       <rect\n'
    svg_string += '          width="%f"\n' % (w)
    svg_string += '          height="%f"\n' % (h)
    svg_string += '          rx="%f"\n' % (rx)
    svg_string += '          ry="%f"\n' % (ry)
    svg_string += '          x="%f"\n' % (x)
    svg_string += '          y="%f"\n' % (y)
    svg_string += _svg_style('fill:%s;stroke:%s;' % (fill, stroke))
    return svg_string


def _svg_indicator():
    ''' Returns a wedge-shaped indicator as SVG '''
    svg_string = '%s %s' % ('<path d="m1.5 1.5 L 18.5 1.5 L 10 13.5 L 1.5',
                            '1.5 z"\n')
    svg_string += _svg_style('fill:#ff0000;stroke:#ff0000;stroke-width:3.0;')
    return svg_string


def _svg_bead(fill, stroke, stretch=1.0):
    ''' Returns a bead-shaped SVG object; scale is used to elongate '''
    h = 15 + 30 * (stretch - 1.0)
    h2 = 30 * stretch - 1.5
    svg_string = '<path d="m 1.5 15 A 15 13.5 90 0 1 15 1.5 L 25 1.5 A 15 \
13.5 90 0 1 38.5 15 L 38.5 %f A 15 13.5 90 0 1 25 %f L 15 %f A 15 13.5 90 0 \
1 1.5 %f L 1.5 15 z"\n' % (h, h2, h2, h)
    svg_string += _svg_style('fill:%s;stroke:%s;stroke-width:1.5' % \
                             (fill, stroke))
    return svg_string


def _svg_header(w, h, scale, stretch=1.0):
    ''' Returns SVG header; some beads are elongated (stretch) '''
    svg_string = '<?xml version="1.0" encoding="UTF-8"'
    svg_string += ' standalone="no"?>\n'
    svg_string += '<!-- Created with Python -->\n'
    svg_string += '<svg\n'
    svg_string += '   xmlns:svg="http://www.w3.org/2000/svg"\n'
    svg_string += '   xmlns="http://www.w3.org/2000/svg"\n'
    svg_string += '   version="1.0"\n'
    svg_string += '%s%f%s' % ('   width="', w * scale, '"\n')
    svg_string += '%s%f%s' % ('   height="', h * scale * stretch, '">\n')
    svg_string += '%s%f%s%f%s' % ('<g\n       transform="matrix(',
                                  scale, ', 0, 0,', scale, ',0,0)">\n')
    return svg_string


def _svg_footer():
    ''' Returns SVG footer '''
    svg_string = '</g>\n'
    svg_string += '</svg>\n'
    return svg_string


def _svg_style(extras=''):
    ''' Returns SVG style for shape rendering '''
    return '%s%s%s' % ('style="', extras, '"/>\n')


def _calc_fade(bead_color, fade_color, i, n):
    ''' Fade from bead color to fade color '''
    r = i * float.fromhex('0x' + fade_color[1:3]) / n + \
        (n - i) * float.fromhex('0x' + bead_color[1:3]) / n
    g = i * float.fromhex('0x' + fade_color[3:5]) / n + \
        (n - i) * float.fromhex('0x' + bead_color[3:5]) / n
    b = i * float.fromhex('0x' + fade_color[5:]) / n + \
        (n - i) * float.fromhex('0x' + bead_color[5:]) / n
    return '#%02x%02x%02x' % (int(r), int(g), int(b))


class Bead():
    ''' The Bead class is used to define the individual beads. '''

    def __init__(self, sprite, offset, value, max_fade=MAX_FADE_LEVEL,
                 tristate=False):
        ''' We store a sprite, an offset, and a value for each bead. '''
        self.spr = sprite
        self.offset = offset
        # Decimals will be converted to fractions;
        # and we want to avoid decimal points in our whole numbers.
        if value < 1:
            self.value = value
        else:
            self.value = int(value)
        self.state = 0
        self.spr.type = 'bead'
        self.fade_level = 0  # Used for changing color.
        self.max_fade_level = max_fade
        self.tristate = tristate  # Beads can be +/- or off.

    def hide(self):
        ''' Hide the sprite associated with the bead. '''
        self.spr.hide()

    def show(self):
        ''' Show the sprite associated with the bead. '''
        self.spr.set_layer(BEAD_LAYER)

    def move(self, offset):
        ''' Generic move method: sets state and level. '''
        self.spr.move_relative((0, offset))
        if not self.tristate:
            self.state = 1 - self.state
        elif self.state == 1:  # moving bead back to center
            self.state = 0
        elif self.state == -1:  # moving bead back to center
            self.state = 0
        else:  # bead is in the center
            if offset > 0:  # moving bead down to bottom
                self.state = -1
            else:  # moving bead up to top
                self.state = 1
        self.set_fade_level(self.max_fade_level)
        self.update_label()

    def move_up(self):
        ''' Move a bead up as far as it will go. '''
        self.move(-self.offset)

    def move_down(self):
        ''' Move a bead down as far as it will go. '''
        self.move(self.offset)

    def get_value(self):
        ''' Return a value based upon bead state. '''
        return self.state * self.value

    def get_state(self):
        ''' Is the bead active? '''
        return self.state

    def set_color(self, color):
        ''' Set the color of the bead. '''
        self.spr.set_image(color)
        self.spr.inval()
        self.show()

    def set_label_color(self, color):
        ''' Set the label color for a bead (default is black). '''
        self.spr.set_label_color(color)

    def get_fade_level(self):
        ''' Return color fade level of bead. '''
        return self.fade_level

    def set_fade_level(self, fade_level):
        ''' Set color fade level of bead. '''
        self.fade_level = fade_level

    def update_label(self):
        ''' Label active beads. '''
        value = self.get_value()
        if self.state == 1 and value < 10000 and value > 0.05:
            value = self.get_value()
            if value < 1:
                self.spr.set_label(dec2frac(value))
            else:
                self.spr.set_label(int(value))
        elif self.state == -1 and value > -10000 and value < -0.05:
            value = self.get_value()
            if value > -1:
                self.spr.set_label('–' + dec2frac(-value))
            else:
                self.spr.set_label(int(value))
        else:
            self.spr.set_label('')


class Rod():
    ''' The Rod class is used to define a rod to hold beads. '''

    def __init__(self, sprites, color, frame_height, i, x, y, scale,
                 cuisenaire=False, bead_color=None):
        ''' We store a sprite for each rod and allocate its beads. '''
        rod = _svg_header(10, frame_height - (FRAME_STROKE_WIDTH * 2),
                          scale) + \
              _svg_rect(10, frame_height - (FRAME_STROKE_WIDTH * 2),
                        0, 0, 0, 0, color, '#404040') + \
              _svg_footer()

        self.index = i
        self.scale = scale
        self.sprites = sprites
        self.spr = Sprite(sprites, x, y, _svg_str_to_pixbuf(rod))
        self.spr.type = 'frame'
        self.beads = []
        self.lozenge = False
        self.white_beads = []
        self.color_beads = []

        if cuisenaire:  # Bead size scaled to bead value
            bead_scale = 10.0 / (self.index + 1)
            self.lozenge = True
        else:
            bead_scale = 1.0

        for i in range(MAX_FADE_LEVEL + 1):
            if bead_color is None:
                fade = _calc_fade('#FFFFFF', '#FFFF00', i, MAX_FADE_LEVEL)
            else:
                fade = _calc_fade(bead_color, '#FFFFFF', i, MAX_FADE_LEVEL)
            self.white_beads.append(_svg_str_to_pixbuf(
                _svg_header(BEAD_WIDTH, BEAD_HEIGHT, self.scale,
                            stretch=bead_scale) + \
                _svg_bead(fade, '#000000', stretch=bead_scale) + \
                _svg_footer()))

        self.black_bead = _svg_str_to_pixbuf(
                _svg_header(BEAD_WIDTH, BEAD_HEIGHT, self.scale,
                            stretch=bead_scale) + \
                _svg_bead('#000000', '#000000', stretch=bead_scale) + \
                _svg_footer())

        for i in range(len(COLORS)):
            self.color_beads.append(_svg_str_to_pixbuf(
                _svg_header(BEAD_WIDTH, BEAD_HEIGHT, self.scale,
                            stretch=bead_scale) + \
                _svg_bead(COLORS[i], '#000000', stretch=bead_scale) + \
                _svg_footer()))

        bo = (BEAD_WIDTH - BEAD_OFFSET) * self.scale / 2
        ro = (BEAD_WIDTH + 5) * self.scale / 2
        self.label = Sprite(self.sprites, x - bo, y + self.spr.rect[3],
                            _svg_str_to_pixbuf(
                _svg_header(BEAD_WIDTH, BEAD_HEIGHT, self.scale,
                            stretch=1.0) + \
                _svg_rect(BEAD_WIDTH, BEAD_HEIGHT, 0, 0, 0, 0,
                          'none', 'none') + \
                _svg_footer()))
        self.label.type = 'frame'
        self.label.set_label_color('#FFFFFF')
        self.label.set_layer(MARK_LAYER)

    def allocate_beads(self, top_beads, bot_beads, top_factor,
                       bead_value, bot_size, color=False, middle_black=False,
                       all_black=False, tristate=False):
        ''' Beads get allocated per rod '''
        self.top_beads = top_beads  # number of beads above the bar
        self.bot_beads = bot_beads  # number of beads below the bar
        # number of beads that could fit might not match number of beads
        # (e.g., Schety)
        self.bot_size = bot_size
        # top bead value == bead value * top factor
        self.top_factor = top_factor
        self.fade = False

        x = self.spr.rect[0]
        y = self.spr.rect[1]
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.scale
        bo = (BEAD_WIDTH - BEAD_OFFSET) * self.scale / 4
        ro = (BEAD_WIDTH + 5) * self.scale / 2

        # how far this bead moves
        bead_displacement = 2 * BEAD_HEIGHT * self.scale

        if color:
            bead_color = self.color_beads[self.index]
        elif all_black:
            bead_color = self.black_bead
        elif middle_black:  # special patterning for Schety
            if bot_beads == self.bot_size:
                middle = [4, 5]
            else:
                middle = [1, 2]
        else:
            bead_color = self.white_beads[0]
            self.fade = True

        if self.fade:
            max_fade_level = MAX_FADE_LEVEL
        else:
            max_fade_level = 0

        for b in range(top_beads):
            self.beads.append(Bead(Sprite(
                self.sprites, x - ro + bo, y + b * BEAD_HEIGHT * self.scale,
                bead_color), bead_displacement,
                top_factor * bead_value, max_fade=max_fade_level))
        for b in range(bot_beads):
            displacement = bead_displacement
            if top_beads > 0:
                yy = y + (top_beads + 5 + b) * BEAD_HEIGHT * self.scale
            else:
                yy = y + (2 + b) * BEAD_HEIGHT * self.scale
            if all_black:
                bead_color = self.black_bead
            elif middle_black:
                if b in middle:
                    bead_color = self.black_bead
                else:
                    bead_color = self.white_beads[0]
            elif not color:
                bead_color = self.white_beads[0]
            # short row
            if not self.lozenge and (self.bot_beads < self.bot_size):
                offset = (self.bot_size - self.bot_beads) * BEAD_HEIGHT * \
                    self.scale
                yy += offset
                displacement += offset
            # center tristate beads vertically on the rod
            if tristate:
                if self.lozenge:
                    offset = BEAD_HEIGHT * self.scale
                else:
                    offset = (self.bot_size - self.bot_beads + 2) * \
                        BEAD_HEIGHT * self.scale / 2
                yy -= offset
                displacement -= offset
            self.beads.append(Bead(Sprite(self.sprites, x - ro + bo,
                                          yy, bead_color), displacement,
                                   bead_value, tristate=tristate,
                                   max_fade=max_fade_level))
            if bead_color == self.black_bead:
                self.beads[-1].set_label_color('#ffffff')
            # Lozenged-shaped beads need to be spaced out more
            if self.beads[-1].spr.rect[3] > BEAD_HEIGHT * self.scale:
                self.beads[-1].spr.move_relative((0, b * (
                    self.beads[-1].spr.rect[3] - (BEAD_HEIGHT * self.scale))))

        if color:
            for bead in self.beads:
                bead.set_label_color(LABELS[self.index])

    def hide(self):
        for bead in self.beads:
            bead.hide()
        self.spr.hide()
        self.label.hide()

    def show(self):
        for bead in self.beads:
            bead.show()
        self.spr.set_layer(ROD_LAYER)
        self.label.set_layer(MARK_LAYER)

    def get_max_value(self):
        ''' Returns maximum numeric value for this rod '''
        max = 0
        for bead in self.beads:
            max += bead.value
        return max

    def get_value(self):
        sum = 0
        for bead in self.beads:
            sum += bead.get_value()
        return sum

    def get_bead_count(self):
        ''' Returns number of active bottom-bead equivalents on this rod'''
        count = 0
        for i, bead in enumerate(self.beads):
            if bead.get_state() == 1:
                if i < self.top_beads:
                    count += self.top_factor
                else:
                    count += 1
            if bead.get_state() == -1:
                count -= 1
        return count

    def set_number(self, number):
        ''' Try to set a value equal to number; return any remainder '''
        count = 0
        for i, bead in enumerate(self.beads):
            if number >= bead.value:
                number -= bead.value
                if i < self.top_beads:
                    count += self.top_factor
                else:
                    count += 1
        self.set_value(count)
        return number

    def set_value(self, value):
        ''' Move beads to represent a numeric value '''
        if self.top_beads > 0:
            bot = value % self.top_factor
            top = (value - bot) / self.top_factor
        else:
            bot = value
            top = 0
        self.reset()
        # Set the top.
        for i in range(top):
            self.beads[self.top_beads - i - 1].move_down()
        # Set the bottom
        for i in range(bot):
            self.beads[self.top_beads + i].move_up()

        if value > 0:
            self.set_label(self.get_bead_count())
        else:
            self.label.set_label('')

    def reset(self):
        # Clear the top.
        for i in range(self.top_beads):
            if self.beads[i].get_state() == 1:
                self.beads[i].move_up()
        # Clear the bottom.
        for i in range(self.bot_beads):
            if self.beads[self.top_beads + i].get_state() == 1:
                self.beads[self.top_beads + i].move_down()
        # Fade beads
        for bead in self.beads:
            if bead.fade_level > 0:
                bead.fade_level = 0
                bead.set_color(self.white_beads[0])
        self.label.set_label('')

    def fade_colors(self):
        ''' Reduce the saturation level of every bead. '''
        if self.fade:
            for bead in self.beads:
                if bead.get_fade_level() > 0:
                    bead.set_color(self.white_beads[bead.get_fade_level() - 1])
                    bead.set_fade_level(bead.get_fade_level() - 1)

    def move_bead(self, sprite, dy):
        ''' Move a bead (or beads) up or down a rod. '''

        # Find the bead associated with the sprite.
        i = -1
        for bead in self.beads:
            if sprite == bead.spr:
                i = self.beads.index(bead)
                break
        if i == -1:
            # _logger.debug('bead not found')
            return False

        if i < self.top_beads:
            if dy > 0 and bead.get_state() == 0:
                if self.fade and bead.max_fade_level > 0:
                    bead.set_color(self.white_beads[3])
                bead.move_down()
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads - i):
                    if self.beads[i + ii].state == 0:
                        if self.fade and bead.max_fade_level > 0:
                            self.beads[i + ii].set_color(self.white_beads[3])
                        self.beads[i + ii].move_down()
            elif dy < 0 and bead.state == 1:
                if self.fade and bead.max_fade_level > 0:
                    bead.set_color(self.white_beads[3])
                bead.move_up()
                # Make sure beads above this bead are also moved.
                for ii in range(i + 1):
                    if self.beads[i - ii].state == 1:
                        if self.fade and bead.max_fade_level > 0:
                            self.beads[i - ii].set_color(self.white_beads[3])
                        self.beads[i - ii].move_up()
        else:
            if dy < 0 and bead.state == 0:
                if self.fade and bead.max_fade_level > 0:
                    bead.set_color(self.white_beads[3])
                bead.move_up()
                # Make sure beads above this bead are also moved.
                for ii in range(i - self.top_beads + 1):
                    if self.beads[i - ii].state == 0:
                        if self.fade and bead.max_fade_level > 0:
                            self.beads[i - ii].set_color(self.white_beads[3])
                        self.beads[i - ii].move_up()
            elif dy < 0 and bead.state == -1:
                if self.fade and bead.max_fade_level > 0:
                    bead.set_color(self.white_beads[3])
                bead.move_up()
                for ii in range(i - self.top_beads + 1):
                    if self.beads[i - ii].state == -1:
                        if self.fade and bead.max_fade_level > 0:
                            self.beads[i - ii].set_color(self.white_beads[3])
                        self.beads[i - ii].move_up()
            elif dy > 0 and bead.state == 1:
                if self.fade and bead.max_fade_level > 0:
                    bead.set_color(self.white_beads[3])
                bead.move_down()
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads + self.bot_beads - i):
                    if self.beads[i + ii].state == 1:
                        if self.fade and bead.max_fade_level > 0:
                            self.beads[i + ii].set_color(self.white_beads[3])
                        self.beads[i + ii].move_down()
            elif dy > 0 and bead.state == 0 and bead.tristate:
                if self.fade and bead.max_fade_level > 0:
                    bead.set_color(self.white_beads[3])
                bead.move_down()
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads + self.bot_beads - i):
                    if self.beads[i + ii].state == 0:
                        if self.fade and bead.max_fade_level > 0:
                            self.beads[i + ii].set_color(self.white_beads[3])
                        self.beads[i + ii].move_down()

        self.set_label(self.get_bead_count())

    def set_label(self, n):
        ''' Different abaci use different labeling schemes. '''
        # Use hex notation on hex abacus
        if self.top_beads == 1 and self.bot_beads == 7 and \
                self.top_factor == 8:
            self.label.set_label('%x' % n)
        # Only show 0 on binary abacus
        elif n == 0 and not (self.top_beads == 0 and self.bot_beads == 1):
            self.label.set_label('')
        else:
            self.label.set_label(n)
        return True


class Abacus():
    ''' The Abacus class is used to define the user interaction. '''

    def __init__(self, canvas, parent=None):
        ''' Initialize the canvas and set up the callbacks. '''
        self.activity = parent

        if parent is None:        # Starting from command line
            self.sugar = False
            self.canvas = canvas
            self.bead_colors = ['#FFFFFF', '#FFFFFF']
        else:                     # Starting from Sugar
            self.sugar = True
            self.canvas = canvas
            self.bead_colors = parent.bead_colors
            parent.show_all()

        _logger.debug('bead colors %s %s', self.bead_colors[0],
                      self.bead_colors[1])
        self.canvas.set_can_focus(True)
        self.canvas.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.canvas.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.canvas.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.canvas.connect('draw', self.__draw_cb)
        self.canvas.connect('button-press-event', self._button_press_cb)
        self.canvas.connect('button-release-event', self._button_release_cb)
        self.canvas.connect('motion-notify-event', self._mouse_move_cb)
        self.canvas.connect('key_press_event', self._keypress_cb)
        self.width = Gdk.Screen.width()
        self.height = Gdk.Screen.height() - GRID_CELL_SIZE
        self.sprites = Sprites(self.canvas)
        self.scale = 1.33 * Gdk.Screen.height() / 900.0
        self.dragpos = 0
        self.press = None
        self.last = None

        locale.setlocale(locale.LC_NUMERIC, '')
        self.decimal_point = locale.localeconv()['decimal_point']
        if self.decimal_point == '' or self.decimal_point is None:
            self.decimal_point = '.'

        background_svg = _svg_header(self.width, self.height, 1.0) + \
            _svg_rect(self.width, self.height, 0, 0, 0, 0, '#FFFFFF',
                      '#FFFFFF') + \
            _svg_footer()
        background = Sprite(self.sprites, 0, 0,
                            _svg_str_to_pixbuf(background_svg))
        background.set_layer(1)

        self.japanese = None
        self.russian = None
        self.mayan = None
        self.binary = None
        self.hex = None
        self.decimal = None
        self.fraction = None
        self.caacupe = None
        self.cuisenaire = None
        self.custom = None

        self.chinese = Suanpan(self, self.bead_colors)
        self.mode = self.chinese
        self.mode.show()

    def select_abacus(self, abacus):
        self.mode.hide()
        value = int(float(self.mode.value()))
        if abacus == 'chinese':
            if self.chinese is None:
                self.chinese = Suanpan(self, self.bead_colors)
            self.mode = self.chinese
        elif abacus == 'japanese':
            if self.japanese is None:
                self.japanese = Soroban(self, self.bead_colors)
            self.mode = self.japanese
        elif abacus == 'decimal':
            if self.decimal is None:
                self.decimal = Decimal(self, self.bead_colors)
            self.mode = self.decimal
        elif abacus == 'mayan':
            if self.mayan is None:
                self.mayan = Nepohualtzintzin(self, self.bead_colors)
            self.mode = self.mayan
        elif abacus == 'hex':
            if self.hex is None:
                self.hex = Hex(self, self.bead_colors)
            self.mode = self.hex
        elif abacus == 'binary':
            if self.binary is None:
                self.binary = Binary(self, self.bead_colors)
            self.mode = self.binary
        elif abacus == 'custom':
            if self.custom is None:
                self.custom = Custom(self, self.bead_colors)
            self.mode = self.custom
        elif abacus == 'russian':
            if self.russian is None:
                self.russian = Schety(self, self.bead_colors)
            self.mode = self.russian
        elif abacus == 'fraction':
            if self.fraction is None:
                self.fraction = Fractions(self, self.bead_colors)
            self.mode = self.fraction
        elif abacus == 'caacupe':
            if self.caacupe is None:
                self.caacupe = Caacupe(self, self.bead_colors)
            self.mode = self.caacupe
        elif abacus == 'cuisenaire':
            if self.cuisenaire is None:
                self.cuisenaire = Cuisenaire(self)
            self.mode = self.cuisenaire
        self.mode.set_value_from_number(value)
        self.mode.show()
        self.mode.label(self.generate_label())
        _logger.debug('Setting mode to %s' % (self.mode.name))

    def _button_press_cb(self, win, event):
        ''' Callback to handle the button presses '''
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.press = self.sprites.find_sprite((x, y))
        self.last = self.press
        if self.press is not None:
            if self.press.type == 'bead':
                self.dragpos = y
            elif self.press.type == 'mark':
                self.dragpos = x
            elif self.press == self.mode.label_bar:
                self.mode.label(self.generate_label(sum_only=True) + CURSOR)
                number = self.press.labels[0].replace(CURSOR, '')
                if '/' in number:  # need to convert to decimal form
                    try:
                        userdefined = {}
                        exec 'def f(): return ' + number.replace(' ', '+') + \
                            '.' in globals(), userdefined
                        value = userdefined.values()[0]()
                        number = str(value)
                        self.press.set_label(
                            number.replace('.', self.decimal_point) + CURSOR)
                    except:
                        traceback.print_exc()
                        number = ''
                self.press = None
            else:
                self.press = None
        return True

    def _mouse_move_cb(self, win, event):
        ''' Callback to handle the mouse moves '''
        if self.press is None:
            self.dragpos = 0
            return True
        win.grab_focus()
        x, y = map(int, event.get_coords())
        if self.press.type == 'mark':
            mx, my = self.mode.mark.get_xy()
            self.mode.move_mark(x - mx)
        return True

    def _button_release_cb(self, win, event):
        ''' Callback to handle the button releases '''
        if self.press is None:
            self.dragpos = 0
            return True
        win.grab_focus()
        x, y = map(int, event.get_coords())
        if self.press.type == 'bead':
            self.mode.move_bead(self.press, y - self.dragpos)
        self.press = None
        self.mode.label(self.generate_label())
        return True

    def _keypress_cb(self, area, event):
        ''' Keypress: moving the slides with the arrow keys '''
        k = Gdk.keyval_name(event.keyval)
        if k in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'period',
                 'minus', 'Return', 'BackSpace', 'comma']:
            if self.last == self.mode.label_bar:
                self._process_numeric_input(self.last, k)
        elif k == 'r':
            self.mode.reset_abacus()
        return True

    def _process_numeric_input(self, sprite, keyname):
        ''' Make sure numeric input is valid. '''
        oldnum = sprite.labels[0].replace(CURSOR, '')
        newnum = oldnum
        if len(oldnum) == 0:
            oldnum = '0'
        if keyname == 'minus':
            if oldnum == '0':
                newnum = '-'
            elif oldnum[0] != '-':
                newnum = '-' + oldnum
            else:
                newnum = oldnum
        elif keyname == 'comma' and self.decimal_point == ',' and \
                ',' not in oldnum:
            newnum = oldnum + ','
        elif keyname == 'period' and self.decimal_point == '.' and \
                '.' not in oldnum:
            newnum = oldnum + '.'
        elif keyname == 'BackSpace':
            if len(oldnum) > 0:
                newnum = oldnum[:len(oldnum) - 1]
            else:
                newnum = ''
        elif keyname in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if oldnum == '0':
                newnum = keyname
            else:
                newnum = oldnum + keyname
        elif keyname == 'Return':
            self.mode.reset_abacus()
            self.mode.set_value_from_number(
                float(newnum.replace(self.decimal_point, '.')))
            self.mode.label(self.generate_label())
            return
        else:
            newnum = oldnum
        if newnum == '.':
            newnum = '0.'
        if len(newnum) > 0 and newnum != '-':
            try:
                float(newnum.replace(self.decimal_point, '.'))
            except ValueError, e:
                newnum = oldnum
        sprite.set_label(newnum + CURSOR)

    # Handle the expose-event by drawing
    def __draw_cb(self, canvas, cr):
        self.sprites.redraw_sprites(cr=cr)

    def _destroy_cb(self, win, event):
        ''' Callback to handle quit '''
        Gtk.main_quit()

    def generate_label(self, sum_only=False):
        ''' The complexity below is to make the label as simple as possible '''
        rod_sums = ''
        multiple_rods = False
        for x in self.mode.get_rod_values():
            if x > 0:
                if x > 0.005:
                    rod_value = dec2frac(x)
                else:
                    rod_value = str(x)
                if rod_sums == '':
                    rod_sums = rod_value
                else:
                    multiple_rods = True
                    rod_sums += ' + %s' % (rod_value)
            elif x < 0:
                if x < 0.005:
                    rod_value = dec2frac(-x)
                else:
                    rod_value = str(-x)
                if rod_sums == '':
                    rod_sums = '–%s' % (rod_value)
                else:
                    multiple_rods = True
                    rod_sums += ' – %s' % (rod_value)
        if rod_sums == '':
            return ''
        else:
            abacus_value = float(self.mode.value())
            if abacus_value == 0:
                value = '0'
            elif abacus_value > 0:
                whole = int(floor(abacus_value))
                fraction = abacus_value - whole
                if whole == 0:
                    if fraction > 0.005:
                        value = dec2frac(fraction)
                    else:
                        value = str(fraction)
                elif fraction == 0:
                    value = '%d' % (whole)
                else:
                    if fraction > 0.005:
                        value = '%d %s' % (whole, dec2frac(fraction))
                    else:
                        value = '%d %s' % (whole, str(fraction))
            else:
                whole = int(ceil(abacus_value))
                fraction = abacus_value - whole
                if whole == 0:
                    if fraction < 0.005:
                        value = '–%s' % (dec2frac(-fraction))
                    else:
                        value = '–%s' % (str(-fraction))
                elif fraction == 0:
                    value = '–%d' % (-whole)
                else:
                    if fraction < 0.005:
                        value = '–%d %s' % (-whole, dec2frac(-fraction))
                    else:
                        value = '–%d %s' % (-whole, str(-fraction))
            if value == '' or value == '–':
                value = '0'
            if multiple_rods and not sum_only:
                return rod_sums + ' = ' + value
            else:
                return value


class AbacusGeneric():
    ''' A generic abacus: a frame, rods, and beads. '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Define the physical paramters. '''
        self.name = 'suanpan'
        self.num_rods = 15
        self.bot_beads = 5
        self.top_beads = 2
        self.base = 10
        self.top_factor = 5

    def create(self, dots=False):
        ''' Create and position the sprites that compose the abacus '''
        # Width is a function of the number of rods
        self.frame_width = self.num_rods * (BEAD_WIDTH + BEAD_OFFSET) + \
            FRAME_STROKE_WIDTH * 2
        # Height is a function of the number of beads
        if self.top_beads > 0:
            self.frame_height = (self.bot_beads + self.top_beads + 5) * \
                BEAD_HEIGHT + FRAME_STROKE_WIDTH * 2
        else:
            self.frame_height = (self.bot_beads + 2) * BEAD_HEIGHT + \
                FRAME_STROKE_WIDTH * 2

        # Draw the frame...
        x = (self.abacus.width - (self.frame_width * self.abacus.scale)) / 2
        y = int(BEAD_HEIGHT * 1.5)
        frame = _svg_header(self.frame_width, self.frame_height,
                            self.abacus.scale) + \
                            _svg_rect(self.frame_width, self.frame_height,
                                      FRAME_STROKE_WIDTH / 2,
                                      FRAME_STROKE_WIDTH / 2, 0, 0,
                                      '#000000', '#000000') + \
                            _svg_rect(self.frame_width - \
                                          (FRAME_STROKE_WIDTH * 2),
                                      self.frame_height - \
                                          (FRAME_STROKE_WIDTH * 2), 0, 0,
                                      FRAME_STROKE_WIDTH, FRAME_STROKE_WIDTH,
                                      '#C0C0C0', '#000000') \
                                      + \
                            _svg_footer()
        self.frame = Sprite(self.abacus.sprites, x, y,
                            _svg_str_to_pixbuf(frame))
        self.frame.type = 'frame'

        # Some abaci (Soroban) use a dot to show the units position
        if dots:
            dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
            dotx = int(self.abacus.width / 2) - 5
            doty = [y + 5, y + self.frame.rect[3] - 15]
            self.dots = []
            white_dot = _svg_header(10, 10, self.abacus.scale) + \
                        _svg_circle(5, 5, 5, '#FFFFFF', '#000000') + \
                        _svg_footer()
            self.dots.append(Sprite(self.abacus.sprites,
                                    dotx, doty[0],
                                    _svg_str_to_pixbuf(white_dot)))
            self.dots.append(Sprite(self.abacus.sprites,
                                    dotx, doty[1],
                                    _svg_str_to_pixbuf(white_dot)))

            black_dot = _svg_header(10, 10, self.abacus.scale) + \
                        _svg_circle(5, 5, 5, '#282828', '#FFFFFF') + \
                        _svg_footer()
            for i in range(int(self.num_rods / 4 - 1)):  # mark 1000s
                if i % 2 == 0:
                    dot = black_dot
                else:
                    dot = white_dot
                self.dots.append(Sprite(self.abacus.sprites,
                                        dotx - 3 * (i + 1) * dx, doty[0],
                                        _svg_str_to_pixbuf(dot)))
                self.dots.append(Sprite(self.abacus.sprites,
                                        dotx + 3 * (i + 1) * dx, doty[0],
                                        _svg_str_to_pixbuf(dot)))
                self.dots.append(Sprite(self.abacus.sprites,
                                        dotx - 3 * (i + 1) * dx, doty[1],
                                        _svg_str_to_pixbuf(dot)))
                self.dots.append(Sprite(self.abacus.sprites,
                                        dotx + 3 * (i + 1) * dx, doty[1],
                                        _svg_str_to_pixbuf(dot)))
            for dot in self.dots:
                dot.set_layer(DOT_LAYER)
                dot.type = 'frame'

        # Draw the label bar
        label = _svg_header(self.frame_width, BEAD_HEIGHT,
                            self.abacus.scale) + \
                _svg_rect(self.frame_width, BEAD_HEIGHT, 0, 0, 0, 0,
                          'none', 'none') + \
                _svg_footer()
        self.label_bar = Sprite(self.abacus.sprites, x, 0,
                                _svg_str_to_pixbuf(label))
        self.label_bar.type = 'frame'
        self.label_bar.set_label_attributes(12, rescale=False)
        self.label_bar.set_label_color('black')

        # and then the rods and beads.
        x += FRAME_STROKE_WIDTH * self.abacus.scale
        y += FRAME_STROKE_WIDTH * self.abacus.scale

        self.rods = []
        self.beads = []

        self.draw_rods_and_beads(x, y)

        # Draw the dividing bar...
        bar = _svg_header(self.frame_width - (FRAME_STROKE_WIDTH * 2),
                          BEAD_HEIGHT, self.abacus.scale) + \
              _svg_rect(self.frame_width - (FRAME_STROKE_WIDTH * 2),
                        BEAD_HEIGHT, 0, 0, 0, 0, '#000000', '#000000') + \
              _svg_footer()
        if self.top_beads > 0:
            self.bar = Sprite(self.abacus.sprites, x,
                              y + (self.top_beads + 2) * BEAD_HEIGHT * \
                                  self.abacus.scale,
                              _svg_str_to_pixbuf(bar))
        else:
            self.bar = Sprite(self.abacus.sprites, x,
                              y - FRAME_STROKE_WIDTH * self.abacus.scale,
                              _svg_str_to_pixbuf(bar))
        self.bar.type = 'frame'

        # and finally, the mark.
        mark = _svg_header(20, 15, self.abacus.scale) + \
               _svg_indicator() + \
               _svg_footer()
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        self.mark = Sprite(self.abacus.sprites, x + (self.num_rods - 1) * dx,
                           y - (FRAME_STROKE_WIDTH / 2) * self.abacus.scale,
                           _svg_str_to_pixbuf(mark))
        self.mark.type = 'mark'

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads '''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            bead_value = pow(self.base, self.num_rods - i - 1)
            self.rods.append(Rod(self.abacus.sprites,
                                 ROD_COLORS[i % len(ROD_COLORS)],
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 bead_color=bead_color))
            self.rods[-1].allocate_beads(self.top_beads, self.bot_beads,
                                         self.top_factor,
                                         bead_value, self.bot_beads)

    def hide(self):
        ''' Hide the rod, beads, mark, and frame. '''
        for rod in self.rods:
            rod.hide()
        self.bar.hide()
        self.label_bar.hide()
        self.frame.hide()
        self.mark.hide()
        if hasattr(self, 'dots'):
            for dot in self.dots:
                dot.hide()

    def show(self):
        ''' Show the rod, beads, mark, and frame. '''
        self.frame.set_layer(FRAME_LAYER)
        for rod in self.rods:
            rod.show()
        self.bar.set_layer(BAR_LAYER)
        self.label_bar.set_layer(BAR_LAYER)
        if hasattr(self, 'dots'):
            for dot in self.dots:
                dot.set_layer(DOT_LAYER)
        self.mark.set_layer(MARK_LAYER)

    def set_value(self, string):
        ''' Set abacus to value in string '''
        value = string.split()
        # Move the beads to correspond to column values.
        try:
            for i, rod in enumerate(self.rods):
                rod.set_value(int(value[i]))
        except IndexError:
            _logger.debug('bad saved string length %s (%d != 2 * %d)',
                          string, len(string), self.num_rods)
        except ValueError:
            _logger.debug('bad saved string type %s (%s)',
                          string, str(value[i]))

    def max_value(self):
        ''' Maximum value possible on abacus '''
        max = 0
        for rod in self.rods:
            max += rod.get_max_value()
        return max

    def set_value_from_number(self, number):
        ''' Set abacus to value in string '''
        self.reset_abacus()
        if number <= self.max_value():
            for rod in self.rods:
                number = rod.set_number(number)
                if number == 0:
                    break

    def reset_abacus(self):
        ''' Reset beads to original position '''
        for rod in self.rods:
            rod.reset()

    def value(self, count_beads=False):
        ''' Return a string representing the value of each rod. '''

        if count_beads:
            # Save the value associated with each rod as a 2-byte integer.
            string = ''
            value = []
            for r in range(self.num_rods + 1):  # +1 for overflow
                value.append(0)

            # Tally the values on each rod.
            for r, rod in enumerate(self.rods):
                value[r + 1] = rod.get_bead_count()

            # Save the value associated with each rod as a 2-byte integer.
            for j in value[1:]:
                string += '%2d ' % (j)
        else:
            rod_sum = 0
            for rod in self.rods:
                rod_sum += rod.get_value()
            string = str(rod_sum)
        return(string)

    def label(self, string):
        ''' Label with the string. (Used with self.value) '''
        self.label_bar.set_label(string)

    def move_mark(self, dx):
        ''' Move indicator horizontally across the top of the frame. '''
        self.mark.move_relative((dx, 0))

    def fade_colors(self):
        ''' Reduce the saturation level of every bead. '''
        for rod in self.rods:
            rod.fade_colors()

    def move_bead(self, sprite, dy):
        ''' Move a bead (or beads) up or down a rod. '''
        self.fade_colors()
        for rod in self.rods:
            if rod.move_bead(sprite, dy):
                break

    def get_rod_values(self):
        ''' Return the sum of the values per rod as an array '''
        v = [0] * (self.num_rods + 1)

        for r, rod in enumerate(self.rods):
            v[r + 1] = rod.get_value()
        return v[1:]


class Custom(AbacusGeneric):
    ''' A custom-made abacus '''

    def __init__(self, abacus, rods, top, bottom, factor, base,
                 bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.name = 'custom'
        self.num_rods = rods
        self.bot_beads = bottom
        self.top_beads = top
        self.base = base
        self.top_factor = factor
        self.create()


class Nepohualtzintzin(AbacusGeneric):
    ''' A Mayan abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Specify parameters that define the abacus '''
        self.name = 'nepohualtzintzin'
        self.num_rods = 13
        self.bot_beads = 4
        self.top_beads = 3
        self.base = 20
        self.top_factor = 5


class Suanpan(AbacusGeneric):
    ''' A Chinese abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Create a Chinese abacus: 15 by (5,2). '''
        self.name = 'suanpan'
        self.num_rods = 15
        self.bot_beads = 5
        self.top_beads = 2
        self.base = 10
        self.top_factor = 5


class Soroban(AbacusGeneric):
    ''' A Japanese abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create(dots=True)

    def set_parameters(self):
        ''' create a Japanese abacus: 15 by (4,1) '''
        self.name = 'soroban'
        self.num_rods = 15
        self.bot_beads = 4
        self.top_beads = 1
        self.base = 10
        self.top_factor = 5

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads: units offset to center'''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            bead_value = pow(self.base, int(self.num_rods / 2) - i)
            self.rods.append(Rod(self.abacus.sprites,
                                 ROD_COLORS[i % len(ROD_COLORS)],
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 bead_color=bead_color))
            self.rods[-1].allocate_beads(self.top_beads, self.bot_beads,
                                         self.top_factor,
                                         bead_value, self.bot_beads)


class Hex(AbacusGeneric):
    ''' A hexadecimal abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' create a hexadecimal abacus: 15 by (7,1) '''
        self.name = 'hexadecimal'
        self.num_rods = 15
        self.bot_beads = 7
        self.top_beads = 1
        self.base = 16
        self.top_factor = 8


class Decimal(AbacusGeneric):
    ''' A decimal abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' create a decimal abacus: 10 by (10,0) '''
        self.name = 'decimal'
        self.num_rods = 10
        self.bot_beads = 10
        self.top_beads = 0
        self.base = 10
        self.top_factor = 1

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads: override bead color'''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            bead_value = pow(self.base, self.num_rods - i - 1)
            self.rods.append(Rod(self.abacus.sprites, '#404040',
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 bead_color=bead_color))
            self.rods[-1].allocate_beads(self.top_beads, self.bot_beads,
                                         self.top_factor,
                                         bead_value, self.bot_beads,
                                         color=True)


class Binary(AbacusGeneric):
    ''' A binary abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' create a Binary abacus: 15 by (1,0) '''
        self.name = 'binary'
        self.num_rods = 15
        self.bot_beads = 1
        self.top_beads = 0
        self.base = 2
        self.top_factor = 1


class Schety(AbacusGeneric):
    ''' A Russian abacus '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Create a Russian abacus: 15 by 10 (with one rod of 4 beads). '''
        self.name = 'schety'
        self.top_beads = 0
        self.bot_beads = 10
        self.bead_count = (10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 4, 10, 10,
                           10, 10)
        self.bead_value = (10 ** 9, 10 ** 8, 10 ** 7, 10 ** 6, 10 ** 5,
                           10000, 1000, 100, 10, 1, .25, .1, .01, .001, .0001)
        self.num_rods = len(self.bead_count)
        self.base = 10
        self.top_factor = 1

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads: short column for 1/4 '''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            self.rods.append(Rod(self.abacus.sprites, '#404040',
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 bead_color=bead_color))
            self.rods[-1].allocate_beads(self.top_beads, self.bead_count[i],
                                         self.top_factor, self.bead_value[i],
                                         self.bead_count[0], middle_black=True)


class Fractions(Schety):
    ''' Inherit from Russian abacus. '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Create an abacus with fractions: 15 by 10 (with 1/2, 1/3. 1/4,
            1/5, 1/6, 1/8, 1/9, 1/10, 1/12). '''
        self.bead_count = (10, 10, 10, 10, 10, 10, 2, 3, 4, 5, 6, 8, 9, 10, 12)
        self.bead_value = (100000, 10000, 1000, 100, 10, 1, .5, 1 / 3., .25,
                           .2, 1 / 6., .125, 1 / 9., .1, 1 / 12.)
        self.name = 'fraction'
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 12
        self.base = 10
        self.top_factor = 1

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads: short column for 1/4 '''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            self.rods.append(Rod(self.abacus.sprites, '#404040',
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 bead_color=bead_color))
            if i < 6:
                all_black = False
            else:
                all_black = True
            self.rods[-1].allocate_beads(self.top_beads, self.bead_count[i],
                                         self.top_factor,
                                         self.bead_value[i],
                                         self.bead_count[-1],
                                         all_black=all_black)


class Caacupe(Fractions):
    ''' Inherit from Fraction abacus. '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Create an abacus with fractions: 15 by 10 (with 1/2, 1/3. 1/4,
            1/5, 1/6, 1/8, 1/9, 1/10, 1/12). '''
        self.bead_count = (10, 10, 10, 10, 10, 10, 2, 3, 4, 5, 6, 8, 9, 10, 12)
        self.bead_value = (100000, 10000, 1000, 100, 10, 1, .5, 1 / 3., .25,
                           .2, 1 / 6., .125, 1 / 9., .1, 1 / 12.)
        self.name = 'caacupe'
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 12
        self.base = 10
        self.top_factor = 1

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads: short column for 1/4 '''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            self.rods.append(Rod(self.abacus.sprites, '#404040',
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 bead_color=bead_color))
            if i < 6:
                all_black = False
            else:
                all_black = True
            self.rods[-1].allocate_beads(self.top_beads, self.bead_count[i],
                                         self.top_factor,
                                         self.bead_value[i],
                                         self.bead_count[-1],
                                         all_black=all_black, tristate=True)


class Cuisenaire(Caacupe):
    ''' Inherit from Caacupe abacus. '''

    def __init__(self, abacus, bead_colors=None):
        ''' Specify parameters that define the abacus '''
        self.abacus = abacus
        self.bead_colors = bead_colors
        self.set_parameters()
        self.create()

    def set_parameters(self):
        ''' Create an abacus with fractions: 10 by 10 (with 1/1, 1/2, 1/3. 1/4,
            1/5, 1/6, 1/7, 1/8, 1/9, 1/10). '''
        self.bead_count = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        self.bead_value = (1, .5, 1 / 3., .25,
                           .2, 1 / 6., 1 / 7., .125, 1 / 9., .1)
        self.name = 'cuisenaire'
        self.num_rods = 10
        self.top_beads = 0
        self.bot_beads = 10
        self.base = 10
        self.top_factor = 1

    def draw_rods_and_beads(self, x, y):
        ''' Draw the rods and beads: short column for 1/4 '''
        dx = (BEAD_WIDTH + BEAD_OFFSET) * self.abacus.scale
        ro = (BEAD_WIDTH + 5) * self.abacus.scale / 2
        for i in range(self.num_rods):
            if self.bead_colors is not None:
                bead_color = self.bead_colors[i % 2]
            else:
                bead_color = None
            self.rods.append(Rod(self.abacus.sprites, '#404040',
                                 self.frame_height,
                                 i, x + i * dx + ro, y, self.abacus.scale,
                                 cuisenaire=True, bead_color=bead_color))
            self.rods[-1].allocate_beads(self.top_beads, self.bead_count[i],
                                         self.top_factor,
                                         self.bead_value[i],
                                         self.bead_count[-1],
                                         color=True, tristate=True)
