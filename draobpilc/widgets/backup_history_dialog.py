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

from draobpilc.lib import gpaste_client


class BackupHistoryDialog(Gtk.Dialog):

    def __init__(self, transient_for=None, current_name=None):
        super().__init__(use_header_bar=True)

        self.set_title(_('Backup history'))
        self.set_resizable(False)
        if transient_for: self.set_transient_for(transient_for)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_destroy_with_parent(True)
        self.set_modal(True)
        self.add_buttons(
            _('Backup'),
            Gtk.ResponseType.OK,
            _('Cancel'),
            Gtk.ResponseType.CANCEL
        )

        self._current_name = current_name or gpaste_client.get_history_name()
        backup_name = self._current_name + _('_backup')

        self._label = Gtk.Label()
        self._label.set_label (
            _('Under which name do you want to backup this history?')
        )
        self._label.props.margin = 10

        self._error_label = Gtk.Label()
        self._error_label.props.margin = 10
        self._error_label.hide()

        label_overlay = Gtk.Overlay()
        label_overlay.add(self._label)
        label_overlay.add_overlay(self._error_label)

        self._entry = Gtk.Entry()
        self._entry.props.margin = 10
        self._entry.set_text(backup_name)
        self._entry.connect('activate', self._on_entry_activate)
        self._entry.props.buffer.connect('notify::text',
            lambda b, p: self._hide_error()
        )

        content_area = self.get_content_area()
        content_area.add(label_overlay)
        content_area.add(self._entry)
        content_area.show_all()

        self.connect('response', self._on_response)

    def _on_entry_activate(self, entry):
        self._backup_history(self._entry.get_text()) and self.destroy()

    def _on_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            self._backup_history(self._entry.get_text()) and self.destroy()
        else:
            self.destroy()

    def _hide_error(self):
        self._error_label.hide()
        self._label.set_opacity(1)

    def _show_error(self):
        self._label.set_opacity(0)
        self._error_label.show()

    def _backup_history(self, name):
        histories = gpaste_client.list_histories()

        if name in histories:
            msg = _('Name "%s" already exists.') % name
            self._error_label.set_markup('<span fgcolor="red">%s</span>' % msg)
            self._show_error()
            return False

        gpaste_client.backup_history(self._current_name, name)

        return True
