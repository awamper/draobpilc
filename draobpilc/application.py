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

from dbus.exceptions import DBusException

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
from draobpilc.widgets.main_toolbox import MainToolbox
from draobpilc.widgets.about_dialog import AboutDialog
from draobpilc.widgets.preferences import show_preferences

CONNECTION_IDS = {
    'SHOW_EDITOR': 0,
    'HIDE_EDITOR': 0
}


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
        self._merger.connect('merge', self.merge_items)

        self._main_toolbox = MainToolbox()
        self._main_toolbox.prefs_btn.connect('clicked',
            lambda b: self.show_prefs()
        )
        self._main_toolbox.about_btn.connect('clicked',
            lambda b: self.show_about()
        )
        self._main_toolbox.quit_btn.connect('clicked',
            lambda b: self.quit()
        )
        self._main_toolbox.track_btn.connect('clicked',
            lambda b: gpaste_client.track(b.get_active())
        )
        self._main_toolbox.track_btn.set_active(gpaste_client.get_prop('Active'))
        self._main_toolbox.restart_btn.connect('clicked', self._restart_daemon)

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
        gpaste_client.connect('Tracking',
            lambda t: self._main_toolbox.track_btn.set_active(t)
        )
        common.APPLICATION = self

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
            self._merger.reveal(False)

            if self._editor.is_visible():
                self._hide_editor()

            self._show_editor(selected[0])
        elif not selected:
            self._hide_editor()
            self._merger.reveal(False)
        else:
            if CONNECTION_IDS['SHOW_EDITOR']:
                GLib.source_remove(CONNECTION_IDS['SHOW_EDITOR'])
                CONNECTION_IDS['SHOW_EDITOR'] = 0

            self._editor.reveal(False)

            self._merger.set_items(selected)
            self._merger.reveal(True)

    def _on_item_activated(self, items_view, history_item):
        gpaste_client.select(history_item.index)
        self._items_view.search_box.entry.set_text('')
        self.hide()

    def _show_editor(self, history_item):
        def on_timeout():
            CONNECTION_IDS['SHOW_EDITOR'] = 0
            self._editor.set_item(history_item)
            self._editor.reveal(True)

        if CONNECTION_IDS['HIDE_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['HIDE_EDITOR'])
            CONNECTION_IDS['HIDE_EDITOR'] = 0

        if CONNECTION_IDS['SHOW_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['SHOW_EDITOR'])
            CONNECTION_IDS['SHOW_EDITOR'] = 0

        if not self._merger.get_reveal_child():
            CONNECTION_IDS['SHOW_EDITOR'] = GLib.timeout_add(
                common.SETTINGS[common.SHOW_EDITOR_TIMEOUT],
                on_timeout
            )

    def _hide_editor(self):
        def on_timeout():
            CONNECTION_IDS['HIDE_EDITOR'] = 0
            self._editor.reveal(False, clear_after_transition=True)

        if CONNECTION_IDS['HIDE_EDITOR']:
            GLib.source_remove(CONNECTION_IDS['HIDE_EDITOR'])
            CONNECTION_IDS['HIDE_EDITOR'] = 0

        CONNECTION_IDS['HIDE_EDITOR'] = GLib.timeout_add(
            common.SETTINGS[common.HIDE_EDITOR_TIMEOUT],
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

    def _on_open_item(self, action, param):
        selected_items = self._items_view.get_selected()
        if not selected_items: return
        item = selected_items[0]
        if not item.app_info: return

        uri = item.raw.strip()
        if item.kind != gpaste_client.Kind.LINK:
            uri = 'file://%s' % item.raw

        item.app_info.launch_uris([uri])
        self.hide()

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
        elif utils.is_pointer_inside_widget(self._main_toolbox):
            pass
        else:
            self.hide()

    def _restart_daemon(self, button):
        try:
            gpaste_client.reexecute()
        except DBusException:
            pass

        utils.restart_app()

    def _on_editor_wrap_action(self, action, param):
        if common.SETTINGS[common.EDITOR_WRAP_TEXT]:
            common.SETTINGS[common.EDITOR_WRAP_TEXT] = False
        else:
            common.SETTINGS[common.EDITOR_WRAP_TEXT] = True

    def merge_items(self, merger, items):
        merged_text = self._merger.buffer.props.text
        if not merged_text: return

        gpaste_client.add(merged_text)
        self._items_view.halt_updates = False
        self.hide()
        self._merger.reveal(False)

    def do_activate(self):
        if self._window:
            self.show()
            return None

        overlay = Gtk.Overlay()
        overlay.add(self._merger)
        overlay.add_overlay(self._editor)

        self._window = Window(self)
        self._window.connect('configure-event', self._resize)
        self._window.connect('button-release-event', self._hide_on_click)
        self._window.grid.attach(overlay, 0, 0, 1, 1)
        self._window.grid.attach(self._items_view, 1, 0, 1, 2)
        self._window.grid.attach(self._main_toolbox, 0, 1, 1, 1)

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
        self.set_accels_for_action(
            'app.delete',
            [common.SETTINGS[common.DELETE_ITEM]]
        )

        show_histories_action = Gio.SimpleAction.new('show_histories_manager', None)
        show_histories_action.connect('activate', self.show_histories_manager)
        self.add_action(show_histories_action)
        self.set_accels_for_action(
            'app.show_histories_manager',
            [common.SETTINGS[common.SHOW_HISTORIES]]
        )

        focus_search_action = Gio.SimpleAction.new('focus_search', None)
        focus_search_action.connect('activate',
            lambda a, p: self._items_view.search_box.entry.grab_focus()
        )
        self.add_action(focus_search_action)
        self.set_accels_for_action(
            'app.focus_search',
            [common.SETTINGS[common.FOCUS_SEARCH]]
        )

        editor_wrap_action = Gio.SimpleAction.new('editor_wrap_text', None)
        editor_wrap_action.connect('activate', self._on_editor_wrap_action)
        self.add_action(editor_wrap_action)
        self.set_accels_for_action(
            'app.editor_wrap_text',
            [common.SETTINGS[common.EDITOR_WRAP_TEXT_SHORTCUT]]
        )

        open_item_action = Gio.SimpleAction.new('open_item', None)
        open_item_action.connect('activate', self._on_open_item)
        self.add_action(open_item_action)
        self.set_accels_for_action(
            'app.open_item',
            [common.SETTINGS[common.OPEN_ITEM]]
        )

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

    def show_histories_manager(self, action, param):
        self._items_view.histories_manager.show()

    def show_prefs(self):
        show_preferences()
        self.hide()

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
