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

from distutils.version import StrictVersion

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf

from draobpilc import get_data_path
from draobpilc import common
from draobpilc import version
from draobpilc.lib import utils
from draobpilc.lib import gpaste_client
from draobpilc.history_item import HistoryItem
from draobpilc.history_items import HistoryItems
from draobpilc.widgets.window import Window
from draobpilc.widgets.editor import Editor
from draobpilc.widgets.merger import Merger
from draobpilc.widgets.items_view import ItemsView
from draobpilc.widgets.about_dialog import AboutDialog

CONNECTION_IDS = {
    'SHOW_EDITOR': 0,
    'HIDE_EDITOR': 0
}
SHOW_EDITOR_TIMEOUT = 500 # ms
HIDE_EDITOR_TIMEOUT = 1000 # ms


class Application(Gtk.Application):

    def __init__(self):
        super().__init__()

        self.set_application_id(version.APP_ID)
        self.set_flags(Gio.ApplicationFlags.FLAGS_NONE)

        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(common.CSS_PATH)
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        gtk_settings = Gtk.Settings.get_default()
        gtk_settings.props.gtk_application_prefer_dark_theme = True

        self._window = None
        self._editor = Editor()
        self._editor.connect('enter-notify', self._on_editor_enter)
        self._editor.connect('leave-notify', self._on_editor_leave)
        self._merger = Merger()
        self._history_items = HistoryItems()

        self._items_view = ItemsView()
        self._items_view.connect('item-activated', self._on_item_activated)
        self._items_view.connect('item-entered',
            lambda view, item: (
                self._show_editor(item) if view.n_selected == 1 else None
            )
        )
        self._items_view.connect('item-left',
            lambda view, item: self._hide_editor()
        )
        self._items_view.listbox.connect(
            'selected-rows-changed',
            self._on_selection_changed
        )
        self._items_view.bind(self._history_items)

        gpaste_client.connect('ShowHistory', self.toggle)
        common.APPLICATION = self

    def _check_version(self):
        current_version = gpaste_client.get_prop('Version')

        if (
            StrictVersion(current_version) <
            StrictVersion(version.GPASTE_VERSION)
        ):
            msg = _(
                'GPaste version >= {0} is required, '
                'current version == {1}.'
            ).format(
                version.GPASTE_VERSION,
                current_version
            )
            message_dialog = Gtk.MessageDialog(
                None,
                Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                version.APP_NAME
            )
            message_dialog.set_position(Gtk.WindowPosition.CENTER)
            message_dialog.set_icon_from_file(common.ICON_PATH)
            message_dialog.props.secondary_text = msg
            message_dialog.run()
            self.quit()

    def _resize(self, window, event):
        size = window.get_size()

        list_width = round(
            size[0] / 100 * common.SETTINGS[common.WIDTH_PERCENTS]
        )

        editor_width = round(
            (size[0] - list_width) / 100 *
            common.SETTINGS[common.EDITOR_WIDTH_PERCENTS]
        )
        editor_height = round(
            size[1] / 100 * common.SETTINGS[common.EDITOR_HEIGHT_PERCENTS]
        )

        self._items_view.set_size_request(list_width, -1)
        self._editor.set_size_request(editor_width, editor_height)
        self._merger.set_size_request(editor_width, editor_height)

    def _on_selection_changed(self, listbox):
        selected = self._items_view.get_selected()
        if not selected: return

        if len(selected) == 1:
            self._merger.hide()

            if self._editor.is_visible():
                self._hide_editor()

            self._show_editor(selected[0])
        elif not selected:
            self._hide_editor()
            self._merger.hide()
        else:
            if CONNECTION_IDS['SHOW_EDITOR']:
                GLib.source_remove(CONNECTION_IDS['SHOW_EDITOR'])
                CONNECTION_IDS['SHOW_EDITOR'] = 0

            self._editor.hide()

            self._merger.set_items(selected)
            self._merger.show()

    def _on_item_activated(self, items_view, history_item):
        gpaste_client.select(history_item.index)
        self._items_view.search_box.entry.set_text('')
        self.hide()

    def _show_editor(self, history_item):
        def on_timeout():
            CONNECTION_IDS['SHOW_EDITOR'] = 0
            self._editor.set_item(history_item)
            self._editor.show()

        if CONNECTION_IDS['HIDE_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['HIDE_EDITOR'])
            CONNECTION_IDS['HIDE_EDITOR'] = 0

        if CONNECTION_IDS['SHOW_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['SHOW_EDITOR'])
            CONNECTION_IDS['SHOW_EDITOR'] = 0

        if not self._merger.get_reveal_child():
            CONNECTION_IDS['SHOW_EDITOR'] = GLib.timeout_add(
                SHOW_EDITOR_TIMEOUT,
                on_timeout
            )

    def _hide_editor(self):
        def on_timeout():
            CONNECTION_IDS['HIDE_EDITOR'] = 0
            self._editor.hide(clear_after_transition=True)

        if CONNECTION_IDS['HIDE_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['HIDE_EDITOR'])
            CONNECTION_IDS['HIDE_EDITOR'] = 0

        CONNECTION_IDS['HIDE_EDITOR'] = GLib.timeout_add(
            HIDE_EDITOR_TIMEOUT,
            on_timeout
        )

    def _on_editor_enter(self, editor, event):
        if CONNECTION_IDS['HIDE_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['HIDE_EDITOR'])
            CONNECTION_IDS['HIDE_EDITOR'] = 0

    def _on_editor_leave(self, editor, event):
        self._hide_editor()

    def _on_delete_action(self, action, param):
        selected_items = self._items_view.get_selected()
        if not selected_items: return

        index = selected_items[0].index
        gpaste_client.delete(index)

    def _hide_on_click(self, window, event):
        pointer_x, pointer_y = event.get_coords()

        if (
            self._editor.get_reveal_child() and
            utils.is_pointer_inside_widget(self._editor)
        ):
            pass
        elif (
            self._merger.get_reveal_child() and
            utils.is_pointer_inside_widget(self._merger)
        ):
            pass
        elif utils.is_pointer_inside_widget(self._items_view):
            pass
        else:
            self.hide()

    def do_activate(self):
        self._check_version()

        if self._window:
            return None

        self._window = Window(self)
        self._window.connect('configure-event', self._resize)
        self._window.connect('button-release-event', self._hide_on_click)
        overlay = Gtk.Overlay()
        overlay.add(self._editor)
        overlay.add_overlay(self._merger)
        self._window.box.add(overlay)
        self._window.box.add(self._items_view)

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.builder = Gtk.Builder()
        file_name = get_data_path('app_menu.ui')
        self.builder.add_from_file(file_name)

        app_menu = self.builder.get_object('app_menu')
        self.set_app_menu(app_menu)

        delete_action = Gio.SimpleAction.new('delete', None)
        delete_action.connect('activate', self._on_delete_action)
        self.add_action(delete_action)
        self.set_accels_for_action('app.delete', ['Delete'])

        delete_action = Gio.SimpleAction.new('show_history_switcher', None)
        delete_action.connect('activate', self.show_history_switcher)
        self.add_action(delete_action)
        self.set_accels_for_action('app.show_history_switcher', ['<Ctrl>S'])

        preferences_action = Gio.SimpleAction.new('preferences', None)
        preferences_action.connect('activate', lambda a, p: self.show_prefs())
        self.add_action(preferences_action)

        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', lambda a, p: self.show_about())
        self.add_action(about_action)

        close_action = Gio.SimpleAction.new('hide', None)
        close_action.connect('activate', lambda a, p: self.hide())
        self.add_action(close_action)

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', lambda a, p: self.quit())
        self.add_action(quit_action)

        if common.SETTINGS[common.STARTUP_NOTIFICATION]:
            utils.notify(body=_(
                '%s is now running, press <b>%s</b> to use it.' % (
                    version.APP_NAME,
                    gpaste_client.SETTINGS['show-history']
                )
            ))

    def toggle(self):
        if self._window.props.visible:
            self.hide()
        else:
            self.show()

    def show_history_switcher(self, action, param):
        self._items_view.history_switcher.show()

    def show_prefs(self):
        preferences_dialog = PreferencesDialog()
        preferences_dialog.set_modal(True)
        preferences_dialog.set_transient_for(self._window)
        preferences_dialog.run()
        preferences_dialog.destroy()

    def show_about(self):
        about_dialog = AboutDialog()
        about_dialog.set_transient_for(self._window)
        about_dialog.show()

    def show(self):
        self._window.show_all()
        self._window.maximize()
        self._window.get_window().focus(Gdk.CURRENT_TIME)
        self._window.present_with_time(Gdk.CURRENT_TIME)
        self._items_view.select_first()

    def hide(self):
        self._window.hide()
