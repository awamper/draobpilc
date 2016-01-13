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

from draobpilc import common
from draobpilc import version


class Window(Gtk.ApplicationWindow):

    def __init__(self, app):
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
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.stick()
        self.maximize()

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        self.set_visual(visual)

        self.box = Gtk.Box()
        self.box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.box.set_valign(Gtk.Align.FILL)
        self.box.set_halign(Gtk.Align.FILL)
        self.box.set_vexpand(True)
        self.box.set_hexpand(True)

        self.add(self.box)
        self.show_all()
