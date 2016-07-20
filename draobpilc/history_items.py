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

from gi.repository import GLib

from draobpilc import common
from draobpilc.lib import fuzzy
from draobpilc.lib import gpaste_client
from draobpilc.lib.signals import Emitter
from draobpilc.history_item import HistoryItem


class HistoryItems(Emitter):

    def __init__(self):
        super().__init__()

        self._items = []
        self._filter_result = []
        self._filter_mode = False
        self._raw_history = []

        self.add_signal('removed')
        self.add_signal('changed')

        self._signal_match = gpaste_client.connect('Update', self._on_update)
        self.reload_history()

    def __len__(self):
        if self._filter_mode:
            result = min(
                len(self._filter_result),
                common.SETTINGS[common.MAX_FILTER_RESULTS]
            )
        else:
            result = len(self._items)

        return result

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, key):
        return self.items[key]

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

        for item in self.items:
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

        self.items.remove(item)
        self._sync_index()
        self.emit('removed', item=item)
        self.emit('changed')

    def reload_history(self, emit_signal=True):
        self.reset_filter(emit_signal=False)
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
        self._sync_index()
        self._items = sorted(new_list, key=lambda e: e.index)
        if emit_signal: self.emit('changed')

    def clear(self):
        self._raw_history.clear()
        self._items.clear()
        self.reset_filter(emit_signal=False)
        self.emit('changed')

    def freeze(self, freeze):
        if freeze:
            if not self._signal_match: return

            gpaste_client.disconnect(self._signal_match)
            self._signal_match = None
        else:
            self._signal_match = gpaste_client.connect(
                'Update',
                self._on_update
            )

    def filter(self, term='', kinds=None, index=None):
        if not any([term, kinds, index]):
            self.reset_filter(emit_signal=True)
            return
        else:
            self.reset_filter(emit_signal=False)

        self._filter_mode = True

        for item in self._items:
            if index and item.index == index:
                self._filter_result.append(item)
                break

            if kinds and item.kind not in kinds: continue

            match = fuzzy.match(
                term,
                item.text,
                common.SETTINGS[common.FUZZY_SEARCH_MAX_DISTANCE]
            )

            if match:
                item.markup = match.get_highlighted(
                    escape_func=GLib.markup_escape_text,
                    highlight_template=HistoryItem.FILTER_HIGHLIGHT_TPL
                )
                item.sort_score = match.score
                self._filter_result.append(item)
            else:
                item.markup = None
                item.sort_score = None

        self._filter_result.sort(key=lambda e: e.sort_score)
        self.emit('changed')

    def reset_filter(self, emit_signal=True):
        if not self._filter_mode: return

        for filtered in self._filter_result:
            filtered.markup = None
            filtered.sort_score = None

        self._filter_result.clear()
        self._filter_mode = False
        if emit_signal: self.emit('changed')

    @property
    def items(self):
        if self._filter_mode:
            self._filter_result.sort(key=lambda e: e.sort_score)
            return self._filter_result[:common.SETTINGS[common.MAX_FILTER_RESULTS]]
        else:
            self._items.sort(key=lambda e: e.index)
            return self._items
    
    @property
    def n_total(self):
        return len(self._items)
    
    @property
    def filter_mode(self):
        return self._filter_mode
