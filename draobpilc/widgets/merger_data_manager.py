#!/usr/bin/env python3

# Copyright 2015 Ivan awamper@gmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

from gi.repository import Gtk

from draobpilc import common

ITEM_MARGIN = 5
FRAME_MARGIN = 10


class MergerDataItem(Gtk.Box):

    def __init__(self, name, value, escape=True):
        super().__init__()

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)

        if escape:
            try:
                name = name.encode('unicode_escape').decode('utf8')
            except UnicodeDecodeError:
                pass

            try:
                value = value.encode('unicode_escape').decode('utf8')
            except UnicodeDecodeError:
                pass

        self.name_entry = Gtk.Entry()
        self.name_entry.props.margin = ITEM_MARGIN
        self.name_entry.set_text(name)

        self.value_entry = Gtk.Entry()
        self.value_entry.props.margin = ITEM_MARGIN
        self.value_entry.set_text(value)

        self.delete_btn = Gtk.Button.new_from_icon_name(
            'edit-delete-symbolic',
            Gtk.IconSize.SMALL_TOOLBAR
        )
        self.delete_btn.props.margin = ITEM_MARGIN

        self.add(self.name_entry)
        self.add(self.value_entry)
        self.add(self.delete_btn)

        self.show_all()


class MergerDataManager(Gtk.Dialog):

    def __init__(self, label, key, transient_for=None):
        super().__init__()

        self.set_title(label)
        self.set_transient_for(transient_for)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_destroy_with_parent(True)
        self.set_modal(True)

        if transient_for:
            self.set_transient_for(transient_for)
            toplevel = self.get_toplevel()

            if toplevel:
                width, height = transient_for.get_size()
                height = round(height * 0.7)
                toplevel.set_size_request(width, height)

        self._key = key

        self._name_entry = Gtk.Entry()
        self._name_entry.set_placeholder_text(_('Name'))
        self._name_entry.props.margin = ITEM_MARGIN
        self._name_entry.connect('activate', self._add_new)

        self._value_entry = Gtk.Entry()
        self._value_entry.set_placeholder_text(_('Value'))
        self._value_entry.props.margin = ITEM_MARGIN
        self._value_entry.connect('activate', self._add_new)

        self._add_btn = Gtk.Button.new_from_icon_name(
            'list-add-symbolic',
            Gtk.IconSize.SMALL_TOOLBAR
        )
        self._add_btn.props.margin = ITEM_MARGIN
        self._add_btn.connect('clicked', self._add_new)

        self._grid = Gtk.Grid()
        self._grid.attach(self._name_entry, 0, 0, 1, 1)
        self._grid.attach(self._value_entry, 1, 0, 1, 1)
        self._grid.attach(self._add_btn, 2, 0, 1, 1)
        self._grid.set_halign(Gtk.Align.CENTER)

        frame = Gtk.Frame()
        frame.set_label(_('Add new (name, value)'))
        frame.add(self._grid)
        frame.props.margin = FRAME_MARGIN

        self._items_box = Gtk.Box()
        self._items_box.set_orientation(Gtk.Orientation.VERTICAL)
        self._items_box.set_hexpand(True)
        self._items_box.set_vexpand(True)
        self._items_box.set_halign(Gtk.Align.CENTER)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_valign(Gtk.Align.FILL)
        scrolled_window.set_halign(Gtk.Align.FILL)
        scrolled_window.add(self._items_box)

        items_frame = Gtk.Frame()
        items_frame.set_label(_('Edit'))
        items_frame.add(scrolled_window)
        items_frame.props.margin = FRAME_MARGIN

        content_area = self.get_content_area()
        content_area.add(frame)
        content_area.add(items_frame)
        content_area.show_all()

        self._update()

    def _update(self):
        items = sorted(json.loads(common.SETTINGS[self._key]))

        for name, value in items:
            self._add_item(name, value)

    def _add_new(self, button):
        name = self._name_entry.get_text()
        value = self._value_entry.get_text()
        self._add_item(name, value, False)
        self._save_changes()

        self._name_entry.set_text('')
        self._value_entry.set_text('')
        self._name_entry.grab_focus()

    def _add_item(self, name, value, escape=True):
        name = name.strip()
        if not name: return False

        item = MergerDataItem(name, value, escape)
        item.name_entry.props.buffer.connect(
            'notify::text',
            self._save_changes
        )
        item.value_entry.props.buffer.connect(
            'notify::text',
            self._save_changes
        )
        item.delete_btn.connect(
            'clicked',
            self._delete_item,
            item
        )
        self._items_box.add(item)

        return True

    def _delete_item(self, button, item):
        item.destroy()
        self._save_changes()

    def _save_changes(self, *args, **kwargs):
        items = []

        for item in self._items_box.get_children():
            name = item.name_entry.get_text()
            try:
                name = name.encode('utf8').decode('unicode-escape')
            except UnicodeDecodeError:
                pass

            value = item.value_entry.get_text()
            try:
                value = value.encode('utf8').decode('unicode-escape')
            except UnicodeDecodeError:
                pass

            if not name or not value: continue

            items.append([name, value])

        json_string = json.dumps(items)
        common.SETTINGS[self._key] = json_string
