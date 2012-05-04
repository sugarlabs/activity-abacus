# -*- coding: utf-8 -*-
# Copyright (c) 2011, Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA


from gi.repository import Gtk

from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.radiotoolbutton import RadioToolButton


def button_factory(icon_name, toolbar, callback, cb_arg=None, tooltip=None,
                    accelerator=None):
    ''' Factory for making toolbar buttons '''
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
    if hasattr(toolbar, 'insert'):  # the main toolbar
        toolbar.insert(button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(button, -1)
    button.show()
    return button


def radio_factory(icon_name, toolbar, callback, cb_arg=None,
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


def label_factory(label_text, toolbar):
    ''' Factory for adding a label to a toolbar '''
    label = Gtk.Label(label=label_text)
    label.set_line_wrap(True)
    label.show()
    toolitem = Gtk.ToolItem()
    toolitem.add(label)
    toolbar.insert(toolitem, -1)
    toolitem.show()
    return label


def spin_factory(default, min_value, max_value, callback, toolbar):
    ''' Factory for making toolbar value spinners '''
    spin_adj = Gtk.Adjustment(default, min_value, max_value, 1, 32, 0)
    spin = Gtk.SpinButton()
    spin.set_adjustment(spin_adj)
    spin.connect('value-changed', callback)
    spin.set_numeric(True)
    spin.show()
    toolitem = Gtk.ToolItem()
    toolitem.add(spin)
    if toolbar is not None:
        toolbar.insert(toolitem, -1)
        toolitem.show()
        return spin
    else:
        toolitem.show()
        return spin, toolitem


def separator_factory(toolbar, expand=False, visible=True):
    ''' Add a separator to a toolbar '''
    separator = Gtk.SeparatorToolItem()
    separator.props.draw = visible
    separator.set_expand(expand)
    toolbar.insert(separator, -1)
    separator.show()
