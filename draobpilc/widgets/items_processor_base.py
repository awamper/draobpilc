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

from gi.repository import Gtk


class ItemsProcessorPriority():

    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4


class ItemsProcessorBase(Gtk.Bin):

    MARGIN = 10

    def __init__(self, title, priority=ItemsProcessorPriority.NORMAL, default=False):
        super().__init__()

        self.items = []
        self.priority = priority
        self.default = default

        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.title = title

        self.grid = Gtk.Grid()

        self.add(self.grid)
        self.show_all()

    def set_items(self, items):
        self.items = items

    def clear(self):
        self.items.clear()

    def can_process(self, items):
        return True
