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

from gi.repository import Gdk, Gtk

from draobpilc import common
from draobpilc.history_item import HistoryItem
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.processors import editor, previewer
from draobpilc.widgets.history_item_view import (FilesButton, Infobox,
                                                 LinksButton)
from draobpilc.widgets.items_processors import ItemsProcessors


class PreviewWindow(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_title('Clipboard Preview')
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_modal(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_urgency_hint(True)
        self.set_decorated(False)
        self.set_name('ClipboardPreview')
        self.set_icon_from_file(common.ICON_PATH)
        self.set_keep_above(True)
        self.set_keep_below(False)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.connect('configure-event', self._resize)
        self.stick()
        self.maximize()

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        self.set_visual(visual)

        self.box = Gtk.Box()
        self.box.set_orientation(Gtk.Orientation.VERTICAL)
        self.box.set_valign(Gtk.Align.CENTER)
        self.box.set_halign(Gtk.Align.CENTER)

        self.add(self.box)

    def _resize(self, window, event):
        pass


class ClipboardPreview(PreviewWindow):

    def __init__(self, history_item=None):
        super().__init__()

        self._title = Gtk.Label('Clipboard Contents')
        self._title.set_name('ClipboardPreviewTitle')
        self._title.set_vexpand(False)
        self._title.set_hexpand(True)
        self._title.set_valign(Gtk.Align.CENTER)
        self._title.set_halign(Gtk.Align.FILL)

        self._editor = editor.Editor()
        self._previewer = previewer.Previewer()

        self._items_processors = ItemsProcessors()
        self._items_processors.set_hexpand(False)
        self._items_processors.set_vexpand(False)
        self._items_processors.show_switcher = False
        self._items_processors.add_processor(self._editor)
        self._items_processors.add_processor(self._previewer)

        self._bottom_box = Gtk.Box()
        self._bottom_box.set_name('ClipboardPreviewBottom')
        self._bottom_box.set_hexpand(True)
        self._bottom_box.set_halign(Gtk.Align.FILL)
        self._bottom_box.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.box.add(self._title)
        self.box.add(self._items_processors)
        self.box.add(self._bottom_box)

        if history_item: self.set_item(history_item)

    def _resize(self, window, event):
        size = window.get_size()

        processors_width = round(size[0] * 0.5)
        processors_height = round(size[1] * 0.5)

        self._items_processors.set_size_request(
            processors_width,
            processors_height
        )
        self._previewer.set_max_size(
            processors_width,
            processors_height
        )
        self._previewer.reload()

    def set_item(self, history_item):
        self._items_processors.set_items([history_item])

        for child in self._bottom_box.get_children(): child.destroy()
        button = None
        show_infobox = True

        if (
            len(history_item.links) > 1 or (
                history_item.kind == HistoryItemKind.FILE and
                history_item.n_lines > 1
            )
        ):
            if history_item.kind == HistoryItemKind.FILE:
                button = FilesButton(history_item)
                show_infobox = False
            else:
                button = LinksButton(history_item)
                show_infobox = False

        if show_infobox:
            infobox = Infobox(history_item)
            infobox.set_hexpand(False)
            infobox.set_halign(Gtk.Align.START)
        else:
            infobox = None

        if infobox: self._bottom_box.add(infobox)

        if button:
            if infobox:
                button.set_halign(Gtk.Align.END)
            else:
                button.set_halign(Gtk.Align.START)

            button.set_hexpand(True)
            self._bottom_box.add(button)

        self._bottom_box.show_all()


class ClipboardEmpty(PreviewWindow):

    def __init__(self):
        super().__init__()

        self._title = Gtk.Label('Clipboard is empty')
        self._title.set_name('ClipboardPreviewEmptyLabel')
        self._title.set_vexpand(True)
        self._title.set_hexpand(True)
        self._title.set_valign(Gtk.Align.CENTER)
        self._title.set_halign(Gtk.Align.CENTER)
        self.box.add(self._title)

    def set_item(self, item):
        pass


EMPTY_WINDOW = ClipboardEmpty()
PREVIEW_WINDOW = ClipboardPreview()
PREVIEW_WINDOW.connect('key-release-event', lambda _, __: hide())
_current_window = PREVIEW_WINDOW


def get_history_item_for_clipboard():
    clipboard = Gtk.Clipboard.get_default(Gdk.Display.get_default())

    if clipboard.wait_is_image_available():
        kind = HistoryItemKind.IMAGE
    elif clipboard.wait_is_uris_available():
        kind = HistoryItemKind.FILE
    else:
        kind = HistoryItemKind.TEXT

    text = clipboard.wait_for_text()

    if text:
        item = HistoryItem.new_from_raw(text, kind)
    else:
        item = None

    return item


def show():
    item = get_history_item_for_clipboard()

    if not item:
        _current_window = EMPTY_WINDOW
    else:
        _current_window = PREVIEW_WINDOW

    _current_window.set_item(item)
    _current_window.show_all()
    _current_window.maximize()
    _current_window.get_window().focus(Gdk.CURRENT_TIME)
    _current_window.present_with_time(Gdk.CURRENT_TIME)


def hide():
    _current_window.hide()


def toggle():
    if _current_window.is_visible():
        hide()
    else:
        show()
