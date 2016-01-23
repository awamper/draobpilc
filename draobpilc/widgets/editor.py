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

import time

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets.item_thumb import ItemThumb

PREVIEW_LABEL = '<span fgcolor="grey" size="xx-large"><b>%s</b></span>' % _('Preview')
EDITOR_LABEL = '<span fgcolor="grey" size="xx-large"><b>%s</b></span>' % _('Editor')
WRAP_MODE_LABEL = '<span fgcolor="grey" size="small"><b>%s</b></span>' % _('"wrap text" is on')
MARGIN = 10
TRANSITION_DURATION = 300


class Editor(Gtk.Revealer):

    __gsignals__ = {
        'enter-notify': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'leave-notify': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    timeout_ms = GObject.property(
        type=int,
        default=common.SETTINGS[common.EDIT_TIMEOUT_MS]
    )

    def __init__(self):
        super().__init__()

        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_reveal_child(False)
        self.set_transition_duration(TRANSITION_DURATION)
        self.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)

        self.item = None
        self._timeout_id = 0
        common.SETTINGS.bind(
            common.EDIT_TIMEOUT_MS,
            self,
            'timeout_ms',
            Gio.SettingsBindFlags.DEFAULT
        )

        self._label = Gtk.Label()
        self._label.set_margin_top(MARGIN)
        self._label.set_margin_bottom(MARGIN)
        self._label.set_margin_left(MARGIN)
        self._label.set_halign(Gtk.Align.START)
        self._label.set_valign(Gtk.Align.CENTER)

        self._wrap_mode_label = Gtk.Label()
        self._wrap_mode_label.set_markup(WRAP_MODE_LABEL)
        self._wrap_mode_label.set_margin_top(MARGIN)
        self._wrap_mode_label.set_margin_bottom(MARGIN)
        self._wrap_mode_label.set_margin_right(MARGIN)
        self._wrap_mode_label.set_halign(Gtk.Align.END)
        self._wrap_mode_label.set_valign(Gtk.Align.CENTER)

        self._textview = Gtk.TextView()
        self._textview.set_name('EditorTextView')
        self._textview.set_vexpand(True)
        self._textview.set_hexpand(True)
        self._textview.set_can_default(False)
        self._textview.show()
        self._textview.props.buffer.connect('changed', self._on_text_changed)

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.connect('enter-notify-event', self._on_enter)
        self._scrolled_window.connect('leave-notify-event', self._on_leave)
        self._scrolled_window.set_margin_bottom(MARGIN)
        self._scrolled_window.set_margin_left(MARGIN)
        self._scrolled_window.set_margin_right(MARGIN)
        self._scrolled_window.add(self._textview)
        self._scrolled_window.set_no_show_all(True)
        self._scrolled_window.hide()

        self._thumb = ItemThumb()
        self._thumb.set_vexpand(True)
        self._thumb.set_hexpand(True)
        self._thumb.set_valign(Gtk.Align.CENTER)
        self._thumb.set_halign(Gtk.Align.CENTER)
        self._thumb.props.margin = MARGIN
        self._thumb.set_no_show_all(True)
        self._thumb.hide()

        self._grid = Gtk.Grid()
        self._grid.set_name('EditorGrid')
        self._grid.attach(self._label, 0, 0, 1, 1)
        self._grid.attach(self._wrap_mode_label, 1, 0, 1, 1)
        self._grid.attach(self._scrolled_window, 0, 1, 2, 1)
        self._grid.attach(self._thumb, 0, 2, 2, 1)

        self.add(self._grid)
        self.show_all()

        self._update_wrap_mode()
        common.SETTINGS.connect(
            'changed::' + common.EDITOR_WRAP_TEXT,
            lambda s, p: self._update_wrap_mode()
        )

    def _on_enter(self, sender, event):
        self.emit('enter-notify', event)

    def _on_leave(self, sender, event):
        self.emit('leave-notify', event)

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
            self.props.timeout_ms,
            self._edit_item
        )

    def _edit_item(self):
        self._timeout_id = 0
        if self.item is None: return GLib.SOURCE_REMOVE

        contents = self._textview.props.buffer.props.text

        if contents and contents != self.item.raw:
            gpaste_client.replace(self.item.index, contents)

        return GLib.SOURCE_REMOVE

    def _remove_item(self):
        self.item = None
        self._textview.props.buffer.set_text('')
        self._thumb.clear()

    def set_item(self, history_item):
        if history_item is None:
            self._remove_item()
            return

        self.item = history_item

        if self.item.thumb_path:
            allocation = self.get_allocation()
            self._thumb.set_filename(
                self.item.thumb_path,
                allocation.width * 0.8,
                allocation.height * 0.8
            )
            self._label.set_markup(PREVIEW_LABEL)
            self._scrolled_window.hide()
            self._wrap_mode_label.hide()
            self._thumb.show()
        else:
            self._thumb.hide()
            self._scrolled_window.show()
            self._update_wrap_mode()

        self._textview.props.buffer.set_text(self.item.raw)

        if (
            self.item.kind != gpaste_client.Kind.TEXT and
            self.item.kind != gpaste_client.Kind.LINK
        ):
            self._label.set_markup(PREVIEW_LABEL)
            self._textview.set_editable(False)
        else:
            self._label.set_markup(EDITOR_LABEL)
            self._textview.set_editable(True)

    def clear(self):
        self.set_item(None)

    def reveal(self, reveal, clear_after_transition=False):
        def on_timeout():
            if not reveal: self.hide()
            if clear_after_transition: self.clear()

        if reveal: self.show()
        self.set_reveal_child(reveal)
        GLib.timeout_add(TRANSITION_DURATION, on_timeout)
