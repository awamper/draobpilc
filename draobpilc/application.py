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

from keybinder.keybinder_gtk import KeybinderGtk

from draobpilc import get_data_path
from draobpilc import common
from draobpilc import version
from draobpilc.processors import (
    editor,
    merger,
    previewer
)
from draobpilc.lib import utils
from draobpilc.lib import gpaste_client
from draobpilc.history_item import HistoryItem
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.history_items import HistoryItems
from draobpilc.widgets import shortcuts_window
from draobpilc.widgets.window import Window
from draobpilc.widgets.search_box import SearchBox
from draobpilc.widgets.items_view import ItemsView
from draobpilc.widgets.main_toolbox import MainToolbox
from draobpilc.widgets.about_dialog import AboutDialog
from draobpilc.widgets.preferences import show_preferences
from draobpilc.widgets.items_processors import ItemsProcessors
from draobpilc.widgets.backup_history_dialog import BackupHistoryDialog
from draobpilc.widgets import clipboard_preview


class Application(Gtk.Application):

    def __init__(self):
        super().__init__()

        self.set_application_id(version.APP_ID)
        self.set_flags(Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

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
        self._editor = editor.Editor()
        self._previewer = previewer.Previewer()
        self._merger = merger.Merger()
        self._merger.connect('merge', self.merge_items)
        self._items_processors = ItemsProcessors()
        self._items_processors.add_processor(self._editor)
        self._items_processors.add_processor(self._previewer)
        self._items_processors.add_processor(self._merger)

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
        self._main_toolbox.restart_btn.connect(
            'clicked',
            self._restart_daemon
        )
        self._main_toolbox.close_btn.connect(
            'clicked',
            lambda b: self.hide(reset_search=True)
        )
        self._main_toolbox.track_btn.connect('clicked',
            lambda b: gpaste_client.track(b.get_active())
        )
        self._main_toolbox.track_btn.set_active(
            gpaste_client.get_prop('Active')
        )
        self._main_toolbox.help_btn.connect(
            'clicked',
            lambda b: shortcuts_window.show_or_false(self._window)
        )

        self._history_items = HistoryItems()

        self._search_box = SearchBox()
        self._search_box.connect('search-changed',
            self._on_search_changed
        )
        self._search_box.connect('search-index',
            lambda sb, i: self._on_search_changed(sb, search_index=i)
        )
        self._search_box.entry.connect('activate',
            self._on_entry_activated
        )

        self._items_view = ItemsView()
        self._items_view.connect(
            'item-activated',
            self._on_item_activated
        )
        self._items_view.connect(
            'item-entered',
            self._on_item_entered
        )
        self._items_view.connect(
            'item-left',
            lambda iv, i: self.selection_changed()
        )
        self._items_view.listbox.connect(
            'selected-rows-changed',
            lambda iv: self.selection_changed()
        )
        self._items_view.bind(self._history_items)

        gpaste_client.connect('ShowHistory', self.toggle)
        gpaste_client.connect('Tracking',
            lambda t: self._main_toolbox.track_btn.set_active(t)
        )
        common.APPLICATION = self

        keybinder = KeybinderGtk()
        keybinder.register(
            common.SETTINGS[common.SHOW_CLIPBOARD_PREVIEW],
            lambda *_, **__: GLib.idle_add(clipboard_preview.toggle)
        )
        keybinder.start()

    def _resize(self, window, event):
        size = window.get_size()

        list_width = round(
            size[0] / 100 * common.SETTINGS[common.WIDTH_PERCENTS]
        )

        processors_width = round(
            (size[0] - list_width) / 100 *
            common.SETTINGS[common.PROCESSOR_WIDTH_PERCENTS]
        )
        processors_height = round(
            size[1] / 100 * common.SETTINGS[common.PROCESSOR_HEIGHT_PERCENTS]
        )

        self._items_view.set_size_request(list_width, -1)
        self._items_processors.set_size_request(
            processors_width,
            processors_height
        )
        self._previewer.set_max_size(processors_width, processors_height)

    def _on_search_changed(self, search_box, search_index=None):
        self._history_items.filter(
            term=self._search_box.search_text,
            kinds=self._search_box.flags,
            index=search_index
        )

    def _on_entry_activated(self, entry):
        items = self._items_view.get_selected()
        if items: self._on_item_activated(self._items_view, items[0])
        return True

    def _on_item_activated(self, items_view, history_item):
        gpaste_client.select(history_item.index)
        self._search_box.entry.set_text('')
        self.hide()

    def _on_item_entered(self, items_view, item):
        if self._items_view.n_selected != 1: return

        self._items_processors.set_items(
            [item],
            timeout=common.SETTINGS[common.SET_ITEMS_TIMEOUT]
        )

    def _on_delete_action(self, action, param):
        selected_items = self._items_view.get_selected()
        if not selected_items: return

        self.delete_items(selected_items)

    def _on_open_item(self, action, param):
        selected_items = self._items_view.get_selected()
        if not selected_items: return
        item = selected_items[0]
        if not item.app_info: return

        uri = item.raw.strip()
        if item.kind != HistoryItemKind.LINK:
            uri = 'file://%s' % item.raw

        item.app_info.launch_uris([uri])
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

    def _on_backup_history(self, action, param):
        dialog = BackupHistoryDialog(self._window)
        dialog.run()

    def _on_reset_search_action(self, action, param):
        self._search_box.reset()
        self._search_box.entry.grab_focus()

    def _on_key_press(self, window, event):
        if not common.SETTINGS[common.ENABLE_ACTIVATE_NUMBER_KB]: return

        result, keyval = event.get_keyval()
        is_control = event.get_state() == Gdk.ModifierType.CONTROL_MASK
        number_keyvals = [
            Gdk.KEY_1,
            Gdk.KEY_2,
            Gdk.KEY_3,
            Gdk.KEY_4,
            Gdk.KEY_5,
            Gdk.KEY_6,
            Gdk.KEY_7,
            Gdk.KEY_8,
            Gdk.KEY_9
        ]

        if keyval == Gdk.KEY_Control_L:
            self._items_view.show_shortcut_hints(True)
        else:
            if is_control and keyval in number_keyvals:
                self._items_view.show_shortcut_hints(False)
                item = self._items_view.get_for_shortcut(
                    number_keyvals.index(keyval)
                )
                if item: self._items_view.activate_item(item)

    def _on_key_release(self, window, event):
        if not common.SETTINGS[common.ENABLE_ACTIVATE_NUMBER_KB]: return

        result, keyval = event.get_keyval()

        if keyval == Gdk.KEY_Control_L:
            self._items_view.show_shortcut_hints(False)

    def _bind_action(self, name, target, settings_key, callback):
        def on_settings_change(settings, key, target):
            self.set_accels_for_action(target, [settings[key]])

        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        self.set_accels_for_action(
            target,
            [common.SETTINGS[settings_key]]
        )

        common.SETTINGS.connect(
            'changed::' + settings_key,
            on_settings_change,
            target
        )

    def selection_changed(self):
        selected = self._items_view.get_selected()
        self._items_processors.set_items(
            selected,
            timeout=common.SETTINGS[common.SET_ITEMS_TIMEOUT]
        )

    def delete_items(self, items, resume_selection=True):
        delete_indexes = [item.index for item in items]
        delete_indexes = sorted(delete_indexes)

        self._history_items.freeze(True)
        if resume_selection: self._items_view.save_selection()

        for i, index in enumerate(delete_indexes):
            delete_index = index - i
            if delete_index < 0: continue
            gpaste_client.delete(delete_index)

        filter_active = self._search_box.search_text or self._search_box.flags
        self._history_items.freeze(False)
        self._history_items.reload_history(emit_signal=not filter_active)

        if filter_active:
            self._on_search_changed(self._search_box)

        if resume_selection: self._items_view.resume_selection()

    def merge_items(self, merger, items, delete_merged):
        merged_text = self._merger.buffer.props.text
        if not merged_text: return

        if delete_merged: self.delete_items(items, resume_selection=False)
        gpaste_client.add(merged_text)
        self.hide()

    def do_command_line(self, command_line):
        Gtk.Application.do_command_line(self, command_line)

        show_preferences = False
        if '--preferences' in command_line.get_arguments():
            show_preferences = True

        self.do_activate(show_preferences)
        
        return 0

    def do_activate(self, show_preferences_dialog=False):
        if self._window:
            if show_preferences_dialog: show_preferences()
            else: self.show()
            return None

        right_box = Gtk.Box()
        right_box.set_name('RightBox')
        right_box.set_orientation(Gtk.Orientation.VERTICAL)
        right_box.add(self._search_box)
        right_box.add(self._items_view)

        self._window = Window(self)
        self._window.connect('configure-event', self._resize)
        self._window.connect('key-press-event', self._on_key_press)
        self._window.connect('key-release-event', self._on_key_release)
        self._window.connect(
            'focus-out-event',
            lambda _, __: self._items_view.show_shortcut_hints(False)
        )
        self._window.grid.attach(self._items_processors, 0, 0, 1, 1)
        self._window.grid.attach(self._main_toolbox, 0, 1, 1, 1)
        self._window.grid.attach(right_box, 1, 0, 1, 2)

        if show_preferences_dialog: show_preferences()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        actions = [
            [
                'delete',
                'app.delete',
                common.DELETE_ITEM,
                self._on_delete_action
            ],
            [
                'show_histories',
                'app.show_histories',
                common.SHOW_HISTORIES,
                self.show_histories_manager
            ],
            [
                'focus_search',
                'app.focus_search',
                common.FOCUS_SEARCH,
                lambda _, __: self._search_box.entry.grab_focus()
            ],
            [
                'reset_search',
                'app.reset_search',
                common.RESET_SEARCH,
                self._on_reset_search_action
            ],
            [
                'editor_wrap_text',
                'app.editor_wrap_text',
                common.EDITOR_WRAP_TEXT_SHORTCUT,
                self._on_editor_wrap_action
            ],
            [
                'open_item',
                'app.open_item',
                common.OPEN_ITEM,
                self._on_open_item
            ],
            [
                'backup_history',
                'app.backup_history',
                common.BACKUP_HISTORY,
                self._on_backup_history
            ],
            [
                'keep_search',
                'app.keep_search',
                common.KEEP_SEARCH_AND_CLOSE,
                lambda _, __: self.hide(False)
            ],
            [
                'hide',
                'app.hide',
                common.HIDE_APP,
                lambda _, __: self.hide()
            ],
            [
                'quit',
                'app.quit',
                common.QUIT_APP,
                lambda _, __: self.quit()
            ],
            [
                'show_help',
                'app.show_help',
                common.SHOW_HELP,
                lambda _, __: shortcuts_window.show_or_false(self._window)
            ],
            [
                'load_all_history',
                'app.load_all_history',
                common.LOAD_ALL_HISTORY,
                lambda _, __: self._items_view.load_rest_items()
            ]
        ]

        for name, target, key, callback in actions:
            self._bind_action(name, target, key, callback)

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

        grab_focus = True

        if (
            self._search_box.entry.get_text() or
            common.SETTINGS[common.FOCUS_SEARCH_ON_OPEN]
        ):
            self._search_box.entry.grab_focus()
            grab_focus = False

        self._items_view.select_first(grab_focus=grab_focus)

    def hide(self, reset_search=True):
        self._window.hide()
        if reset_search: self._search_box.reset()
