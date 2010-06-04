#!/usr/bin/env python

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

import pygtk
pygtk.require('2.0')
import gtk

from gettext import gettext as _

from abacus_window import Abacus

class AbacusMain:
    def __init__(self):
        self.r = 0
        self.tw = None

        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        try:
            data_file = open('.abacusrc', 'r')
        except IOError:
            data_file = open('.abacusrc', 'a+')
            data_file.write(str(50)+'\n')
            data_file.write(str(50)+'\n')
            data_file.write(str(800)+'\n')
            data_file.write(str(550)+'\n')
            data_file.seek(0)
        self.x = int(data_file.readline())
        self.y = int(data_file.readline())
        self.width = int(data_file.readline())
        self.height = int(data_file.readline())
        self.win.set_default_size(self.width, self.height)
        self.win.move(self.x, self.y)
        self.win.maximize()
        self.win.set_title(_("Abacus"))
        self.win.connect("delete_event", lambda w,e: gtk.main_quit())

        menu = gtk.Menu()
        menu_items = gtk.MenuItem(_("Saunpan"))
        menu.append(menu_items)
        menu_items.connect("activate", self._c_cb)
        menu_items.show()
        menu_items = gtk.MenuItem(_("Soroban"))
        menu.append(menu_items)
        menu_items.connect("activate", self._j_cb)
        menu_items.show()
        menu_items = gtk.MenuItem(_("Schety"))
        menu.append(menu_items)
        menu_items.connect("activate", self._r_cb)
        menu_items.show()
        menu_items = gtk.MenuItem(_("Nepohualtzintzin"))
        menu.append(menu_items)
        menu_items.connect("activate", self._m_cb)
        menu_items = gtk.MenuItem(_("Binary"))
        menu.append(menu_items)
        menu_items.connect("activate", self._b_cb)
        menu_items = gtk.MenuItem(_("Hexadecimal"))
        menu.append(menu_items)
        menu_items.connect("activate", self._h_cb)
        menu_items = gtk.MenuItem(_("Fraction"))
        menu.append(menu_items)
        menu_items.connect("activate", self._f_cb)
        menu_items.show()
        menu_items = gtk.MenuItem(_("Quit"))
        menu.append(menu_items)
        menu_items.connect("activate", self.destroy)
        menu_items.show()
        root_menu = gtk.MenuItem("Tools")
        root_menu.show()
        root_menu.set_submenu(menu)

        # A vbox to put a menu and the canvas in:
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

    def _hide_all(self):
        self.abacus.chinese.hide()
        self.abacus.japanese.hide()
        self.abacus.russian.hide()
        self.abacus.mayan.hide()
        self.abacus.binary.hide()
        self.abacus.hex.hide()
        self.abacus.fraction.hide()

    def _c_cb(self, widget):
        self._hide_all()
        self.abacus.chinese.show()
        self.abacus.mode = self.abacus.chinese
        return True

    def _j_cb(self, widget):
        self._hide_all()
        self.abacus.japanese.show()
        self.abacus.mode = self.abacus.japanese
        return True

    def _r_cb(self, widget):
        self._hide_all()
        self.abacus.russian.show()
        self.abacus.mode = self.abacus.russian
        return True

    def _m_cb(self, widget):
        self._hide_all()
        self.abacus.mayan.show()
        self.abacus.mode = self.abacus.mayan
        return True

    def _b_cb(self, widget):
        self._hide_all()
        self.abacus.binary.show()
        self.abacus.mode = self.abacus.binary
        return True

    def _h_cb(self, widget):
        self._hide_all()
        self.abacus.hex.show()
        self.abacus.mode = self.abacus.hex
        return True

    def _f_cb(self, widget):
        self._hide_all()
        self.abacus.fraction.show()
        self.abacus.mode = self.abacus.fraction
        return True

    def destroy(self, event, data=None):
        """ Callback for destroy event. """
        gtk.main_quit()

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    AbacusMain()
    main()
