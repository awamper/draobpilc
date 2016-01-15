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
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject

from draobpilc import common
from draobpilc.lib import utils
from draobpilc.lib import fuzzy
from draobpilc.widgets.search_box import SearchBox
from draobpilc.widgets.history_switcher import HistorySwitcher
from draobpilc.widgets.items_counter import ItemsCounter

HIGHLIGHT_TEMPLATE = '<span bgcolor="yellow" fgcolor="black"><b>%s</b></span>'


class AlreadyBound(Exception):
    """ raise when ItemsView already bound to HistoryItems """


class ItemsView(Gtk.Box):

    __gsignals__ = {
        'item-activated': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'item-selected': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'item-entered': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'item-left': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self):
        super().__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.END)
        self.set_vexpand(True)
        self.set_hexpand(False)
        self.set_name('ItemsViewBox')
        self.connect('key-release-event', self._on_key_release)

        self._bound_history = None
        self._last_entered_item = None
        self._last_selected_index = None
        self._last_search_string = ''
        self._filter_mode = False
        self._show_index = None

        self._history_switcher = HistorySwitcher()
        self._items_counter = ItemsCounter()
        self.search_box = SearchBox()
        self.search_box.connect('search-changed', self.filter)
        self.search_box.connect('search-index', self.search_index)
        self.search_box.entry.connect('activate', self._on_entry_activated)

        placeholder = Gtk.Label()
        placeholder.set_markup(
            '<span font-size="xx-large">History is empty</span>'
        )
        placeholder.show()

        self._listbox = Gtk.ListBox()
        self._listbox.set_name('ItemsViewList')
        self._listbox.set_placeholder(placeholder)
        self._listbox.set_sort_func(self._sort_rows)
        self._listbox.set_filter_func(self._filter_row)
        self._listbox.connect('row-selected', self._on_row_selected)
        self._listbox.connect('row-activated', self._on_row_activated)
        self._listbox.connect('motion-notify-event', self._on_motion_event)
        self._listbox.connect('leave-notify-event', self._on_leave_event)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_name('ItemsViewScrolledWindow')
        scrolled.set_margin_top(10)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.add(self._listbox)

        bottom_box = Gtk.Box()
        bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        bottom_box.add(self._items_counter)
        bottom_box.add(self._history_switcher)

        box_margin = 10
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_margin_top(box_margin)
        box.set_margin_left(box_margin)
        box.set_margin_right(box_margin)
        box.add(self.search_box)
        box.add(scrolled)
        box.add(bottom_box)

        self.add(box)
        self.show_all()

    def __len__(self):
        return len(self._listbox.get_children())

    def _on_key_release(self, window, event):
        if self.search_box.entry.has_focus():
            return False

        char = chr(Gdk.keyval_to_unicode(event.keyval))
        if not char.isalpha():
            return False

        self.search_box.entry.grab_focus()
        self.search_box.entry.set_text(self.search_box.entry.get_text() + char)
        self.search_box.entry.set_position(-1)

        return True

    def _on_leave_event(self, listbox, event):
        if self._last_entered_item:
            self.emit('item-left', self._last_entered_item)
            self._last_entered_item = None

    def _on_motion_event(self, listbox, event):
        row = self._listbox.get_row_at_y(event.y)
        
        if row:
            item = row.get_child().item

            if not self._last_entered_item:
                self._last_entered_item = item
                self.emit('item-entered', item)
            elif self._last_entered_item != item:
                self.emit('item-left', self._last_entered_item)
                self.emit('item-entered', item)
                self._last_entered_item = item
        elif self._last_entered_item:
            self.emit('item-left', self._last_entered_item)
            self._last_entered_item = None

    def _on_row_selected(self, listbox, row):
        if row: self.emit('item-selected', row.get_child().item)

    def _on_row_activated(self, listbox, row):
        if row: self.emit('item-activated', row.get_child().item)

    def _on_entry_activated(self, entry):
        item = self.get_selected()
        if item: self.emit('item-activated', item[0])
        return True

    def _on_changed(self, history_items):
        self.clear()
        self.load_all()
        self._resume_selection()

    def _remove(self, history_items, item=None):
        self._save_selection()
        result = False
        if not item: return result

        row = self._get_row_for_item(item)
        if row:
            row.remove(row.get_child())
            row.destroy()
            result = True

        return result

    def _get_row_for_item(self, item):
        result = False

        for row in self._listbox.get_children():
            if row.get_child().item == item:
                result = row
                break

        return result

    def _sort_rows(self, row1, row2):
        def compare_index(index1, index2):
            result = 0

            if index1 < index2:
                result = -1
            elif index1 > index2:
                result = 1

            return result

        def compare_score(score1, score2):
            result = 0
            if score1 is None: score1 = 9999999
            if score2 is None: score2 = 9999999

            if score1 < score2:
                result = -1
            elif score1 > score2:
                result = 1

            return result

        item1 = row1.get_child().item
        item2 = row2.get_child().item

        result = compare_score(item1.sort_score, item2.sort_score)

        if not result:
            result = compare_index(item1.index, item2.index)

        return result

    def _filter_row(self, row):
        result = True
        search_string = self.search_box.entry.get_text()
        history_item = row.get_child().item

        if self._show_index:
            if history_item.index == self._show_index: return True
            else: return False

        if self._filter_mode and not row.get_mapped():
            return False

        if not search_string.strip():
            history_item.markup = None
            history_item.sort_score = None
            return result

        match = fuzzy.match(
            search_string,
            history_item.text,
            common.SETTINGS[common.FUZZY_SEARCH_MAX_DISTANCE]
        )

        if match:
            history_item.markup = match.get_highlighted(
                escape_func=GLib.markup_escape_text,
                highlight_template=HIGHLIGHT_TEMPLATE
            )
            history_item.sort_score = match.score
            result = True
        else:
            history_item.markup = None
            history_item.sort_score = None
            result = False

        return result

    def _save_selection(self):
        selected = self.get_selected()

        if not selected:
            self._last_selected_index = 0
            return None

        self._last_selected_index = selected[0].index

    def _resume_selection(self):
        if not self._last_selected_index: return

        if len(self._bound_history) == self._last_selected_index:
            self._last_selected_index -= 1

        children = self._listbox.get_children()

        for row in children:
            index = row.get_child().item.index

            if index == self._last_selected_index:
                self._listbox.select_row(row)
                # i'm sorry
                GLib.timeout_add(200, lambda *a, **ka: row.grab_focus())
                break

    def bind(self, history_items):
        if self._bound_history:
            raise AlreadyBound()

        self._bound_history = history_items
        self._bound_history.connect('changed', self._on_changed)
        self._bound_history.connect('removed', self._remove)
        self._items_counter.bind(self._bound_history)
        self._items_counter.update()

        self.load_all()

    def load_all(self):
        self.clear()

        for item in self._bound_history:
            self._listbox.add(item.widget)

        self._items_counter.update()
        self.show_all()

    def set_active_item(self):
        def on_clipboard(clipboard, text):
            first_row = self._listbox.get_children()[0]
            item = first_row.get_child().item
            if item.raw != text: return

            first_row.set_selectable(False)
            first_row.set_activatable(False)
            first_row.get_child().set_sensitive(False)

        if len(self) < 1: return

        for row in self._listbox.get_children():
            row.set_selectable(True)
            row.set_activatable(True)
            row.get_child().set_sensitive(True)

        clipboard = Gtk.Clipboard.get_default(Gdk.Display.get_default())
        text = clipboard.wait_for_text()
        on_clipboard(clipboard, text)

    def search_index(self, search_box, index):
        self._show_index = index
        self._listbox.invalidate_filter()

    def filter(self, search_box):
        self._show_index = None
        search_string = self.search_box.entry.get_text().strip()

        if len(search_string) > len(self._last_search_string):
            self._filter_mode = True
        else:
            self._filter_mode = False

        self._listbox.invalidate_filter()
        self._listbox.invalidate_sort()
        self.select_first(grab_focus=False)
        self.reset_scroll()
        
        if search_string:
            self._last_search_string = search_string
        else:
            self._last_search_string = ''

    def select_first(self, grab_focus=False):
        self.set_active_item()

        for row in self._listbox.get_children():
            if not row.get_selectable(): continue

            self._listbox.select_row(row)
            if grab_focus: row.grab_focus()
            break

    def get_selected(self):
        result = []
        rows = self._listbox.get_selected_rows()

        for row in rows:
            result.append(row.get_child().item)

        return result

    def clear(self):
        for row in self._listbox.get_children():
            child = row.get_child()
            if child: row.remove(child)
            row.destroy()

        self._items_counter.update()

    def reset_scroll(self):
        adjustment = self._listbox.get_adjustment()
        lower = adjustment.get_lower()
        adjustment.set_value(lower)

    @property
    def history_switcher(self):
        return self._history_switcher
    