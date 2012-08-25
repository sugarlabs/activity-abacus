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

from sugar.activity import activity
from sugar import profile
try:  # 0.86+ toolbar widgets
    from sugar.graphics.toolbarbox import ToolbarBox
    HAS_TOOLBARBOX = True
except ImportError:
    HAS_TOOLBARBOX = False
if HAS_TOOLBARBOX:
    from sugar.graphics.toolbarbox import ToolbarButton
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton
from sugar.datastore import datastore
from sugar.graphics.alert import NotifyAlert

from gettext import gettext as _
import locale

import logging
_logger = logging.getLogger('abacus-activity')

from abacus_window import Abacus, Custom, Suanpan, Soroban, Schety,\
                          Nepohualtzintzin, Binary, Hex, Decimal, Fractions,\
                          Caacupe, Cuisenaire, MAX_RODS, MAX_TOP, MAX_BOT
from toolbar_utils import separator_factory, radio_factory, label_factory, \
    button_factory, spin_factory


NAMES = {
    # TRANS: http://en.wikipedia.org/wiki/Soroban (Japanese abacus)
    'suanpan': _('Suanpan'),
    # TRANS: http://en.wikipedia.org/wiki/Suanpan (Chinese abacus)
    'soroban': _('Soroban'),
    'decimal': _('Decimal'),
    # TRANS: http://en.wikipedia.org/wiki/Abacus#Native_American_abaci)
    'nepohualtzintzin': _('Nepohualtzintzin'),
    'hexadecimal': _('Hexadecimal'),
    'binary': _('Binary'),
    # TRANS: http://en.wikipedia.org/wiki/Abacus#Russian_abacus
    'schety': _('Schety'),
    'fraction': _('Fraction'),
    # TRANS: Caacupé is an abacus invented by teachers in Caacupé, Paraguay
    'caacupe': _('Caacupé'),
    'cuisenaire': _('Rods'),
    'custom': _('Custom')
    }

class AbacusActivity(activity.Activity):

    def __init__(self, handle):
        ''' Initiate activity. '''
        super(AbacusActivity, self).__init__(handle)

        self._setting_up = True
        self.bead_colors = profile.get_color().to_string().split(',')

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

            separator_factory(toolbox.toolbar, False, True)

            button_factory('edit-clear', toolbox.toolbar,
                            self._reset_cb, tooltip=_('Reset'))

            separator_factory(toolbox.toolbar, False, True)

            self._label = label_factory(toolbox.toolbar, NAMES['suanpan'])

            separator_factory(toolbox.toolbar, True, False)

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

            toolbox.add_toolbar(_('Project'), abacus_toolbar)
            toolbox.add_toolbar(_('Custom'), custom_toolbar)
            toolbox.add_toolbar(_('Edit'), edit_toolbar)

            button_factory('edit-delete', edit_toolbar,
                            self._reset_cb, tooltip=_('Reset'))

            self._label = label_factory(edit_toolbar, NAMES['suanpan'])

            separator_factory(edit_toolbar, False, True)

            toolbox.set_current_toolbar(1)

            # no sharing
            if hasattr(toolbox, 'share'):
                toolbox.share.hide()
            elif hasattr(toolbox, 'props'):
                toolbox.props.visible = False

        self.decimal = radio_factory('decimal', abacus_toolbar,
                                     self._radio_cb, cb_arg='decimal',
                                     tooltip=NAMES['decimal'],
                                     group=None)

        self.japanese = radio_factory('soroban', abacus_toolbar,
                                      self._radio_cb, cb_arg='soroban',
                                      tooltip=_('Soroban'),
                                      group=self.decimal)

        self.chinese = radio_factory('suanpan', abacus_toolbar,
                                     self._radio_cb, cb_arg='suanpan',
                                     tooltip=NAMES['suanpan'],
                                     group=self.decimal)

        separator_factory(abacus_toolbar)

        self.mayan = radio_factory('nepohualtzintzin', abacus_toolbar,
                                   self._radio_cb, cb_arg='nepohualtzintzin',
                                   tooltip=NAMES['nepohualtzintzin'],
                                   group=self.decimal)

        self.hex = radio_factory('hexadecimal', abacus_toolbar,
                                 self._radio_cb, cb_arg='hexadecimal',
                                 tooltip=NAMES['hexadecimal'],
                                 group=self.decimal)

        self.binary = radio_factory('binary', abacus_toolbar,
                                    self._radio_cb, cb_arg='binary',
                                    tooltip=NAMES['binary'],
                                    group=self.decimal)

        separator_factory(abacus_toolbar)

        self.russian = radio_factory('schety', abacus_toolbar,
                                     self._radio_cb, cb_arg='schety',
                                     tooltip=NAMES['schety'],
                                     group=self.decimal)

        self.fraction = radio_factory('fraction', abacus_toolbar,
                                      self._radio_cb, cb_arg='fraction',
                                      tooltip=NAMES['fraction'],
                                      group=self.decimal)

        self.caacupe = radio_factory('caacupe', abacus_toolbar,
                                     self._radio_cb, cb_arg='caacupe',
                                     tooltip=NAMES['caacupe'],
                                     group=self.decimal)

        separator_factory(abacus_toolbar)

        self.cuisenaire = radio_factory('cuisenaire', abacus_toolbar,
                                        self._radio_cb,
                                        cb_arg='cuisenaire',
                                        tooltip=NAMES['cuisenaire'],
                                        group=self.decimal)

        separator_factory(abacus_toolbar)

        self.custom = radio_factory('custom', abacus_toolbar,
                                    self._radio_cb,
                                    cb_arg='custom',
                                    tooltip=_('Custom'), group=self.decimal)

        preferences_button = button_factory(
            'preferences-system', custom_toolbar, self._preferences_palette_cb,
            tooltip=_('Custom'))
                
        self._palette = preferences_button.get_palette()
        button_box = gtk.VBox()
        # TRANS: Number of rods on the abacus
        self._rods_spin = self._add_spinner_and_label(
            15, 1, MAX_RODS, _('Rods:'), self._rods_spin_cb, button_box)
        # TRANS: Number of beads in the top section of the abacus
        self._top_spin = self._add_spinner_and_label(
            2, 0, MAX_TOP, _('Top:'), self._top_spin_cb, button_box)
        # TRANS: Number of beads in the bottom section of the abacus
        self._bottom_spin = self._add_spinner_and_label(
            2, 0, MAX_BOT, _('Bottom:'), self._bottom_spin_cb, button_box)
        # TRANS: Scale factor between bottom and top beads
        self._value_spin = self._add_spinner_and_label(
            5, 1, MAX_BOT + 1, _('Factor:'), self._value_spin_cb, button_box)
        # TRANS: Scale factor between rods
        self._base_spin = self._add_spinner_and_label(
            10, 1, (MAX_TOP + 1) * MAX_BOT, _('Base:'), self._base_spin_cb,
            button_box)
        button_box.show_all()
        self._palette.set_content(button_box)

        self.custom_maker = button_factory('new-abacus', custom_toolbar,
                                           self._custom_cb,
                                           tooltip=_('Custom'))

        copy = button_factory('edit-copy', edit_toolbar, self._copy_cb,
                              tooltip=_('Copy'), accelerator='<Ctrl>c')
        paste = button_factory('edit-paste', edit_toolbar, self._paste_cb,
                               tooltip=_('Paste'), accelerator='<Ctrl>v')

        self.toolbox.show()

        '''
        if HAS_TOOLBARBOX:
            # start with abacus toolbar expanded
            abacus_toolbar_button.set_expanded(True)
        '''

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
        self._setting_up = False

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
                self._select_abacus('soroban')
                self.japanese.set_active(True)
            elif self.metadata['abacus'] == 'schety':
                self._select_abacus('schety')
                self.russian.set_active(True)
            elif self.metadata['abacus'] == 'nepohualtzintzin':
                self._select_abacus('nepohualtzintzin')
                self.mayan.set_active(True)
            elif self.metadata['abacus'] == 'binary':
                self._select_abacus('binary')
                self.binary.set_active(True)
            elif self.metadata['abacus'] == 'hexadecimal':
                self._select_abacus('hexadecimal')
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
                self._select_abacus('custom')
                self.custom.set_active(True)
            if 'value' in self.metadata:
                _logger.debug('restoring value %s', self.metadata['value'])
                self.abacus.mode.set_value(self.metadata['value'])
                self.abacus.mode.label(self.abacus.generate_label())

    def _preferences_palette_cb(self, button):
        if self._palette:
            if not self._palette.is_up():
                self._palette.popup(immediate=True,
                                    state=self._palette.SECONDARY)
            else:
                self._palette.popdown(immediate=True)
            return

    def _radio_cb(self, button, abacus):
        self._select_abacus(abacus)

    def _reset_cb(self, button=None):
        self.abacus.mode.reset_abacus()
        self.abacus.mode.label(self.abacus.generate_label())

    def _notify_new_abacus(self, prompt):
        ''' Loading a new abacus can be slooow, so alert the user. '''
        alert = NotifyAlert(3)
        alert.props.title = prompt
        alert.props.msg = _('A new abacus is loading.')

        def _notification_alert_response_cb(alert, response_id, self):
            self.remove_alert(alert)

        alert.connect('response', _notification_alert_response_cb, self)
        self.add_alert(alert)
        alert.show()

    def _select_abacus(self, abacus):
        ''' Display the selected abacus; hide the others '''
        if not hasattr(self, 'abacus'):
            return
        if self._setting_up:
            return
        if self.abacus.mode.name == abacus:
            return

        self._notify_new_abacus(NAMES[abacus])
        # Give the alert time to load
        gobject.timeout_add(100, self._switch_modes, abacus)

    def _switch_modes(self, abacus):
        # Save current value
        value = int(float(self.abacus.mode.value()))
        if abacus == 'custom':
            self._custom_cb()
            self.abacus.mode = self.abacus.custom
        else:
            self.abacus.select_abacus(abacus)
        # Load saved value
        self.abacus.mode.set_value_from_number(value)
        self.abacus.mode.label(self.abacus.generate_label())
        self._label.set_text(NAMES[abacus])

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
        self.abacus.mode.hide()
        if self.abacus.custom is not None:
            self.abacus.custom.hide()
        self.abacus.custom = Custom(self.abacus, self.abacus.bead_colors)
        self.abacus.custom.set_custom_parameters(
            rods=self._rods_spin.get_value_as_int(),
            top=self._top_spin.get_value_as_int(),
            bot=self._bottom_spin.get_value_as_int(),
            factor=self._value_spin.get_value_as_int(),
            base=self._base_spin.get_value_as_int())
        self.abacus.custom.create()
        self.abacus.custom.draw_rods_and_beads()
        self.abacus.custom.show()

        self._select_abacus('custom')

        # self.abacus.mode = self.abacus.custom
        self.custom.set_active(True)
        self._label.set_text(NAMES['custom'])

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

    def _add_spinner_and_label(self, default_value, min_value, max_value,
                               tooltip, cb, box):
        ''' Add a spinner and a label to a box '''
        spinner_and_label = gtk.HBox()
        spinner, item = spin_factory(default_value, min_value, max_value,
                                     cb, None)
        label = gtk.Label(tooltip)
        label.set_justify(gtk.JUSTIFY_LEFT)
        label.set_line_wrap(True)
        label.show()
        spinner_and_label.pack_start(label)
        label = gtk.Label(' ')
        label.show()
        spinner_and_label.pack_start(label)
        spinner_and_label.pack_start(item)
        box.pack_start(spinner_and_label, False, False, padding=5)
        spinner_and_label.show()
        return spinner
