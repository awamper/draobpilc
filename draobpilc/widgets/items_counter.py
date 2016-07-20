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

LABEL_TEMPLATE = _('<b>%i</b> items')
LABEL_FILTER_TEMPLATE = _('Showing <b>%i</b> out of <b>%i</b>')


class ItemsCounter(Gtk.Label):

    def __init__(self, list_box, history_items=None):
        super().__init__()

        self.set_vexpand(False)
        self.set_hexpand(False)

        self._list_box = None
        self._history_items = None

        self.bind(list_box)
        self.show()
        self.update()

    def set_history_items(self, items):
        self._history_items = items

    def bind(self, list_box):
        if isinstance(list_box, Gtk.ListBox):
            self._list_box = list_box
            list_box.connect('add', lambda _, __: self.update())
            list_box.connect('remove', lambda _, __: self.update())

    def update(self):
        if not self._list_box or not self._history_items:
            self.set_markup(LABEL_TEMPLATE % 0)
            return

        children = self._list_box.get_children()

        if (
            self._history_items.filter_mode or
            len(children) < self._history_items.n_total
        ):
            label = LABEL_FILTER_TEMPLATE % (
                len(children),
                self._history_items.n_total,
            )
        else:
            label = LABEL_TEMPLATE % self._history_items.n_total

        self.set_markup(label)
