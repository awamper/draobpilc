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
from gi.repository import GdkPixbuf

from draobpilc import common

MARGIN = common.SETTINGS[common.ITEM_PREVIEW_MARGIN]
DEFAULT_WIDTH = (
    common.SETTINGS[common.ITEM_MAX_HEIGHT] - MARGIN
)
DEFAULT_HEIGHT = (
    common.SETTINGS[common.ITEM_MAX_HEIGHT] - MARGIN * 2
)


class ItemThumb(Gtk.Image):

    def __init__(
        self,
        filename=None,
        max_width=DEFAULT_WIDTH,
        max_height=DEFAULT_HEIGHT,
        ratio=True
    ):
        super().__init__()
        self.set_margin_left(MARGIN)
        self.set_margin_top(MARGIN)
        self.set_margin_bottom(MARGIN)

        self._filename = None
        if filename: self.set_filename(filename, max_width, max_height, ratio)

    def set_filename(self, filename, max_width, max_height, ratio=True):
        self._filename = filename
        pixbuf = ItemThumb.get_pixbuf(filename, max_width, max_height, ratio)
        self.set_from_pixbuf(pixbuf)        

    def resize(self, width, height):
        old_pixbuf = self.props.pixbuf

        if (
            old_pixbuf.props.width == width and
            old_pixbuf.props.height == height
        ): return None

        if width > 0:
            width = width - MARGIN
        if height > 0:
            height = height - MARGIN * 2

        self.clear()
        new_pixbuf = ItemThumb.get_pixbuf(self._filename, width, height)
        if new_pixbuf: self.set_from_pixbuf(new_pixbuf)

    @staticmethod
    def get_pixbuf(
        filename,
        max_width=DEFAULT_WIDTH,
        max_height=DEFAULT_HEIGHT,
        ratio=True
    ):
        if (
            max_width < 1 and max_width != -1 or
            max_height < 1 and max_height != -1
        ): return None

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename,
            max_width,
            max_height,
            ratio
        )

        return pixbuf
