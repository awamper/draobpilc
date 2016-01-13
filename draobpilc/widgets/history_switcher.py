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

DELETE_BUTTON_SIZE = 14
NAME_TEMPLATE = '%s (%i)'


class HistorySwitcherItem(Gtk.Box):

    def __init__(self, name):
        super().__init__()

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_halign(Gtk.Align.FILL)

        self.name = name
        self.size = gpaste_client.get_history_size(self.name)

        self.link = Gtk.LinkButton()
        self.link.set_no_show_all(True)
        self.link.set_label(NAME_TEMPLATE % (self.name, self.size))
        self.link.set_halign(Gtk.Align.START)

        self._label = Gtk.Label()
        self._label.set_no_show_all(True)
        self._label.set_label(NAME_TEMPLATE % (self.name, self.size))
        self._label.hide()
        label_style_context = self._label.get_style_context()
        label_style_context.add_class('flat')
        label_style_context.add_class('text-button')
        label_style_context.add_class('button')


        icon_theme = Gtk.IconTheme.get_default()
        icon_info = icon_theme.lookup_icon(
            'edit-delete-symbolic',
            DELETE_BUTTON_SIZE,
            Gtk.IconLookupFlags.FORCE_SIZE
        )
        pixbuf, _ = icon_info.load_symbolic_for_context(
            self.get_style_context()
        )
        btn_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.delete_btn = Gtk.Button()
        self.delete_btn.set_hexpand(True)
        self.delete_btn.set_halign(Gtk.Align.END)
        self.delete_btn.set_image(btn_image)
        self.delete_btn.set_relief(Gtk.ReliefStyle.NONE)

        self.add(self.link)
        self.add(self._label)
        self.add(self.delete_btn)
        self.show_all()
        self.set_active(False)

    def set_active(self, active=False):
        if active:
            self.link.hide()
            self._label.show()
        else:
            self._label.hide()
            self.link.show()


class HistorySwitcher(Gtk.Box): 

    def __init__(self):
        super().__init__()

        self.set_name('HistorySwitcherBox')
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_halign(Gtk.Align.END)
        self.set_valign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(False)

        self.link = Gtk.LinkButton()
        self.link.connect('activate-link', self._on_activate_link)
        self.link.set_label('...')

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

    def _on_history_swicther_item(self, link, history_switcher_item):
        self._switch_history(history_switcher_item.name)
        return True

    def _on_history_delete(self, button, history_switcher_item):
        gpaste_client.delete_history(history_switcher_item.name)

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
            history_switcher_item = HistorySwitcherItem(history_name)
            history_switcher_item.link.connect(
                'activate-link',
                self._on_history_swicther_item,
                history_switcher_item
            )
            history_switcher_item.delete_btn.connect(
                'clicked',
                self._on_history_delete,
                history_switcher_item
            )
            self._box.add(history_switcher_item)

            if history_name == current_name:
                self._set_active(history_name)
                history_switcher_item.set_active(True)

        self._box.show_all()

    def show(self):
        self.popover.show()
