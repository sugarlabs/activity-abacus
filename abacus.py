#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010-14, Walter Bender

# This file is part of the Abacus Activity.

# The Abacus Activity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# The Abacus Activity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with the Abacus Activity.  If not, see <http://www.gnu.org/licenses/>.


from gi.repository import Gtk, Gdk

from gettext import gettext as _

from abacus_window import Abacus


class AbacusMain:
    ABACI = {
        'b': 'binary',
        'c': 'suanpan',
        'f': 'fraction',
        'h': 'hexadecimal',
        'j': 'soroban',
        'm': 'nepohualtzintzin',
        'r': 'schety',
        'd': 'decimal',
        'C': 'caacupe',
        'R': 'cuisenaire'
    }

    def __init__(self):
        self.r = 0
        self.tw = None

        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.x = 50
        self.y = 50
        self.width = 800
        self.height = 550
        self.win.set_default_size(self.width, self.height)
        self.win.move(self.x, self.y)
        self.win.maximize()
        self.win.set_title(_('Abacus'))
        self.win.connect('delete_event', lambda w, e: Gtk.main_quit())

        menu = Gtk.Menu()
        for k, v in self.ABACI.iteritems():
            menu_items = Gtk.MenuItem.new_with_label(v)
            menu.append(menu_items)
            menu_items.connect('activate', self._switch_abacus_cb, k)
        menu_items = Gtk.MenuItem.new_with_label(_('Reset'))
        menu.append(menu_items)
        menu_items.connect('activate', self._reset)
        menu_items = Gtk.MenuItem.new_with_label(_('Quit'))
        menu.append(menu_items)
        menu_items.connect('activate', self.destroy)
        menu_items.show()
        root_menu = Gtk.MenuItem.new_with_label('Tools')
        root_menu.show()
        root_menu.set_submenu(menu)

        vbox = Gtk.VBox()
        self.win.add(vbox)
        vbox.show()

        menu_bar = Gtk.MenuBar()
        vbox.pack_start(menu_bar, False, False, 2)

        menu_bar.append(root_menu)
        menu_bar.show_all()

        canvas = Gtk.DrawingArea()
        width = Gdk.Screen.width()
        height = Gdk.Screen.height()
        canvas.set_size_request(width, height)
        vbox.pack_end(canvas, True, True, 0)

        self.win.show()

        self.abacus = Abacus(canvas)
        canvas.show()
        self.abacus.win = self.win
        self.abacus.activity = self
        self.abacus.init()

    def set_title(self, title):
        self.win.set_title(title)
        return

    def _switch_abacus_cb(self, widget, user):
        value = int(float(self.abacus.mode.value()))
        self.abacus.select_abacus(self.ABACI[user])
        self.abacus.mode.set_value_from_number(value)
        self.abacus.mode.label(self.abacus.generate_label())
        return True

    def _reset(self, event, data=None):
        ''' Reset beads to initial position '''
        self.abacus.mode.reset_abacus()
        self.abacus.mode.label(self.abacus.generate_label())
        return

    def destroy(self, event, data=None):
        ''' Callback for destroy event. '''
        Gtk.main_quit()


def main():
    Gtk.main()
    return 0

if __name__ == '__main__':
    AbacusMain()
    main()
