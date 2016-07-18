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
from gi.repository import GObject

from draobpilc.lib import gpaste_client
from draobpilc.widgets.backup_history_dialog import BackupHistoryDialog

ITEM_BUTTON_SIZE = 14
NAME_TEMPLATE = '%s (%i)'
TRANSITION_TIME_MS = 500


class ItemAction():

    EMPTY = 1
    DELETE = 2
    BACKUP = 3


class ItemButton(Gtk.Button):

    def __init__(self, icon_name, icon_size, tooltip, expand=False):
        super().__init__()

        icon_theme = Gtk.IconTheme.get_default()

        icon_info = icon_theme.lookup_icon(
            icon_name,
            icon_size,
            Gtk.IconLookupFlags.FORCE_SIZE
        )
        pixbuf, __ = icon_info.load_symbolic_for_context(
            self.get_style_context()
        )
        btn_image = Gtk.Image.new_from_pixbuf(pixbuf)

        self.set_hexpand(expand)
        self.set_halign(Gtk.Align.END)
        self.set_image(btn_image)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_tooltip_text(tooltip)


class ItemConfirmation(Gtk.Revealer):

    def __init__(self):
        super().__init__()

        self.set_reveal_child(False)
        self.set_transition_duration(TRANSITION_TIME_MS)
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)

        self.label = Gtk.Label()
        self.label.set_name('HistoriesManagerConfirmationLabel')
        style_context = self.label.get_style_context()

        self.yes_btn = ItemButton(
            'emblem-ok-symbolic',
            ITEM_BUTTON_SIZE,
            _('Yes'),
            expand=True
        )
        self.no_btn = ItemButton(
            'process-stop-symbolic',
            ITEM_BUTTON_SIZE,
            _('No'),
            expand=False
        )

        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
        box.set_halign(Gtk.Align.FILL)
        box.add(self.label)
        box.add(self.yes_btn)
        box.add(self.no_btn)

        self.add(box)


class HistoriesManagerItem(Gtk.Box):

    __gsignals__ = {
        'action-request': (GObject.SIGNAL_RUN_FIRST, None, (int,))
    }

    def __init__(self, name):
        super().__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._wait_for_confirm = None
        self.name = name
        self.size = gpaste_client.get_history_size(self.name)

        self.link = Gtk.LinkButton()
        self.link.set_label(NAME_TEMPLATE % (self.name, self.size))
        self.link.set_halign(Gtk.Align.START)

        self.backup_btn = ItemButton(
            'document-save-symbolic',
            ITEM_BUTTON_SIZE,
            _('Backup history'),
            expand=True
        )
        self.backup_btn.connect(
            'clicked',
            lambda b: self.emit('action-request', ItemAction.BACKUP)
        )

        self.empty_btn = ItemButton(
            'edit-clear-all-symbolic',
            ITEM_BUTTON_SIZE,
            _('Empty history'),
            expand=False
        )
        self.empty_btn.connect(
            'clicked',
            self._request_confirmation,
            ItemAction.EMPTY
        )

        self.delete_btn = ItemButton(
            'edit-delete-symbolic',
            ITEM_BUTTON_SIZE,
            _('Delete history'),
            expand=False
        )
        self.delete_btn.connect(
            'clicked',
            self._request_confirmation,
            ItemAction.DELETE
        )

        self._box = Gtk.Box()
        self._box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self._box.set_halign(Gtk.Align.FILL)
        self._box.add(self.link)
        self._box.add(self.backup_btn)
        self._box.add(self.empty_btn)
        self._box.add(self.delete_btn)

        self._revealer = Gtk.Revealer()
        self._revealer.set_reveal_child(True)
        self._revealer.set_transition_duration(TRANSITION_TIME_MS)
        self._revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self._revealer.add(self._box)

        self._confirmation_revealer = ItemConfirmation()
        self._confirmation_revealer.label.set_label(_('Are you sure?'))
        self._confirmation_revealer.yes_btn.connect('clicked', self._confirm)
        self._confirmation_revealer.no_btn.connect('clicked', self._cancel)

        self.add(self._revealer)
        self.add(self._confirmation_revealer)
        self.show_all()

        self.set_active(False)

    def _hide_confirm_dialog(self):
        self._confirmation_revealer.set_transition_type(
            Gtk.RevealerTransitionType.SLIDE_UP
        )
        self._confirmation_revealer.set_reveal_child(False)

        self._revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self._revealer.show_all()
        self._revealer.set_reveal_child(True)

    def _show_confirm_dialog(self):
        self._revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self._revealer.set_reveal_child(False)

        self._confirmation_revealer.set_transition_type(
            Gtk.RevealerTransitionType.SLIDE_UP
        )
        self._confirmation_revealer.show_all()
        self._confirmation_revealer.set_reveal_child(True)

        self._confirmation_revealer.no_btn.grab_focus()

    def _confirm(self, yes_btn):
        if not self._wait_for_confirm: return

        self.emit('action-request', self._wait_for_confirm)
        self._wait_for_confirm = None
        self._hide_confirm_dialog()

    def _cancel(self, no_btn):
        self._wait_for_confirm = None
        self._hide_confirm_dialog()

    def _request_confirmation(self, button, action):
        self._wait_for_confirm = action
        self._show_confirm_dialog()

    def set_active(self, active=False):
        self.link.set_sensitive(not active)


class HistoriesManager(Gtk.Box):

    def __init__(self):
        super().__init__()

        self.set_name('HistoriesManagerBox')
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_halign(Gtk.Align.END)
        self.set_valign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(False)

        self.link = Gtk.LinkButton()
        self.link.connect('activate-link', self._on_activate_link)
        self.link.set_label('...')
        self.link.set_tooltip_text(_('Open histories manager'))

        self._entry = Gtk.Entry()
        self._entry.set_placeholder_text(_('New history'))
        self._entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY,
            'list-add-symbolic'
        )
        self._entry.connect('activate', self._on_entry_activate)

        self._box = Gtk.Box()
        self._box.set_orientation(Gtk.Orientation.VERTICAL)
        self._box.add(self._entry)

        self.popover = Gtk.Popover()
        self.popover.set_relative_to(self.link)
        self.popover.add(self._box)

        self.add(self.link)

        gpaste_client.connect('SwitchHistory', self.update)
        gpaste_client.connect('DeleteHistory', self.update)
        self.update()

    def _on_entry_activate(self, entry):
        history_name = self._entry.get_text().strip()
        if history_name: self._switch_history(history_name)
        self._entry.set_text('')
        self.update()

    def _on_activate_link(self, link):
        self.show()
        return True

    def _on_histories_manager_item(self, link, histories_manager_item):
        self._switch_history(histories_manager_item.name)
        return True

    def _on_item_action(self, histories_manager_item, action):
        if action == ItemAction.EMPTY:
            gpaste_client.empty_history(histories_manager_item.name)
            self.update()
        elif action == ItemAction.DELETE:
            gpaste_client.delete_history(histories_manager_item.name)
        elif action == ItemAction.BACKUP:
            dialog = BackupHistoryDialog(
                self.get_toplevel(),
                histories_manager_item.name
            )
            dialog.run()
        else:
            pass

    def _set_active(self, name):
        self.link.set_label(name)

    def _clear(self):
        for child in self._box:
            if child != self._entry: child.destroy()

    def _switch_history(self, name):
        gpaste_client.switch_history(name)
        self.popover.hide()

    def update(self, *args, **kwargs):
        self._clear()
        self.link.set_sensitive(True)
        histories = gpaste_client.list_histories()
        current_name = gpaste_client.get_history_name()

        if len(histories) <= 1:
            self.link.set_sensitive(False)
            return None

        for history_name in histories:
            histories_manager_item = HistoriesManagerItem(history_name)
            histories_manager_item.link.connect(
                'activate-link',
                self._on_histories_manager_item,
                histories_manager_item
            )
            histories_manager_item.connect(
                'action-request',
                self._on_item_action
            )
            self._box.add(histories_manager_item)

            if history_name == current_name:
                self._set_active(history_name)
                histories_manager_item.set_active(True)

        self._box.show_all()

    def show(self):
        self.popover.show()
