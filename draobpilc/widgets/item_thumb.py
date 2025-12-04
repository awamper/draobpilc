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
import logging
from typing import Optional

import gi  # type: ignore
from gi.repository import Gtk  # type: ignore
from gi.repository import GdkPixbuf  # type: ignore

from draobpilc import common


DEFAULT_WIDTH: int = common.SETTINGS[common.ITEM_MAX_HEIGHT]
DEFAULT_HEIGHT: int = common.SETTINGS[common.ITEM_MAX_HEIGHT]
DEFAULT_RATIO: bool = True


class ItemThumb(Gtk.Box):

    def __init__(
        self,
        file_path: Optional[str] = None,
        max_width: int = DEFAULT_WIDTH,
        max_height: int = DEFAULT_HEIGHT,
        ratio: bool = DEFAULT_RATIO,
        fallback_icon_name: str = 'image-missing'
    ) -> None:
        super().__init__()
        self.get_style_context().add_class('item-thumb')

        self._image = Gtk.Image()
        self.add(self._image)

        self._file_path: Optional[str] = file_path
        self._max_width: int = max_width
        self._max_height: int = max_height
        self._ratio: bool = ratio
        self._fallback_icon_name: str = fallback_icon_name

        if self._file_path:
            self._try_set_image()
        else:
            self.set_default()

    def _try_set_image(self) -> bool:
        result = False
        if not self._max_width or not self._max_height:
            return result

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                self._file_path,
                self._max_width,
                self._max_height,
                self._ratio
            )
            self._image.set_from_pixbuf(pixbuf)
            result = True
        except gi.repository.GLib.GError as e:  # type: ignore
            logging.error(e)

        if not result:
            self.set_default()
        else:
            self.show_all()

        return result

    def set_default(self) -> None:
        self.clear()
        self._image.set_from_icon_name(self._fallback_icon_name, Gtk.IconSize.DIALOG)
        self.show_all()

    def clear(self) -> None:
        self._file_path = None
        self._max_width = DEFAULT_WIDTH
        self._max_height = DEFAULT_HEIGHT
        self._ratio = DEFAULT_RATIO

        if self._image:
            self._image.clear()
            self._image.hide()

    def change_image(self, file_path: Optional[str], max_width: Optional[int] = None, max_height: Optional[int] = None) -> bool:
        self.clear()
        result = False

        if not file_path:
            return result

        self._file_path = file_path
        if max_width: self._max_width = max_width
        if max_height: self._max_height = max_height

        result = self._try_set_image()
        return result

    def resize(self, width: int, height: int, ratio: bool = DEFAULT_RATIO) -> bool:
        result = False

        if self._file_path and width and height:
            self._max_width = width
            self._max_height = height
            self._ratio = ratio
            self._try_set_image()
            result = True

        return result

