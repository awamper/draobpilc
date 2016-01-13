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

from draobpilc.history_item import HistoryItem
from draobpilc.lib import gpaste_client
from draobpilc.lib.signals import Emitter


class HistoryItems(Emitter):

    def __init__(self):
        super().__init__()

        self._items = []
        self._raw_history = []

        self.add_signal('removed')
        self.add_signal('changed')

        gpaste_client.connect('Update', self._on_update)
        self.reload_history()

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def _on_update(self, action, target, position):
        self._raw_history = gpaste_client.get_raw_history()

        if action == gpaste_client.Action.REPLACE:
            if target == gpaste_client.Target.ALL:
                self.reload_history()
            elif target == gpaste_client.Target.POSITION:
                self.reload_item(position)
            else:
                pass
        elif action == gpaste_client.Action.REMOVE:
            if target == gpaste_client.Target.ALL:
                self.clear()
            elif target == gpaste_client.Target.POSITION:
                self.remove(position)
        else:
            pass

    def _get_by_raw(self, raw):
        result = None

        for item in self._items:
            if item.raw != raw: continue
            result = item
            break

        return result

    def _sync_index(self):
        for item in self._items:
            try:
                gpaste_index = self._raw_history.index(item.raw)
            except ValueError:
                pass
            else:
                if gpaste_index != item.index:
                    item.index = gpaste_index

    def get(self, index):
        result = None

        for item in self._items:
            if item.index != index: continue

            result = item
            break

        return result

    def reload_item(self, index):
        item = self.get(index)
        if not item: return False

        item.load_data(index)
        return True

    def remove(self, index):
        item = self.get(index)
        if not item: return False

        self._items.remove(item)
        self._sync_index()
        self.emit('removed', item=item)
        self.emit('changed')

    def reload_history(self):
        self._raw_history = gpaste_client.get_raw_history()

        if len(self._raw_history) == 0:
            self.clear()
            return None

        new_list = []
        new_items = []

        for index, raw in enumerate(self._raw_history):
            old_item = self._get_by_raw(raw)

            if old_item:
                new_list.append(old_item)
            else: 
                new_item = HistoryItem(index)
                new_items.append(new_item)

        new_list.extend(new_items)
        self._items = new_list
        self._sync_index()
        self.emit('changed')

    def clear(self):
        self._raw_history.clear()
        self._items.clear()
        self.emit('changed')
