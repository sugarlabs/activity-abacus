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

import gtk

from gettext import gettext as _

from abacus_window import Abacus, Custom, Suanpan, Soroban, Schety,\
                          Nepohualtzintzin, Binary, Hex, Decimal, Fractions,\
                          Caacupe, Cuisenaire


class AbacusMain:

    def __init__(self):
        self.r = 0
        self.tw = None

        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
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
        self.win.connect('delete_event', lambda w, e: gtk.main_quit())

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

        menu = gtk.Menu()
	for k, v in ABACI.iteritems():
		menu_items = gtk.MenuItem(v)
		menu.append(menu_items)
		menu_items.connect('activate', self._switch_abacus_cb, k)
        menu_items = gtk.MenuItem(_('Reset'))
        menu.append(menu_items)
        menu_items.connect('activate', self._reset)
        menu_items = gtk.MenuItem(_('Quit'))
        menu.append(menu_items)
        menu_items.connect('activate', self.destroy)
        menu_items.show()
        root_menu = gtk.MenuItem('Tools')
        root_menu.show()
        root_menu.set_submenu(menu)

        vbox = gtk.VBox(False, 0)
        self.win.add(vbox)
        vbox.show()

        menu_bar = gtk.MenuBar()
        vbox.pack_start(menu_bar, False, False, 2)
        menu_bar.show()

        menu_bar.append(root_menu)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.show()
        canvas = gtk.DrawingArea()
        width = gtk.gdk.screen_width()
        height = gtk.gdk.screen_height()
        canvas.set_size_request(width, height) 
        sw.add_with_viewport(canvas)
        canvas.show()
        vbox.pack_end(sw, True, True)

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
        gtk.main_quit()

def main():
    gtk.main()
    return 0

if __name__ == '__main__':
    AbacusMain()
    main()
