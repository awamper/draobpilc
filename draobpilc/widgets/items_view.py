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
from draobpilc.widgets.histories_manager import HistoriesManager
from draobpilc.widgets.items_counter import ItemsCounter

HIGHLIGHT_TEMPLATE = '<span bgcolor="yellow" fgcolor="black"><b>%s</b></span>'


class AlreadyBound(Exception):
    """ raise when ItemsView already bound to HistoryItems """


class ItemsView(Gtk.Box):

    AUTOSCROLL_BORDER_OFFSET = 100
    AUTOSCROLL_TIMEOUT_MS = 50
    AUTOSCROLL_STEP = 10

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

        self._bound_history = None
        self._last_entered_item = None
        self._last_selected_index = None
        self._last_search_string = ''
        self._filter_mode = False
        self._show_index = None
        self._autoscroll_timeout_id = 0

        self._histories_manager = HistoriesManager()
        self._items_counter = ItemsCounter()
        self.search_box = SearchBox()
        self.search_box.connect('search-changed', self.filter)
        self.search_box.connect('search-index', self.search_index)
        self.search_box.entry.connect('activate', self._on_entry_activated)

        placeholder = Gtk.Label()
        placeholder.set_markup(
            '<span font-size="xx-large">%s</span>' % _('Nothing')
        )
        placeholder.show()

        self._listbox = Gtk.ListBox()
        self._listbox.set_name('ItemsViewList')
        self._listbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self._listbox.set_activate_on_single_click(False)
        self._listbox.set_placeholder(placeholder)
        self._listbox.set_sort_func(self._sort_rows)
        self._listbox.set_filter_func(self._filter_row)
        self._listbox.connect('row-selected', self._on_row_selected)
        self._listbox.connect('row-activated', self._on_row_activated)
        self._listbox.connect('motion-notify-event', self._on_motion_event)
        self._listbox.connect('leave-notify-event', self._on_leave_event)
        self._listbox.connect('button-press-event', self._on_button_press_event)
        self._listbox.connect('button-release-event', self._on_button_release_event)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_name('ItemsViewScrolledWindow')
        scrolled.set_margin_top(10)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.add(self._listbox)

        bottom_box = Gtk.Box()
        bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        bottom_box.add(self._items_counter)
        bottom_box.add(self._histories_manager)

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

    def _on_leave_event(self, listbox, event):
        if self._last_entered_item:
            self.emit('item-left', self._last_entered_item)
            self._last_entered_item = None

    def _on_motion_event(self, listbox, event):

        def do_autoscroll_and_selection():
            adjustment = self._listbox.get_adjustment()
            new_value = adjustment.get_value() + ItemsView.AUTOSCROLL_STEP
            adjustment.set_value(new_value)
            row = self._listbox.get_row_at_y(
                new_value + adjustment.get_page_increment()
            )
            if not row.is_selected(): self._listbox.select_row(row)

            return True

        def maybe_toggle_selection(row):
            if event.state == Gdk.ModifierType.BUTTON3_MASK:
                self.toggle_selection(row)

        if event.state == Gdk.ModifierType.BUTTON3_MASK:
            adjustment = self._listbox.get_adjustment()
            autoscroll_border = (
                adjustment.get_value() +
                adjustment.get_page_increment() -
                ItemsView.AUTOSCROLL_BORDER_OFFSET
            )
            if event.y > autoscroll_border:
                if not self._autoscroll_timeout_id:
                    self._autoscroll_timeout_id = GLib.timeout_add(
                        ItemsView.AUTOSCROLL_TIMEOUT_MS,
                        do_autoscroll_and_selection
                    )
            elif event.y < autoscroll_border and self._autoscroll_timeout_id:
                GLib.source_remove(self._autoscroll_timeout_id)
                self._autoscroll_timeout_id = 0

        row = self._listbox.get_row_at_y(event.y)
        
        if row:
            item = row.get_child().item

            if not self._last_entered_item:
                self._last_entered_item = item
                maybe_toggle_selection(row)
                self.emit('item-entered', item)
            elif self._last_entered_item != item:
                maybe_toggle_selection(row)
                self.emit('item-left', self._last_entered_item)
                self.emit('item-entered', item)
                self._last_entered_item = item
        elif self._last_entered_item:
            self.emit('item-left', self._last_entered_item)
            self._last_entered_item = None

    def _on_button_press_event(self, listbox, event):
        row = self._listbox.get_row_at_y(event.y)
        if not row or event.button != 3: return
        self.toggle_selection(row)

    def _on_button_release_event(self, listbox, event):
        if self._autoscroll_timeout_id:
            GLib.source_remove(self._autoscroll_timeout_id)
            self._autoscroll_timeout_id = 0

    def _on_row_selected(self, listbox, row):
        if row: self.emit('item-selected', row.get_child().item)

    def _on_row_activated(self, listbox, row):
        if row: self.emit('item-activated', row.get_child().item)

    def _on_entry_activated(self, entry):
        item = self.get_selected()
        if item: self.emit('item-activated', item[0])
        return True

    def _on_changed(self, history_items):
        self.search_box.reset()
        self.load_all()
        self.resume_selection() or self.select_first()
        self._last_selected_index = 0

    def _remove(self, history_items, item=None):
        self.save_selection()
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
        history_item = row.get_child().item

        if self._show_index:
            if history_item.index == self._show_index: return True
            else: return False

        if self._filter_mode and not row.get_mapped():
            return False

        if (
            self.search_box.flags and
            history_item.kind not in self.search_box.flags
        ):
            return False

        if not self.search_box.search_text:
            history_item.markup = None
            history_item.sort_score = None
            return result

        match = fuzzy.match(
            self.search_box.search_text,
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

    def save_selection(self):

        def get_current_index(child):
            result = None

            for i, ch in enumerate(self._listbox.get_children()):
                if not ch.get_mapped() or ch != child: continue
                result = i
                break

            return result

        selected_row = self._listbox.get_selected_rows()

        try:
            selected_row = selected_row[0]
        except IndexError:
            return

        self._last_selected_index = get_current_index(selected_row)

    def resume_selection(self):

        def get_mapped_children():
            children = []

            for child in self._listbox.get_children():
                if child.get_mapped(): children.append(child)

            return children

        if not self._last_selected_index: return False
        children = get_mapped_children()

        if len(children) == self._last_selected_index:
            self._last_selected_index -= 1

        for i, row in enumerate(children):
            if i == self._last_selected_index:
                self._listbox.select_row(row)
                # i'm sorry
                GLib.timeout_add(200, lambda *a, **ka: row.grab_focus())
                break

        return True

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
            for row in self._listbox.get_children():
                item_widget = row.get_child()
                item = item_widget.item

                if item.raw != text:
                    row.set_activatable(True)
                    item_widget.set_sensitive(True)
                    item_widget.get_style_context().remove_class('active')
                else:
                    row.set_activatable(False)
                    item_widget.get_style_context().add_class('active')

        if len(self) < 1: return

        clipboard = Gtk.Clipboard.get_default(Gdk.Display.get_default())
        text = clipboard.wait_for_text()
        on_clipboard(clipboard, text)

    def search_index(self, search_box, index):
        self._show_index = index
        self._listbox.invalidate_filter()

    def filter(self, search_box):
        self._show_index = None

        if len(self.search_box.search_text) > len(self._last_search_string):
            self._filter_mode = True
        else:
            self._filter_mode = False

        self._listbox.invalidate_filter()
        self._listbox.invalidate_sort()
        self.select_first(grab_focus=False)
        self._items_counter.update()

        if self.search_box.search_text:
            self._last_search_string = self.search_box.search_text
        else:
            self._last_search_string = ''

    def select_first(self, grab_focus=False):
        self._listbox.unselect_all()
        self.set_active_item()

        for row in self._listbox.get_children():
            if not row.get_activatable() or not row.get_mapped(): continue

            self._listbox.select_row(row)
            if grab_focus: row.grab_focus()
            break

        self.reset_scroll()

    def get_selected(self):
        result = []
        rows = self._listbox.get_selected_rows()

        for row in rows:
            result.append(row.get_child().item)

        return result

    def clear(self):
        self._listbox.unselect_all()

        if self._autoscroll_timeout_id:
            GLib.source_remove(self._autoscroll_timeout_id)
            self._autoscroll_timeout_id = 0

        for row in self._listbox.get_children():
            child = row.get_child()
            if child: row.remove(child)
            row.destroy()

        self._items_counter.update()

    def reset_scroll(self):
        adjustment = self._listbox.get_adjustment()
        lower = adjustment.get_lower()
        adjustment.set_value(lower)

    def toggle_selection(self, row):
        if row.is_selected(): self._listbox.unselect_row(row)
        else: self._listbox.select_row(row) 

    @property
    def histories_manager(self):
        return self._histories_manager

    @property
    def listbox(self):
        return self._listbox

    @property
    def n_selected(self):
        selected = self.get_selected()
        return len(selected)
