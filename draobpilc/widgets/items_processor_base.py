#!/usr/bin/env python3

# Copyright 2016-2025 Ivan awamper@gmail.com
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

from __future__ import annotations

from typing import List, Optional

from gi.repository import Gtk  # type: ignore

from draobpilc.history_item import HistoryItem


class ItemsProcessorPriority():

    LOWEST: int = 0
    LOW: int = 1
    NORMAL: int = 2
    HIGH: int = 3
    HIGHEST: int = 4


class ItemsProcessorBase(Gtk.Bin):

    MARGIN: int = 10

    def __init__(self, title: str, priority: int = ItemsProcessorPriority.NORMAL, default: bool = False) -> None:
        super().__init__()
        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.title: str = title
        self.items: List[HistoryItem] = []
        self.priority: int = priority
        self.default: bool = default
        self.grid: Gtk.Grid = Gtk.Grid()

        self.add(self.grid)
        self.show_all()

    def set_items(self, items: List[HistoryItem]) -> None:
        self.items = items

    def clear(self) -> None:
        self.items.clear()

    def can_process(self, items: List[HistoryItem]) -> bool:
        result = True
        return result

    def reload(self) -> None:
        if self.items: self.set_items(self.items)

    @property
    def item(self) -> Optional[HistoryItem]:
        item = None

        try:
            item = self.items[0]
        except IndexError:
            pass

        return item

