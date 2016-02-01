#!/usr/bin/env python3

# Copyright 2016 Ivan awamper@gmail.com
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
from gi.repository import GLib

from draobpilc.widgets.items_processor_base import ItemsProcessorBase


class ItemsProcessors(Gtk.Box):

    MARGIN = 10

    def __init__(self):
        super().__init__()

        self.set_name('ProcessorBox')
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(300)
        self._stack.props.margin = ItemsProcessors.MARGIN

        self._switcher = Gtk.StackSwitcher()
        self._switcher.set_stack(self._stack)
        self._switcher.props.margin = ItemsProcessors.MARGIN

        self.add(self._switcher)
        self.add(self._stack)
        self.show_all()

        self._items = []

    def __iter__(self):
        return iter(self.processors)

    def _get_for_items(self, items):
        result = None

        for processor in self:
            if not processor.can_process(items): continue

            if result and processor.priority > result.priority:
                result = processor
            elif not result:
                result = processor

        return result

    def _get_for_title(self, title):
        result = None

        for processor in self:
            if processor.title == title:
                result = processor
                break

        return result

    def _update_switcher(self):
        for button in self._switcher.get_children():
            if not isinstance(button, Gtk.RadioButton): continue

            for label in button.get_children():
                if not isinstance(label, Gtk.Label): continue
                processor = self._get_for_title(label.get_text())
                if not processor: continue

                button.set_sensitive(processor.get_sensitive())

    def add_processor(self, processor):
        if not isinstance(processor, ItemsProcessorBase):
            raise ValueError(
                '"processor" must be instance of ItemsProcessorBase'
            )
        else:
            processor.set_sensitive(False)
            self._stack.add_titled(
                processor,
                processor.title,
                processor.title
            )

    def set_items(self, items):
        if self._items == items: return

        if not items:
            self._items.clear()
        else:
            self._items = items

        for processor in self:
            if items is None:
                processor.clear()
                processor.set_sensitive(False)
            else:
                if processor.can_process(items):
                    processor.set_sensitive(True)
                    processor.set_items(items)
                else:
                    processor.set_sensitive(False)
                    processor.clear()

        processor = self._get_for_items(self._items)

        if processor:
            self._stack.set_visible_child(processor)
        else:
            self._stack.set_visible_child(self.default)

        self._update_switcher()

    @property
    def processors(self):
        return self._stack.get_children()

    @property
    def default(self):
        result = None

        for processor in self:
            if not processor.default: continue

            if result and processor.priority > result.priority:
                result = processor
            elif not result:
                result = processor

        return result
