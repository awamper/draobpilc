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

from gi import require_version
from gi.repository import Gtk

try:
    require_version('GtkSource', '3.0')
except ValueError:
    GTK_SOURCE_INSTALLED = False
else:
    from gi.repository import GtkSource
    GTK_SOURCE_INSTALLED = True

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets.item_thumb import ItemThumb
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
        self._path_entry.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY,
            False
        )
        self._path_entry.props.margin = ItemsProcessorBase.MARGIN

        if GTK_SOURCE_INSTALLED:
            self._textview = GtkSource.View()
            self._textview.set_show_line_numbers(True)
            self._lang_manager = GtkSource.LanguageManager.get_default()
        else:
            self._textview = Gtk.TextView()
            self._lang_manager = None

        self._textview.set_name('EditorTextView')
        self._textview.set_vexpand(True)
        self._textview.set_hexpand(True)
        self._textview.set_can_default(False)
        self._textview.set_editable(False)
        self._textview.show()

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_margin_bottom(ItemsProcessorBase.MARGIN)
        self._scrolled_window.set_margin_left(ItemsProcessorBase.MARGIN)
        self._scrolled_window.set_margin_right(ItemsProcessorBase.MARGIN)
        self._scrolled_window.add(self._textview)
        self._scrolled_window.set_no_show_all(True)
        self._scrolled_window.hide()

        self.grid.set_name('PreviwerGrid')
        self.grid.attach(self._path_entry, 0, 0, 2, 1)
        self.grid.attach(self._thumb, 0, 1, 2, 1)
        self.grid.attach(self._scrolled_window, 0, 1, 2, 1)

    def _is_previewable_type(self, content_type):
        if content_type and content_type.startswith('text'):
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
        self._textview.props.buffer.set_text('')
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
            self._scrolled_window.show()
            self._path_entry.show()

            lang = None

            with open(self.item.raw, 'r') as fp:
                contents = fp.read()

                if self._lang_manager:
                    lang = self._lang_manager.guess_language(
                        self.item.raw,
                        contents
                    )
                self._textview.props.buffer.set_text(contents)

            if lang:
                self._textview.props.buffer.set_language(lang)
                self._textview.set_monospace(True)
            else:
                self._textview.props.buffer.set_language(None)
                self._textview.set_monospace(False)
        elif self.item.thumb_path:
            allocation = self.get_allocation()
            self._thumb.set_filename(
                self.item.thumb_path,
                allocation.width * 0.8,
                allocation.height * 0.8
            )
            self._scrolled_window.hide()
            self._thumb.show()
            self._path_entry.show()
        else:
            self._path_entry.hide()
            self._thumb.hide()

            self._scrolled_window.show()
            self._textview.props.buffer.set_text(self.item.raw)
            self._textview.props.buffer.set_language(None)
            self._textview.set_monospace(False)

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

    @property
    def item(self):
        item = None

        try:
            item = self.items[0]
        except IndexError:
            pass

        return item
