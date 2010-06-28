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

from abacus_window import Abacus, Custom, Suanpan, Soroban, Schety,\
                          Nepohualtzintzin, Binary, Hex, Decimal, Fractions,\
                          Caacupe

def _button_factory(icon_name, tooltip, callback, toolbar):
    """Factory for making toolbar buttons"""
    my_button = ToolButton( icon_name )
    my_button.set_tooltip(tooltip)
    my_button.props.sensitive = True
    my_button.connect('clicked', callback)
    if hasattr(toolbar, 'insert'): # the main toolbar
        toolbar.insert(my_button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(my_button, -1)
    my_button.show()
    return my_button

def _label_factory(label, toolbar):
    """ Factory for adding a label to a toolbar """
    my_label = gtk.Label(label)
    my_label.set_line_wrap(True)
    my_label.show()
    _toolitem = gtk.ToolItem()
    _toolitem.add(my_label)
    toolbar.insert(_toolitem, -1)
    _toolitem.show()
    return my_label

def _spin_factory(default, min, max, callback, toolbar):
    _spin_adj = gtk.Adjustment(default, min, max, 1, 32, 0)
    my_spin = gtk.SpinButton(_spin_adj, 0, 0)
    _spin_id = my_spin.connect('value-changed', callback)
    my_spin.set_numeric(True)
    my_spin.show()
    _toolitem = gtk.ToolItem()
    _toolitem.add(my_spin)
    toolbar.insert(_toolitem, -1)
    _toolitem.show()
    return my_spin

def _separator_factory(toolbar, expand=False, visible=True):
    """ add a separator to a toolbar """
    _separator = gtk.SeparatorToolItem()
    _separator.props.draw = visible
    _separator.set_expand(expand)
    toolbar.insert(_separator, -1)
    _separator.show()

#
# Sugar activity
#
class AbacusActivity(activity.Activity):

    def __init__(self, handle):
        """ Initiate activity. """
        super(AbacusActivity,self).__init__(handle)

        _abacus_toolbar = gtk.Toolbar()
        _custom_toolbar = gtk.Toolbar()
        if _new_sugar_system:
            # Use 0.86 toolbar design
            toolbox = ToolbarBox()

            activity_button = ActivityToolbarButton(self)
            toolbox.toolbar.insert(activity_button, 0)
            activity_button.show()

            self._basic_abacus(toolbox.toolbar)

            _separator_factory(toolbox.toolbar)

            _abacus_toolbar_button = ToolbarButton(
                    page=_abacus_toolbar,
                    icon_name='list-add')
            _abacus_toolbar.show()
            toolbox.toolbar.insert(_abacus_toolbar_button, -1)
            _abacus_toolbar_button.show()

            _custom_toolbar_button = ToolbarButton(
                    page=_custom_toolbar,
                    icon_name='view-source')
            _custom_toolbar.show()
            toolbox.toolbar.insert(_custom_toolbar_button, -1)
            _custom_toolbar_button.show()

            _separator_factory(toolbox.toolbar, True, False)

            stop_button = StopButton(self)
            stop_button.props.accelerator = _('<Ctrl>Q')
            toolbox.toolbar.insert(stop_button, -1)
            stop_button.show()

            # no sharing
            self.max_participants = 1

            self.set_toolbox(toolbox)
            _abacus_toolbar_button.set_expanded(True)
            toolbox.show()

        else:
            # Use pre-0.86 toolbar design
            toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(toolbox)

            toolbox.add_toolbar( _('Project'), _abacus_toolbar )
            toolbox.add_toolbar( _('Custom'), _custom_toolbar )

            self._basic_abacus(_abacus_toolbar)

            toolbox.set_current_toolbar(1)

            # no sharing
            if hasattr(toolbox, 'share'):
               toolbox.share.hide()
            elif hasattr(toolbox, 'props'):
               toolbox.props.visible = False

        # Add the buttons and spinners to the toolbars
        self.japanese = _button_factory("soroban-off", _('Soroban'),
                                        self._japanese_cb, _abacus_toolbar)
        self.russian = _button_factory("schety-off", _('Schety'),
                                       self._russian_cb, _abacus_toolbar)
        self.mayan = _button_factory("nepohualtzintzin-off",
                                     _('Nepohualtzintzin'),
                                     self._mayan_cb, _abacus_toolbar)
        self.binary = _button_factory("binary-off", _('Binary'),
                                      self._binary_cb, _abacus_toolbar)
        self.hex = _button_factory("hex-off", _('Hexadecimal'), self._hex_cb,
                                   _abacus_toolbar)
        self.fraction = _button_factory("fraction-off", _('Fraction'),
                                        self._fraction_cb, _abacus_toolbar)
        self.caacupe = _button_factory("caacupe-off", _('Caacupé'),
                                        self._caacupe_cb, _abacus_toolbar)

        self._rods_label = _label_factory(_("Rods:")+" ", _custom_toolbar)
        self._rods_spin = _spin_factory(15, 1, 20, self._rods_spin_cb,
                                        _custom_toolbar)
        self._top_label = _label_factory(_("Top:")+" ", _custom_toolbar)
        self._top_spin = _spin_factory(2, 0, 4, self._top_spin_cb,
                                       _custom_toolbar)
        self._bottom_label = _label_factory(_("Bottom:")+" ",
                                            _custom_toolbar)
        self._bottom_spin = _spin_factory(5, 1, 20, self._bottom_spin_cb,
                                          _custom_toolbar)
        self._value_label = _label_factory(_("Factor:")+" ", _custom_toolbar)
        self._value_spin = _spin_factory(5, 1, 20, self._value_spin_cb,
                                         _custom_toolbar)
        self._base_label = _label_factory(_("Base:")+" ", _custom_toolbar)
        self._base_spin = _spin_factory(10, 1, 24, self._base_spin_cb,
                                        _custom_toolbar)

        self.custom = _button_factory("new-game", _('Custom'),
                                      self._custom_cb, _custom_toolbar)

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
            self._rods_spin.set_value(int(self.metadata['rods']))
            self._top_spin.set_value(int(self.metadata['top']))
            self._bottom_spin.set_value(int(self.metadata['bottom']))
            self._value_spin.set_value(int(self._metadata['factor']))
            self._base_spin.set_value(int(self.metadata['base']))
        except:
            pass
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
            elif self.metadata['abacus'] == 'hexadecimal':
                self._hex_cb(None)
            elif self.metadata['abacus'] == 'fraction':
                self._fraction_cb(None)
            elif self.metadata['abacus'] == 'caacupe':
                self._caacupe_cb(None)
            elif self.metadata['abacus'] == 'decimal':
                self._decimal_cb(None)
            elif self.metadata['abacus'] == 'custom':
                self._custom_cb(None)
            else:
                self._chinese_cb(None)
        except:
            pass
        try:
            self.abacus.mode.set_value(self.metadata['value'])
            self.abacus.mode.label(self.abacus.generate_label())
        except:
            pass

    def _basic_abacus(self, toolbar):
        """ Add Chinese and decimal abacuses to toolbar """
        self.chinese = _button_factory("suanpan-on", _('Suanpan'),
                                       self._chinese_cb, toolbar)
        self.decimal = _button_factory("decimal-off", _('Decimal'),
                                       self._decimal_cb, toolbar)

    def _all_off(self):
        """ Set all icons to 'off' and hide all of the abacuses """
        self.chinese.set_icon("suanpan-off")
        self.japanese.set_icon("soroban-off")
        self.russian.set_icon("schety-off")
        self.mayan.set_icon("nepohualtzintzin-off")
        self.binary.set_icon("binary-off")
        self.hex.set_icon("hex-off")
        self.fraction.set_icon("fraction-off")
        self.caacupe.set_icon("caacupe-off")
        self.decimal.set_icon("decimal-off")
        if self.abacus.chinese is not None:
            self.abacus.chinese.hide()
        if self.abacus.japanese is not None:
            self.abacus.japanese.hide()
        if self.abacus.russian is not None:
            self.abacus.russian.hide()
        if self.abacus.mayan is not None:
            self.abacus.mayan.hide()
        if self.abacus.binary is not None:
            self.abacus.binary.hide()
        if self.abacus.hex is not None:
            self.abacus.hex.hide()
        if self.abacus.fraction is not None:
            self.abacus.fraction.hide()
        if self.abacus.decimal is not None:
            self.abacus.decimal.hide()
        if self.abacus.caacupe is not None:
            self.abacus.caacupe.hide()
        if self.abacus.custom is not None:
            self.abacus.custom.hide()

    def _select_abacus(self, button, icon, abacus):
        """ Display the selected abacus; hide the others """
        self._all_off()
        if button is not None:
            button.set_icon(icon)
        self.abacus.mode = abacus
        self.abacus.mode.show()
        _logger.debug("Setting mode to %s" % (self.abacus.mode.name))

    def _rods_spin_cb(self, button):
        return

    def _top_spin_cb(self, button):
        return

    def _bottom_spin_cb(self, button):
        return

    def _value_spin_cb(self, button):
        return

    def _base_spin_cb(self, button):
        return

    def _custom_cb(self, button):
        """ Display the custom abacus; hide the others """
        if self.abacus.custom is not None:
            self.abacus.custom.hide()
        self.abacus.custom = Custom(self.abacus,
                             self._rods_spin.get_value_as_int(),
                             self._top_spin.get_value_as_int(),
                             self._bottom_spin.get_value_as_int(),
                             self._value_spin.get_value_as_int(),
                             self._base_spin.get_value_as_int())
        self._select_abacus(None, None, self.abacus.custom)

    def _chinese_cb(self, button):
        """ Display the suanpan; hide the others """
        if self.abacus.chinese is None:
            self.abacus.chinese = Suanpan(self.abacus)
        self._select_abacus(self.chinese, self.abacus.chinese.name+"-on",
                            self.abacus.chinese)

    def _japanese_cb(self, button):
        """ Display the soroban; hide the others """
        if self.abacus.japanese is None:
            self.abacus.japanese = Soroban(self.abacus)
        self._select_abacus(self.japanese, self.abacus.japanese.name+"-on",
                            self.abacus.japanese)

    def _russian_cb(self, button):
        """ Display the schety; hide the others """
        if self.abacus.russian is None:
            self.abacus.russian = Schety(self.abacus)
        self._select_abacus(self.russian, self.abacus.russian.name+"-on",
                            self.abacus.russian)

    def _mayan_cb(self, button):
        """ Display the nepohualtzintzin; hide the others """
        if self.abacus.mayan is None:
            self.abacus.mayan = Nepohualtzintzin(self.abacus)
        self._select_abacus(self.mayan, self.abacus.mayan.name+"-on",
                            self.abacus.mayan)

    def _binary_cb(self, button):
        """ Display the binary; hide the others """
        if self.abacus.binary is None:
            self.abacus.binary = Binary(self.abacus)
        self._select_abacus(self.binary, self.abacus.binary.name+"-on",
                            self.abacus.binary)

    def _hex_cb(self, button):
        """ Display the hex; hide the others """
        if self.abacus.hex is None:
            self.abacus.hex = Hex(self.abacus)
        self._select_abacus(self.hex, self.abacus.hex.name+"-on",
                            self.abacus.hex)

    def _decimal_cb(self, button):
        """ Display the decimal; hide the others """
        if self.abacus.decimal is None:
            self.abacus.decimal = Decimal(self.abacus)
        self._select_abacus(self.decimal, self.abacus.decimal.name+"-on",
                            self.abacus.decimal)

    def _fraction_cb(self, button):
        """ Display the fraction; hide the others """
        if self.abacus.fraction is None:
            self.abacus.fraction = Fractions(self.abacus)
        self._select_abacus(self.fraction, self.abacus.fraction.name+"-on",
                            self.abacus.fraction)

    def _caacupe_cb(self, button):
        """ Display the Caacupe; hide the others """
        if self.abacus.caacupe is None:
            self.abacus.caacupe = Caacupe(self.abacus)
        self._select_abacus(self.caacupe, self.abacus.caacupe.name+"-on",
                            self.abacus.caacupe)

    def write_file(self, file_path):
        """ Write the bead positions to the Journal """
        _logger.debug("Saving current abacus to Journal: %s " % (
                       self.abacus.mode.name))
        try:
            self.metadata['abacus'] = self.abacus.mode.name
            self.metadata['value'] = self.abacus.mode.value(True)
            self.metadata['rods'] = str(self._rods_spin.get_value_as_int())
            self.metadata['top'] = str(self._top_spin.get_value_as_int())
            self.metadata['bottom'] = str(self._bottom_spin.get_value_as_int())
            self.metadata['factor'] = str(self._value_spin.get_value_as_int())
            self.metadata['base'] = str(self._base_spin.get_value_as_int())
        except:
            pass

