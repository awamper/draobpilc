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

import os

from gi.repository import Gio
from gi.repository import Gtk

from draobpilc import common
from draobpilc.lib import gpaste_client
from draobpilc.widgets.link_widget import LinkWidget


class FileLinkWidget(LinkWidget):
    def __init__(self, file_path):
        super().__init__(file_path)

        self._file_path = self._link

        copy_content_button = Gtk.Button.new_from_icon_name('document-open-symbolic', Gtk.IconSize.BUTTON)
        copy_content_button.set_tooltip_text('Copy file content')
        copy_content_button.set_relief(Gtk.ReliefStyle.NONE)
        copy_content_button.connect('clicked', self._on_copy_content_clicked)
        self._action_box.add(copy_content_button)

    def _get_app_info(self, file_path):
        app_info = False

        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path): return app_info

        uri = 'file://%s' % file_path
        file_ = Gio.file_new_for_uri(uri)
        info = file_.query_info(
            'standard::content-type',
            Gio.FileQueryInfoFlags.NONE
        )
        content_type = info.get_content_type()

        if content_type:
            app_info = Gio.AppInfo.get_default_for_type(
                content_type,
                False
            )

        return app_info

    def _on_link_clicked(self, button):
        uri = 'file://%s' % os.path.expanduser(self._file_path)
        Gio.AppInfo.launch_default_for_uri(uri)
        common.APPLICATION.hide()
        return True

    def _on_copy_content_clicked(self, button):
        gpaste_client.add_file(self._file_path)
        common.APPLICATION.hide()
