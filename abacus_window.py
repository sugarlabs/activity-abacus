# -*- coding: utf-8 -*-
#Copyright (c) 2010, Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

BWIDTH = 40
BHEIGHT = 30
BOFFSET = 10
FSTROKE = 45
FRAME_LAYER = 100
ROD_LAYER = 101
BEAD_LAYER = 102
BAR_LAYER = 103
MARK_LAYER = 104

ROD_COLORS = ["#006ffe", "#007ee7", "#0082c4", "#0089ab", "#008c8b",
              "#008e68", "#008e4c", "#008900", "#5e7700", "#787000",
              "#876a00", "#986200", "#ab5600", "#d60000", "#e30038"]


import pygtk
pygtk.require('2.0')
import gtk
from math import pow
import logging
_logger = logging.getLogger("abacus-activity")

try:
    from sugar.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except:
    GRID_CELL_SIZE = 0

from sprites import Sprites, Sprite

#
# Utilities for generating artwork as SVG
#

def _svg_str_to_pixbuf(svg_string):
    """ Load pixbuf from SVG string """
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf

def _svg_rect(w, h, rx, ry, x, y, fill, stroke):
    """ Returns an SVG rectangle """
    svg_string = "       <rect\n"
    svg_string += "          width=\"%f\"\n" % (w)
    svg_string += "          height=\"%f\"\n" % (h)
    svg_string += "          rx=\"%f\"\n" % (rx)
    svg_string += "          ry=\"%f\"\n" % (ry)
    svg_string += "          x=\"%f\"\n" % (x)
    svg_string += "          y=\"%f\"\n" % (y)
    svg_string += _svg_style("fill:%s;stroke:%s;" % (fill, stroke))
    return svg_string

def _svg_indicator():
    """ Returns a wedge-shaped indicator as SVG """
    svg_string = "%s %s" % ("<path d=\"m1.5 1.5 L 18.5 1.5 L 10 13.5 L 1.5",
                            "1.5 z\"\n")
    svg_string += _svg_style("fill:#ff0000;stroke:#ff0000;stroke-width:3.0;")
    return svg_string

def _svg_bead(fill, stroke):
    """ Returns a bead-shaped SVG object """
    svg_string = "%s %s %s %s" % ("<path d=\"m1.5 15 A 15 13.5 90 0 1",
                                  "15 1.5 L 25 1.5 A 15 13.5 90 0 1 38.5",
                                  "15 A 15 13.5 90 0 1 25 28.5 L 15",
                                  "28.5 A 15 13.5 90 0 1 1.5 15 z\"\n")
    svg_string += _svg_style("fill:%s;stroke:%s;stroke-width:1.5" %\
                             (fill, stroke))
    return svg_string

def _svg_header(w, h, scale):
    """ Returns SVG header """
    svg_string = "<?xml version=\"1.0\" encoding=\"UTF-8\""
    svg_string += " standalone=\"no\"?>\n"
    svg_string += "<!-- Created with Python -->\n"
    svg_string += "<svg\n"
    svg_string += "   xmlns:svg=\"http://www.w3.org/2000/svg\"\n"
    svg_string += "   xmlns=\"http://www.w3.org/2000/svg\"\n"
    svg_string += "   version=\"1.0\"\n"
    svg_string += "%s%f%s" % ("   width=\"", w*scale, "\"\n")
    svg_string += "%s%f%s" % ("   height=\"", h*scale, "\">\n")
    svg_string += "%s%f%s%f%s" % ("<g\n       transform=\"matrix(", 
                                  scale, ",0,0,", scale,
                                  ",0,0)\">\n")
    return svg_string

def _svg_footer():
    """ Returns SVG footer """
    svg_string = "</g>\n"
    svg_string += "</svg>\n"
    return svg_string

def _svg_style(extras=""):
    """ Returns SVG style for shape rendering """
    return "%s%s%s" % ("style=\"", extras, "\"/>\n")

class Bead():
    """ The Bead class is used to define the individual beads. """

    def __init__(self, sprite, offset, value):
        """ We store an sprite, an offset, and a value for each bead """
        self.spr = sprite
        self.offset = offset
        if value < 1:
            self.value = value
        else:
            self.value = int(value)
        self.state = 0
        self.spr.type = 'bead'
        self.level = 0 # Used for changing color

    def hide(self):
        """ Hide the sprite associated with the bead """
        self.spr.hide()

    def show(self):
        """ Show the sprite associated with the bead """
        self.spr.set_layer(BEAD_LAYER)

    def move_up(self):
        """ Move a bead up as far as it will go, """
        self.spr.move_relative((0, -self.offset))
        self.state = 1-self.state
        self.set_level(3)

    def move_down(self):
        """ Move a bead down as far as it will go. """
        self.spr.move_relative((0, self.offset))
        self.state = 1-self.state
        self.set_level(3)

    def get_value(self):
        """ Return a value if bead state is 1 """
        if self.state == 1:
            return self.value
        else:
            return 0

    def get_state(self):
        """ Is the bead 'active' """
        return self.state

    def set_color(self, color):
        """ Set color of bead """
        self.spr.set_image(color)
        self.spr.inval()
        self.show()

    def get_level(self):
        """ Return color level of bead -- used for fade """
        return self.level

    def set_level(self, level):
        """ Set color level of bead -- used for fade """
        self.level = level

class Abacus():
    """ The Abacus class is used to define the user interaction. """

    def __init__(self, canvas, parent=None):
        """ Initialize the canvas and set up the callbacks. """
        self.activity = parent

        if parent is None:        # Starting from command line
            self.sugar = False
            self.canvas = canvas
        else:                     # Starting from Sugar
            self.sugar = True
            self.canvas = canvas
            parent.show_all()

        self.canvas.set_flags(gtk.CAN_FOCUS)
        self.canvas.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.canvas.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.canvas.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.canvas.connect("expose-event", self._expose_cb)
        self.canvas.connect("button-press-event", self._button_press_cb)
        self.canvas.connect("button-release-event", self._button_release_cb)
        self.canvas.connect("motion-notify-event", self._mouse_move_cb)
        self.width = gtk.gdk.screen_width()
        self.height = gtk.gdk.screen_height()-GRID_CELL_SIZE
        self.sprites = Sprites(self.canvas)
        self.scale = gtk.gdk.screen_height()/900.0
        self.dragpos = 0
        self.press = None

        self.chinese = Suanpan(self)
        self.japanese = Soroban(self)
        self.russian = Schety(self)
        self.mayan = Nepohualtzintzin(self)
        self.binary = Binary(self)
        self.hex = Hex(self)
        self.fraction = Fractions(self)
        self.custom = None

        self.chinese.show()
        self.japanese.hide()
        self.russian.hide()
        self.mayan.hide()
        self.binary.hide()
        self.hex.hide()
        self.fraction.hide()
        self.mode = self.chinese

    def _button_press_cb(self, win, event):
        """ Callback to handle the button presses """
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.press = self.sprites.find_sprite((x,y))
        if self.press is not None:
            if self.press.type == 'bead':
                self.dragpos = y
            elif self.press.type == 'mark':
                self.dragpos = x
            else:
                self.press = None
        return True

    def _mouse_move_cb(self, win, event):
        """ Callback to handle the mouse moves """
        if self.press is None:
            self.dragpos = 0
            return True
        win.grab_focus()
        x, y = map(int, event.get_coords())
        if self.press.type == 'bead':
            self.mode.move_bead(self.press, y-self.dragpos)
        elif self.press.type == 'mark':
            mx, my = self.mode.mark.get_xy()
            self.mode.move_mark(x-mx)

    def _button_release_cb(self, win, event):
        """ Callback to handle the button releases """
        if self.press == None:
            return True
        self.press = None
        self.mode.label(self.mode.value())
        return True

    def _expose_cb(self, win, event):
        """ Callback to handle window expose events """
        self.sprites.redraw_sprites()
        return True

    def _destroy_cb(self, win, event):
        """ Callback to handle quit """
        gtk.main_quit()


class AbacusGeneric():
    """ A generic abacus: a frame, rods, and beads. """

    def __init__(self, abacus):
        """ Specify parameters that define the abacus """
        self.abacus = abacus
        self.set_parameters()
        self.create()

    def set_parameters(self):
        """ Define the physical paramters. """
        self.name = "suanpan"
        self.num_rods = 15
        self.bot_beads = 5
        self.top_beads = 2
        self.base = 10
        self.top_factor = 5

    def create(self):
        """ Create and position the sprites that compose the abacus """

        # Width is a function of the number of rods
        self.frame_width = self.num_rods*(BWIDTH+BOFFSET)+FSTROKE*2

        # Height is a function of the number of beads
        if self.top_beads > 0:
            self.frame_height = (self.bot_beads+self.top_beads+5)*BHEIGHT +\
                                FSTROKE*2
        else:
            self.frame_height = (self.bot_beads+2)*BHEIGHT + FSTROKE*2

        # Draw the frame...
        x = (self.abacus.width-(self.frame_width*self.abacus.scale))/2
        y = (self.abacus.height-(self.frame_height*self.abacus.scale))/2
        _frame = _svg_header(self.frame_width, self.frame_height,
                             self.abacus.scale) +\
                 _svg_rect(self.frame_width, self.frame_height, 
                           FSTROKE/2, FSTROKE/2, 0, 0, "#000000", "#000000") +\
                 _svg_rect(self.frame_width-(FSTROKE*2), 
                           self.frame_height-(FSTROKE*2), 0, 0,
                           FSTROKE, FSTROKE, "#808080", "#000000") +\
                 _svg_footer()
        self.frame = Sprite(self.abacus.sprites, x, y, 
                            _svg_str_to_pixbuf(_frame))
        self.frame.type = 'frame'

        # and then the rods and beads.
        self.rods = []
        self.beads = []
        x += FSTROKE*self.abacus.scale
        y += FSTROKE*self.abacus.scale

        self.draw_rods_and_beads(x, y)

        # Draw the dividing bar...
        _bar = _svg_header(self.frame_width-(FSTROKE*2), BHEIGHT,
                           self.abacus.scale) +\
               _svg_rect(self.frame_width-(FSTROKE*2), BHEIGHT, 0, 0, 0, 0,
                         "#000000", "#000000") +\
               _svg_footer()
        if self.top_beads > 0:
            self.bar = Sprite(self.abacus.sprites, x,
                              y+(self.top_beads+2)*BHEIGHT*self.abacus.scale,
                              _svg_str_to_pixbuf(_bar))
        else:
            self.bar = Sprite(self.abacus.sprites, x,
                              y-FSTROKE*self.abacus.scale,
                              _svg_str_to_pixbuf(_bar))

        self.bar.type = 'frame'
        self.bar.set_label_color('white')

        # and finally, the mark.
        _mark = _svg_header(20, 15, self.abacus.scale) +\
                _svg_indicator() +\
                _svg_footer()
        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        self.mark = Sprite(self.abacus.sprites, x+(self.num_rods-1)*dx,
                           y-((FSTROKE/2)*self.abacus.scale),
                           _svg_str_to_pixbuf(_mark))
        self.mark.type = 'mark'

    def draw_rods_and_beads(self, x, y):
        """ Draw the rods and beads """
        _white = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#ffffff", "#000000") +\
                 _svg_footer()
        _yellow1 = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#ffffcc", "#000000") +\
                 _svg_footer()
        _yellow2 = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#ffff88", "#000000") +\
                 _svg_footer()
        _yellow3 = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#ffff00", "#000000") +\
                 _svg_footer()
        self.colors = [_svg_str_to_pixbuf(_white),
                       _svg_str_to_pixbuf(_yellow1),
                       _svg_str_to_pixbuf(_yellow2),
                       _svg_str_to_pixbuf(_yellow3)]

        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        bo =  (BWIDTH-BOFFSET)*self.abacus.scale/4
        ro =  (BWIDTH+5)*self.abacus.scale/2
        for i in range(self.num_rods):
            _rod = _svg_header(10, self.frame_height-(FSTROKE*2),
                               self.abacus.scale) +\
                   _svg_rect(10, self.frame_height-(FSTROKE*2), 0, 0, 0, 0,
                             ROD_COLORS[i%len(ROD_COLORS)], "#404040") +\
                   _svg_footer()
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+ro, y,
                                    _svg_str_to_pixbuf(_rod)))

            for b in range(self.top_beads):
                self.beads.append(Bead(Sprite(self.abacus.sprites, x+i*dx+bo,
                                              y+b*BHEIGHT*self.abacus.scale,
                                              self.colors[0]),
                                       2*BHEIGHT*self.abacus.scale,
                                       self.top_factor*(pow(self.base,
                                                        self.num_rods-i-1))))
            for b in range(self.bot_beads):
                if self.top_beads > 0:
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(self.top_beads+5+b)*\
                                                  BHEIGHT*self.abacus.scale,
                                                  self.colors[0]),
                                           2*BHEIGHT*self.abacus.scale,
                                           pow(self.base,self.num_rods-i-1)))
                else:
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(2+b)*BHEIGHT\
                                                  *self.abacus.scale,
                                                  self.colors[0]),
                                           2*BHEIGHT*self.abacus.scale,
                                           pow(self.base,self.num_rods-i-1)))

        for rod in self.rods:
            rod.type = "frame"

    def hide(self):
        """ Hide the rod, beads, mark, and frame. """
        for rod in self.rods:
            rod.hide()
        for bead in self.beads:
            bead.hide()
        self.bar.hide()
        self.frame.hide()
        self.mark.hide()

    def show(self):
        """ Show the rod, beads, mark, and frame. """
        self.frame.set_layer(FRAME_LAYER)
        for rod in self.rods:
            rod.set_layer(ROD_LAYER)
        for bead in self.beads:
            bead.show()
        self.bar.set_layer(BAR_LAYER)
        self.mark.set_layer(MARK_LAYER)

    def set_value(self, string):
        """ Set abacus to value in string """
        _logger.debug("restoring %s: %s" % (self.name, string))
        # String has two bytes per column.
        v = []
        for r in range(self.num_rods):
            v.append(0)

        # Convert string to column values.
        if len(string) == 2*self.num_rods:
            for i in range(self.num_rods):
                v[self.num_rods-i-1] = int(
                              string[2*self.num_rods-i*2-1:2*self.num_rods-i*2])
        else:
            _logger.debug("bad saved string %s (%d != 2*%d)" % (string,
                          len(string), self.num_rods))

        # Move the beads to correspond to column values.
        for r in range(self.num_rods):
            self.set_rod_value(r, v[r])

    def set_rod_value(self, r, v):
        """ Move beads on rod r to represent value v """
        bot = v % self.top_factor
        top = (v-bot)/self.top_factor
        top_bead_index = r*(self.top_beads+self.bot_beads)
        bot_bead_index = r*(self.top_beads+self.bot_beads)+self.top_beads

        # Clear the top.
        for i in range(self.top_beads):
            if self.beads[top_bead_index+i].get_state() == 1:
                self.beads[top_bead_index+i].move_up()
        # Clear the bottom.
        for i in range(self.bot_beads):
            if self.beads[bot_bead_index+i].get_state() == 1:
                self.beads[bot_bead_index+i].move_down()
        # Set the top.
        for i in range(top):
            self.beads[top_bead_index+self.top_beads-i-1].move_down()
        # Set the bottom
        for i in range(bot):
            self.beads[bot_bead_index+i].move_up()

    def value(self, count_beads=False):
        """ Return a string representing the value of each rod. """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, bead in enumerate(self.beads):
            r = i/(self.top_beads+self.bot_beads)
            j = i % (self.top_beads+self.bot_beads)
            if bead.get_state() == 1:
                if j < self.top_beads:
                    v[r+1] += self.top_factor
                else:
                    v[r+1] += 1

        if count_beads:
            # Save the value associated with each rod as a 2-byte integer.
            for j in v[1:]:
                string += "%2d" % (j)
        else:
            sum = 0
            for bead in self.beads:
                sum += bead.get_value()
            string = str(sum)

        return(string)

    def label(self, string):
        """ Label the crossbar with the string. (Used with self.value) """
        self.bar.set_label(string)

    def move_mark(self, dx):
        """ Move indicator horizontally across the top of the frame. """
        self.mark.move_relative((dx, 0))

    def fade_colors(self):
        """ Reduce the saturation level of every bead. """
        for bead in self.beads:
            if bead.get_level() > 0:
                bead.set_color(self.colors[bead.get_level()-1])
                bead.set_level(bead.get_level()-1)

    def move_bead(self, sprite, dy):
        """ Move a bead (or beads) up or down a rod. """

        # find the bead associated with the sprite
        i = -1
        for bead in self.beads:
            if sprite == bead.spr:
                i = self.beads.index(bead)
                break
        if i == -1:
            print "bead not found"
            return

        b = i % (self.top_beads+self.bot_beads)
        if b < self.top_beads:
            if dy > 0 and bead.get_state() == 0:
                self.fade_colors()
                bead.set_color(self.colors[3])
                bead.move_down()
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads-b):
                    if self.beads[i+ii].state == 0:
                        self.beads[i+ii].set_color(self.colors[3])
                        self.beads[i+ii].move_down()
            elif dy < 0 and bead.state == 1:
                self.fade_colors()
                bead.set_color(self.colors[3])
                bead.move_up()
                # Make sure beads above this bead are also moved.
                for ii in range(b+1):
                    if self.beads[i-ii].state == 1:
                        self.beads[i-ii].set_color(self.colors[3])
                        self.beads[i-ii].move_up()
        else:
            if dy < 0 and bead.state == 0:
                self.fade_colors()
                bead.set_color(self.colors[3])
                bead.move_up()
                # Make sure beads above this bead are also moved.
                for ii in range(b-self.top_beads+1):
                    if self.beads[i-ii].state == 0:
                        self.beads[i-ii].set_color(self.colors[3])
                        self.beads[i-ii].move_up()
            elif dy > 0 and bead.state == 1:
                self.fade_colors()
                bead.set_color(self.colors[3])
                bead.move_down()
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads+self.bot_beads-b):
                    if self.beads[i+ii].state == 1:
                        self.beads[i+ii].set_color(self.colors[3])
                        self.beads[i+ii].move_down()


class Custom(AbacusGeneric):
    """ A custom-made abacus """

    def __init__(self, abacus, rods, top, bottom, factor, base):
        """ Specify parameters that define the abacus """
        self.abacus = abacus
        self.name = 'custom'
        self.num_rods = rods
        self.bot_beads = bottom
        self.top_beads = top
        self.base = base
        self.top_factor = factor
        self.create()


class Nepohualtzintzin(AbacusGeneric):
    """ A Mayan abacus """

    def set_parameters(self):
        """ Specify parameters that define the abacus """
        self.name = 'nepohualtzintzin'
        self.num_rods = 13
        self.bot_beads = 4
        self.top_beads = 3
        self.base = 20
        self.top_factor = 5


class Suanpan(AbacusGeneric):
    """ A Chinese abacus """

    def set_parameters(self):
        """ Create a Chinese abacus: 15 by (5,2). """
        self.name = 'saunpan'
        self.num_rods = 15
        self.bot_beads = 5
        self.top_beads = 2
        self.base = 10
        self.top_factor = 5


class Soroban(AbacusGeneric):
    """ A Japanese abacus """

    def set_parameters(self):
        """ create a Japanese abacus: 15 by (4,1) """
        self.name = 'soroban'
        self.num_rods = 15
        self.bot_beads = 4
        self.top_beads = 1
        self.base = 10
        self.top_factor = 5


class Hex(AbacusGeneric):
    """ A hexadecimal abacus """

    def set_parameters(self):
        """ create a hexadecimal abacus: 15 by (7,1) """
        self.name = 'hexadecimal'
        self.num_rods = 15
        self.bot_beads = 7
        self.top_beads = 1
        self.base = 16
        self.top_factor = 8


class Binary(AbacusGeneric):
    """ A binary abacus """

    def set_parameters(self):
        """ create a Binary abacus: 15 by (1,0) """
        self.name = 'binary'
        self.num_rods = 15
        self.bot_beads = 1
        self.top_beads = 0
        self.base = 2
        self.top_factor = 1


class Schety(AbacusGeneric):
    """ A Russian abacus """

    def set_parameters(self):
        """ Create a Russian abacus: 15 by 10 (with one rod of 4 beads). """
        self.name = "schety"
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 10
        self.bead_count = (10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 4, 10, 10,
                           10, 10)
        self.base = 10
        self.top_factor = 5

    def draw_rods_and_beads(self, x, y):
        """ Override default in order to make a short rod """
        _white = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#ffffff", "#000000") +\
                 _svg_footer()
        self.white = _svg_str_to_pixbuf(_white)
        _black = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#000000", "#000000") +\
                 _svg_footer()
        self.black = _svg_str_to_pixbuf(_black)

        dx = (BWIDTH+BOFFSET)*self.abacus.scale

        self.beads = []
        self.rods = []
        bo =  (BWIDTH-BOFFSET)*self.abacus.scale/4
        ro =  (BWIDTH+5)*self.abacus.scale/2
        for i in range(self.num_rods):
            _rod = _svg_header(10, self.frame_height-(FSTROKE*2),
                               self.abacus.scale) +\
                   _svg_rect(10, self.frame_height-(FSTROKE*2), 0, 0, 0, 0,
                             ROD_COLORS[(i+5)%len(ROD_COLORS)], "#404040") +\
                   _svg_footer()
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+ro, y,
                                    _svg_str_to_pixbuf(_rod)))

            if i == 10:
                for b in range(4):
                    if b in [1, 2]:
                        color = self.black
                    else:
                        color = self.white
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(8+b)*BHEIGHT*\
                                                  self.abacus.scale,
                                                  color),
                                           8*BHEIGHT*self.abacus.scale,
                                           0.25)) # 1/4 ruples
            elif i < 10:
                for b in range(self.bot_beads):
                    if b in [4, 5]:
                        color = self.black
                    else:
                        color = self.white
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(2+b)*BHEIGHT*\
                                                  self.abacus.scale,
                                                  color),
                                           2*BHEIGHT*self.abacus.scale,
                                           pow(10,9-i)))
            else:
                for b in range(self.bot_beads):
                    if b in [4, 5]:
                        color = self.black
                    else:
                        color = self.white
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(2+b)*BHEIGHT*\
                                                  self.abacus.scale,
                                                  color),
                                           2*BHEIGHT*self.abacus.scale,
                                           1.0/pow(10,i-10)))

        for r in self.rods:
            r.type = "frame"

    def move_bead(self, sprite, dy):
        """ Move a bead (or beads) up or down a rod. """

        # find the bead associated with the sprite
        i = -1
        for bead in self.beads:
            if sprite == bead.spr:
                i = self.beads.index(bead)
                break
        if i == -1:
            print "bead not found"
            return

        # Find out which row i corresponds to
        count = 0
        for r in range(len(self.bead_count)):
            count += self.bead_count[r]
            if i < count:
                break
        # Take into account the number of beads per rod
        o = self.bot_beads - self.bead_count[r] + 2
        b = i - (count-self.bead_count[r])
        n = self.bead_count[r]

        if dy < 0 and bead.state == 0:
            bead.move_up()
            # Make sure beads above this bead are also moved.
            for ii in range(b+1):
                if self.beads[i-ii].get_state() == 0:
                    self.beads[i-ii].move_up()
        elif dy > 0 and bead.state == 1:
            bead.move_down()
            # Make sure beads below this bead are also moved.
            for ii in range(n-b):
                if self.beads[i+ii].get_state() == 1:
                    self.beads[i+ii].move_down()


class Fractions(Schety):
    """ Inherit from Russian abacus. """

    def set_parameters(self):
        """ Create an abacus with fractions: 15 by 10 (with 1/2, 1/3. 1/4,
            1/5, 1/6, 1/8, 1/9, 1/10, 1/12). """
        self.bead_count = (10, 10, 10, 10, 10, 10, 2, 3, 4, 5, 6, 8, 9, 10, 12)
        self.name = "fraction"
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 12
        self.base = 10
        self.top_factor = 5

    def draw_rods_and_beads(self, x, y):
        """ Override default in order to make a short rod """
        _white = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffffff", "#000000") +\
                _svg_footer()
        self.white = _svg_str_to_pixbuf(_white)
        _black = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                 _svg_bead("#000000", "#000000") +\
                 _svg_footer()
        self.black = _svg_str_to_pixbuf(_black)

        dx = (BWIDTH+BOFFSET)*self.abacus.scale

        self.beads = []
        self.rods = []
        bo =  (BWIDTH-BOFFSET)*self.abacus.scale/4
        ro =  (BWIDTH+5)*self.abacus.scale/2
        for i in range(self.num_rods):
            _rod = _svg_header(10, self.frame_height-(FSTROKE*2),
                               self.abacus.scale) +\
                   _svg_rect(10, self.frame_height-(FSTROKE*2), 0, 0, 0, 0,
                            ROD_COLORS[(i+9)%len(ROD_COLORS)], "#404040") +\
                   _svg_footer()
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+ro, y,
                                    _svg_str_to_pixbuf(_rod)))

            for b in range(self.bead_count[i]):
                if i < 6: # whole-number beads are white
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(14-self.bead_count[i]+b)*\
                                                  BHEIGHT*self.abacus.scale,
                                                  self.white),
                                           4*BHEIGHT*self.abacus.scale,
                                           pow(10,5-i)))
                else: # fraction beads are black
                    self.beads.append(Bead(Sprite(self.abacus.sprites,
                                                  x+i*dx+bo,
                                                  y+(14-self.bead_count[i]+b)*\
                                                  BHEIGHT*self.abacus.scale,
                                                  self.black),
                                           (14-self.bead_count[i])*BHEIGHT*\
                                           self.abacus.scale,
                                           1.0/self.bead_count[i]))
        for r in self.rods:
            r.type = "frame"
