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

from gi import require_version

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

try:
    require_version('GtkSource', '3.0')
except ValueError:
    GTKSOURCE_INSTALLED = False
    TextView = Gtk.TextView
else:
    from gi.repository import GtkSource
    GTKSOURCE_INSTALLED = True
    TextView = GtkSource.View

from draobpilc import common

WRAP_MODE_LABEL = '<span fgcolor="grey" size="small"><b>%s</b></span>'
WRAP_MODE_LABEL = WRAP_MODE_LABEL % _('wrap text')


class TextWindow(Gtk.Overlay):

    __gsignals__ = {
        'changed': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    MARGIN = 10

    def __init__(self):
        super().__init__()

        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.FILL)

        self._timeout_id = 0

        self.textview = TextView()
        self.textview.set_vexpand(True)
        self.textview.set_hexpand(True)
        self.textview.set_can_default(False)
        self.buffer.connect('changed', self._on_text_changed)

        if GTKSOURCE_INSTALLED:
            self.textview.set_show_line_numbers(True)
            self.lang_manager = GtkSource.LanguageManager.get_default()
            self.textview.set_monospace(False)
            self.buffer.set_language(None)
        else:
            self.lang_manager = None

        self._wrap_mode_btn = Gtk.CheckButton.new_with_label('')
        self._wrap_mode_btn.set_halign(Gtk.Align.END)
        self._wrap_mode_btn.set_valign(Gtk.Align.START)
        self._wrap_mode_btn.set_hexpand(True)
        self._wrap_mode_btn.set_margin_top(round(TextWindow.MARGIN / 2))
        self._wrap_mode_btn.set_active(common.SETTINGS[common.EDITOR_WRAP_TEXT])
        self._wrap_mode_btn.set_opacity(0.5)
        self._wrap_mode_btn.connect(
            'enter-notify-event',
            lambda b, e: b.set_opacity(1)
        )
        self._wrap_mode_btn.connect(
            'leave-notify-event',
            lambda b, e: b.set_opacity(0.5)
        )

        btn_children = self._wrap_mode_btn.get_children()
        if btn_children and isinstance(btn_children[0], Gtk.Label):
            btn_children[0].set_markup(WRAP_MODE_LABEL)
        self._wrap_mode_btn.connect(
            'toggled',
            lambda b: self._update_wrap_mode()
        )

        self.window = Gtk.ScrolledWindow()
        self.window.add(self.textview)
        self.window.set_margin_bottom(TextWindow.MARGIN)
        self.window.set_margin_left(TextWindow.MARGIN)
        self.window.set_margin_right(TextWindow.MARGIN)

        self.add(self.window)
        self.add_overlay(self._wrap_mode_btn)
        self.show_all()

        common.SETTINGS.connect(
            'changed::' + common.EDITOR_WRAP_TEXT,
            lambda s, k: self._wrap_mode_btn.set_active(s[k])
        )
        self._update_wrap_mode()

    def _on_text_changed(self, buffer):
        def on_timeout():
            self._timeout_id = 0
            self.emit('changed', buffer)
            return GLib.SOURCE_REMOVE

        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0

        self._timeout_id = GLib.timeout_add(
            common.SETTINGS[common.EDIT_TIMEOUT_MS],
            on_timeout
        )

    def _update_wrap_mode(self):
        wrap = self._wrap_mode_btn.get_active()

        if wrap:
            common.SETTINGS[common.EDITOR_WRAP_TEXT] = wrap
            self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        else:
            common.SETTINGS[common.EDITOR_WRAP_TEXT] = wrap
            self.textview.set_wrap_mode(Gtk.WrapMode.NONE)

    def set_filename(self, filename=None):
        if not self.lang_manager: return

        lang = self.lang_manager.guess_language(
            filename,
            self.buffer.props.text
        )

        if lang:
            self.buffer.set_language(lang)
            self.textview.set_monospace(True)
        else:
            self.buffer.set_language(None)
            self.textview.set_monospace(False)

    @property
    def buffer(self):
        return self.textview.props.buffer
