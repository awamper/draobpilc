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
from draobpilc.widgets.histories_manager import HistoriesManager
from draobpilc.widgets.items_counter import ItemsCounter


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
        self.set_halign(Gtk.Align.FILL)
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_name('ItemsViewBox')

        self._bound_history = None
        self._last_entered_item = None
        self._last_selected_index = None
        self._show_index = None
        self._autoscroll_timeout_id = 0

        self._histories_manager = HistoriesManager()

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
        self._listbox.connect('row-selected', self._on_row_selected)
        self._listbox.connect('row-activated', self._on_row_activated)
        self._listbox.connect('motion-notify-event', self._on_motion_event)
        self._listbox.connect('leave-notify-event', self._on_leave_event)
        self._listbox.connect('button-press-event', self._on_button_press_event)
        self._listbox.connect('button-release-event', self._on_button_release_event)

        self._items_counter = ItemsCounter(self._listbox)
        self._load_rest_btn = Gtk.LinkButton()
        self._load_rest_btn.set_label('load all history')
        self._load_rest_btn.set_no_show_all(True)
        self._load_rest_btn.connect(
            'activate-link',
            lambda _: self.load_rest_items()
        )
        self._load_rest_btn.hide()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_name('ItemsViewScrolledWindow')
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.add(self._listbox)

        bottom_box = Gtk.Box()
        bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        bottom_box.add(self._items_counter)
        bottom_box.add(self._load_rest_btn)
        bottom_box.add(self._histories_manager)

        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
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
        if not row: return
        item = row.get_child().item
        if item: self.activate_item(item)

    def _on_changed(self, history_items):
        self.show_items()
        self.set_active_item()
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

    def save_selection(self):

        def get_current_index(child):
            result = None

            for i, ch in enumerate(self._listbox.get_children()):
                if ch != child: continue
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
        if not self._last_selected_index: return False
        children = self._listbox.get_children()

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
        self._items_counter.set_history_items(self._bound_history)
        self._items_counter.update()

        self.show_items()

    def show_items(self):
        limit = common.SETTINGS[common.ITEMS_VIEW_LIMIT]
        items = self._bound_history
        if limit: items = items[:limit]
        self.clear()

        for item in items:
            self._listbox.add(item.widget)

        if len(items) < len(self._bound_history): 
            self._load_rest_btn.show()
        else:
            self._load_rest_btn.hide()

        self.show_all()

    def load_rest_items(self):
        limit = common.SETTINGS[common.ITEMS_VIEW_LIMIT]
        if not limit: return

        for item in self._bound_history[limit:]:
            self._listbox.add(item.widget)

        self._load_rest_btn.hide()
        self.show_all()
        return True

    def set_active_item(self):

        def on_clipboard(clipboard, text):
            for row in self._listbox.get_children():
                item_widget = row.get_child()
                item = item_widget.item

                if item.raw != text:
                    row.set_activatable(True)
                    item_widget.set_sensitive(True)
                    item_widget.set_active(False)
                else:
                    row.set_activatable(False)
                    item_widget.set_active(True)

        if len(self) < 1: return

        clipboard = Gtk.Clipboard.get_default(Gdk.Display.get_default())
        text = clipboard.wait_for_text()
        on_clipboard(clipboard, text)

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

    def reset_scroll(self):
        adjustment = self._listbox.get_adjustment()
        lower = adjustment.get_lower()
        adjustment.set_value(lower)

    def toggle_selection(self, row):
        if row.is_selected(): self._listbox.unselect_row(row)
        else: self._listbox.select_row(row) 

    def activate_item(self, item):
        if item: self.emit('item-activated', item)

    def get_by_number(self, number):
        result = None
        curr_index = None
        children = self._listbox.get_children()

        for index, row in enumerate(children):
            visible = utils.is_visible_on_scroll(
                self._listbox.get_adjustment(),
                row
            )
            
            if visible:
                if curr_index is None:
                    curr_index = 0
                else:
                    curr_index += 1

            if not curr_index is None and curr_index == number:
                result = row.get_child().item
                break

        return result

    def show_shortcut_hints(self, show):
        curr_index = None
        children = self._listbox.get_children()

        if show:
            for index, row in enumerate(children):
                visible = utils.is_visible_on_scroll(
                    self._listbox.get_adjustment(),
                    row
                )
                
                if visible:
                    if curr_index is None:
                        curr_index = 0
                    else:
                        curr_index += 1

                    row.get_child().show_shortcut_hint(curr_index + 1)
        else:
            for row in children:
                row.get_child().show_shortcut_hint(None)

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
