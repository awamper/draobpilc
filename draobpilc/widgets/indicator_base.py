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

from gi.repository import Gtk  # type: ignore

from draobpilc.history_item_kind import HistoryItemKind


class IndicatorBase(Gtk.Box):

    def __init__(self) -> None:
        super().__init__()

    def set_kind(self, kind: HistoryItemKind) -> None:
        style_context: Gtk.StyleContext = self.get_style_context()

        for class_ in style_context.list_classes():
            style_context.remove_class(class_)

        if kind == HistoryItemKind.FILE:
            style_context.add_class('file')
        elif kind == HistoryItemKind.IMAGE:
            style_context.add_class('image')
        elif kind == HistoryItemKind.LINK:
            style_context.add_class('link')
        else:
            style_context.add_class('text')
