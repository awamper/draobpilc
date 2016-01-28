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
from gi.repository import GObject

from draobpilc.lib import utils


class ItemsProcessorBase(Gtk.Bin):

    MARGIN = 10
    TRANSITION_DURATION = 300

    def __init__(self):
        super().__init__()

        self.items = []

        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self._label = Gtk.Label()
        self._label.props.margin = ItemsProcessorBase.MARGIN
        self._label.set_halign(Gtk.Align.START)
        self._label.set_valign(Gtk.Align.CENTER)

        self.grid = Gtk.Grid()
        self.grid.attach(self._label, 0, 0, 1, 1)

        self._revealer = Gtk.Revealer()
        self._revealer.set_reveal_child(False)
        self._revealer.set_transition_duration(
            ItemsProcessorBase.TRANSITION_DURATION
        )
        self._revealer.set_transition_type(
            Gtk.RevealerTransitionType.CROSSFADE
        )
        self._revealer.add(self.grid)

        self.add(self._revealer)
        self.show_all()

    def set_title(self, title, markup=False):
        if not title:
            self._label.set_text('')
        else:
            if markup: self._label.set_markup(title)
            else: self._label.set_text(title)

    def set_items(self, items):
        if not items:
            self.clear()
        else:
            self.items = items

    def clear(self):
        self.items.clear()

    def reveal(self, reveal, animation=True, on_done=None):
        def on_timeout():
            if not reveal: self.hide()
            if on_done: on_done(self)

        if self._revealer.get_reveal_child() == reveal: return

        if not animation:
            self._revealer.set_transition_duration(0)
        else:
            self._revealer.set_transition_duration(
                ItemsProcessorBase.TRANSITION_DURATION
            )

        if reveal: self.show()
        self._revealer.set_reveal_child(reveal)

        GLib.timeout_add(ItemsProcessorBase.TRANSITION_DURATION, on_timeout)
