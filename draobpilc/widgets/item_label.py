#!/usr/bin/env python3

# Copyright 2025 Ivan awamper@gmail.com
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

from gi.repository import Gtk, Pango  # type: ignore

from draobpilc import common


class ItemLabel(Gtk.Label):

    def __init__(self) -> None:
        super().__init__()

        self.set_name('HistoryItemLabel')
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.CENTER)
        self.set_vexpand(True)
        self.set_ellipsize(Pango.EllipsizeMode.END)
        self.set_line_wrap(True)
        self.set_line_wrap_mode(Pango.WrapMode.CHAR)
        self.set_lines(common.SETTINGS[common.ITEM_MAX_LINES])
