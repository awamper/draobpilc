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

import weakref

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Pango

from draobpilc import common
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.widgets.item_thumb import ItemThumb

INFOSTRING_TEMPLATE = '<span size="x-small"><b>▶ %s</b></span>'


class IndicatorBase(Gtk.Box):

    def __init__(self):
        super().__init__()

    def set_kind(self, kind):
        style_context = self.get_style_context()

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


class ItemKindIndicator(IndicatorBase):

    def __init__(self, kind):
        super().__init__()

        self.set_name('HistoryItemKindIndicator')
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(False)
        self.set_size_request(common.SETTINGS[common.KIND_INDICATOR_WIDTH], -1)
        self.set_kind(kind)
        self.show()


class ItemLabel(Gtk.Label):

    def __init__(self):
        super().__init__()

        self.set_name('HistoryItemLabel')
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.CENTER)
        self.set_vexpand(True)
        self.set_ellipsize(Pango.EllipsizeMode.END)
        self.set_line_wrap(True)
        self.set_line_wrap_mode(Pango.WrapMode.CHAR)
        self.set_lines(common.SETTINGS[common.ITEM_MAX_LINES])


class Infobox(Gtk.Box):

    def __init__(self, item):
        super().__init__()

        self.set_name('Infobox')
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.END)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_margin_left(5)
        self.set_margin_bottom(5)

        self._weakref = weakref.ref(item)

        if self.item.app_info:
            name = self.item.app_info.get_display_name()
            gicon = self.item.app_info.get_icon()

            if gicon:
                icon_theme = Gtk.IconTheme.get_default()
                icon_info = icon_theme.lookup_by_gicon(
                    gicon,
                    16,
                    Gtk.IconLookupFlags.FORCE_SIZE
                )
                if icon_info:
                    pixbuf = icon_info.load_icon()
                    icon = Gtk.Image()
                    icon.set_margin_right(5)
                    icon.set_from_pixbuf(pixbuf)
                    self.add(icon)

            if name:
                app_name = Gtk.LinkButton()
                app_name.connect('activate-link', self._on_activate_link)
                app_name.set_halign(Gtk.Align.START)
                app_name.set_name('AppNameLink')
                app_name.set_label(name)
                self.add(app_name)

                style_context = app_name.get_style_context()
                style_context.remove_class('text-button')
                style_context.remove_class('button')

        if self.item.info_string:
            label = Gtk.Label()
            label.set_margin_left(5)
            label.set_halign(Gtk.Align.START)
            label.set_markup(INFOSTRING_TEMPLATE % self.item.info_string)
            self.add(label)

    def _on_activate_link(self, link_button):
        uri = self.item.raw.strip()
        if self.item.kind != HistoryItemKind.LINK:
            uri = 'file://%s' % self.item.raw

        self.item.app_info.launch_uris([uri])
        common.APPLICATION.hide()
        return True

    @property
    def item(self):
        return self._weakref()


class LinksButton(Gtk.LinkButton):

    def __init__(self, item):
        super().__init__()

        self.set_name('LinksButton')
        self.set_label('%i links' % len(item.links))
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.END)
        self.set_margin_left(5)
        self.set_margin_bottom(5)
        self.connect('activate-link', self._on_activate_link)

        style_context = self.get_style_context()
        style_context.remove_class('text-button')
        style_context.remove_class('button')

        self._weakref = weakref.ref(item)

        self._box = Gtk.Box()
        self._box.set_orientation(Gtk.Orientation.VERTICAL)

        height_request = 300
        if len(self.item.links) <= 5: height_request = 150
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC
        )
        scrolled_window.set_size_request(300, height_request)
        scrolled_window.add(self._box)
        scrolled_window.show_all()

        self._popover = Gtk.Popover()
        self._popover.set_relative_to(self)
        self._popover.add(scrolled_window)

        self.populate()

    def _on_activate_link(self, link):
        self._popover.show()
        return True

    def populate(self):
        for link in self.item.links:
            button = Gtk.LinkButton()
            button.set_halign(Gtk.Align.START)
            button.set_label(link[0:40])
            button.set_tooltip_text(link)
            button.set_uri(link)
            button.connect('activate-link', lambda b: common.APPLICATION.hide())
            self._box.add(button)

        self._box.show_all()

    @property
    def item(self):
        return self._weakref()


class FilesButton(LinksButton):

    def __init__(self, item):
        super().__init__(item)

        self.set_label('%i files' % self.item.n_lines)

    def _on_activate_file_link(self, link_button, file_name):
        uri = 'file://%s' % file_name
        Gio.AppInfo.launch_default_for_uri(uri)
        common.APPLICATION.hide()
        return True

    def populate(self):
        for file_ in self.item.raw.split('\n'):
            button = Gtk.LinkButton()
            button.set_halign(Gtk.Align.START)
            button.set_label(file_[0:40])
            button.set_tooltip_text(file_)
            button.connect('activate-link', self._on_activate_file_link, file_)
            self._box.add(button)

        self._box.show_all()


class ActiveIndicator(IndicatorBase):

    def __init__(self, kind):
        super().__init__()

        self.set_name('HistoryItemViewActiveIndicator')
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.START)
        self.set_no_show_all(True)
        self.set_size_request(-1, 4)
        self.hide()

        self.set_kind(kind)


class ShortcutHint(Gtk.Box):

    def __init__(self):
        super().__init__()

        self.set_name('HistoryItemViewShortcutHint')
        self.set_no_show_all(True)
        self.set_vexpand(False)
        self.set_hexpand(False)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.START)
        self.set_size_request(40, 40)

        self.label = Gtk.Label()
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_vexpand(False)
        self.label.set_hexpand(True)
        self.label.show()

        self.add(self.label)

    def set_hint(self, text):
        self.label.set_label(text)


class HistoryItemView(Gtk.Box):

    def __init__(self, history_item):
        super().__init__()

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_name('HistoryItemBox')
        self.connect('enter-notify-event', self._on_enter_event)
        self.connect('leave-notify-event', self._on_leave_event)

        self._weakref = weakref.ref(history_item, lambda w: self.destroy())
        self._preview = None
        self._kind_indicator = ItemKindIndicator(self.item.kind)
        self._label = ItemLabel()
        self._active_indicator = ActiveIndicator(self.item.kind)
        self._shortcut_hint = ShortcutHint()
        self.set_active(False)

        if (
            self.item.kind == HistoryItemKind.TEXT and self.item.links
        ):
            self._infobox = LinksButton(self.item)
        elif (
            self.item.kind == HistoryItemKind.FILE and
            self.item.n_lines > 1
        ):
            self._infobox = FilesButton(self.item)
        else:
            if (
                self.item.kind == HistoryItemKind.LINK or
                self.item.kind == HistoryItemKind.FILE or
                common.SETTINGS[common.SHOW_TEXT_INFO]
            ):
                self._infobox = Infobox(self.item)
            else:
                # dummy
                self._infobox = Gtk.Box()

        self._grid = Gtk.Grid()
        self._grid.attach(self._kind_indicator, 1, 1, 1, 2)
        self._grid.attach(self._label, 2, 1, 1, 1)
        self._grid.attach(self._infobox, 2, 2, 1, 1)
        self._grid.attach(self._active_indicator, 0 , 0, 3, 1)

        if (
            self.item.thumb_path and
            common.SETTINGS[common.SHOW_THUMBNAILS]
        ):
            self._preview = ItemThumb(
                self.item.thumb_path,
                -1,
                common.SETTINGS[common.ITEM_MAX_HEIGHT]
            )
            self._grid.attach(self._preview, 1, 1, 1, 2)

        overlay = Gtk.Overlay()
        overlay.add(self._grid)
        overlay.add_overlay(self._shortcut_hint)

        self.add(overlay)
        self.show_all()

    def _on_enter_event(self, box, event):
        pass

    def _on_leave_event(self, box, event):
        pass

    def set_label(self, markup):
        self._label.set_markup(markup)

    def set_active(self, active):
        if active:
            self._active_indicator.show()
        else:
            self._active_indicator.hide()

    def show_shortcut_hint(self, hint):
        if hint is None:
            self._shortcut_hint.hide()
        else:
            self._shortcut_hint.set_hint(str(hint))
            self._shortcut_hint.show()

    @property
    def item(self):
        return self._weakref()
    