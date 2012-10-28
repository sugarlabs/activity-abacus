#!/usr/bin/env python
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

from gi.repository import Gtk, Gdk

from gettext import gettext as _

from abacus_window import Abacus, Custom, Suanpan, Soroban, Schety,\
                          Nepohualtzintzin, Binary, Hex, Decimal, Fractions,\
                          Caacupe, Cuisenaire


class AbacusMain:

    def __init__(self):
        self.r = 0
        self.tw = None

        self.win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        try:
            data_file = open('.abacusrc', 'r')
        except IOError:
            data_file = open('.abacusrc', 'a+')
            data_file.write(str(50) + '\n')
            data_file.write(str(50) + '\n')
            data_file.write(str(800) + '\n')
            data_file.write(str(550) + '\n')
            data_file.seek(0)
        self.x = int(data_file.readline())
        self.y = int(data_file.readline())
        self.width = int(data_file.readline())
        self.height = int(data_file.readline())
        self.win.set_default_size(self.width, self.height)
        self.win.move(self.x, self.y)
        self.win.maximize()
        self.win.set_title(_('Abacus'))
        self.win.connect('delete_event', lambda w, e: Gtk.main_quit())

	ABACI = {
		'c': _('Suanpan'),
		'j': _('Soroban'),
		'r': _('Schety'),
		'm': _('Nepohualtzintzin'),
		'b': _('Binary'),
		'h': _('Hexadecimal'),
		'f': _('Fraction'),
		'd': _('Decimal'),
		'C': _('Caacupé'),
		'R': _('Rods')
	}

        menu = Gtk.Menu()
	for k, v in ABACI.iteritems():
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
        menu_bar.show()

        menu_bar.append(root_menu)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.show()
        canvas = Gtk.DrawingArea()
        width = Gdk.Screen.width()
        height = Gdk.Screen.height()
        canvas.set_size_request(width, height) 
        sw.add_with_viewport(canvas)
        canvas.show()
        vbox.pack_end(sw, True, True, 0)

        self.win.show_all()

        self.abacus = Abacus(canvas)
        self.abacus.win = self.win
        self.abacus.activity = self

    def set_title(self, title):
        self.win.set_title(title)
        return

    def _switch_abacus_cb(self, widget, user):
	ABACI = {
		'b': 'binary',
		'c': 'saupan',
		'f': 'fraction',
		'h': 'hexadecimal',
		'j': 'soroban',
		'm': 'nepohualtzintzin',
		'r': 'schety',
		'd': 'decimal',
		'C': 'caacupe',
		'R': 'cuisenaire'
	}
        value = int(float(self.abacus.mode.value()))
        self.abacus.select_abacus(ABACI[user])
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
