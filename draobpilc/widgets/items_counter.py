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

from draobpilc.history_items import HistoryItems

LABEL_TEMPLATE = _('Total: <b>%i</b>')
LABEL_FILTER_TEMPLATE = _('Showing <b>%i</b> out of <b>%i</b> total')


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
        if isinstance(history_items, HistoryItems):
            self._history_items = history_items
            history_items.connect('changed', self.update)

    def update(self, history_items=None):
        if not self._history_items:
            self.set_markup(LABEL_TEMPLATE % 0)
            return

        shown = 0
        total = len(self._history_items)

        for item in self._history_items:
            if item.widget.get_mapped(): shown += 1

        if shown and shown < total:
            label = LABEL_FILTER_TEMPLATE % (shown, total)
        else:
            label = LABEL_TEMPLATE % total

        self.set_markup(label)
