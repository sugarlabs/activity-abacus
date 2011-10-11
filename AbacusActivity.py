# -*- coding: utf-8 -*-
#Copyright (c) 2010-11, Walter Bender

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
try:  # 0.86+ toolbar widgets
    from sugar.graphics.toolbarbox import ToolbarBox
    HAS_TOOLBARBOX = True
except ImportError:
    HAS_TOOLBARBOX = False
if HAS_TOOLBARBOX:
    from sugar.bundle.activitybundle import ActivityBundle
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton
    from sugar.graphics.toolbarbox import ToolbarButton
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.icon import Icon
from sugar.datastore import datastore

from gettext import gettext as _
import locale

import logging
_logger = logging.getLogger('abacus-activity')

from abacus_window import Abacus, Custom, Suanpan, Soroban, Schety,\
                          Nepohualtzintzin, Binary, Hex, Decimal, Fractions,\
                          Caacupe, Cuisenaire


def _button_factory(icon_name, toolbar, callback, cb_arg=None, tooltip=None,
                    accelerator=None):
    '''Factory for making toolbar buttons'''
    button = ToolButton(icon_name)
    if tooltip is not None:
        button.set_tooltip(tooltip)
    button.props.sensitive = True
    if accelerator is not None:
        button.props.accelerator = accelerator
    if cb_arg is None:
        button.connect('clicked', callback)
    else:
        button.connect('clicked', cb_arg)
    if hasattr(toolbar, 'insert'): # the main toolbar
        toolbar.insert(button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(button, -1)
    button.show()
    return button


def _radio_factory(icon_name, toolbar, callback, cb_arg=None,
                          tooltip=None, group=None):
    ''' Add a radio button to a toolbar '''
    button = RadioToolButton(group=group)
    button.set_named_icon(icon_name)
    if tooltip is not None:
        button.set_tooltip(tooltip)
    if cb_arg is None:
        button.connect('clicked', callback)
    else:
        button.connect('clicked', callback, cb_arg)
    if hasattr(toolbar, 'insert'):  # the main toolbar
        toolbar.insert(button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(button, -1)
    button.show()
    return button


def _label_factory(label_text, toolbar):
    ''' Factory for adding a label to a toolbar '''
    label = gtk.Label(label_text)
    label.set_line_wrap(True)
    label.show()
    toolitem = gtk.ToolItem()
    toolitem.add(label)
    toolbar.insert(toolitem, -1)
    toolitem.show()
    return label


def _spin_factory(default, min, max, callback, toolbar):
    spin_adj = gtk.Adjustment(default, min, max, 1, 32, 0)
    spin = gtk.SpinButton(spin_adj, 0, 0)
    spin_id = spin.connect('value-changed', callback)
    spin.set_numeric(True)
    spin.show()
    toolitem = gtk.ToolItem()
    toolitem.add(spin)
    toolbar.insert(toolitem, -1)
    toolitem.show()
    return spin


def _separator_factory(toolbar, expand=False, visible=True):
    ''' add a separator to a toolbar '''
    separator = gtk.SeparatorToolItem()
    separator.props.draw = visible
    separator.set_expand(expand)
    toolbar.insert(separator, -1)
    separator.show()


class AbacusActivity(activity.Activity):

    def __init__(self, handle):
        ''' Initiate activity. '''
        super(AbacusActivity, self).__init__(handle)

        # no sharing
        self.max_participants = 1

        abacus_toolbar = gtk.Toolbar()
        custom_toolbar = gtk.Toolbar()
        edit_toolbar = gtk.Toolbar()

        if HAS_TOOLBARBOX:
            # Use 0.86 toolbar design
            toolbox = ToolbarBox()

            activity_button = ActivityToolbarButton(self)
            toolbox.toolbar.insert(activity_button, 0)
            activity_button.show()

            edit_toolbar_button = ToolbarButton(label=_('Edit'),
                                                page=edit_toolbar,
                                                icon_name='toolbar-edit')
            edit_toolbar_button.show()
            toolbox.toolbar.insert(edit_toolbar_button, -1)
            edit_toolbar_button.show()

            abacus_toolbar_button = ToolbarButton(
                    page=abacus_toolbar,
                    icon_name='abacus-list')
            abacus_toolbar.show()
            toolbox.toolbar.insert(abacus_toolbar_button, -1)
            abacus_toolbar_button.show()

            custom_toolbar_button = ToolbarButton(
                    page=custom_toolbar,
                    icon_name='view-source')
            custom_toolbar.show()
            toolbox.toolbar.insert(custom_toolbar_button, -1)
            custom_toolbar_button.show()

            _separator_factory(toolbox.toolbar, False, True)

            _button_factory('edit-delete', toolbox.toolbar,
                            self._reset_cb, tooltip=_('Reset'))

            _separator_factory(toolbox.toolbar, True, False)

            stop_button = StopButton(self)
            stop_button.props.accelerator = _('<Ctrl>Q')
            toolbox.toolbar.insert(stop_button, -1)
            stop_button.show()

            self.set_toolbox(toolbox)
            toolbox.show()

        else:
            # Use pre-0.86 toolbar design
            toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(toolbox)

            toolbox.add_toolbar( _('Project'), abacus_toolbar )
            toolbox.add_toolbar( _('Custom'), custom_toolbar )
            toolbox.add_toolbar(_('Edit'), edit_toolbar)

            _button_factory('edit-delete', edit_toolbar,
                            self._reset_cb, tooltip=_('Reset'))

            _separator_factory(edit_toolbar, False, True)

            toolbox.set_current_toolbar(1)

            # no sharing
            if hasattr(toolbox, 'share'):
                toolbox.share.hide()
            elif hasattr(toolbox, 'props'):
               toolbox.props.visible = False

        # TRANS: simple decimal abacus
        self.decimal = _radio_factory('decimal', abacus_toolbar,
                                      self._radio_cb, cb_arg='decimal',
                                      tooltip=_('Decimal'),
                                      group=None)

        # TRANS: http://en.wikipedia.org/wiki/Soroban (Japanese abacus)
        self.japanese = _radio_factory('soroban', abacus_toolbar,
                                       self._radio_cb, cb_arg='japanese',
                                       tooltip=_('Soroban'),
                                       group=self.decimal)

        # TRANS: http://en.wikipedia.org/wiki/Suanpan (Chinese abacus)
        self.chinese = _radio_factory('suanpan', abacus_toolbar,
                                      self._radio_cb, cb_arg='chinese',
                                      tooltip=_('Suanpan'),
                                      group=self.decimal)

        _separator_factory(abacus_toolbar)

        # TRANS: http://en.wikipedia.org/wiki/Abacus#Native_American_abaci
        self.mayan = _radio_factory('nepohualtzintzin', abacus_toolbar,
                                    self._radio_cb, cb_arg='mayan',
                                    tooltip=_('Nepohualtzintzin'),
                                    group=self.decimal)

        # TRANS: hexidecimal abacus
        self.hex = _radio_factory('hexadecimal', abacus_toolbar,
                                  self._radio_cb, cb_arg='hex',
                                  tooltip=_('Hexadecimal'),
                                  group=self.decimal)

        # TRANS: binary abacus
        self.binary = _radio_factory('binary', abacus_toolbar,
                                     self._radio_cb, cb_arg='binary',
                                     tooltip=_('Binary'),
                                     group=self.decimal)

        _separator_factory(abacus_toolbar)

        # TRANS: http://en.wikipedia.org/wiki/Abacus#Russian_abacus
        self.russian = _radio_factory('schety', abacus_toolbar,
                                      self._radio_cb, cb_arg='russian',
                                      tooltip=_('Schety'),
                                      group=self.decimal)

        # TRANS: abacus for adding fractions
        self.fraction = _radio_factory('fraction', abacus_toolbar,
                                       self._radio_cb, cb_arg='fraction',
                                       tooltip=_('Fraction'),
                                       group=self.decimal)

        # TRANS: Abacus invented by teachers in Caacupé, Paraguay
        self.caacupe = _radio_factory('caacupe', abacus_toolbar,
                                      self._radio_cb, cb_arg='caacupe',
                                      tooltip=_('Caacupé'),
                                      group=self.decimal)

        _separator_factory(abacus_toolbar)

        # TRANS: Cuisenaire Rods
        self.cuisenaire = _radio_factory('cuisenaire', abacus_toolbar,
                                         self._radio_cb,
                                         cb_arg='cuisenaire',
                                         tooltip=_('Rods'), group=self.decimal)

        # TRANS: Number of rods on the abacus
        self._rods_label = _label_factory(_('Rods:') + ' ', custom_toolbar)
        self._rods_spin = _spin_factory(15, 1, 20, self._rods_spin_cb,
                                        custom_toolbar)
        # TRANS: Number of beads in the top section of the abacus
        self._top_label = _label_factory(_('Top:') + ' ', custom_toolbar)
        self._top_spin = _spin_factory(2, 0, 4, self._top_spin_cb,
                                       custom_toolbar)
        # TRANS: Number of beads in the bottom section of the abacus
        self._bottom_label = _label_factory(_('Bottom:') + ' ',
                                            custom_toolbar)
        self._bottom_spin = _spin_factory(5, 1, 20, self._bottom_spin_cb,
                                          custom_toolbar)
        # TRANS: Scale factor between bottom and top beads
        self._value_label = _label_factory(_('Factor:') + ' ', custom_toolbar)
        self._value_spin = _spin_factory(5, 1, 20, self._value_spin_cb,
                                         custom_toolbar)
        # TRANS: Scale factor between rods
        self._base_label = _label_factory(_('Base:') + ' ', custom_toolbar)
        self._base_spin = _spin_factory(10, 1, 24, self._base_spin_cb,
                                        custom_toolbar)

        _separator_factory(custom_toolbar, False, False)

        self.custom = _button_factory('new-abacus', custom_toolbar,
                                      self._custom_cb,
                                      tooltip=_('Custom'))

        copy = _button_factory('edit-copy', edit_toolbar, self._copy_cb,
                               tooltip=_('Copy'), accelerator='<Ctrl>c')
        paste = _button_factory('edit-paste', edit_toolbar, self._paste_cb,
                                tooltip=_('Paste'), accelerator='<Ctrl>v')

        self.toolbox.show()

        if HAS_TOOLBARBOX:
            # start with abacus toolbar expanded
            abacus_toolbar_button.set_expanded(True)

        self.chinese.set_active(True)

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
        if 'rods' in self.metadata:
            self._rods_spin.set_value(int(self.metadata['rods']))
        if 'top' in self.metadata:
            self._top_spin.set_value(int(self.metadata['top']))
        if 'bottom' in self.metadata:
            self._bottom_spin.set_value(int(self.metadata['bottom']))
        if 'factor' in self.metadata:
            self._value_spin.set_value(int(self.metadata['factor']))
        if 'base' in self.metadata:
            self._base_spin.set_value(int(self.metadata['base']))
        if 'abacus' in self.metadata:
            # Default is Chinese
            _logger.debug('restoring %s', self.metadata['abacus'])
            if self.metadata['abacus'] == 'soroban':
                self._select_abacus('japanese')
                self.japanese.set_active(True)
            elif self.metadata['abacus'] == 'schety':
                self._select_abacus('russian')
                self.russian.set_active(True)
            elif self.metadata['abacus'] == 'nepohualtzintzin':
                self._select_abacus('mayan')
                self.mayan.set_active(True)
            elif self.metadata['abacus'] == 'binary':
                self._select_abacus('binary')
                self.binary.set_active(True)
            elif self.metadata['abacus'] == 'hexadecimal':
                self._select_abacus('hex')
                self.hex.set_active(True)
            elif self.metadata['abacus'] == 'fraction':
                self._select_abacus('fraction')
                self.fraction.set_active(True)
            elif self.metadata['abacus'] == 'caacupe':
                self._select_abacus('caacupe')
                self.caacupe.set_active(True)
            elif self.metadata['abacus'] == 'cuisenaire':
                self._select_abacus('cuisenaire')
                self.cuisenaire.set_active(True)
            elif self.metadata['abacus'] == 'decimal':
                self._select_abacus('decimal')
                self.decimal.set_active(True)
            elif self.metadata['abacus'] == 'custom':
                self._custom_cb()
            if 'value' in self.metadata:
                _logger.debug('restoring value %s', self.metadata['value'])
                self.abacus.mode.set_value(self.metadata['value'])
                self.abacus.mode.label(self.abacus.generate_label())

    def _radio_cb(self, button, abacus):
        self._select_abacus(abacus)

    def _reset_cb(self, button=None):
        self.abacus.mode.reset_abacus()
        self.abacus.mode.label(self.abacus.generate_label())

    def _select_abacus(self, abacus):
        ''' Display the selected abacus; hide the others '''
        if not hasattr(self, 'abacus'):
            return
        self.abacus.select_abacus(abacus)

    def _rods_spin_cb(self, button=None):
        return

    def _top_spin_cb(self, button=None):
        return

    def _bottom_spin_cb(self, button=None):
        return

    def _value_spin_cb(self, button=None):
        return

    def _base_spin_cb(self, button=None):
        return

    def _custom_cb(self, button=None):
        ''' Display the custom abacus; hide the others '''
        value = float(self.abacus.mode.value(count_beads=False))
        if self.abacus.custom is not None:
            self.abacus.custom.hide()
        self.abacus.custom = Custom(self.abacus,
                             self._rods_spin.get_value_as_int(),
                             self._top_spin.get_value_as_int(),
                             self._bottom_spin.get_value_as_int(),
                             self._value_spin.get_value_as_int(),
                             self._base_spin.get_value_as_int())
        self._select_abacus(self.abacus.custom)
        self.abacus.mode.reset_abacus()
        self.abacus.mode.set_value_from_number(value)
        self.abacus.mode.label(self.abacus.generate_label())

    def _copy_cb(self, arg=None):
        ''' Copy a number to the clipboard from the active abacus. '''
        clipBoard = gtk.Clipboard()
        text = self.abacus.generate_label(sum_only=True)
        if text is not None:
            clipBoard.set_text(text)
        return

    def _paste_cb(self, arg=None):
        ''' Paste a number from the clipboard to the active abacus. '''
        clipBoard = gtk.Clipboard()
        text = clipBoard.wait_for_text()
        if text is not None:
            try:
                self.abacus.mode.set_value_from_number(float(text))
            except ValueError, e:
                _logger.debug(str(e))
                return
            self.abacus.mode.label(self.abacus.generate_label())
        return

    def write_file(self, file_path):
        ''' Write the bead positions to the Journal '''
        _logger.debug('Saving current abacus to Journal: %s %s' % (
                       self.abacus.mode.name, self.abacus.mode.value(True)))
        self.metadata['abacus'] = self.abacus.mode.name
        self.metadata['value'] = self.abacus.mode.value(True)
        self.metadata['rods'] = str(self._rods_spin.get_value_as_int())
        self.metadata['top'] = str(self._top_spin.get_value_as_int())
        self.metadata['bottom'] = str(self._bottom_spin.get_value_as_int())
        self.metadata['factor'] = str(self._value_spin.get_value_as_int())
        self.metadata['base'] = str(self._base_spin.get_value_as_int())
