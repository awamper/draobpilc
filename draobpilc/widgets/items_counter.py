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

LABEL_TEMPLATE = _('Total: %s')


class ItemsCounter(Gtk.Label):

    def __init__(self, history_items=None):
        super().__init__()

        self.set_vexpand(False)
        self.set_hexpand(False)

        self._history_items = None

        self.bind(history_items)
        self.show()
        self.update()

    def bind(self, history_items):
        if history_items:
            self._history_items = history_items
            history_items.connect('changed', self.update)

    def update(self, history_items=None):
        if self._history_items:
            label = LABEL_TEMPLATE % str(len(self._history_items))
            self.set_label(label)
        else:
            self.set_label(LABEL_TEMPLATE % '...')
