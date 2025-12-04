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

import json
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

from gi.repository import Gtk  # type: ignore
from gi.repository import GObject  # type: ignore

from draobpilc import common
from draobpilc.history_item import HistoryItem
from draobpilc.processors.processor_textwindow import TextWindow
from draobpilc.widgets.items_processor_base import (
    ItemsProcessorBase,
    ItemsProcessorPriority
)

if TYPE_CHECKING:
    _ = lambda s: s

COUNTER_LABEL_TPL: str = (
    '<span size="xx-large">%s</span>' % _('Merge <b>%i</b> items.')
)
COMBOBOX_NONE_STRING: str = 'Draobpilc.Merger.ComboBoxText.Id == None'


class Merger(ItemsProcessorBase):

    __gsignals__ = {
        'merge': (GObject.SIGNAL_RUN_FIRST, None, (object, bool)),
        'delete': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self) -> None:
        super().__init__(_('Merge'), ItemsProcessorPriority.HIGHEST)

        self._counter_label: Gtk.Label = Gtk.Label()
        self._counter_label.set_markup(COUNTER_LABEL_TPL % 0)
        self._counter_label.set_hexpand(True)
        self._counter_label.set_vexpand(False)
        self._counter_label.set_valign(Gtk.Align.CENTER)
        self._counter_label.set_halign(Gtk.Align.CENTER)

        self._decorator_label: Gtk.Label = Gtk.Label()
        self._decorator_label.props.margin = ItemsProcessorBase.MARGIN
        self._decorator_label.set_label(_('Decorator'))

        self._decorator_combo: Gtk.ComboBoxText = Gtk.ComboBoxText.new_with_entry()
        self._decorator_combo.connect('changed', lambda c: self.update())
        self._decorator_combo.props.margin = ItemsProcessorBase.MARGIN

        self._separator_label: Gtk.Label = Gtk.Label()
        self._separator_label.props.margin = ItemsProcessorBase.MARGIN
        self._separator_label.set_label(_('Separator'))

        self._separator_combo: Gtk.ComboBoxText = Gtk.ComboBoxText.new_with_entry()
        self._separator_combo.connect('changed', lambda c: self.update())
        self._separator_combo.props.margin = ItemsProcessorBase.MARGIN

        self._text_window: TextWindow = TextWindow()
        self._text_window.textview.set_name('MergerTextView')

        self._merge_btn: Gtk.Button = Gtk.Button()
        self._merge_btn.set_label(_('Merge'))
        self._merge_btn.connect(
            'clicked',
            lambda b: self.emit('merge', self.items, False)
        )

        self._merge_del_btn: Gtk.Button = Gtk.Button()
        self._merge_del_btn.set_label(_('Merge & Delete'))
        self._merge_del_btn.set_tooltip_text(
            _('Merge and delete merged items')
        )
        self._merge_del_btn.connect(
            'clicked',
            lambda b: self.emit('merge', self.items, True)
        )

        self._delete_btn: Gtk.Button = Gtk.Button()
        self._delete_btn.set_label(_('Delete'))
        self._delete_btn.set_tooltip_text(_('Delete selected items'))
        self._delete_btn.get_style_context().add_class('destructive-action')
        self._delete_btn.connect('clicked', lambda b: self.emit('delete', self.items))

        self._reverse_order_btn: Gtk.CheckButton = Gtk.CheckButton(_('Reverse order'))
        self._reverse_order_btn.props.margin = ItemsProcessorBase.MARGIN
        self._reverse_order_btn.set_active(False)
        self._reverse_order_btn.connect('toggled', lambda b: self.update())

        buttons_box: Gtk.ButtonBox = Gtk.ButtonBox()
        buttons_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        buttons_box.props.margin = ItemsProcessorBase.MARGIN
        buttons_box.add(self._merge_del_btn)
        buttons_box.add(self._merge_btn)
        buttons_box.add(self._delete_btn)

        self.grid.set_name('MergerBox')
        self.grid.attach(self._counter_label, 0, 1, 2, 1)
        self.grid.attach(self._decorator_label, 0, 2, 1, 1)
        self.grid.attach(self._decorator_combo, 0, 3, 1, 1)
        self.grid.attach(self._separator_label, 1, 2, 1, 1)
        self.grid.attach(self._separator_combo, 1, 3, 1, 1)
        self.grid.attach(self._text_window, 0, 4, 2, 1)
        self.grid.attach(self._reverse_order_btn, 0, 5, 2, 1)
        self.grid.attach(buttons_box, 0, 6, 2, 1)

        common.SETTINGS.connect(
            'changed::' + common.MERGE_DEFAULT_DECORATOR,
            self._on_settings_changed
        )
        common.SETTINGS.connect(
            'changed::' + common.MERGE_DEFAULT_SEPARATOR,
            self._on_settings_changed
        )
        common.SETTINGS.connect(
            'changed::' + common.MERGE_DECORATORS,
            lambda s, k: self._update_merge_data()
        )
        common.SETTINGS.connect(
            'changed::' + common.MERGE_SEPARATORS,
            lambda s, k: self._update_merge_data()
        )

        self._update_merge_data()

    def _on_settings_changed(self, settings: Any, key: str) -> None:
        if key == common.MERGE_DEFAULT_DECORATOR:
            combo = self._decorator_combo
        else:
            combo = self._separator_combo

        if not settings[key]:
            combo.set_active_id(COMBOBOX_NONE_STRING)
        else:
            combo.set_active_id(settings[key])

    def _update_merge_data(self) -> None:
        self._decorator_combo.remove_all()
        self._separator_combo.remove_all()

        decorators: List[List[str]] = json.loads(common.SETTINGS[common.MERGE_DECORATORS])
        decorators.append([_('None'), COMBOBOX_NONE_STRING])
        for decorator in decorators:
            self._decorator_combo.append(decorator[1], decorator[0])

        default_decorator: str = common.SETTINGS[common.MERGE_DEFAULT_DECORATOR]
        if not default_decorator:
            self._decorator_combo.set_active_id(COMBOBOX_NONE_STRING)
        else:
            self._decorator_combo.set_active_id(default_decorator)

        separators: List[List[str]] = json.loads(common.SETTINGS[common.MERGE_SEPARATORS])
        separators.append([_('None'), COMBOBOX_NONE_STRING])
        for separator in separators:
            self._separator_combo.append(separator[1], separator[0])

        default_separator: str = common.SETTINGS[common.MERGE_DEFAULT_SEPARATOR]
        if not default_separator:
            self._separator_combo.set_active_id(COMBOBOX_NONE_STRING)
        else:
            self._separator_combo.set_active_id(default_separator)

    def _get_merged_text(self) -> str:

        def get_decorator() -> str:
            decorator: Optional[str] = self._decorator_combo.get_active_id()

            if decorator == COMBOBOX_NONE_STRING:
                decorator = ''
            elif not decorator:
                decorator = self._decorator_combo.get_active_text()

                try:
                    decorator = decorator.encode('utf8').decode('unicode-escape')
                except UnicodeDecodeError:
                    pass

            return decorator if decorator else ''

        def get_separator() -> str:
            separator: Optional[str] = self._separator_combo.get_active_id()

            if separator == COMBOBOX_NONE_STRING:
                separator = ''
            elif not separator:
                separator = self._separator_combo.get_active_text()

                try:
                    separator = separator.encode('utf8').decode('unicode-escape')
                except UnicodeDecodeError:
                    pass

            return separator if separator else ''

        result: str = ''
        merge_items: List[HistoryItem] = self.items

        if self._reverse_order_btn.get_active():
            merge_items = list(reversed(merge_items))

        for i, item in enumerate(merge_items):
            decorator = get_decorator()
            separator = get_separator()
            if item.raw is not None:
                result += decorator + item.raw + decorator
            else:
                print(f"Merger: can't get contents of {item}")

            if i < len(merge_items) - 1: result += separator

        return result

    def update(self) -> None:
        self._counter_label.set_markup(
            COUNTER_LABEL_TPL % len(self.items)
        )

        if len(self.items) < 2:
            self.buffer.set_text('')
        else:
            preview = self._get_merged_text()
            self.buffer.set_text(preview)

    def set_items(self, items: List[HistoryItem]) -> None:
        super().set_items(items)
        self.update()

    def clear(self) -> None:
        super().clear()
        self._reverse_order_btn.set_active(False)
        self._update_merge_data()
        self.update()

    def can_process(self, items: List[HistoryItem]) -> bool:
        result = False
        if len(items) > 1:
            result = True
        
        return result

    @property
    def buffer(self) -> Gtk.TextBuffer:
        return self._text_window.textview.props.buffer
