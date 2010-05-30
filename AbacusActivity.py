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
    _new_sugar_system = True
except ImportError:
    _new_sugar_system = False
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.icon import Icon
from sugar.datastore import datastore

from gettext import gettext as _
import locale

import logging
_logger = logging.getLogger("abacus-activity")

from abacus_window import Abacus

#
# Sugar activity
#
class AbacusActivity(activity.Activity):

    def __init__(self, handle):
        """ Initiate activity. """
        super(AbacusActivity,self).__init__(handle)

        if _new_sugar_system:
            # Use 0.86 toolbar design
            toolbar_box = ToolbarBox()

            # Buttons added to the Activity toolbar
            activity_button = ActivityToolbarButton(self)
            toolbar_box.toolbar.insert(activity_button, 0)
            activity_button.show()

            # Suanpan (Chinese abacus) 2:5
            self.chinese = ToolButton( "Con" )
            self.chinese.set_tooltip(_('Suanpan'))
            self.chinese.props.sensitive = True
            self.chinese.connect('clicked', self._chinese_cb)
            toolbar_box.toolbar.insert(self.chinese, -1)
            self.chinese.show()

            # Soroban (Japanese abacus) 1:4
            self.japanese = ToolButton( "Joff" )
            self.japanese.set_tooltip(_('Soroban'))
            self.japanese.props.sensitive = True
            self.japanese.connect('clicked', self._japanese_cb)
            toolbar_box.toolbar.insert(self.japanese, -1)
            self.japanese.show()

            # Schety (Russian abacus) 0:10
            self.russian = ToolButton( "Roff" )
            self.russian.set_tooltip(_('Schety'))
            self.russian.props.sensitive = True
            self.russian.connect('clicked', self._russian_cb)
            toolbar_box.toolbar.insert(self.russian, -1)
            self.russian.show()

            # Nepohualtzintzin (Mayan abacus) 3:4 (base 20)
            self.mayan = ToolButton( "Moff" )
            self.mayan.set_tooltip(_('Nepohualtzintzin'))
            self.mayan.props.sensitive = True
            self.mayan.connect('clicked', self._mayan_cb)
            toolbar_box.toolbar.insert(self.mayan, -1)
            self.mayan.show()

            # Binary (base 2)
            self.binary = ToolButton( "Boff" )
            self.binary.set_tooltip(_('Binary'))
            self.binary.props.sensitive = True
            self.binary.connect('clicked', self._binary_cb)
            toolbar_box.toolbar.insert(self.binary, -1)
            self.binary.show()

            # Fractions (1/2, 1/3, 1/4, 1/5, 1/6, 1/8, 1/9, 1/10, 1/12)
            self.fraction = ToolButton( "Foff" )
            self.fraction.set_tooltip(_('Fraction'))
            self.fraction.props.sensitive = True
            self.fraction.connect('clicked', self._fraction_cb)
            toolbar_box.toolbar.insert(self.fraction, -1)
            self.fraction.show()

            separator = gtk.SeparatorToolItem()
            separator.props.draw = False
            separator.set_expand(True)
            separator.show()
            toolbar_box.toolbar.insert(separator, -1)

            # The ever-present Stop Button
            stop_button = StopButton(self)
            stop_button.props.accelerator = _('<Ctrl>Q')
            toolbar_box.toolbar.insert(stop_button, -1)
            stop_button.show()

            self.set_toolbar_box(toolbar_box)
            toolbar_box.show()

        else:
            # Use pre-0.86 toolbar design
            self.toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(self.toolbox)

            self.projectToolbar = ProjectToolbar(self)
            self.toolbox.add_toolbar( _('Project'), self.projectToolbar )

            self.toolbox.show()

        # Create a canvas
        canvas = gtk.DrawingArea()
        canvas.set_size_request(gtk.gdk.screen_width(),
                                gtk.gdk.screen_height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        # Initialize the canvas
        self.abacus = Abacus(canvas, self)

        # Read the current mode from the Journal
        try:
            if self.metadata['abacus'] == 'suanpan':
                self._chinese_cb(None)
            elif self.metadata['abacus'] == 'soroban':
                self._japanese_cb(None)
            elif self.metadata['abacus'] == 'schety':
                self._russian_cb(None)
            elif self.metadata['abacus'] == 'nepohualtzintzin':
                self._mayan_cb(None)
            elif self.metadata['abacus'] == 'binary':
                self._binary_cb(None)
            elif self.metadata['abacus'] == 'fraction':
                self._fraction_cb(None)
            else:
                self._chinese_cb(None)
        except:
            pass
        try:
            self.abacus.mode.set_value(self.metadata['value'])
            self.abacus.mode.label(self.abacus.mode.value())
        except:
            pass

    def _all_off(self):
        self.chinese.set_icon("Coff")
        self.japanese.set_icon("Joff")
        self.russian.set_icon("Roff")
        self.mayan.set_icon("Moff")
        self.binary.set_icon("Boff")
        self.fraction.set_icon("Foff")
        self.abacus.chinese.hide()
        self.abacus.japanese.hide()
        self.abacus.russian.hide()
        self.abacus.mayan.hide()
        self.abacus.binary.hide()
        self.abacus.fraction.hide()

    def _chinese_cb(self, button):
        """ Display the suanpan; hide the others """
        self._all_off()
        self.chinese.set_icon("Con")
        self.abacus.chinese.show()
        self.abacus.mode = self.abacus.chinese
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _japanese_cb(self, button):
        """ Display the soroban; hide the others """
        self._all_off()
        self.japanese.set_icon("Jon")
        self.abacus.japanese.show()
        self.abacus.mode = self.abacus.japanese
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _russian_cb(self, button):
        """ Display the schety; hide the others """
        self._all_off()
        self.russian.set_icon("Ron")
        self.abacus.russian.show()
        self.abacus.mode = self.abacus.russian
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _mayan_cb(self, button):
        """ Display the nepohualtzintzin; hide the others """
        self._all_off()
        self.mayan.set_icon("Mon")
        self.abacus.mayan.show()
        self.abacus.mode = self.abacus.mayan
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _binary_cb(self, button):
        """ Display the binary; hide the others """
        self._all_off()
        self.binary.set_icon("Bon")
        self.abacus.binary.show()
        self.abacus.mode = self.abacus.binary
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _fraction_cb(self, button):
        """ Display the fraction; hide the others """
        self._all_off()
        self.fraction.set_icon("Fon")
        self.abacus.fraction.show()
        self.abacus.mode = self.abacus.fraction
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def write_file(self, file_path):
        """ Write the bead positions to the Journal """
        _logger.debug("Saving current abacus to Journal: %s " % (
                       self.abacus.mode.name))
        try:
            self.metadata['abacus'] = self.abacus.mode.name
            self.metadata['value'] = self.abacus.mode.value(True)
        except:
            pass

#
# Project toolbar for pre-0.86 toolbars
#
class ProjectToolbar(gtk.Toolbar):

    def __init__(self, pc):
        """ Initiate 'old-style' toolbars."""
        gtk.Toolbar.__init__(self)
        self.activity = pc

        # Chinese style
        self.activity.chinese = ToolButton( "Con" )
        self.activity.chinese.set_tooltip(_('Saunpan'))
        self.activity.chinese.props.sensitive = True
        self.activity.chinese.connect('clicked', self.activity._chinese_cb)
        self.insert(self.activity.chinese, -1)
        self.activity.chinese.show()

        # Japanese style
        self.activity.japanese = ToolButton( "Joff" )
        self.activity.japanese.set_tooltip(_('Soroban'))
        self.activity.japanese.props.sensitive = True
        self.activity.japanese.connect('clicked', self.activity._japanese_cb)
        self.insert(self.activity.japanese, -1)
        self.activity.japanese.show()

        # Russian style
        self.activity.russian = ToolButton( "Roff" )
        self.activity.russian.set_tooltip(_('Schety'))
        self.activity.russian.props.sensitive = True
        self.activity.russian.connect('clicked', self.activity._russian_cb)
        self.insert(self.activity.russian, -1)
        self.activity.russian.show()

        # Mayan style
        self.activity.mayan = ToolButton( "Moff" )
        self.activity.mayan.set_tooltip(_('Nepohualtzintzin'))
        self.activity.mayan.props.sensitive = True
        self.activity.mayan.connect('clicked', self.activity._mayan_cb)
        self.insert(self.activity.mayan, -1)
        self.activity.mayan.show()

        # Binary style
        self.activity.binary = ToolButton( "Boff" )
        self.activity.binary.set_tooltip(_('Binary'))
        self.activity.binary.props.sensitive = True
        self.activity.binary.connect('clicked', self.activity._binary_cb)
        self.insert(self.activity.binary, -1)
        self.activity.binary.show()

        # Fraction style
        self.activity.fraction = ToolButton( "Foff" )
        self.activity.fraction.set_tooltip(_('Fraction'))
        self.activity.fraction.props.sensitive = True
        self.activity.fraction.connect('clicked', self.activity._fraction_cb)
        self.insert(self.activity.fraction, -1)
        self.activity.fraction.show()
