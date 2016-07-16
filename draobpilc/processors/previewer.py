#!/usr/bin/env python3

# Copyright 2016 Ivan awamper@gmail.com
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

import os

from gi.repository import Gtk
from gi.repository import Gio

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets.item_thumb import ItemThumb
from draobpilc.processors.processor_textwindow import TextWindow
from draobpilc.widgets.items_processor_base import (
    ItemsProcessorBase,
    ItemsProcessorPriority
)


class Previewer(ItemsProcessorBase):

    def __init__(self):
        super().__init__(_('Preview'), ItemsProcessorPriority.HIGH)

        self._thumb = ItemThumb()
        self._thumb.set_vexpand(True)
        self._thumb.set_hexpand(True)
        self._thumb.set_valign(Gtk.Align.CENTER)
        self._thumb.set_halign(Gtk.Align.CENTER)
        self._thumb.props.margin = ItemsProcessorBase.MARGIN
        self._thumb.set_no_show_all(True)
        self._thumb.hide()

        self._path_entry = Gtk.Entry()
        self._path_entry.set_editable(False)
        self._path_entry.set_hexpand(True)
        self._path_entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY,
            'system-file-manager-symbolic'
        )
        self._path_entry.set_tooltip_text(
            _('Click to locate the file on disk')
        )
        )
        self._path_entry.connect('icon-release', self._on_icon_release)
        self._path_entry.props.margin = ItemsProcessorBase.MARGIN

        self._text_window = TextWindow()
        self._text_window.set_no_show_all(True)
        self._text_window.textview.set_name('EditorTextView')
        self._text_window.textview.set_editable(False)
        self._text_window.hide()

        self.grid.set_name('PreviwerGrid')
        self.grid.attach(self._path_entry, 0, 0, 2, 1)
        self.grid.attach(self._thumb, 0, 1, 2, 1)
        self.grid.attach(self._text_window, 0, 1, 2, 1)

    def _on_icon_release(self, entry, icon_pos, event):
        if icon_pos != Gtk.EntryIconPosition.PRIMARY: return

        app_info = Gio.AppInfo.get_default_for_type('inode/directory', True)
        if not app_info: return
        app_info.launch_uris(['file://%s' % self._path_entry.get_text()], None)
        common.APPLICATION.hide()

    def _is_previewable_type(self, content_type):
        if (
            content_type and content_type.startswith('text') or
            'bash' in content_type
        ):
            return True
        else:
            return False

    def _preview_supported(self, item):
        if (
            item.kind == gpaste_client.Kind.FILE or
            item.kind == gpaste_client.Kind.IMAGE
        ):
            return True
        elif (
            not item or
            not os.path.exists(item.raw) or
            not common.SETTINGS[common.PREVIEW_TEXT_FILES] or
            not self._is_previewable_type(item.content_type)
        ):
            return False

        return True

    def clear(self):
        super().clear()

        self._path_entry.set_text('')
        self._text_window.buffer.set_text('')
        self._thumb.clear()

    def set_items(self, items):
        self.items = items
        self._path_entry.set_text(self.item.raw)
        exists = os.path.exists(self.item.raw)

        if (
            exists and
            self._preview_supported(self.item) and
            self._is_previewable_type(self.item.content_type)
        ):
            self._thumb.hide()
            self._text_window.show()
            self._path_entry.show()

            with open(self.item.raw, 'r') as fp:
                contents = fp.read()
                self._text_window.set_filename(self.item.raw)
                self._text_window.buffer.set_text(contents)
        elif self.item.thumb_path:
            allocation = self.get_allocation()
            self._thumb.set_filename(
                self.item.thumb_path,
                allocation.width * 0.8,
                allocation.height * 0.8
            )
            self._text_window.hide()
            self._thumb.show()
            self._path_entry.show()
        else:
            self._path_entry.hide()
            self._thumb.hide()

            self._text_window.show()
            self._text_window.buffer.set_text(self.item.raw)
            self._text_window.set_filename(None)

    def can_process(self, items):
        if (
            len(items) == 1 and (
                self._preview_supported(items[0]) or
                items[0].thumb_path
            )
        ):
            return True
        else:
            return False
