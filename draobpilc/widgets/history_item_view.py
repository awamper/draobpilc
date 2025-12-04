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
from typing import Optional, Union, TYPE_CHECKING

from gi.repository import Gtk, Gdk  # type: ignore

from draobpilc import common
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.widgets.item_thumb import ItemThumb
from draobpilc.widgets.indicator_base import IndicatorBase
from draobpilc.widgets.item_kind_indicator import ItemKindIndicator
from draobpilc.widgets.item_label import ItemLabel
from draobpilc.widgets.infobox import Infobox
from draobpilc.widgets.links_button import LinksButton
from draobpilc.widgets.shortcut_hint import ShortcutHint

if TYPE_CHECKING:
    from draobpilc.history_item import HistoryItem


class HistoryItemView(Gtk.Box):

    def __init__(self, history_item: "HistoryItem") -> None:
        super().__init__()

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_name('HistoryItemBox')
        self.connect('enter-notify-event', self._on_enter_event)
        self.connect('leave-notify-event', self._on_leave_event)

        self._weakref: weakref.ReferenceType["HistoryItem"] = weakref.ref(history_item, self._on_weakref)
        self._preview: Optional[ItemThumb] = None
        self._kind_indicator: ItemKindIndicator = ItemKindIndicator(self.item.kind if self.item and self.item.kind else HistoryItemKind.TEXT)
        self._label: ItemLabel = ItemLabel()
        self._shortcut_hint: ShortcutHint = ShortcutHint()

        self._infobox: Union[LinksButton, Infobox, Gtk.Box]
        if self.item:
            if self.item.kind == HistoryItemKind.TEXT and self.item.links:
                self._infobox = LinksButton(self.item)
            elif self.item.kind in (HistoryItemKind.LINK, HistoryItemKind.FILE) or common.SETTINGS[common.SHOW_TEXT_INFO]:
                self._infobox = Infobox(self.item)
            else:
                # dummy
                self._infobox = Gtk.Box()
        else:
            # dummy
            self._infobox = Gtk.Box()

        self._grid: Gtk.Grid = Gtk.Grid()
        self._grid.get_style_context().add_class('history-item-box')
        self._grid.attach(self._kind_indicator, 0, 0, 1, 2)
        self._grid.attach(self._label, 2, 0, 1, 1)
        self._grid.attach(self._infobox, 2, 1, 1, 1)

        if (
            self.item and self.item.thumb_path and
            common.SETTINGS[common.SHOW_THUMBNAILS]
        ):
            self._preview = ItemThumb(
                self.item.thumb_path,
                -1,
                common.SETTINGS[common.ITEM_MAX_HEIGHT]
            )
            self._grid.attach(self._preview, 1, 0, 1, 2)
        elif (
            self.item and self.item.kind == HistoryItemKind.FILE and
            self.item.content_type and
            self.item.content_type.startswith('video/') and
            common.SETTINGS[common.SHOW_THUMBNAILS]
        ):
            # Display a symbolic icon for video files without thumbnails
            video_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
                "video-x-generic-symbolic", Gtk.IconSize.DIALOG
            )
            video_icon.set_pixel_size(common.SETTINGS[common.ITEM_MAX_HEIGHT])
            video_icon.set_margin_start(20)
            video_icon.set_margin_end(20)
            self._grid.attach(video_icon, 1, 0, 1, 2)
            # Center the icon within its allocated space
            video_icon.set_halign(Gtk.Align.CENTER)
            video_icon.set_valign(Gtk.Align.CENTER)
        elif (
            self.item and self.item.kind == HistoryItemKind.FILE and
            self.item.content_type and
            self.item.content_type.startswith('audio/') and
            common.SETTINGS[common.SHOW_THUMBNAILS]
        ):
            # Display a symbolic icon for audio files without thumbnails
            audio_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
                "audio-x-generic-symbolic", Gtk.IconSize.DIALOG
            )
            audio_icon.set_pixel_size(common.SETTINGS[common.ITEM_MAX_HEIGHT])
            audio_icon.set_margin_start(20)
            audio_icon.set_margin_end(20)
            self._grid.attach(audio_icon, 1, 0, 1, 2)
            # Center the icon within its allocated space
            audio_icon.set_halign(Gtk.Align.CENTER)
            audio_icon.set_valign(Gtk.Align.CENTER)


        self.set_active(False)

        overlay: Gtk.Overlay = Gtk.Overlay()
        overlay.add(self._grid)
        overlay.add_overlay(self._shortcut_hint)

        self.add(overlay)
        self.show_all()

    def _on_weakref(self, obj: weakref.ReferenceType["HistoryItem"]) -> None:
        self.destroy()

    def _on_enter_event(self, box: Gtk.Box, event: Gdk.Event) -> None:
        pass

    def _on_leave_event(self, box: Gtk.Box, event: Gdk.Event) -> None:
        pass

    def set_label(self, markup: str) -> None:
        self._label.set_markup(markup)

    def set_active(self, active: bool) -> None:
        style_context: Gtk.StyleContext = self._grid.get_style_context()

        if active:
            style_context.add_class('history-item-box-active')
        else:
            style_context.remove_class('history-item-box-active')

    def show_shortcut_hint(self, hint: Optional[Union[str, int]]) -> None:
        if hint is None:
            self._shortcut_hint.hide()
        else:
            self._shortcut_hint.set_hint(str(hint))
            self._shortcut_hint.show()

    @property
    def item(self) -> Optional["HistoryItem"]:
        return self._weakref()
    
