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

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import sugar
from sugar.activity import activity
try: # 0.86+ toolbar widgets
    from sugar.bundle.activitybundle import ActivityBundle
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton
    from sugar.graphics.toolbarbox import ToolbarBox
    from sugar.graphics.toolbarbox import ToolbarButton
except ImportError:
    pass
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.icon import Icon
from sugar.datastore import datastore

from gettext import gettext as _
import locale
import os.path

import logging
_logger = logging.getLogger("abacus-activity")

from abacus_window import Abacus

#
# Sugar activity
#
class AbacusActivity(activity.Activity):

    def __init__(self, handle):
        super(AbacusActivity,self).__init__(handle)

        try:
            # Use 0.86 toolbar design
            toolbar_box = ToolbarBox()

            # Buttons added to the Activity toolbar
            activity_button = ActivityToolbarButton(self)
            toolbar_box.toolbar.insert(activity_button, 0)
            activity_button.show()

            # Suanpan (Chinese abacus) 2:5
            self.chinese = ToolButton( "Con" )
            self.chinese.set_tooltip(_('suanpan'))
            self.chinese.props.sensitive = True
            self.chinese.connect('clicked', self._chinese_cb)
            toolbar_box.toolbar.insert(self.chinese, -1)
            self.chinese.show()

            # Soroban (Japanese abacus) 1:4
            self.japanese = ToolButton( "Joff" )
            self.japanese.set_tooltip(_('soroban'))
            self.japanese.props.sensitive = True
            self.japanese.connect('clicked', self._japanese_cb)
            toolbar_box.toolbar.insert(self.japanese, -1)
            self.japanese.show()

            # Schety (Russian abacus) 0:10
            self.russian = ToolButton( "Roff" )
            self.russian.set_tooltip(_('schety'))
            self.russian.props.sensitive = True
            self.russian.connect('clicked', self._russian_cb)
            toolbar_box.toolbar.insert(self.russian, -1)
            self.russian.show()

            separator = gtk.SeparatorToolItem()
            separator.props.draw = False
            separator.set_expand(True)
            separator.show()
            toolbar_box.toolbar.insert(separator, -1)

            # The ever-present Stop Button
            stop_button = StopButton(self)
            stop_button.props.accelerator = '<Ctrl>Q'
            toolbar_box.toolbar.insert(stop_button, -1)
            stop_button.show()

            self.set_toolbar_box(toolbar_box)
            toolbar_box.show()

        except NameError:
            # Use pre-0.86 toolbar design
            self.toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(self.toolbox)

            self.projectToolbar = ProjectToolbar(self)
            self.toolbox.add_toolbar( _('Project'), self.projectToolbar )

            self.toolbox.show()

        # Create a canvas
        canvas = gtk.DrawingArea()
        canvas.set_size_request(gtk.gdk.screen_width(), \
                                gtk.gdk.screen_height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        # Initialize the canvas
        self.abacus = Abacus(canvas, os.path.join(activity.get_bundle_path(),
                                                  'images/'), self)

        """
        # Read the slider positions from the Journal
        try:
            self.tw.A.spr.move_relative((int(self.metadata['A']),0))
            self.tw.C.spr.move_relative((int(self.metadata['C']),0))
            self.tw.C_tab_left.spr.move_relative((int(self.metadata['C']),0))
            self.tw.C_tab_right.spr.move_relative((int(self.metadata['C'])+\
                                                   SWIDTH-100,0))
            self.tw.D.spr.move_relative((int(self.metadata['D']),0))
            self.tw.R.spr.move_relative((int(self.metadata['R']),0))
            self.tw.R_tab_top.spr.move_relative((int(self.metadata['R']),0))
            self.tw.R_tab_bot.spr.move_relative((int(self.metadata['R']),0))
            self.tw.slider_on_top = self.metadata['slider']
            if self.tw.slider_on_top == 'A':
                self._show_a()
            else:
                self._show_c()
            window._update_results_label(self.tw)
            window._update_slider_labels(self.tw)
        except:
            self._show_c()
        """

    def _chinese_cb(self, button):
        self._show_c()
        return True

    def _show_c(self):
        self.chinese.set_icon("Con")
        self.japanese.set_icon("Joff")
        self.russian.set_icon("Roff")
        self.abacus.chinese.show()
        self.abacus.japanese.hide()
        self.abacus.russian.hide()
        self.abacus.mode = self.abacus.chinese

    def _japanese_cb(self, button):
        self._show_j()
        return True

    def _show_j(self):
        self.chinese.set_icon("Coff")
        self.japanese.set_icon("Jon")
        self.russian.set_icon("Roff")
        self.abacus.chinese.hide()
        self.abacus.japanese.show()
        self.abacus.russian.hide()
        self.abacus.mode = self.abacus.japanese

    def _russian_cb(self, button):
        self._show_r()
        return True

    def _show_r(self):
        self.chinese.set_icon("Coff")
        self.japanese.set_icon("Joff")
        self.russian.set_icon("Ron")
        self.abacus.chinese.hide()
        self.abacus.japanese.hide()
        self.abacus.russian.show()
        self.abacus.mode = self.abacus.russian

    """
    Write the slider positions to the Journal
    """
    """
    def write_file(self, file_path):
        _logger.debug("Write slider on top: " + self.tw.slider_on_top)
        self.metadata['slider'] = self.tw.slider_on_top
        x,y = self.tw.A.spr.get_xy()
        _logger.debug("Write A offset: " + str(x))
        self.metadata['A'] = str(x)
        x,y = self.tw.C.spr.get_xy()
        _logger.debug("Write C offset: " + str(x))
        self.metadata['C'] = str(x)
        x,y = self.tw.D.spr.get_xy()
        _logger.debug("Write D offset: " + str(x))
        self.metadata['D'] = str(x)
        x,y = self.tw.R.spr.get_xy()
        _logger.debug("Write r offset: " + str(x))
        self.metadata['R'] = str(x)
    """

#
# Project toolbar for pre-0.86 toolbars
#
class ProjectToolbar(gtk.Toolbar):

    def __init__(self, pc):
        gtk.Toolbar.__init__(self)
        self.activity = pc

        # Chinese style
        self.activity.chinese = ToolButton( "Con" )
        self.activity.chinese.set_tooltip(_('saunpan'))
        self.activity.chinese.props.sensitive = True
        self.activity.chinese.connect('clicked', self.activity._chinese_cb)
        self.insert(self.activity.chinese, -1)
        self.activity.chinese.show()

        # Japanese style
        self.activity.japanese = ToolButton( "Joff" )
        self.activity.japanese.set_tooltip(_('soroban'))
        self.activity.japanese.props.sensitive = True
        self.activity.japanese.connect('clicked', self.activity._japanese_cb)
        self.insert(self.activity.japanese, -1)
        self.activity.japanese.show()

        # Russian style
        self.activity.russian = ToolButton( "Roff" )
        self.activity.russian.set_tooltip(_('schety'))
        self.activity.russian.props.sensitive = True
        self.activity.russian.connect('clicked', self.activity._russian_cb)
        self.insert(self.activity.russian, -1)
        self.activity.russian.show()
