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

import json

from gi.repository import Gtk
from gi.repository import GObject

from draobpilc import common
from draobpilc.widgets.items_processor_base import (
    ItemsProcessorBase,
    ItemsProcessorPriority
)

COUNTER_LABEL_TPL = (
    '<span size="xx-large">%s</span>' % _('Merge <b>%i</b> items.')
)
COMBOBOX_NONE_STRING = 'Draobpilc.Merger.ComboBoxText.Id == None'


class Merger(ItemsProcessorBase):

    __gsignals__ = {
        'merge': (GObject.SIGNAL_RUN_FIRST, None, (object, bool))
    }

    def __init__(self):
        super().__init__(_('Merge'), ItemsProcessorPriority.HIGHEST)

        self._counter_label = Gtk.Label()
        self._counter_label.set_markup(COUNTER_LABEL_TPL % 0)
        self._counter_label.set_hexpand(True)
        self._counter_label.set_vexpand(False)
        self._counter_label.set_valign(Gtk.Align.CENTER)
        self._counter_label.set_halign(Gtk.Align.CENTER)

        self._decorator_label = Gtk.Label()
        self._decorator_label.props.margin = ItemsProcessorBase.MARGIN
        self._decorator_label.set_label(_('Decorator'))

        self._decorator_combo = Gtk.ComboBoxText.new_with_entry()
        self._decorator_combo.connect('changed', lambda c: self.update())
        self._decorator_combo.props.margin = ItemsProcessorBase.MARGIN

        self._separator_label = Gtk.Label()
        self._separator_label.props.margin = ItemsProcessorBase.MARGIN
        self._separator_label.set_label(_('Separator'))

        self._separator_combo = Gtk.ComboBoxText.new_with_entry()
        self._separator_combo.connect('changed', lambda c: self.update())
        self._separator_combo.props.margin = ItemsProcessorBase.MARGIN

        self._textview = Gtk.TextView()
        self._textview.set_name('MergerTextView')
        self._textview.set_vexpand(True)
        self._textview.set_hexpand(True)

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.props.margin = ItemsProcessorBase.MARGIN
        self._scrolled_window.add(self._textview)

        self._merge_btn = Gtk.Button()
        self._merge_btn.set_label(_('Merge'))
        self._merge_btn.connect(
            'clicked',
            lambda b: self.emit('merge', self.items, False)
        )

        self._merge_del_btn = Gtk.Button()
        self._merge_del_btn.set_label(_('Merge & Delete'))
        self._merge_del_btn.set_tooltip_text(
            _('Merge and delete merged items')
        )
        self._merge_del_btn.connect(
            'clicked',
            lambda b: self.emit('merge', self.items, True)
        )

        buttons_box = Gtk.ButtonBox()
        buttons_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        buttons_box.props.margin = ItemsProcessorBase.MARGIN
        buttons_box.add(self._merge_del_btn)
        buttons_box.add(self._merge_btn)

        self.grid.set_name('MergerBox')
        self.grid.attach(self._counter_label, 0, 1, 2, 1)
        self.grid.attach(self._decorator_label, 0, 2, 1, 1)
        self.grid.attach(self._decorator_combo, 0, 3, 1, 1)
        self.grid.attach(self._separator_label, 1, 2, 1, 1)
        self.grid.attach(self._separator_combo, 1, 3, 1, 1)
        self.grid.attach(self._scrolled_window, 0, 4, 2, 1)
        self.grid.attach(buttons_box, 0, 5, 2, 1)

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

    def _on_settings_changed(self, settings, key):
        if key == common.MERGE_DEFAULT_DECORATOR:
            combo = self._decorator_combo
        else:
            combo = self._separator_combo

        if not settings[key]:
            combo.set_active_id(COMBOBOX_NONE_STRING)
        else:
            combo.set_active_id(settings[key])

    def _update_merge_data(self):
        self._decorator_combo.remove_all()
        self._separator_combo.remove_all()

        decorators = json.loads(common.SETTINGS[common.MERGE_DECORATORS])
        decorators.append([_('None'), COMBOBOX_NONE_STRING])
        for decorator in decorators:
            self._decorator_combo.append(decorator[1], decorator[0])

        default_decorator = common.SETTINGS[common.MERGE_DEFAULT_DECORATOR]
        if not default_decorator:
            self._decorator_combo.set_active_id(COMBOBOX_NONE_STRING)
        else:
            self._decorator_combo.set_active_id(default_decorator)

        separators = json.loads(common.SETTINGS[common.MERGE_SEPARATORS])
        separators.append([_('None'), COMBOBOX_NONE_STRING])
        for separator in separators:
            self._separator_combo.append(separator[1], separator[0])

        default_separator = common.SETTINGS[common.MERGE_DEFAULT_SEPARATOR]
        if not default_separator:
            self._separator_combo.set_active_id(COMBOBOX_NONE_STRING)
        else:
            self._separator_combo.set_active_id(default_separator)

    def _get_merged_text(self):

        def get_decorator():
            decorator = self._decorator_combo.get_active_id()

            if decorator == COMBOBOX_NONE_STRING:
                decorator = ''
            elif not decorator:
                decorator = self._decorator_combo.get_active_text()

                try:
                    decorator = decorator.encode('utf8').decode('unicode-escape')
                except UnicodeDecodeError:
                    pass

            return decorator

        def get_separator():
            separator = self._separator_combo.get_active_id()

            if separator == COMBOBOX_NONE_STRING:
                separator = ''
            elif not separator:
                separator = self._separator_combo.get_active_text()

                try:
                    separator = separator.encode('utf8').decode('unicode-escape')
                except UnicodeDecodeError:
                    pass

            return separator

        result = ''

        for item in self.items:
            decorator = get_decorator()
            separator = get_separator()
            result += decorator + item.raw + decorator + separator

        return result

    def update(self):
        self._counter_label.set_markup(
            COUNTER_LABEL_TPL % len(self.items)
        )

        if len(self.items) < 2:
            self.buffer.set_text('')
        else:
            preview = self._get_merged_text()
            self.buffer.set_text(preview)

    def set_items(self, items):
        super().set_items(items)
        self.update()

    def clear(self):
        super().clear()
        self.update()

    def can_process(self, items):
        if len(items) > 1:
            return True
        else:
            return False

    @property
    def buffer(self):
        return self._textview.props.buffer
