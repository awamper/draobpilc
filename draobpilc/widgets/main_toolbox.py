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


class MainToolbox(Gtk.Box):

    def __init__(self):
        super().__init__()

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_opacity(0.6)

        self.prefs_btn = Gtk.Button.new_from_icon_name(
            'preferences-system-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self.prefs_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.prefs_btn.set_tooltip_text(_('Preferences'))

        self.about_btn = Gtk.Button.new_from_icon_name(
            'help-about-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self.about_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.about_btn.set_tooltip_text(_('About'))

        self.quit_btn = Gtk.Button.new_from_icon_name(
            'application-exit-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self.quit_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.quit_btn.set_tooltip_text(_('Quit'))

        self.add(self.prefs_btn)
        self.add(self.about_btn)
        self.add(self.quit_btn)
        self.show_all()
