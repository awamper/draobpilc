#!/usr/bin/env python3

# Copyright 2016-2025 Ivan awamper@gmail.com
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

from __future__ import annotations

from typing import Any, List, Tuple, TYPE_CHECKING

from gi.repository import Gtk  # type: ignore

from draobpilc import common

if TYPE_CHECKING:
    _ = lambda s: s

SHORTCUTS_LIST: List[Tuple[str, str]] = []
SHORTCUTS: List[Tuple[str, List[Tuple[str, str]]]] = [
    (_('All Shortcuts'), SHORTCUTS_LIST),
]

for key, value in common.SHORTCUTS_KEYS.items():
    SHORTCUTS_LIST.append((common.SETTINGS[key], value))

NUMBERS_LIST: List[Tuple[str, str]] = []
SHORTCUTS.append(
    (_('Activate item'), NUMBERS_LIST),
)

for i in range(1, 10):
    NUMBERS_LIST.append((_(f'<Ctrl>{i}'), _(f'Activate item #{i}')))


def _build_shortcut_window(data: List[Tuple[str, List[Tuple[str, str]]]]) -> Gtk.ShortcutsWindow:
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


def is_supported() -> bool:
    return hasattr(Gtk, 'ShortcutsWindow')


def show_or_false(parent: Gtk.Window) -> bool:
    if is_supported():
        window = _build_shortcut_window(SHORTCUTS)
        window.set_transient_for(parent)
        window.set_position(Gtk.WindowPosition.CENTER)
        window.set_modal(True)
        window.show()
        return True
    else:
        return False

