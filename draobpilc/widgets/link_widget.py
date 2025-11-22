#!/usr/bin/env python3

# Copyright 2025 Ivan awamper@gmail.com
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

import urllib.parse

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import Pango

from draobpilc.lib import gpaste_client
from draobpilc import common


MAX_LINK_LABEL_WIDTH = 50


class LinkWidget(Gtk.Box):
    def __init__(self, link):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name('LinkWidget')

        self._link = link
        self._app_info = self._get_app_info(self._link)

        browser_icon = self._get_icon(self._app_info)
        link_button = self._get_link_button()
        link_button.connect('activate-link', self._on_link_clicked)

        copy_button = Gtk.Button.new_from_icon_name("edit-copy", Gtk.IconSize.BUTTON)
        copy_button.set_relief(Gtk.ReliefStyle.NONE)
        copy_button.set_tooltip_text('Copy')
        copy_button.connect("clicked", self._on_copy_clicked)

        self._action_box = self._get_action_box()
        self._action_box.pack_start(copy_button, False, False, 0)

        grid = Gtk.Grid()
        grid.attach(browser_icon, 0, 0, 1, 1)
        grid.attach(link_button, 1, 0, 1, 1)
        grid.attach(self._action_box, 2, 0, 1, 1)
        grid.set_column_spacing(3)
        self.add(grid)

    def _get_icon(self, app_info):
        # Get default browser icon
        browser_icon = Gtk.Image.new_from_icon_name(
            'web-browser',
            Gtk.IconSize.BUTTON
        )
        browser_icon.set_margin_start(5)
        browser_icon.set_margin_end(5)

        if app_info:
            gicon = app_info.get_icon()
            if gicon:
                icon_theme = Gtk.IconTheme.get_default()
                icon_info = icon_theme.lookup_by_gicon(
                    gicon,
                    16, # Size of the icon
                    Gtk.IconLookupFlags.FORCE_SIZE
                )
                if icon_info:
                    pixbuf = icon_info.load_icon()
                    browser_icon.set_from_pixbuf(pixbuf)

        return browser_icon

    def _get_link_button(self):
        link_button = Gtk.LinkButton()
        link_button.set_name('LinkWidgetLink')
        link_button.set_label(self._link[0:MAX_LINK_LABEL_WIDTH])
        link_button.set_uri(self._link)
        link_button.set_tooltip_text(self._link)
        link_button.set_halign(Gtk.Align.START)
        link_button.set_hexpand(True)
        link_style_context = link_button.get_style_context()
        link_style_context.remove_class('text-button')
        link_style_context.remove_class('button')
        
        link_label = link_button.get_child()
        if isinstance(link_label, Gtk.Label):
            link_label.set_ellipsize(Pango.EllipsizeMode.END)
            link_label.set_max_width_chars(MAX_LINK_LABEL_WIDTH)
            link_label.set_single_line_mode(True)

        return link_button

    def _get_action_box(self):
        action_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL
        )
        action_box.set_halign(Gtk.Align.END)
        
        return action_box

    def _get_app_info(self, uri):
        parsed_uri = urllib.parse.urlparse(uri)
        scheme = parsed_uri.scheme
        if not scheme: scheme = 'http'
        app_info = Gio.AppInfo.get_default_for_uri_scheme(scheme)
        return app_info

    def _on_link_clicked(self, button):
        self._app_info.launch_uris([self._link])
        common.APPLICATION.hide()
        return True

    def _on_copy_clicked(self, button):
        gpaste_client.add(self._link)
        common.APPLICATION.hide()
