#!/usr/bin/env python3

# Copyright 2015-2025 Ivan awamper@gmail.com
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

import argparse
import logging
import threading
from typing import Any, Callable, List, Optional, TYPE_CHECKING

from dbus.exceptions import DBusException  # type: ignore
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk  # type: ignore

from draobpilc import common, get_data_path, version
from draobpilc.history_item import HistoryItem
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.history_items import HistoryItems
from draobpilc.lib import gpaste_client, utils
from draobpilc.processors import editor, merger, previewer
from draobpilc.widgets import shortcuts_window
from draobpilc.widgets.about_dialog import AboutDialog
from draobpilc.widgets.backup_history_dialog import BackupHistoryDialog
from draobpilc.widgets.items_processors import ItemsProcessors
from draobpilc.widgets.items_view import ItemsView
from draobpilc.widgets.main_toolbox import MainToolbox
from draobpilc.widgets.preferences import show_preferences
from draobpilc.widgets.search_box import SearchBox
from draobpilc.widgets.window import Window

if TYPE_CHECKING:
    _ = lambda s: s


class Application(Gtk.Application):

    def __init__(self) -> None:
        super().__init__()

        self.set_application_id(version.APP_ID)
        self.set_flags(Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        self.args: Optional[argparse.Namespace] = None
        self._window: Optional[Window] = None
        self._editor: Optional[editor.Editor] = None
        self._previewer: Optional[previewer.Previewer] = None
        self._merger: Optional[merger.Merger] = None
        self._items_processors: Optional[ItemsProcessors] = None
        self._main_toolbox: Optional[MainToolbox] = None
        self._history_items: Optional[HistoryItems] = None
        self._search_box: Optional[SearchBox] = None
        self._items_view: Optional[ItemsView] = None
        self._deletion_progress_bar: Optional[Gtk.ProgressBar] = None

    def _resize(self, window: Window, event: Any) -> None:
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

        if self._items_view:
            self._items_view.set_size_request(list_width, -1)
        if self._items_processors:
            self._items_processors.set_size_request(
                processors_width,
                processors_height
            )
        if self._previewer:
            self._previewer.set_max_size(processors_width, processors_height)

    def _on_search_changed(self, search_box: SearchBox, search_index: Optional[int] = None) -> None:
        if self._history_items and self._search_box:
            self._history_items.filter(
                term=self._search_box.search_text,
                kinds=self._search_box.flags,
                index=search_index
            )

    def _on_entry_activated(self, entry: Gtk.Entry) -> bool:
        if self._items_view:
            items = self._items_view.get_selected()
            if items:
                self._on_item_activated(self._items_view, items[0])

        return True

    def _on_search_entry_key_press(self, widget: Gtk.Widget, event: Any) -> bool:
        if event.keyval == Gdk.KEY_Down and self._items_view:
            self._items_view.select_first(grab_focus=True)
            return True
        return False

    def _on_items_view_focus_search(self, items_view: ItemsView, event: Any) -> None:
        if self._search_box and self._search_box.entry:
            self._search_box.entry.grab_focus()
            if event.string:
                self._search_box.entry.event(event)

    def _on_item_activated(self, items_view: ItemsView, history_item: HistoryItem) -> None:
        if history_item.uuid:
            gpaste_client.select(history_item.uuid)
        if self._search_box and self._search_box.entry:
            self._search_box.entry.set_text('')
        self.hide()

    def _on_item_entered(self, items_view: ItemsView, item: HistoryItem) -> None:
        if not self._items_view or self._items_view.n_selected != 1: return

        if self._items_processors:
            self._items_processors.set_items(
                [item],
                timeout=common.SETTINGS[common.SET_ITEMS_TIMEOUT]
            )

    def _on_delete_action(self, action: Gio.SimpleAction, param: Any) -> None:
        if self._items_view:
            selected_items = self._items_view.get_selected()
            if not selected_items: return

            self.delete_items(selected_items)

    def _on_open_item(self, action: Gio.SimpleAction, param: Any) -> None:
        if not self._items_view:
            return

        selected_items = self._items_view.get_selected()
        if not selected_items: return
        item = selected_items[0]
        if not item.app_info or not item.raw: return

        uri = item.raw.strip()
        if item.kind != HistoryItemKind.LINK:
            uri = 'file://%s' % uri

        item.app_info.launch_uris([uri])
        self.hide()

    def _restart_daemon(self, button: Gtk.Button) -> None:
        try:
            gpaste_client.reexecute()
        except DBusException:
            pass

        utils.restart_app()

    def _on_editor_wrap_action(self, action: Gio.SimpleAction, param: Any) -> None:
        common.SETTINGS[common.EDITOR_WRAP_TEXT] = not common.SETTINGS[common.EDITOR_WRAP_TEXT]

    def _on_backup_history(self, action: Gio.SimpleAction, param: Any) -> None:
        dialog = BackupHistoryDialog(self._window)
        dialog.run()

    def _on_reset_search_action(self, action: Gio.SimpleAction, param: Any) -> None:
        if self._search_box:
            self._search_box.reset()

            if self._search_box.entry:
                self._search_box.entry.grab_focus()

    def _on_key_press(self, window: Window, event: Any) -> None:
        if not common.SETTINGS[common.ENABLE_ACTIVATE_NUMBER_KB] or not self._items_view: return

        result, keyval = event.get_keyval()
        is_control = bool(event.get_state() & Gdk.ModifierType.CONTROL_MASK)
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
                if item and self._items_view:
                    self._items_view.activate_item(item)

    def _on_key_release(self, window: Window, event: Any) -> None:
        if not common.SETTINGS[common.ENABLE_ACTIVATE_NUMBER_KB] or not self._items_view: return

        result, keyval = event.get_keyval()

        if keyval == Gdk.KEY_Control_L:
            self._items_view.show_shortcut_hints(False)

    def _bind_action(self, name: str, target: str, settings_key: str, callback: Callable[..., Any]) -> None:
        def on_settings_change(settings: Any, key: str, target: str) -> None:
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

    def _update_deletion_progress(self, fraction: float, text: str) -> bool:
        if self._deletion_progress_bar:
            self._deletion_progress_bar.set_fraction(fraction)
            self._deletion_progress_bar.set_text(text)

        return False

    def _threaded_delete(self, items_to_delete: List[HistoryItem], resume_selection: bool) -> None:
        total_items = len(items_to_delete)
        delete_indexes = sorted([(item.index, item.uuid) for item in items_to_delete])

        for i, index_tuple in enumerate(delete_indexes):
            item_uuid = index_tuple[1]
            if item_uuid:
                try:
                    gpaste_client.delete(item_uuid)
                    fraction = (i + 1) / total_items
                    text = f"Deleting {i+1} of {total_items} items..."
                    GLib.idle_add(self._update_deletion_progress, fraction, text)
                except DBusException as e:
                    logging.warning(f'Error deleting item {item_uuid}: {e}')

        GLib.idle_add(self._on_delete_finished, resume_selection)

    def _on_delete_finished(self, resume_selection: bool) -> bool:
        if self._deletion_progress_bar:
            self._deletion_progress_bar.hide()
            self._deletion_progress_bar.set_fraction(0)
        if self._items_view:
            self._items_view.set_sensitive(True)
        if self._items_processors:
            self._items_processors.set_sensitive(True)

        filter_active: bool = bool(self._search_box and (
            self._search_box.search_text
            or self._search_box.flags
        ))

        if self._history_items:
            self._history_items.freeze(False)
            self._history_items.reload_history(emit_signal=not filter_active)

        if filter_active and self._search_box:
            self._on_search_changed(self._search_box)

        if resume_selection and self._items_view:
            self._items_view.resume_selection()

        return False

    def delete_items(self, items: List[HistoryItem], resume_selection: bool = True) -> None:
        if self._deletion_progress_bar:
            self._deletion_progress_bar.show()
        if self._items_view:
            self._items_view.set_sensitive(False)
        if self._items_processors:
            self._items_processors.set_sensitive(False)

        if self._history_items:
            self._history_items.freeze(True)
        if resume_selection and self._items_view:
            self._items_view.save_selection()

        thread = threading.Thread(target=self._threaded_delete, args=(items, resume_selection))
        thread.daemon = True
        thread.start()

    def selection_changed(self) -> None:
        if not self._items_view or not self._items_processors:
            return

        selected = self._items_view.get_selected()
        self._items_processors.set_items(
            selected,
            timeout=common.SETTINGS[common.SET_ITEMS_TIMEOUT]
        )

    def merge_items(self, merger: merger.Merger, items: List[HistoryItem], delete_merged: bool) -> None:
        if not self._merger or not self._merger.buffer:
            return

        merged_text = self._merger.buffer.props.text
        if not merged_text: return

        if delete_merged: self.delete_items(items, resume_selection=False)
        gpaste_client.add(merged_text)
        self.hide()

    def _on_merger_delete(self, merger: merger.Merger, items: List[HistoryItem]) -> None:
        self.delete_items(items, resume_selection=True)

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        Gtk.Application.do_command_line(self, command_line)

        arguments = command_line.get_arguments()
        if '--toggle' in arguments:
            self.toggle()
            return 0

        show_preferences = False
        if '--preferences' in arguments:
            show_preferences = True

        self.do_activate(show_preferences)

        return 0

    def do_activate(self, show_preferences_dialog: bool = False) -> None:

        if self._window:
            if show_preferences_dialog:
                show_preferences()
            else:
                self.show()
            return None

        self._window = Window(
            self,
            items_processors=self._items_processors,
            main_toolbox=self._main_toolbox,
            search_box=self._search_box,
            items_view=self._items_view,
            deletion_progress_bar=self._deletion_progress_bar
        )
        self._window.connect('configure-event', self._resize)
        self._window.connect('key-press-event', self._on_key_press)
        self._window.connect('key-release-event', self._on_key_release)
        self._window.connect(
            'focus-out-event',
            lambda _, __: self._items_view.show_shortcut_hints(False) if self._items_view else None
        )

        if self.args and self.args.show_preferences:
            show_preferences()

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)

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

        self._editor = editor.Editor()
        self._previewer = previewer.Previewer()
        self._merger = merger.Merger()
        self._merger.connect('merge', self.merge_items)
        self._merger.connect('delete', self._on_merger_delete)
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
        self._search_box.entry.connect(
            'key-press-event',
            self._on_search_entry_key_press
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
        self._items_view.connect(
            'focus-search-requested',
            self._on_items_view_focus_search
        )

        self._deletion_progress_bar = Gtk.ProgressBar()
        self._deletion_progress_bar.set_name('DeletionProgressBar')
        self._deletion_progress_bar.set_halign(Gtk.Align.CENTER)
        self._deletion_progress_bar.set_valign(Gtk.Align.CENTER)
        self._deletion_progress_bar.set_hexpand(True)
        self._deletion_progress_bar.set_text('Progress')
        self._deletion_progress_bar.set_show_text(True)
        self._deletion_progress_bar.set_no_show_all(True)
        self._deletion_progress_bar.hide()

        gpaste_client.connect('ShowHistory', self.toggle)
        gpaste_client.connect('Tracking',
            lambda t: self._main_toolbox.track_btn.set_active(t) if self._main_toolbox and self._main_toolbox.track_btn else None
        )
        common.APPLICATION = self
        
        actions: List[List[Any]] = [
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
            utils.notify(body=_(f'{version.APP_NAME} is now running.'))

    def toggle(self) -> None:
        if self._window and self._window.props.visible:
            self.hide()
        else:
            self.activate()

    def show_histories_manager(self, action: Gio.SimpleAction, param: Any) -> None:
        if self._items_view:
            self._items_view.histories_manager.show()

    def show_prefs(self) -> None:
        show_preferences()
        self.hide()

    def show_about(self) -> None:
        about_dialog = AboutDialog()
        about_dialog.set_transient_for(self._window)
        about_dialog.show()

    def show(self) -> None:
        if self._window:
            self._window.show_all()
            self._window.maximize()
            self._window.get_window().focus(Gdk.CURRENT_TIME)
            self._window.present_with_time(Gdk.CURRENT_TIME)

        grab_focus = True

        if self._search_box and self._search_box.entry and self._search_box.entry.get_text():
            self._search_box.entry.grab_focus()
            grab_focus = False

        if self._items_view:
            self._items_view.select_first(grab_focus=grab_focus)

    def hide(self, reset_search: bool = True) -> None:
        if self._window:
            self._window.hide()
        if reset_search and self._search_box:
            self._search_box.reset()

