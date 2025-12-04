#!/usr/bin/env python3

# Copyright 2015-2025 Ivan awamper@gmail.com
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

from typing import Any, Iterator, List, Optional, Tuple, TYPE_CHECKING, Union

from gi.repository import GLib, GObject  # type: ignore

from draobpilc import common
from draobpilc.history_item import HistoryItem
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.lib import fuzzy, gpaste_client

if TYPE_CHECKING:
    _ = lambda s: s


class HistoryItems(GObject.Object):

    __gsignals__ = {
        'removed': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self) -> None:
        GObject.Object.__init__(self)

        self._items: List[HistoryItem] = []
        self._filter_result: List[HistoryItem] = []
        self._filter_mode: bool = False
        self._raw_history: List[Tuple[str, str]] = [] # List of (uuid, raw_content)

        self._signal_match: Any = gpaste_client.connect('Update', self._on_update)
        self.reload_history()

    def __len__(self) -> int:
        if self._filter_mode:
            result = min(
                len(self._filter_result),
                common.SETTINGS[common.MAX_FILTER_RESULTS]
            )
        else:
            result = len(self._items)

        return result

    def __iter__(self) -> Iterator[HistoryItem]:
        return iter(self.items)

    def __getitem__(self, key: Union[int, slice]) -> Union[HistoryItem, List[HistoryItem]]:
        return self.items[key]

    def _on_update(self, action: str, target: str, position: int) -> None:
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

    def _get_by_uuid(self, uuid: str) -> Optional[HistoryItem]:
        result: Optional[HistoryItem] = None

        for item in self._items:
            if item.uuid != uuid: continue
            result = item
            break

        return result

    def _sync_index(self) -> None:
        for item in self._items:
            # item.uuid and item.raw can be Optional
            if item.uuid is None or item.raw is None:
                continue
            try:
                # _raw_history contains (uuid, raw_content) tuples
                gpaste_index = self._raw_history.index((item.uuid, item.raw))
            except ValueError:
                pass
            else:
                if gpaste_index != item.index:
                    item.index = gpaste_index

    def get(self, index: int) -> Optional[HistoryItem]:
        result: Optional[HistoryItem] = None

        for item in self._items:
            if item.index != index: continue

            result = item
            break

        return result

    def reload_item(self, index: int) -> bool:
        item = self.get(index)
        if not item: return False

        # Ensure index is within bounds of _raw_history
        if not (0 <= index < len(self._raw_history)):
            return False

        new_uuid = self._raw_history[index][0]
        item.load_data(index, new_uuid)
        return True

    def remove(self, index: int) -> bool:
        item = self.get(index)
        if not item: return False

        self._items.remove(item)
        self._sync_index()
        self.emit('removed', item)
        self.emit('changed')
        return True

    def reload_history(self, emit_signal: bool = True) -> None:
        self.reset_filter(emit_signal=False)
        self._raw_history = gpaste_client.get_raw_history()

        if len(self._raw_history) == 0:
            self.clear()
            return None

        new_list: List[HistoryItem] = []
        new_items: List[HistoryItem] = []

        for index, raw in enumerate(self._raw_history):
            uuid = raw[0]
            old_item = self._get_by_uuid(uuid)

            if old_item:
                new_list.append(old_item)
            else: 
                new_item = HistoryItem(index, uuid)
                new_items.append(new_item)

        new_list.extend(new_items)
        self._sync_index()
        self._items = sorted(new_list, key=lambda e: e.index if e.index is not None else -1) # Handle Optional[int]
        if emit_signal: self.emit('changed')
        return None

    def clear(self) -> None:
        self._raw_history.clear()
        self._items.clear()
        self.reset_filter(emit_signal=False)
        self.emit('changed')

    def freeze(self, freeze: bool) -> None:
        if freeze:
            if not self._signal_match: return

            gpaste_client.disconnect(self._signal_match)
            self._signal_match = None
        else:
            self._signal_match = gpaste_client.connect(
                'Update',
                self._on_update
            )

    def filter(self, term: str = '', kinds: Optional[List[HistoryItemKind]] = None, index: Optional[int] = None) -> None:
        if not any([term, kinds, index]):
            self.reset_filter(emit_signal=True)
            return
        else:
            self.reset_filter(emit_signal=False)

        self._filter_mode = True
        self._filter_result.clear()

        for item in self._items:
            if index is not None and item.index == index:
                self._filter_result.append(item)
                break

            if kinds and (item.kind is None or item.kind not in kinds):
                continue

            if item.text is None:
                continue

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

        self._filter_result.sort(key=lambda e: e.sort_score if e.sort_score is not None else -1)
        self.emit('changed')

    def reset_filter(self, emit_signal: bool = True) -> None:
        if not self._filter_mode: return

        for filtered in self._filter_result:
            filtered.markup = None
            filtered.sort_score = None

        self._filter_result.clear()
        self._filter_mode = False
        if emit_signal: self.emit('changed')

    @property
    def items(self) -> List[HistoryItem]:
        if self._filter_mode:
            self._filter_result.sort(key=lambda e: e.sort_score if e.sort_score is not None else -1)
            return self._filter_result[:common.SETTINGS[common.MAX_FILTER_RESULTS]]
        else:
            self._items.sort(key=lambda e: e.index if e.index is not None else -1)
            return self._items
    
    @property
    def n_total(self) -> int:
        return len(self._items)
    
    @property
    def filter_mode(self) -> bool:
        return self._filter_mode
