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

import gi
from gi.repository import Gtk
from gi.repository import GdkPixbuf

from draobpilc import common


DEFAULT_WIDTH = common.SETTINGS[common.ITEM_MAX_HEIGHT]
DEFAULT_HEIGHT = common.SETTINGS[common.ITEM_MAX_HEIGHT]
DEFAULT_RATIO = True


class ItemThumb(Gtk.Box):

    def __init__(
        self,
        file_path=None,
        max_width=DEFAULT_WIDTH,
        max_height=DEFAULT_HEIGHT,
        ratio=DEFAULT_RATIO,
        fallback_icon_name='image-missing'
    ):
        super().__init__()
        self.get_style_context().add_class('item-thumb')

        self._image = Gtk.Image()
        self.add(self._image)

        self._file_path = file_path
        self._max_width = max_width
        self._max_height = max_height
        self._ratio = ratio
        self._fallback_icon_name = fallback_icon_name

        if self._file_path:
            self._try_set_image()
        else:
            self.set_default()

    def _try_set_image(self):
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
        except gi.repository.GLib.GError as e:
            logging.error(e)

        if not result:
            self.set_default()
        else:
            self.show_all()

        return result

    def set_default(self):
        self.clear()
        self._image.set_from_icon_name(self._fallback_icon_name, Gtk.IconSize.DIALOG)
        self.show_all()

    def clear(self):
        self._file_path = None
        self._max_width = DEFAULT_WIDTH
        self._max_height = DEFAULT_HEIGHT
        self._ratio = DEFAULT_RATIO

        if self._image:
            self._image.clear()
            self._image.hide()

    def change_image(self, file_path, max_width=None, max_height=None):
        self.clear()
        result = False

        if not file_path:
            return result

        self._file_path = file_path
        if max_width: self._max_width = max_width
        if max_height: self._max_height = max_height

        result = self._try_set_image()
        return result

    def resize(self, width, height, ratio=DEFAULT_RATIO):
        result = False

        if self._file_path and width and height:
            self._max_width = width
            self._max_height = height
            self._ratio = ratio
            self._try_set_image()
            result = True

        return result
