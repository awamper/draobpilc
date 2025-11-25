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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango




class BaseLinkWidget(Gtk.Box):
    def __init__(self, link):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name('LinkWidget')

        self._link = link
        self._app_info = self._get_app_info(self._link)
        self._icon = self._get_icon(self._app_info)
        link_button = self._get_link_button()
        link_button.connect('query-tooltip', self._on_query_tooltip)
        link_button.connect('enter-notify-event', self._change_cursor)
        link_button.connect('leave-notify-event', self._restore_cursor)
        link_button.connect('clicked', self._on_link_clicked)

        self._action_box = self._get_action_box()
        
        self.grid = Gtk.Grid()
        self.grid.attach(self._icon, 0, 0, 1, 1)
        self.grid.attach(link_button, 1, 0, 1, 1)
        self.grid.attach(self._action_box, 2, 0, 1, 1)
        self.grid.set_column_spacing(3)
        self.add(self.grid)

    def _change_cursor(self, widget, event):
        window = widget.get_window()
        if not window: return False

        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.HAND2)
        window.set_cursor(cursor)

        return False

    def _restore_cursor(self, widget, event):
        window = widget.get_window()
        if window: window.set_cursor(None)

        return False

    def _get_link_button(self):
        link_button = Gtk.Button()
        link_button.set_name('LinkWidgetLink')
        link_button.set_label(self._link)
        link_button.set_has_tooltip(True)
        link_button.set_halign(Gtk.Align.START)
        link_button.set_hexpand(True)
        link_button.set_relief(Gtk.ReliefStyle.NONE)
        link_style_context = link_button.get_style_context()
        link_style_context.add_class('link-widget-button')
        
        link_label = link_button.get_child()
        if isinstance(link_label, Gtk.Label):
            link_label.set_ellipsize(Pango.EllipsizeMode.END)

            link_label.set_single_line_mode(True)

            label_style = link_label.get_style_context()
            label_style.add_class('link-widget-button-label')

        return link_button

    def _get_action_box(self):
        action_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL
        )
        action_box.set_halign(Gtk.Align.END)
        
        return action_box

    # Abstract methods to be implemented by subclasses
    def _get_icon(self, app_info):
        raise NotImplementedError

    def _get_app_info(self, link):
        raise NotImplementedError

    def _on_link_clicked(self, button):
        raise NotImplementedError

    def _on_query_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        raise NotImplementedError
