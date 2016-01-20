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

import re

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from draobpilc import common

ENTRY_PLACE_HOLDER = _('Filter items')
SEARCH_INDEX_RE = re.compile('^#([0-9]+)$')


class SearchBox(Gtk.Box):

    __gsignals__ = {
        'search-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'search-index': (GObject.SIGNAL_RUN_FIRST, None, (int,))
    }

    def __init__(self):
        super().__init__()

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_halign(Gtk.Align.FILL)
        self.entry.set_placeholder_text(ENTRY_PLACE_HOLDER)
        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY,
            'edit-find-symbolic'
        )

        self.spinner = Gtk.Spinner()
        self.spinner.set_halign(Gtk.Align.END)
        self.spinner.set_valign(Gtk.Align.CENTER)
        self.spinner.set_margin_right(10)

        overlay = Gtk.Overlay()
        overlay.add(self.entry)
        overlay.add_overlay(self.spinner)

        self.buffer.connect('notify::text', self._on_text_changed)

        self._timeout_id = 0

        self.add(overlay)
        self.show_all()

    def _on_text_changed(self, buffer, *a, **kw):
        def on_timeout():
            self._timeout_id = 0
            text = self.entry.get_text()
            match = SEARCH_INDEX_RE.findall(text)

            if match:
                self.emit('search-index', int(match[0]))
            else:
                self.emit('search-changed')

            return GLib.SOURCE_REMOVE

        if self._timeout_id != 0:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0

        search_timeout = common.SETTINGS[common.SEARCH_TIMEOUT]
        self._timeout_id = GLib.timeout_add(search_timeout, on_timeout)

    @property
    def buffer(self):
        return self.entry.props.buffer
    