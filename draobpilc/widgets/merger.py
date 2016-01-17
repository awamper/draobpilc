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
from draobpilc.lib import gpaste_client

MARGIN = 10
TRANSITION_DURATION = 300
MERGER_LABEL = (
    '<span fgcolor="grey" size="xx-large"><b>%s</b></span>' % _('Merger')
)
COUNTER_LABEL_TPL = (
    '<span size="xx-large">%s</span>' % _('Merge <b>%i</b> items.')
)


class Merger(Gtk.Revealer):

    __gsignals__ = {
        'merge': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self):
        super().__init__()

        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_reveal_child(False)
        self.set_transition_duration(TRANSITION_DURATION)
        self.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)

        self._history_items = []

        self._label = Gtk.Label()
        self._label.set_margin_top(MARGIN)
        self._label.set_margin_bottom(MARGIN)
        self._label.set_margin_left(MARGIN)
        self._label.set_halign(Gtk.Align.START)
        self._label.set_valign(Gtk.Align.CENTER)
        self._label.set_markup(MERGER_LABEL)

        self._counter_label = Gtk.Label()
        self._counter_label.set_markup(COUNTER_LABEL_TPL % 0)
        self._counter_label.set_hexpand(True)
        self._counter_label.set_vexpand(False)
        self._counter_label.set_valign(Gtk.Align.CENTER)
        self._counter_label.set_halign(Gtk.Align.CENTER)

        self._decorator_label = Gtk.Label()
        self._decorator_label.props.margin = MARGIN
        self._decorator_label.set_label(_('Decorator'))

        self._decorator_combo = Gtk.ComboBoxText.new_with_entry()
        self._decorator_combo.connect('changed', lambda c: self.update())
        self._decorator_combo.props.margin = MARGIN

        decorators = json.loads(common.SETTINGS[common.MERGE_DECORATORS])
        for decorator in decorators:
            self._decorator_combo.append(decorator[1], decorator[0])

        default_decorator = common.SETTINGS[common.MERGE_DEFAULT_DECORATOR]
        self._decorator_combo.set_active_id(default_decorator)

        self._separator_label = Gtk.Label()
        self._separator_label.props.margin = MARGIN
        self._separator_label.set_label(_('Separator'))

        self._separator_combo = Gtk.ComboBoxText.new_with_entry()
        self._separator_combo.connect('changed', lambda c: self.update())
        self._separator_combo.props.margin = MARGIN

        separators = json.loads(common.SETTINGS[common.MERGE_SEPARATORS])
        for separator in separators:
            self._separator_combo.append(separator[1], separator[0])

        default_separator = common.SETTINGS[common.MERGE_DEFAULT_SEPARATOR]
        self._separator_combo.set_active_id(default_separator)

        self._textview = Gtk.TextView()
        self._textview.set_name('MergerTextView')
        self._textview.set_vexpand(True)
        self._textview.set_hexpand(True)

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.props.margin = MARGIN
        self._scrolled_window.add(self._textview)

        self._merge_btn = Gtk.Button()
        self._merge_btn.set_label(_('Merge'))
        self._merge_btn.set_hexpand(True)
        self._merge_btn.props.margin = MARGIN
        self._merge_btn.connect('clicked',
            lambda b: self.emit('merge', self._history_items)
        )

        self._grid = Gtk.Grid()
        self._grid.set_name('MergerBox')
        self._grid.set_orientation(Gtk.Orientation.VERTICAL)
        self._grid.set_vexpand(True)
        self._grid.set_hexpand(True)
        self._grid.set_margin_bottom(MARGIN)
        self._grid.set_margin_left(MARGIN)
        self._grid.set_margin_right(MARGIN)
        self._grid.attach(self._label, 0, 0, 1, 1)
        self._grid.attach(self._counter_label, 0, 1, 2, 1)
        self._grid.attach(self._decorator_label, 0, 2, 1, 1)
        self._grid.attach(self._decorator_combo, 0, 3, 1, 1)
        self._grid.attach(self._separator_label, 1, 2, 1, 1)
        self._grid.attach(self._separator_combo, 1, 3, 1, 1)
        self._grid.attach(self._scrolled_window, 0, 4, 2, 1)
        self._grid.attach(self._merge_btn, 0, 5, 2, 1)

        self.add(self._grid)
        self.show_all()

    def _get_merged_text(self):
        result = ''

        for item in self._history_items:
            decorator = self._decorator_combo.get_active_id()
            if not decorator:
                decorator = self._decorator_combo.get_active_text()

            separator = self._separator_combo.get_active_id()
            if not separator:
                separator = self._separator_combo.get_active_text()

            result += decorator + item.raw + decorator + separator

        return result

    def update(self):
        if not self._history_items: return

        self._counter_label.set_markup(
            COUNTER_LABEL_TPL % len(self._history_items)
        )

        if len(self._history_items) < 2:
            self._merge_btn.set_sensitive(False)
            return

        self._merge_btn.set_sensitive(True)

        preview = self._get_merged_text()
        self.buffer.set_text(preview)

    def set_items(self, history_items):
        self.clear()
        self._history_items = history_items
        self.update()

    def clear(self):
        self._history_items.clear()
        self.update()

    def show(self):
        self.set_reveal_child(True)

    def hide(self, clear_after_transition=False):
        self.set_reveal_child(False)

    @property
    def buffer(self):
        return self._textview.props.buffer
