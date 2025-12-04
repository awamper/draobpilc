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
from typing import Optional, TYPE_CHECKING

from gi.repository import Gtk, Gio, GLib  # type: ignore

from draobpilc.lib import gpaste_client
from draobpilc import common
from draobpilc.widgets.base_link_widget import BaseLinkWidget


if TYPE_CHECKING:
    _ = lambda s: s


class LinkWidget(BaseLinkWidget):
    def __init__(self, link: str) -> None:
        super().__init__(link)

        copy_button = Gtk.Button.new_from_icon_name('edit-copy', Gtk.IconSize.BUTTON)
        copy_button.set_relief(Gtk.ReliefStyle.NONE)
        copy_button.set_tooltip_text('Copy')
        copy_button.connect('clicked', self._on_copy_clicked)
        self._action_box.pack_start(copy_button, False, False, 0)

    def _get_icon(self, app_info: Optional[Gio.AppInfo]) -> Gtk.Image:
        # Get default browser icon
        browser_icon = Gtk.Image.new_from_icon_name(
            'web-browser',
            Gtk.IconSize.SMALL_TOOLBAR
        )
        browser_icon.set_margin_start(5)
        browser_icon.set_margin_end(5)

        if app_info:
            gicon = app_info.get_icon()
            if gicon:
                icon_theme = Gtk.IconTheme.get_default()
                icon_info = icon_theme.lookup_by_gicon(
                    gicon,
                    16,
                    Gtk.IconLookupFlags.FORCE_SIZE
                )
                if icon_info:
                    pixbuf = icon_info.load_icon()
                    browser_icon.set_from_pixbuf(pixbuf)

        return browser_icon

    def _get_app_info(self, uri: str) -> Optional[Gio.AppInfo]:
        parsed_uri = urllib.parse.urlparse(uri)
        scheme = parsed_uri.scheme
        if not scheme:
            scheme = 'http'
        app_info = Gio.AppInfo.get_default_for_uri_scheme(scheme)
        return app_info

    def _on_link_clicked(self, button: Gtk.Button) -> bool:
        if self._app_info:
            self._app_info.launch_uris([self._link])
        common.APPLICATION.hide()
        return True

    def _on_copy_clicked(self, button: Gtk.Button) -> bool:
        gpaste_client.add(self._link)
        common.APPLICATION.hide()
        return True

    def _on_query_tooltip(self, widget: Gtk.Widget, x: int, y: int, keyboard_mode: bool, tooltip: Gtk.Tooltip) -> bool:
        header_text = _('Open url')
        app_name = self._app_info.get_display_name() if self._app_info else None
        if app_name:
            app_name = GLib.markup_escape_text(app_name, -1)
            header_text += _(f' with {app_name}')

        link = GLib.markup_escape_text(self._link, -1)
        tooltip.set_icon_from_icon_name('dialog-information-symbolic', Gtk.IconSize.LARGE_TOOLBAR)
        tooltip.set_markup(f'<b>{header_text}</b>\n<i>{link}</i>')

        return True

