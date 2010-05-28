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
FSTROKE = 30

import pygtk
pygtk.require('2.0')
import gtk
from math import pow
import os
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
    # svg_string += _svg_background()
    return svg_string

def _svg_footer():
    """ Returns SVG footer """
    svg_string = "</g>\n"
    svg_string += "</svg>\n"
    return svg_string

def _svg_style(extras=""):
    """ Returns SVG style for shape rendering """
    return "%s%s%s" % ("style=\"", extras, "\"/>\n")

def load_image(path, name, w, h):
    """ create a pixbuf from a SVG stored in a file """
    return gtk.gdk.pixbuf_new_from_file_at_size(
        os.path.join(path+name+'.svg'), int(w), int(h))

class Abacus():

    def __init__(self, canvas, path, parent=None):
        """ Abacus class """
        self.path = path
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
        # self.russian = Fractions(self)
        self.mayan = Nepohualtzintzin(self)

        self.chinese.show()
        self.japanese.hide()
        self.russian.hide()
        self.mayan.hide()
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

    def __init__(self, abacus):
        """ Specify parameters that define the abacus """
        self.abacus = abacus
        self.name = "suanpan"
        self.num_rods = 15
        self.bot_beads = 2
        self.top_beads = 5
        self.base = 10
        self.create()

    def create(self):
        self.frame_width = self.num_rods*(BWIDTH+BOFFSET)+FSTROKE*2
        if self.top_beads > 0:
            self.frame_height = (self.bot_beads+self.top_beads+5)*BHEIGHT +\
                                FSTROKE*2
            dy = (self.top_beads+2)*BHEIGHT*self.abacus.scale
        else:
            self.frame_height = (self.bot_beads+2)*BHEIGHT + FSTROKE*2
            dy = -FSTROKE
        rod_colors = ["#006ffe", "#007ee7", "#0082c4", "#0089ab", "#008c8b",
                      "#008e68", "#008e4c", "#008900", "#5e7700", "#787000",
                      "#876a00", "#986200", "#ab5600", "#d60000", "#e30038"]

        """ Create an abacus. """
        white = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffffff", "#000000") +\
                _svg_footer()
        yellow1 = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffffcc", "#000000") +\
                _svg_footer()
        yellow2 = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffff88", "#000000") +\
                _svg_footer()
        yellow3 = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffff00", "#000000") +\
                _svg_footer()
        self.colors = [_svg_str_to_pixbuf(white),
                       _svg_str_to_pixbuf(yellow1),
                       _svg_str_to_pixbuf(yellow2),
                       _svg_str_to_pixbuf(yellow3)]
        rod_h = (self.bot_beads+2+1+self.top_beads+2)*BHEIGHT*self.abacus.scale
        w = (self.num_rods+1)*(BWIDTH+BOFFSET)*self.abacus.scale
        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        x = (self.abacus.width-w)/2
        y = (self.abacus.height-rod_h)/2
        o =  (BWIDTH+BOFFSET-5)*self.abacus.scale/2

        # Draw the frame...
        frame = _svg_header(self.frame_width, self.frame_height,
                            self.abacus.scale) +\
                _svg_rect(self.frame_width, self.frame_height, 
                          FSTROKE/2, FSTROKE/2, 0, 0, "#000000", "#000000") +\
                _svg_rect(self.frame_width-(FSTROKE*2), 
                          self.frame_height-(FSTROKE*2), 0, 0,
                          FSTROKE, FSTROKE, "#808080", "#000000") +\
                _svg_footer()
        self.frame = Sprite(self.abacus.sprites, x-BHEIGHT*self.abacus.scale,
                            y-BHEIGHT*self.abacus.scale,
                            _svg_str_to_pixbuf(frame))
        self.frame.type = 'frame'

        # and then the rods and beads.
        self.rods = []
        self.beads = []

        bo =  (BWIDTH-BOFFSET)*self.abacus.scale/4
        ro =  (BWIDTH+5)*self.abacus.scale/2
        for i in range(self.num_rods):
            rod = _svg_header(10, self.frame_height-(FSTROKE*2),
                              self.abacus.scale) +\
                  _svg_rect(10, self.frame_height-(FSTROKE*2), 0, 0, 0, 0,
                            rod_colors[i%len(rod_colors)], "#404040") +\
                  _svg_footer()
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+ro,
                                    y,
                                    _svg_str_to_pixbuf(rod)))     

            for b in range(self.top_beads):
                self.beads.append(Sprite(self.abacus.sprites, x+i*dx+bo,
                                         y+b*BHEIGHT*self.abacus.scale,
                                         self.colors[0]))
            for b in range(self.bot_beads):
                self.beads.append(Sprite(self.abacus.sprites, x+i*dx+bo,
                                         y+(self.top_beads+5+b)*BHEIGHT\
                                            *self.abacus.scale,
                                         self.colors[0]))

        for i in self.beads:
            i.type = 'bead'
            i.state = 0
            i.level = 0

        # Draw the dividing bar...
        bar = _svg_header(self.frame_width-(FSTROKE*2), BHEIGHT,
                          self.abacus.scale) +\
              _svg_rect(self.frame_width-(FSTROKE*2), BHEIGHT, 0, 0, 0, 0,
                        "#000000", "#000000") +\
              _svg_footer()
        self.bar = Sprite(self.abacus.sprites, x, y+dy,
                          _svg_str_to_pixbuf(bar))

        self.bar.type = 'frame'
        self.bar.set_label_color('white')

        # and finally, the mark.
        o =  (BWIDTH+BOFFSET-(FSTROKE/2))*self.abacus.scale/2
        self.mark = Sprite(self.abacus.sprites, x+(self.num_rods-1)*dx+o,
                           y-(BHEIGHT-(FSTROKE/2))*self.abacus.scale,
                           load_image(self.abacus.path, "indicator",
                                      20*self.abacus.scale,
                                      15*self.abacus.scale))
        self.mark.type = 'mark'

    def hide(self):
        """ Hide the rod, beads, mark, and frame. """
        for i in self.rods:
            i.hide()
        for i in self.beads:
            i.hide()
        self.bar.hide()
        self.frame.hide()
        self.mark.hide()

    def show(self):
        """ Show the rod, beads, mark, and frame. """
        self.frame.set_layer(100)
        for i in self.rods:
            i.set_layer(101)
        for i in self.beads:
            i.set_layer(102)
        self.bar.set_layer(103)
        self.mark.set_layer(104)

    def set_value(self, string):
        """ Set abacus to value in string """
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
        bot = v % 5
        top = (v-bot)/5
        top_bead_index = r*(self.top_beads+self.bot_beads)
        bot_bead_index = r*(self.top_beads+self.bot_beads)+self.top_beads

        # Clear the top.
        for i in range(self.top_beads):
            if self.beads[top_bead_index+i].state:
                self.beads[top_bead_index+i].move((0, 
                                                  -2*BHEIGHT*self.abacus.scale))
            self.beads[top_bead_index+i].state = 0
        # Clear the bottom.
        for i in range(self.bot_beads):
            if self.beads[bot_bead_index+i].state:
                self.beads[bot_bead_index+i].move((0, 
                                                   2*BHEIGHT*self.abacus.scale))
            self.beads[bot_bead_index+i].state = 0
        # Set the top.
        for i in range(top):
            self.beads[top_bead_index+self.top_beads-i-1].move_relative((0, 
                                                   2*BHEIGHT*self.abacus.scale))
            self.beads[top_bead_index+self.top_beads-i-1].state = 1 
        # Set the bottom
        for i in range(bot):
            self.beads[bot_bead_index+i].move_relative((0,
                                                  -2*BHEIGHT*self.abacus.scale))
            self.beads[bot_bead_index+i].state = 1 

    def value(self, count_beads=False):
        """ Return a string representing the value of each rod. """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            r = i/(self.top_beads+self.bot_beads)
            j = i % (self.top_beads+self.bot_beads)
            if b.state == 1:
                if j < self.top_beads:
                    v[r+1] += 5
                else:
                    v[r+1] += 1

        if count_beads:
            # Save the value associated with each rod as a 2-byte int.
            for j in v[1:]:
                string += "%2d" % (j)
        else:
            # Carry to the left if a rod has a value > 9.
            for j in range(self.num_rods):
                if v[len(v)-j-1] > 9:
                    v[len(v)-j-1] -= 10
                    v[len(v)-j-2] += 1

            # Convert values to a string.
            for j in v:
                if string != '' or j > 0:
                    string += str(j)

        return(string)

    def label(self, string):
        """ Label the crossbar with the string. (Used with self.value) """
        self.bar.set_label(string)

    def move_mark(self, dx):
        """ Move indicator horizontally across the top of the frame. """
        self.mark.move_relative((dx, 0))

    def set_color(self, bead, level=3):
        """ Set color of bead to one of four fade levels. """
        bead.set_image(self.colors[level])
        bead.inval()
        bead.level = level

    def fade_colors(self):
        """ Reduce the fade level of every bead. """
        for bead in self.beads:
            if bead.level > 0:
                self.set_color(bead, bead.level-1)
  
    def move_bead(self, bead, dy):
        """ Move a bead (or beads) up or down a rod. """
        i = self.beads.index(bead)
        b = i % (self.top_beads+self.bot_beads)
        if b < self.top_beads:
            if dy > 0 and bead.state == 0:
                self.fade_colors()
                self.set_color(bead)
                bead.move_relative((0, 2*BHEIGHT*self.abacus.scale))
                bead.state = 1
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads-b):
                    if self.beads[i+ii].state == 0:
                        self.set_color(self.beads[i+ii])
                        self.beads[i+ii].move_relative((0,
                                                   2*BHEIGHT*self.abacus.scale))
                        self.beads[i+ii].state = 1
            elif dy < 0 and bead.state == 1:
                self.fade_colors()
                self.set_color(bead)
                bead.move_relative((0, -2*BHEIGHT*self.abacus.scale))
                bead.state = 0
                # Make sure beads above this bead are also moved.
                for ii in range(b+1):
                    if self.beads[i-ii].state == 1:
                        self.set_color(self.beads[i-ii])
                        self.beads[i-ii].move_relative((0,
                                                  -2*BHEIGHT*self.abacus.scale))
                        self.beads[i-ii].state = 0
        else:
            if dy < 0 and bead.state == 0:
                self.fade_colors()
                self.set_color(bead)
                bead.move_relative((0, -2*BHEIGHT*self.abacus.scale))
                bead.state = 1
                # Make sure beads above this bead are also moved.
                for ii in range(b-self.top_beads+1):
                    if self.beads[i-ii].state == 0:
                        self.set_color(self.beads[i-ii])
                        self.beads[i-ii].move_relative((0,
                                                  -2*BHEIGHT*self.abacus.scale))
                        self.beads[i-ii].state = 1
            elif dy > 0 and bead.state == 1:
                self.fade_colors()
                self.set_color(bead)
                bead.move_relative((0, 2*BHEIGHT*self.abacus.scale))
                bead.state = 0
                # Make sure beads below this bead are also moved.
                for ii in range(self.top_beads+self.bot_beads-b):
                    if self.beads[i+ii].state == 1:
                        self.set_color(self.beads[i+ii])
                        self.beads[i+ii].move_relative((0,
                                                   2*BHEIGHT*self.abacus.scale))
                        self.beads[i+ii].state = 0

class Nepohualtzintzin(AbacusGeneric):

    def __init__(self, abacus):
        """ Specify parameters that define the abacus """
        self.abacus = abacus
        self.name = 'nepohualtzintzin'
        self.num_rods = 13
        self.bot_beads = 4
        self.top_beads = 3
        self.base = 20
        self.create()

    def value(self, count_beads=False):
        """ Override default: base 20 """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            r = i/(self.top_beads+self.bot_beads)
            j = i % (self.top_beads+self.bot_beads)
            if b.state == 1:
                if count_beads:
                    f = 1
                else:
                    f = pow(2,self.num_rods-r-1)
                if j < self.top_beads:
                    v[r+1] += 5*f
                else:
                    v[r+1] += 1*f

        if count_beads:
            # Save the value associated with each rod as a 2-byte int.
            for j in v[1:]:
                string += "%2d" % (j)
        else:
            # Carry to the left if a rod has a value > 9.
            for j in range(self.num_rods):
                if v[len(v)-j-1] > 9:
                    units = v[len(v)-j-1] % 10
                    tens = v[len(v)-j-1]-units
                    v[len(v)-j-1] = units
                    v[len(v)-j-2] += tens/10

            # Convert values to a string.
            for j in v:
                if string != '' or j > 0:
                    string += str(int(j))
        return(string)


class Suanpan(AbacusGeneric):

    def __init__(self, abacus):
        """ Create a Chinese abacus: 15 by (5,2). """
        self.abacus = abacus
        self.name = 'saunpan'
        self.num_rods = 15
        self.bot_beads = 5
        self.top_beads = 2
        self.base = 10
        self.create()


class Soroban(AbacusGeneric):

    def __init__(self, abacus):
        """ create a Japanese abacus: 15 by (4,1) """
        self.abacus = abacus
        self.name = 'soroban'
        self.num_rods = 15
        self.bot_beads = 4
        self.top_beads = 1
        self.base = 10
        self.create()


class Schety(AbacusGeneric):

    def __init__(self, abacus):
        """ Create a Russian abacus: 15 by 10 (with one rod of 4 beads). """
        self.abacus = abacus
        self.name = "schety"
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 10
        self.base = 10
        self.create()

    def create(self):
        self.frame_width = self.num_rods*(BWIDTH+BOFFSET)+60
        if self.top_beads > 0:
            self.frame_height = (self.bot_beads+self.top_beads+5)*BHEIGHT+60
            dy = (self.top_beads+2)*BHEIGHT*self.abacus.scale
        else:
            self.frame_height = (self.bot_beads+2)*BHEIGHT+60
            dy = -30
        rod_colors = ["#006ffe", "#007ee7", "#0082c4", "#0089ab", "#008c8b",
                      "#008e68", "#008e4c", "#008900", "#5e7700", "#787000",
                      "#876a00", "#986200", "#ab5600", "#d60000", "#e30038"]

        """ Override default in order to make a short rod """
        white = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffffff", "#000000") +\
                _svg_footer()
        black = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#000000", "#000000") +\
                _svg_footer()
        self.white = _svg_str_to_pixbuf(white)
        self.black = _svg_str_to_pixbuf(black)

        # 10 beads + 2 spaces
        rod_h = (self.bot_beads+2)*BHEIGHT*self.abacus.scale
        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        w = (self.num_rods+1)*(BWIDTH+BOFFSET)*self.abacus.scale
        x = (self.abacus.width-w)/2
        y = (self.abacus.height-rod_h)/2

        # Draw the frame...
        frame = _svg_header(self.frame_width, self.frame_height,
                            self.abacus.scale) +\
                _svg_rect(self.frame_width, self.frame_height, 15, 15, 0, 0,
                          "#000000", "#000000") +\
                _svg_rect(self.frame_width-60, self.frame_height-60, 0, 0,
                          30, 30, "#808080", "#000000") +\
                _svg_footer()
        self.frame = Sprite(self.abacus.sprites, x-BHEIGHT*self.abacus.scale,
                            y-BHEIGHT*self.abacus.scale,
                            _svg_str_to_pixbuf(frame))
        self.frame.type = 'frame'

        # and then the beads.
        self.beads = []
        self.rods = []
        o =  (BWIDTH-BOFFSET)/2*self.abacus.scale/2
        bo =  (BWIDTH-BOFFSET)*self.abacus.scale/4
        ro =  (BWIDTH+5)*self.abacus.scale/2
        for i in range(self.num_rods):
            rod = _svg_header(10, self.frame_height-60, self.abacus.scale) +\
                  _svg_rect(10, self.frame_height-60, 0, 0, 0, 0,
                            rod_colors[(i+5)%len(rod_colors)], "#404040") +\
                  _svg_footer()
            self.rods.append(Sprite(self.abacus.sprites, x+i*dx+ro,
                                    y,
                                    _svg_str_to_pixbuf(rod)))     
            if i == 10:
                for b in range(4):
                    if b in [1,2]:
                        color = self.black
                    else:
                        color = self.white
                    self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                             y+(8+b)*BHEIGHT*self.abacus.scale,
                                             color))
            else:
                for b in range(self.bot_beads):
                    if b in [4,5]:
                        color = self.black
                    else:
                        color = self.white
                    self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                             y+(2+b)*BHEIGHT*self.abacus.scale,
                                             color))

        for i in self.beads:
            i.type = 'bead'
            i.state = 0

        # Draw the dividing bar...
        bar = _svg_header(self.frame_width-60, BHEIGHT, self.abacus.scale) +\
              _svg_rect(self.frame_width-60, BHEIGHT, 0, 0, 0, 0,
                        "#000000", "#000000") +\
              _svg_footer()
        self.bar = Sprite(self.abacus.sprites, x, y+dy,
                          _svg_str_to_pixbuf(bar))

        self.bar.type = 'frame'
        self.bar.set_label_color('white')

        # and the mark.
        o =  (BWIDTH+BOFFSET-15)*self.abacus.scale/2
        self.mark = Sprite(self.abacus.sprites, x+(self.num_rods-1)*dx+o,
                           y-(BHEIGHT-15)*self.abacus.scale,
                           load_image(self.abacus.path, "indicator",
                                      20*self.abacus.scale,
                                      15*self.abacus.scale))
        self.mark.type = 'mark'

    def value(self, count_beads=False):
        """ Override to account for fourths """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            if i < 100:
                r = i/self.bot_beads
                if b.state == 1:
                    v[r+1] += 1
            # The 'short' rod
            elif i < 104:
                r = 10
                if b.state == 1:
                    if count_beads:
                        v[r+1] += 1
                    else:
                        v[r+1] += 2.5
            else:
                r = (i+6)/self.bot_beads
                if b.state == 1:
                    v[r+1] += 1

        if count_beads:
            # Save the number of beads on each rod as a 2-byte int.
            for j in v[1:]:
                string += "%2d" % (j)
        else:
            # Carry to the left if a rod has a value > 9.
            # First, process the short rod;
            if v[11] == 10:
                v[10] += 1
            else:
                v[12] += int(v[11])
                v[13] += int(10*v[11]-10*int(v[11]))

            # then, check the rods to the right of the short rod;
            for j in range(4):
                if v[len(v)-j-1] > 9:
                    v[len(v)-j-1] -= 10
                    if j < 3:
                        v[len(v)-j-2] += 1
                    else:
                        v[len(v)-j-3] += 1 # skip over the short rod

            # and finally, the rest of the rods.
            for j in range(6,16):
                if v[len(v)-j-1] > 9:
                    v[len(v)-j-1] -= 10
                    v[len(v)-j-2] += 1

            # Convert values to a string.
            for i, j in enumerate(v):
                if i == 11:
                    string += '.'
                elif string != '' or j > 0:
                    string += str(j)
        return(string)

    def set_rod_value(self, r, v):
        """ Move beads on rod r to represent value v """
        if r == 10:
            beads = 4
            bead_index = r*(self.bot_beads)
            o = 8
        elif r < 10:
            beads = 10
            bead_index = r*(self.bot_beads)
            o = 2
        else:
            beads = 10
            bead_index = r*(self.bot_beads)-6
            o = 2

        # Clear the rod.
        for i in range(beads):
            if self.beads[bead_index+i].state:
                self.beads[bead_index+i].move((0, o*BHEIGHT*self.abacus.scale))
            self.beads[bead_index+i].state = 0

        # Set the rod.
        for i in range(v):
            self.beads[bead_index+i].move_relative((0,
                                                  -o*BHEIGHT*self.abacus.scale))
            self.beads[bead_index+i].state = 1 

    def move_bead(self, bead, dy):
        """ Override to account for short rod """
        i = self.beads.index(bead)
        r = i/self.bot_beads
        # Take into account the rod with just 4 beads
        if r < 10:
            o = 2
            b = i % self.bot_beads
            n = self.bot_beads
        elif i > 99 and i < 104:
            o = 8
            b = i % self.bot_beads
            n = 4
        else:
            o = 2
            b = (i+6) % self.bot_beads
            n = self.bot_beads
        if dy < 0 and bead.state == 0:
            bead.move_relative((0, -o*BHEIGHT*self.abacus.scale))
            bead.state = 1
            # Make sure beads above this bead are also moved.
            for ii in range(b+1):
                if self.beads[i-ii].state == 0:
                    self.beads[i-ii].move_relative((0,
                                                  -o*BHEIGHT*self.abacus.scale))
                    self.beads[i-ii].state = 1
        elif dy > 0 and bead.state == 1:
            bead.move_relative((0, o*BHEIGHT*self.abacus.scale))
            bead.state = 0
            # Make sure beads below this bead are also moved.
            for ii in range(n-b):
                if self.beads[i+ii].state == 1:
                    self.beads[i+ii].move_relative((0,
                                                   o*BHEIGHT*self.abacus.scale))
                    self.beads[i+ii].state = 0


class Fractions(AbacusGeneric):

    def __init__(self, abacus):
        """ Create an abacus with fractions: 15 by 10 (with 1/2, 1/3. 1/4,
            1/5, 1/6, 1/8, 1/9, 1/10, 1/12). """
        self.bead_count = (10, 10, 10, 10, 10, 10, 2, 3, 4, 5, 6, 8, 9, 10, 12)
        self.abacus = abacus
        self.name = "schety"
        self.num_rods = 15
        self.top_beads = 0
        self.bot_beads = 10
        self.frame_width = 810
        self.frame_height = 420
        self.base = 10
        self.create()

    def create(self):
        """ Override default in order to make fraction rods. """
        # 10 beads + 2 spaces
        rod_h = (self.bot_beads+2)*BHEIGHT*self.abacus.scale
        dx = (BWIDTH+BOFFSET)*self.abacus.scale
        w = (self.num_rods+1)*(BWIDTH+BOFFSET)*self.abacus.scale
        x = (self.abacus.width-w)/2
        y = (self.abacus.height-rod_h)/2

        # Draw the frame.
        self.frame = Sprite(self.abacus.sprites, x-BHEIGHT*self.abacus.scale,
                            y-BHEIGHT*self.abacus.scale,
                            load_image(self.abacus.path, self.name+"_frame",
                            self.frame_width*self.abacus.scale,
                            self.frame_height*self.abacus.scale))
        self.frame.type = 'frame'

        # and then the beads.
        white = _svg_header(BWIDTH, BHEIGHT, self.abacus.scale) +\
                _svg_bead("#ffffff", "#000000") +\
                _svg_footer()
        self.white = _svg_str_to_pixbuf(white)
        self.beads = []
        self.rods = []
        o =  (BWIDTH-BOFFSET)/2*self.abacus.scale/2
        for i in range(self.num_rods):
            for b in range(self.bead_count[i]):
                self.beads.append(Sprite(self.abacus.sprites, x+i*dx+o,
                                         y+(12-self.bead_count[i]+b)*BHEIGHT*\
                                         self.abacus.scale,
                                         self.white))

        for i in self.beads:
            i.type = 'bead'
            i.state = 0

        # Draw a bar for the label on top.
        self.bar = Sprite(self.abacus.sprites, x, y-BHEIGHT*self.abacus.scale,
                          load_image(self.abacus.path, self.name+"_bar",
                                     w, BHEIGHT*self.abacus.scale))

        self.bar.type = 'frame'
        self.bar.set_label_color('white')

        # and the mark.
        o =  (BWIDTH+BOFFSET-15)*self.abacus.scale/2
        self.mark = Sprite(self.abacus.sprites, x+(self.num_rods-1)*dx+o,
                           y-(BHEIGHT-15)*self.abacus.scale,
                           load_image(self.abacus.path, "indicator",
                                      20*self.abacus.scale,
                                      15*self.abacus.scale))
        self.mark.type = 'mark'

    def value(self, count_beads=False):
        """ Override to account for fourths """
        string = ''
        v = []
        for r in range(self.num_rods+1): # +1 for overflow
            v.append(0)

        j = -1
        r = -1
        # Tally the values on each rod.
        for i, b in enumerate(self.beads):
            if j < i:
                r+=1
                j+=self.bead_count[r]
            if b.state == 1:
                if count_beads:
                    v[r+1] += 1
                else:
                    v[r+1] += 10/self.bead_count[r]

        if count_beads:
            # Save the number of beads on each rod as a 2-byte int.
            for j in v[1:]:
                string += "%2d" % (j)
        else:
            # Carry to the left if a rod has a value > 9.
            # First, process the short rod;
            if v[11] == 10:
                v[10] += 1
            else:
                v[12] += int(v[11])
                v[13] += int(10*v[11]-10*int(v[11]))

            # then, check the rods to the right of the short rod;
            for j in range(4):
                if v[len(v)-j-1] > 9:
                    v[len(v)-j-1] -= 10
                    if j < 3:
                        v[len(v)-j-2] += 1
                    else:
                        v[len(v)-j-3] += 1 # skip over the short rod

            # and finally, the rest of the rods.
            for j in range(6,16):
                if v[len(v)-j-1] > 9:
                    v[len(v)-j-1] -= 10
                    v[len(v)-j-2] += 1

            # Convert values to a string.
            for i, j in enumerate(v):
                if i == 11:
                    string += '.'
                elif string != '' or j > 0:
                    string += str(j)
        return(string)

    def set_rod_value(self, r, v):
        """ Move beads on rod r to represent value v """
        if r == 10:
            beads = 4
            bead_index = r*(self.bot_beads)
            o = 8
        elif r < 10:
            beads = 10
            bead_index = r*(self.bot_beads)
            o = 2
        else:
            beads = 10
            bead_index = r*(self.bot_beads)-6
            o = 2

        # Clear the rod.
        for i in range(beads):
            if self.beads[bead_index+i].state:
                self.beads[bead_index+i].move((0, o*BHEIGHT*self.abacus.scale))
            self.beads[bead_index+i].state = 0

        # Set the rod.
        for i in range(v):
            self.beads[bead_index+i].move_relative((0,
                                                  -o*BHEIGHT*self.abacus.scale))
            self.beads[bead_index+i].state = 1 

    def move_bead(self, bead, dy):
        """ Override to account for short rod """
        i = self.beads.index(bead)
        r = i/self.bot_beads
        # Take into account the rod with just 4 beads
        if r < 10:
            o = 2
            b = i % self.bot_beads
            n = self.bot_beads
        elif i > 99 and i < 104:
            o = 8
            b = i % self.bot_beads
            n = 4
        else:
            o = 2
            b = (i+6) % self.bot_beads
            n = self.bot_beads
        if dy < 0 and bead.state == 0:
            bead.move_relative((0, -o*BHEIGHT*self.abacus.scale))
            bead.state = 1
            # Make sure beads above this bead are also moved.
            for ii in range(b+1):
                if self.beads[i-ii].state == 0:
                    self.beads[i-ii].move_relative((0,
                                                  -o*BHEIGHT*self.abacus.scale))
                    self.beads[i-ii].state = 1
        elif dy > 0 and bead.state == 1:
            bead.move_relative((0, o*BHEIGHT*self.abacus.scale))
            bead.state = 0
            # Make sure beads below this bead are also moved.
            for ii in range(n-b):
                if self.beads[i+ii].state == 1:
                    self.beads[i+ii].move_relative((0,
                                                   o*BHEIGHT*self.abacus.scale))
                    self.beads[i+ii].state = 0
