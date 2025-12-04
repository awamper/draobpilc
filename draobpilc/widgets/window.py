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

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from gi.repository import Gtk, Gdk  # type: ignore

from draobpilc import common
from draobpilc import version
from draobpilc.widgets.items_processors import ItemsProcessors
from draobpilc.widgets.items_view import ItemsView
from draobpilc.widgets.main_toolbox import MainToolbox
from draobpilc.widgets.search_box import SearchBox

if TYPE_CHECKING:
    from draobpilc.application import Application


class Window(Gtk.ApplicationWindow):

    def __init__(self, app: Application, items_processors: ItemsProcessors, main_toolbox: MainToolbox,
                 search_box: SearchBox, items_view: ItemsView, deletion_progress_bar: Gtk.ProgressBar) -> None:
        super().__init__()

        self.set_application(app)
        self.set_title(version.APP_NAME)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_urgency_hint(True)
        self.set_decorated(False)
        self.set_name('MainWindow')
        self.set_icon_from_file(common.ICON_PATH)
        self.set_keep_above(True)
        self.set_keep_below(False)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.stick()
        self.maximize()

        screen: Gdk.Screen = self.get_screen()
        visual: Gdk.Visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        self.grid: Gtk.Grid = Gtk.Grid()
        self.grid.set_valign(Gtk.Align.FILL)
        self.grid.set_halign(Gtk.Align.FILL)
        self.grid.set_vexpand(True)
        self.grid.set_hexpand(True)

        self.add(self.grid)

        def resize_progress_bar(widget: Any, allocation: Any) -> None:
            parent_width = allocation.width
            target_width = int(parent_width * 0.60)
            deletion_progress_bar.set_size_request(target_width, -1)

        right_box = Gtk.Box()
        right_box.set_name('RightBox')
        right_box.set_orientation(Gtk.Orientation.VERTICAL)
        right_box.add(search_box)
        right_box.add(items_view)
        right_box.connect('size-allocate', resize_progress_bar)

        right_overlay = Gtk.Overlay()
        right_overlay.add(right_box)
        right_overlay.add_overlay(deletion_progress_bar)

        self.grid.attach(items_processors, 0, 0, 1, 1)
        self.grid.attach(main_toolbox, 0, 1, 1, 1)
        self.grid.attach(right_overlay, 1, 0, 1, 2)