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

import os

from gi.repository import Gtk

from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.lib import gpaste_client
from draobpilc.processors.processor_textwindow import TextWindow
from draobpilc.widgets.items_processor_base import (
    ItemsProcessorBase,
    ItemsProcessorPriority
)


class Editor(ItemsProcessorBase):

    def __init__(self):
        super().__init__(
            _('Edit'),
            priority=ItemsProcessorPriority.NORMAL,
            default=True
        )

        self._text_window = TextWindow()
        self._text_window.connect('changed', self._edit_item)
        self._text_window.textview.set_name('EditorTextView')

        self.grid.set_name('EditorGrid')
        self.grid.attach(self._text_window, 0, 0, 1, 1)

    def _edit_item(self, text_window, buffer):
        if not self.item: return

        contents = self._text_window.buffer.props.text

        if contents and contents != self.item.raw:
            gpaste_client.replace(self.item.index, contents)

    def clear(self):
        super().clear()

        self._text_window.buffer.set_text('')
        self._text_window.set_sensitive(False)

    def set_items(self, items):
        self.items = items
        self._text_window.set_sensitive(True)
        self._text_window.buffer.set_text(self.item.raw)
        self._text_window.set_filename(None)

    def can_process(self, items):
        if (
            len(items) == 1 and (
                items[0].kind == HistoryItemKind.TEXT or
                items[0].kind == HistoryItemKind.LINK
            )
        ):
            return True
        else:
            return False
