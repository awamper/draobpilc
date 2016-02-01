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

from gi import require_version
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

try:
    require_version('GtkSource', '3.0')
except ValueError:
    GTK_SOURCE_INSTALLED = False
else:
    from gi.repository import GtkSource
    GTK_SOURCE_INSTALLED = True

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets.items_processor_base import (
    ItemsProcessorBase,
    ItemsProcessorPriority
)

WRAP_MODE_LABEL = '<span fgcolor="grey" size="small"><b>%s</b></span>'
WRAP_MODE_LABEL = WRAP_MODE_LABEL % _('wrap text')


class Editor(ItemsProcessorBase):

    def __init__(self):
        super().__init__(
            _('Edit'),
            priority=ItemsProcessorPriority.NORMAL,
            default=True
        )

        self._timeout_id = 0

        self._wrap_mode_btn = Gtk.CheckButton.new_with_label('')
        self._wrap_mode_btn.set_halign(Gtk.Align.END)
        self._wrap_mode_btn.set_valign(Gtk.Align.START)
        self._wrap_mode_btn.set_hexpand(True)
        self._wrap_mode_btn.props.margin = ItemsProcessorBase.MARGIN
        self._wrap_mode_btn.set_active(common.SETTINGS[common.EDITOR_WRAP_TEXT])
        btn_children = self._wrap_mode_btn.get_children()
        if btn_children and isinstance(btn_children[0], Gtk.Label):
            btn_children[0].set_markup(WRAP_MODE_LABEL)
        self._wrap_mode_btn.connect(
            'toggled',
            lambda b: self._update_wrap_mode()
        )

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
        self._textview.props.buffer.connect('changed', self._on_text_changed)
        self._textview.show()

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_margin_bottom(ItemsProcessorBase.MARGIN)
        self._scrolled_window.set_margin_left(ItemsProcessorBase.MARGIN)
        self._scrolled_window.set_margin_right(ItemsProcessorBase.MARGIN)
        self._scrolled_window.add(self._textview)
        self._scrolled_window.set_no_show_all(True)
        self._scrolled_window.hide()

        self.grid.set_name('EditorGrid')
        self.grid.attach(self._wrap_mode_btn, 0, 0, 2, 1)
        self.grid.attach(self._scrolled_window, 0, 1, 2, 1)

        common.SETTINGS.connect(
           'changed::' + common.EDITOR_WRAP_TEXT,
           lambda s, k: self._wrap_mode_btn.set_active(s[k])
        )
        self._update_wrap_mode()

    def _update_wrap_mode(self):
        wrap = self._wrap_mode_btn.get_active()

        if wrap:
            common.SETTINGS[common.EDITOR_WRAP_TEXT] = wrap
            self._textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        else:
            common.SETTINGS[common.EDITOR_WRAP_TEXT] = wrap
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
        if not self.item: return GLib.SOURCE_REMOVE

        contents = self._textview.props.buffer.props.text

        if contents and contents != self.item.raw:
            gpaste_client.replace(self.item.index, contents)

        return GLib.SOURCE_REMOVE

    def clear(self):
        super().clear()

        self._textview.props.buffer.set_text('')
        self._textview.set_sensitive(False)

    def set_items(self, items):
        self.items = items
        self._textview.set_sensitive(True)

        self._scrolled_window.show()
        self._wrap_mode_btn.show()
        self._textview.props.buffer.set_text(self.item.raw)

        if self._lang_manager:
            lang = self._lang_manager.guess_language(
                None,
                self.item.raw
            )

            if lang:
                self._textview.props.buffer.set_language(lang)
                self._textview.set_monospace(True)
            else:
                self._textview.props.buffer.set_language(None)
                self._textview.set_monospace(False)

    def can_process(self, items):
        if (
            len(items) == 1 and (
                items[0].kind == gpaste_client.Kind.TEXT or
                items[0].kind == gpaste_client.Kind.LINK
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
