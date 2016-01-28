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

from gi.repository import Gtk
from gi.repository import GLib

from draobpilc import common
from draobpilc.widgets.items_processor_base import ItemsProcessorBase


class ItemsProcessors(Gtk.Bin):

    def __init__(self):
        super().__init__()

        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.current = None
        self.grid = Gtk.Grid()

        self.add(self.grid)
        self.show_all()

    def __iter__(self):
        return iter(self.grid.get_children())

    def add_processor(self, processor):
        if not isinstance(processor, ItemsProcessorBase):
            raise ValueError(
                '"processor" must be instance of ItemsProcessorBase'
            )
        else:
            processor.hide()
            self.grid.attach(processor, 0, 0, 1, 1)

    def reveal(self, processor=None, reveal=False, animation=True, on_done=None):
        for child in self:
            if not processor:
                if not reveal: self.current = None
                child.reveal(reveal, animation=animation, on_done=on_done)
                continue

            if child != processor:
                child.reveal(not reveal, animation=animation, on_done=on_done)
            else:
                if reveal:
                    self.current = child
                else:
                    self.current = None

                child.reveal(reveal, animation=animation, on_done=on_done)
