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
from draobpilc.history_item_kind import HistoryItemKind

ENTRY_PLACE_HOLDER = _('Filter items (%s to focus)')
ENTRY_PLACE_HOLDER = ENTRY_PLACE_HOLDER % common.SETTINGS[common.FOCUS_SEARCH]
SEARCH_INDEX_RE = re.compile(r'^#([0-9]+)$')
FLAGS_RE = re.compile(r'^(.*?)\-([lfit]+)$')


class SearchBox(Gtk.Box):

    __gsignals__ = {
        'search-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'search-index': (GObject.SIGNAL_RUN_FIRST, None, (int,))
    }

    def __init__(self):
        super().__init__()

        self.set_name('SearchBox')
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.FILL)
        self.set_vexpand(False)
        self.set_hexpand(True)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_halign(Gtk.Align.FILL)
        self.entry.set_valign(Gtk.Align.START)
        self.entry.set_placeholder_text(ENTRY_PLACE_HOLDER)
        self.entry.connect(
            'icon-release',
            lambda *a, **kw: self.reset()
        )
        self.entry.set_tooltip_text(
            _('You can add "-{flags}" at the end to search for types.') +
            _('\n\tt - text\n\tl - links\n\tf - files\n\ti - images') +
            _('\n\nUse #{number} to filter by index number')
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
        self.flags = []

        self.add(overlay)
        self.show_all()
        self._update_icon()

    def _on_text_changed(self, buffer, *a, **kw):
        def on_timeout():
            self._update_flags()
            self._timeout_id = 0
            match = SEARCH_INDEX_RE.findall(self.search_text)

            if match:
                self.emit('search-index', int(match[0]))
            else:
                self.emit('search-changed')

            return GLib.SOURCE_REMOVE

        if self._timeout_id != 0:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0

        self._update_icon()
        search_timeout = common.SETTINGS[common.SEARCH_TIMEOUT]
        self._timeout_id = GLib.timeout_add(search_timeout, on_timeout)

    def _update_flags(self):
        flags = FLAGS_RE.findall(self.entry.get_text())
        self.flags.clear()

        if not flags: return
        else: flags = flags[0][1]

        if 'l' in flags: self.flags.append(HistoryItemKind.LINK)
        if 'f' in flags: self.flags.append(HistoryItemKind.FILE)
        if 'i' in flags: self.flags.append(HistoryItemKind.IMAGE)
        if 't' in flags: self.flags.append(HistoryItemKind.TEXT)

    def _update_icon(self):
        if self.entry.get_text():
            self.entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.PRIMARY,
                'edit-clear-symbolic'
            )
            self.entry.set_icon_activatable(
                Gtk.EntryIconPosition.PRIMARY,
                True
            )
        else:
            self.entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.PRIMARY,
                'edit-find-symbolic'
            )
            self.entry.set_icon_activatable(
                Gtk.EntryIconPosition.PRIMARY,
                False
            )

    def reset(self):
        self.entry.set_text('')

    @property
    def buffer(self):
        return self.entry.props.buffer

    @property
    def search_text(self):
        text = self.entry.get_text().strip()
        text = FLAGS_RE.sub(r'\1', text)
        return text
