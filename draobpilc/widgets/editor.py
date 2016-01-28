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

import os

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets.item_thumb import ItemThumb
from draobpilc.widgets.items_processor_base import ItemsProcessorBase

PREVIEW_TITLE = '<span fgcolor="grey" size="xx-large"><b>%s</b></span>'
PREVIEW_TITLE = PREVIEW_TITLE % _('Preview')
EDITOR_TITLE = '<span fgcolor="grey" size="xx-large"><b>%s</b></span>'
EDITOR_TITLE = EDITOR_TITLE % _('Editor')
WRAP_MODE_LABEL = '<span fgcolor="grey" size="small"><b>%s</b></span>'
WRAP_MODE_LABEL = WRAP_MODE_LABEL % _('"wrap text" is on')


class Editor(ItemsProcessorBase):

    def __init__(self):
        super().__init__()

        self.item = None
        self._timeout_id = 0

        self._wrap_mode_label = Gtk.Label()
        self._wrap_mode_label.set_markup(WRAP_MODE_LABEL)
        self._wrap_mode_label.set_margin_top(ItemsProcessorBase.MARGIN)
        self._wrap_mode_label.set_margin_bottom(ItemsProcessorBase.MARGIN)
        self._wrap_mode_label.set_margin_right(ItemsProcessorBase.MARGIN)
        self._wrap_mode_label.set_halign(Gtk.Align.END)
        self._wrap_mode_label.set_valign(Gtk.Align.CENTER)

        self._textview = Gtk.TextView()
        self._textview.set_name('EditorTextView')
        self._textview.set_vexpand(True)
        self._textview.set_hexpand(True)
        self._textview.set_can_default(False)
        self._textview.props.buffer.connect('changed', self._on_text_changed)
        self._textview.show()

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_margin_bottom(ItemsProcessorBase.MARGIN)
        self._scrolled_window.set_margin_left(ItemsProcessorBase.MARGIN)
        self._scrolled_window.set_margin_right(ItemsProcessorBase.MARGIN)
        self._scrolled_window.add(self._textview)
        self._scrolled_window.set_no_show_all(True)
        self._scrolled_window.hide()

        self._thumb = ItemThumb()
        self._thumb.set_vexpand(True)
        self._thumb.set_hexpand(True)
        self._thumb.set_valign(Gtk.Align.CENTER)
        self._thumb.set_halign(Gtk.Align.CENTER)
        self._thumb.props.margin = ItemsProcessorBase.MARGIN
        self._thumb.set_no_show_all(True)
        self._thumb.hide()

        self.grid.set_name('EditorGrid')
        self.grid.attach(self._wrap_mode_label, 1, 0, 1, 1)
        self.grid.attach(self._scrolled_window, 0, 1, 2, 1)
        self.grid.attach(self._thumb, 0, 2, 2, 1)

        self._update_wrap_mode()
        common.SETTINGS.connect(
            'changed::' + common.EDITOR_WRAP_TEXT,
            lambda s, p: self._update_wrap_mode()
        )

    def _update_wrap_mode(self):
        if common.SETTINGS[common.EDITOR_WRAP_TEXT]:
            self._wrap_mode_label.show()
            self._textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        else:
            self._wrap_mode_label.hide()
            self._textview.set_wrap_mode(Gtk.WrapMode.NONE)

    def _on_text_changed(self, buffer):
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0

        self._timeout_id = GLib.timeout_add(
            common.SETTINGS[common.EDIT_TIMEOUT_MS],
            self._edit_item
        )

    def _edit_item(self):
        self._timeout_id = 0

        if (
            self.item is None or
            self.item.kind == gpaste_client.Kind.FILE or
            self._preview_supported()
        ): return GLib.SOURCE_REMOVE

        contents = self._textview.props.buffer.props.text

        if contents and contents != self.item.raw:
            gpaste_client.replace(self.item.index, contents)

        return GLib.SOURCE_REMOVE

    def _is_previewable_type(self, content_type):
        if content_type.startswith('text'):
            return True
        else:
            return False

    def _preview_supported(self):
        if (
            not self.item or
            not os.path.exists(self.item.raw) or
            not common.SETTINGS[common.PREVIEW_TEXT_FILES] or
            not self.item.content_type or
            not self._is_previewable_type(self.item.content_type)
        ): return False

        return True

    def clear(self):
        super().clear()

        self.item = None
        self._textview.props.buffer.set_text('')
        self._textview.set_sensitive(False)
        self._thumb.clear()

    def set_items(self, history_item):
        if history_item is None:
            self.clear()
            return

        self.item = history_item
        self._textview.set_sensitive(True)

        if self.item.thumb_path and not self._preview_supported():
            allocation = self.get_allocation()
            self._thumb.set_filename(
                self.item.thumb_path,
                allocation.width * 0.8,
                allocation.height * 0.8
            )
            self.set_title(PREVIEW_TITLE, markup=True)
            self._scrolled_window.hide()
            self._wrap_mode_label.hide()
            self._thumb.show()
        else:
            self._thumb.hide()
            self._scrolled_window.show()
            self._update_wrap_mode()

        if not self._preview_supported():
            self._textview.props.buffer.set_text(self.item.raw)
        else:
            with open(self.item.raw, 'r') as fp:
                contents = fp.read()
                self._textview.props.buffer.set_text(contents)

        if (
            self.item.kind != gpaste_client.Kind.TEXT and
            self.item.kind != gpaste_client.Kind.LINK or
            self._preview_supported()
        ):
            self.set_title(PREVIEW_TITLE, markup=True)
            self._textview.set_editable(False)
        else:
            self.set_title(EDITOR_TITLE, markup=True)
            self._textview.set_editable(True)
