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
from typing import Optional, TYPE_CHECKING

from gi.repository import Gtk, Gio  # type: ignore

from draobpilc import common
from draobpilc.history_item_kind import HistoryItemKind

if TYPE_CHECKING:
    from draobpilc.history_item import HistoryItem


INFOSTRING_TEMPLATE: str = '<span size="x-small"><b>▶ %s</b></span>'


class Infobox(Gtk.Box):

    def __init__(self, item: "HistoryItem") -> None:
        super().__init__()

        self.set_name('Infobox')
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.END)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_margin_left(5)
        self.set_margin_bottom(5)

        self._weakref: weakref.ReferenceType["HistoryItem"] = weakref.ref(item)

        if self.item and self.item.app_info:
            name: Optional[str] = self.item.app_info.get_display_name()
            gicon: Optional[Gio.Icon] = self.item.app_info.get_icon()

            if gicon:
                icon_theme: Gtk.IconTheme = Gtk.IconTheme.get_default()
                icon_info: Optional[Gtk.IconInfo] = icon_theme.lookup_by_gicon(
                    gicon,
                    16,
                    Gtk.IconLookupFlags.FORCE_SIZE
                )
                if icon_info:
                    pixbuf: Gtk.Pixbuf = icon_info.load_icon()
                    icon: Gtk.Image = Gtk.Image()
                    icon.set_margin_right(5)
                    icon.set_from_pixbuf(pixbuf)
                    self.add(icon)

            if name:
                app_name: Gtk.LinkButton = Gtk.LinkButton()
                app_name.connect('activate-link', self._on_activate_link)
                app_name.set_halign(Gtk.Align.START)
                app_name.set_name('AppNameLink')
                app_name.set_label(name)
                self.add(app_name)

                style_context: Gtk.StyleContext = app_name.get_style_context()
                style_context.remove_class('text-button')
                style_context.remove_class('button')

        if self.item and self.item.info_string:
            label: Gtk.Label = Gtk.Label()
            label.set_margin_left(5)
            label.set_halign(Gtk.Align.START)
            label.set_markup(INFOSTRING_TEMPLATE % self.item.info_string)
            self.add(label)

    def _on_activate_link(self, link_button: Gtk.LinkButton) -> bool:
        item = self.item
        if not item:
            return False

        if not item or not item.raw:
            return False

        uri: str = item.raw.strip()
        if item.kind != HistoryItemKind.LINK:
            uri = 'file://%s' % uri

        if item.app_info:
            item.app_info.launch_uris([uri])
        common.APPLICATION.hide()
        return True

    @property
    def item(self) -> Optional["HistoryItem"]:
        return self._weakref()
