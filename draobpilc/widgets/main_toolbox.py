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

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets import shortcuts_window


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
        self.quit_btn.set_name('QuitButton')
        self.quit_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.quit_btn.set_tooltip_text(_('Quit'))

        self._track_img = Gtk.Image.new_from_icon_name(
            'emblem-synchronizing-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self._track_img.set_name('TrackImg')
        self.track_btn = Gtk.ToggleButton()
        self.track_btn.set_name('TrackButton')
        self.track_btn.set_image(self._track_img)
        self.track_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.track_btn.set_tooltip_text(_('Track clipboard changes'))
        self.track_btn.connect('toggled', self._on_toggled)

        self.restart_btn = Gtk.Button.new_from_icon_name(
            'view-refresh-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self.restart_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.restart_btn.set_tooltip_text(_('Restart the daemon'))

        self.close_btn = Gtk.Button.new_from_icon_name(
            'window-close-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self.close_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.close_btn.set_tooltip_text(
            _('Close the app (<Escape> or %s)' % (
                gpaste_client.SETTINGS['show-history']
            ))
        )

        self.help_btn = Gtk.Button.new_from_icon_name(
            'help-browser-symbolic',
            Gtk.IconSize.LARGE_TOOLBAR
        )
        self.help_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.help_btn.set_tooltip_text(
            _('Show help (%s)' % common.SETTINGS[common.SHOW_HELP])
        )

        separator = Gtk.Separator()
        separator.set_name('MainToolboxSeparator')

        if shortcuts_window.is_supported(): self.add(self.help_btn)
        self.add(self.about_btn)
        self.add(self.restart_btn)
        self.add(self.prefs_btn)
        self.add(self.track_btn)
        self.add(self.close_btn)
        self.add(separator)
        self.add(self.quit_btn)
        self.show_all()

    def _on_toggled(self, button):
        style_context = self._track_img.get_style_context()

        if button.get_active():
            style_context.add_class('active')
        else:
            style_context.remove_class('active')
