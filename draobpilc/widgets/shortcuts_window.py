#!/usr/bin/env python3

# Copyright 2016 Ivan awamper@gmail.com
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

SHORTCUTS_LIST = []
SHORTCUTS = (
    (_('All Shortcuts'), SHORTCUTS_LIST),
)

for key, value in common.SHORTCUTS_KEYS.items():
    SHORTCUTS_LIST.append((common.SETTINGS[key], value))


def _build_shortcut_window(data):
    window = Gtk.ShortcutsWindow()
    section = Gtk.ShortcutsSection()
    section.show()

    for group_title, shortcuts in data:
        group = Gtk.ShortcutsGroup(title=group_title)
        group.show()

        for accel, shortcut_title in shortcuts:
            short = Gtk.ShortcutsShortcut(
                title=shortcut_title,
                accelerator=accel
            )
            short.show()
            group.add(short)

        section.add(group)

    window.add(section)
    return window


def is_supported():
    return hasattr(Gtk, 'ShortcutsWindow')


def show_or_false(parent):
    if is_supported():
        window = _build_shortcut_window(SHORTCUTS)
        window.set_transient_for(parent)
        window.set_position(Gtk.WindowPosition.CENTER)
        window.set_modal(True)
        window.show()
        return True
    else:
        return False
