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


import gtk

from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.combobox import ComboBox
from sugar.graphics.toolcombobox import ToolComboBox


def combo_factory(combo_array, toolbar, callback, cb_arg=None,
                  tooltip=None, default=None):
    '''Factory for making a toolbar combo box'''
    combo = ComboBox()
    if tooltip is not None and hasattr(combo, 'set_tooltip_text'):
        combo.set_tooltip_text(tooltip)
    if cb_arg is not None:
        combo.connect('changed', callback, cb_arg)
    else:
        combo.connect('changed', callback)
    for i, selection in enumerate(combo_array):
        combo.append_item(i, selection, None)
    combo.show()
    toolitem = gtk.ToolItem()
    toolitem.add(combo)
    if hasattr(toolbar, 'insert'):  # the main toolbar
        toolbar.insert(toolitem, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(toolitem, -1)
    toolitem.show()
    if default is not None:
        combo.set_active(combo_array.index(default))
    return combo


def entry_factory(default_string, toolbar, tooltip=None, max=3):
    ''' Factory for adding a text box to a toolbar '''
    entry = gtk.Entry()
    entry.set_text(default_string)
    if tooltip is not None and hasattr(entry, 'set_tooltip_text'):
        entry.set_tooltip_text(tooltip)
    entry.set_width_chars(max)
    entry.show()
    toolitem = gtk.ToolItem()
    toolitem.add(entry)
    if hasattr(toolbar, 'insert'):  # the main toolbar
        toolbar.insert(toolitem, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(toolitem, -1)
    toolitem.show()
    return entry


def button_factory(icon_name, toolbar, callback, cb_arg=None, tooltip=None,
                   accelerator=None):
    '''Factory for making toolbar buttons'''
    button = ToolButton(icon_name)
    if tooltip is not None:
        button.set_tooltip(tooltip)
    button.props.sensitive = True
    if accelerator is not None:
        button.props.accelerator = accelerator
    if cb_arg is not None:
        button.connect('clicked', callback, cb_arg)
    else:
        button.connect('clicked', callback)
    if hasattr(toolbar, 'insert'):  # the main toolbar
        toolbar.insert(button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(button, -1)
    button.show()
    return button


def radio_factory(button_name, toolbar, callback, cb_arg=None, tooltip=None,
                  group=None):
    ''' Add a radio button to a toolbar '''
    button = RadioToolButton(group=group)
    button.set_named_icon(button_name)
    if callback is not None:
        if cb_arg is None:
            button.connect('clicked', callback)
        else:
            button.connect('clicked', callback, cb_arg)
    if hasattr(toolbar, 'insert'):  # Add button to the main toolbar...
        toolbar.insert(button, -1)
    else:  # ...or a secondary toolbar.
        toolbar.props.page.insert(button, -1)
    button.show()
    if tooltip is not None:
        button.set_tooltip(tooltip)
    return button


def label_factory(toolbar, label_text, width=None):
    ''' Factory for adding a label to a toolbar '''
    label = gtk.Label(label_text)
    label.set_line_wrap(True)
    if width is not None:
        label.set_size_request(width, -1)  # doesn't work on XOs
    label.show()
    toolitem = gtk.ToolItem()
    toolitem.add(label)
    toolbar.insert(toolitem, -1)
    toolitem.show()
    return label


def separator_factory(toolbar, expand=False, visible=True):
    ''' add a separator to a toolbar '''
    separator = gtk.SeparatorToolItem()
    separator.props.draw = visible
    separator.set_expand(expand)
    toolbar.insert(separator, -1)
    separator.show()


def image_factory(image, toolbar, tooltip=None):
    ''' Add an image to the toolbar '''
    img = gtk.Image()
    img.set_from_pixbuf(image)
    img_tool = gtk.ToolItem()
    img_tool.add(img)
    if tooltip is not None:
        img.set_tooltip_text(tooltip)
    toolbar.insert(img_tool, -1)
    img_tool.show()
    return img


def spin_factory(default, min, max, callback, toolbar):
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

