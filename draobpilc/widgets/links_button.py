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

import weakref
from typing import Optional, TYPE_CHECKING, Any

from gi.repository import Gtk  # type: ignore

from draobpilc.widgets.link_widget import LinkWidget

if TYPE_CHECKING:
    from draobpilc.history_item import HistoryItem

MAX_LINKS_POPOVER_HEIGHT: int = 400
MIN_LINKS_POPOVER_HEIGHT: int = 100
LINKS_POPOVER_ITEM_HEIGHT: int = 50
LINKS_POPOVER_WIDTH: int = 400


class LinksButton(Gtk.LinkButton):

    def __init__(self, item: "HistoryItem") -> None:
        super().__init__()

        self.set_name('LinksButton')

        if item.links:
            self.set_label('%i links' % len(item.links))

        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.END)
        self.set_margin_left(5)
        self.set_margin_bottom(5)
        self.connect('activate-link', self._on_activate_link)

        style_context: Gtk.StyleContext = self.get_style_context()
        style_context.remove_class('text-button')
        style_context.remove_class('button')

        self._weakref: weakref.ReferenceType["HistoryItem"] = weakref.ref(item)

        self._list_box: Gtk.ListBox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)

        n_links: int = len(self.item.links) if self.item and self.item.links else 0
        height_request: int = max(MIN_LINKS_POPOVER_HEIGHT, min(n_links * LINKS_POPOVER_ITEM_HEIGHT, MAX_LINKS_POPOVER_HEIGHT))

        self._scrolled_window: Gtk.ScrolledWindow = Gtk.ScrolledWindow()
        self._scrolled_window.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC
        )
        self._scrolled_window.set_size_request(LINKS_POPOVER_WIDTH, height_request)
        self._scrolled_window.add(self._list_box)
        self._scrolled_window.show_all()

        self._popover: Gtk.Popover = Gtk.Popover()
        self._popover.set_relative_to(self)
        self._popover.add(self._scrolled_window)

        self.populate()

    def _on_activate_link(self, link: Gtk.LinkButton) -> bool:
        self._popover.show()
        return True

    def populate(self) -> None:
        item = self.item
        if not item or not item.links:
            return

        for link_url in item.links:
            link_widget: LinkWidget = LinkWidget(link_url)
            self._list_box.add(link_widget)

        self._list_box.show_all()

    @property
    def item(self) -> Optional["HistoryItem"]:
        return self._weakref()
