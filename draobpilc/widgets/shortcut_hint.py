#!/usr/bin/env python3

# Copyright 2015-2025 Ivan awamper@gmail.com
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

from gi.repository import Gtk  # type: ignore


class ShortcutHint(Gtk.Box):
    label: Gtk.Label

    def __init__(self) -> None:
        super().__init__()

        self.set_name('HistoryItemViewShortcutHint')
        self.set_no_show_all(True)
        self.set_vexpand(False)
        self.set_hexpand(False)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.START)
        self.set_size_request(40, 40)

        self.label = Gtk.Label()
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_vexpand(False)
        self.label.set_hexpand(True)
        self.label.show()

        self.add(self.label)

    def set_hint(self, text: str) -> None:
        self.label.set_label(text)
