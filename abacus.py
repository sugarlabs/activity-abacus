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
		menu_items = Gtk.MenuItem(v)
		menu.append(menu_items)
		menu_items.connect('activate', self._switch_abacus_cb, k)
        menu_items = Gtk.MenuItem(_('Reset'))
        menu.append(menu_items)
        menu_items.connect('activate', self._reset)
        menu_items = Gtk.MenuItem(_('Quit'))
        menu.append(menu_items)
        menu_items.connect('activate', self.destroy)
        menu_items.show()
        root_menu = Gtk.MenuItem('Tools')
        root_menu.show()
        root_menu.set_submenu(menu)

        vbox = Gtk.VBox(False, 0)
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

        self.abacus.japanese = Soroban(self.abacus)
        self.abacus.japanese.hide()
	self.abacus.russian = Schety(self.abacus)
        self.abacus.russian.hide()
	self.abacus.mayan = Nepohualtzintzin(self.abacus)
        self.abacus.mayan.hide()
	self.abacus.binary = Binary(self.abacus)
        self.abacus.binary.hide()
	self.abacus.hex = Hex(self.abacus)
        self.abacus.hex.hide()
	self.abacus.fraction = Fractions(self.abacus)
        self.abacus.fraction.hide()
	self.abacus.decimal = Decimal(self.abacus)
        self.abacus.decimal.hide()
        self.abacus.caacupe = Caacupe(self.abacus)
        self.abacus.caacupe.hide()
        self.abacus.cuisenaire = Cuisenaire(self.abacus)
        self.abacus.cuisenaire.hide()

    def set_title(self, title):
        self.win.set_title(title)
        return

    def _switch_abacus_cb(self, widget, user):
	ABACI = {
		'b': self.abacus.binary,
		'c': self.abacus.chinese,
		'f': self.abacus.fraction,
		'h': self.abacus.hex,
		'j': self.abacus.japanese,
		'm': self.abacus.mayan,
		'r': self.abacus.russian,
		'd': self.abacus.decimal,
		'C': self.abacus.caacupe,
		'R': self.abacus.cuisenaire
	}
	self.abacus.mode.hide()
	self.abacus.mode = ABACI[user]
	self.abacus.mode.show()
        return True

    def _reset(self, event, data=None):
        ''' Reset beads to initial position '''
        self.abacus.mode.reset_abacus()
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
