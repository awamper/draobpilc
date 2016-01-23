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
import json

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import GPaste

from draobpilc import common
from draobpilc import version
from draobpilc.lib import utils

_window = None


def show_preferences():
    def on_destroy(window):
        global _window
        _window = None

    global _window

    if not _window:
        _window = Preferences()
        _window.connect('destroy', on_destroy)

    _window.show_all()
    _window.get_window().focus(Gdk.CURRENT_TIME)
    _window.present_with_time(Gdk.CURRENT_TIME)


class KeybindingsWidget(Gtk.Box):

    class Columns():
        NAME = 0
        ACCEL_NAME = 1
        MODS = 2
        KEY = 3

    def __init__(self, keybindings):
        super().__init__()

        self.set_orientation(Gtk.Orientation.VERTICAL)

        self._keybindings = keybindings

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC,
            Gtk.PolicyType.AUTOMATIC
        )

        self._store = Gtk.ListStore(str, str, int, int)
        self._tree_view = Gtk.TreeView()
        self._tree_view.set_model(self._store)
        self._tree_view.set_vexpand(True)
        self._tree_view.set_hexpand(True)
        self._tree_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

        action_renderer = Gtk.CellRendererText()
        action_column = Gtk.TreeViewColumn()
        action_column.props.title = _('Action')
        action_column.props.expand = True
        action_column.pack_start(action_renderer, True)
        action_column.add_attribute(action_renderer, 'text', 1)
        self._tree_view.append_column(action_column)

        keybinding_renderer = Gtk.CellRendererAccel()
        keybinding_renderer.props.editable = True
        keybinding_renderer.connect('accel-edited', self._on_accel_edited)
        keybinding_column = Gtk.TreeViewColumn()
        keybinding_column.props.title = _('Modify')
        keybinding_column.pack_end(keybinding_renderer, False)
        keybinding_column.add_attribute(
            keybinding_renderer,
            'accel-mods',
            KeybindingsWidget.Columns.MODS
        )
        keybinding_column.add_attribute(
            keybinding_renderer,
            'accel-key',
            KeybindingsWidget.Columns.KEY
        )
        self._tree_view.append_column(keybinding_column)

        scrolled_window.add(self._tree_view)
        self.add(scrolled_window)

        self._refresh()

    def _on_accel_edited(self, renderer, iter_, key, mods, *args):
        value = Gtk.accelerator_name(key, mods)
        iterator = self._store.get_iter_from_string(iter_)

        if not iterator:
            message_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK
            )
            message_dialog.set_markup(_('Can\'t change hotkey.'))
            message_dialog.run()
            message_dialog.destroy()

        name = self._store.get_value(iterator, 0)

        columns = [KeybindingsWidget.Columns.MODS, KeybindingsWidget.Columns.KEY]
        values = [mods, key]
        self._store.set(iterator, columns, values)
        common.SETTINGS[name] = value

    def _refresh(self):
        self._store.clear()
        sorted_keybindings = [(k, self._keybindings[k]) for k in sorted(
            self._keybindings,
            key=self._keybindings.get,
            reverse=False
        )]

        for kb_key, kb_name in sorted_keybindings:
            key, mods = Gtk.accelerator_parse(common.SETTINGS[kb_key])
            iter = self._store.append()
            columns = [
                KeybindingsWidget.Columns.NAME,
                KeybindingsWidget.Columns.ACCEL_NAME,
                KeybindingsWidget.Columns.MODS,
                KeybindingsWidget.Columns.KEY
            ]
            values = [kb_key, kb_name, mods, key]
            self._store.set(iter, columns, values)


class PrefsGrid(Gtk.Grid):

    def __init__(self, settings):
        super().__init__()

        self.set_row_spacing(10)
        self.set_column_spacing(10)

        self._settings = settings
        self._rownum = 0

    def add_entry(self, text, key):
        item = Gtk.Entry()
        item.set_hexpand(False)
        item.set_text(self._settings[key])
        self._settings.bind(key, item, 'text', Gio.SettingsBindFlags.DEFAULT)

        return self.add_row(text, item)

    def add_boolean(self, text, key):
        item = Gtk.Switch()
        item.set_active(self._settings[key])
        self._settings.bind(key, item, 'active', Gio.SettingsBindFlags.DEFAULT)

        return self.add_row(text, item)

    def add_combo(self, text, key, entries_list, type_):
        def on_changed(combo):
            self._settings[key] = type_(combo.props.active_id)

        item = Gtk.ComboBoxText()

        for entry in entries_list:
            item.insert(-1, entry['value'], entry['title'].strip())

        item.set_active_id(self._settings[key])
        item.connect('changed', on_changed)

        return self.add_row(text, item)

    def add_spin(self, label, key, adjust_props={}, spin_props={}, type_=int):
        def on_changed(spin):
            value = None

            if type_ is int:
                value = spin.get_value_as_int()
            else:
                value = spin.get_value()

            self._settings[key] = value

        adjust_default = {
            'lower': 0,
            'upper': 100,
            'step_increment': 1
        }
        adjustment = Gtk.Adjustment()
        adjustment.set_lower(
            adjust_props.get('lower', adjust_default['lower'])
        )
        adjustment.set_upper(
            adjust_props.get('upper', adjust_default['upper'])
        )
        adjustment.set_step_increment(
            adjust_props.get('step_increment', adjust_default['step_increment'])
        )


        spin_button = Gtk.SpinButton()
        spin_button.set_adjustment(adjustment)
        spin_button.set_numeric(True)
        spin_button.set_snap_to_ticks(True)
        spin_button.set_value(self._settings[key])
        spin_button.connect('value-changed', on_changed)

        if type_ is float:
            spin_button.set_digits(2)

        return self.add_row(label, spin_button, True)

    def add_label(self, label):
        item = Gtk.Label()
        item.set_label(label)

        return self.add_item(item)

    def add_row(self, text, widget, wrap=False):
        label = Gtk.Label()
        label.set_text(text)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.set_line_wrap(wrap)

        self.attach(label, 0, self._rownum, 1, 1)  # col, row, colspan, rowspan
        self.attach(widget, 1, self._rownum, 1, 1)
        self._rownum += 1

        return widget

    def add_item(self, widget, col=0, colspan=2, rowspan=1):
        self.attach(widget, col, self._rownum, colspan, rowspan)
        self._rownum += 1

        return widget

    def add_range(self, label, key, range_props):
        def on_changed(slider):
            self._settings[key] = slider.get_value()

        range_props_default = {
            'min': 0,
            'max': 100,
            'step': 10,
            'mark_position': 0,
            'add_mark': False,
            'size': 200,
            'draw_value': True
        }

        range_ = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            range_props.get('min', range_props_default['min']),
            range_props.get('max', range_props_default['max']),
            range_props.get('step', range_props_default['step'])
        )
        range_.set_value(self._settings.get_int(key))
        range_.set_draw_value(range_props.draw_value)
        size = range_props.get('size', range_props_default['size'])
        range_.set_size_request(size, -1)

        if range_props.get('add_mark', range_props_default['add_mark']):
            position = range_props.get(
                'mark_position',
                range_props_default['mark_position']
            )
            range_.add_mark(position, Gtk.PositionType.BOTTOM, None)

        range_.connect('value-changed', on_changed)

        return self.add_row(label, range_, True)

    def add_separator(self):
        separator = Gtk.Separator()
        separator.set_orientation(Gtk.Orientation.HORIZONTAL)

        return self.add_item(separator)


class Preferences(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_title(_('Preferences'))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_name('PreferencesWindow')
        self.set_icon_from_file(common.ICON_PATH)
        self.set_default_size(200, 200)
        self.set_resizable(False)
        self.connect('destroy', self._on_destroy)

        switcher_margin = 5
        stack_margin = 10
        self._transition_duration = 500
        self._need_restart = False

        requires_restart = [
            common.WIDTH_PERCENTS,
            common.ITEM_MAX_LINES,
            common.ITEM_MAX_HEIGHT,
            common.KIND_INDICATOR_WIDTH,
            common.SHOW_INDEXES,
            common.SHOW_TEXT_INFO,
            common.SHOW_THUMBNAILS,
            common.FOCUS_SEARCH,
            common.SHOW_HISTORIES,
            common.DELETE_ITEM,
            common.EDITOR_WRAP_TEXT_SHORTCUT,
            common.OPEN_ITEM,
            common.BACKUP_HISTORY
        ]
        for key in requires_restart:
            common.SETTINGS.connect(
                'changed::' + key,
                self._on_settings_changed
            )

        main = self._get_main_page()
        editor = self._get_editor_page()
        keybindings = self._get_keybindings_page()

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(self._transition_duration)
        stack.props.margin = stack_margin

        stack.add_titled(
            main['page'],
            main['name'],
            main['name']
        )
        stack.add_titled(
            editor['page'],
            editor['name'],
            editor['name']
        )
        stack.add_titled(
            keybindings['page'],
            keybindings['name'],
            keybindings['name']
        )

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        stack_switcher.props.margin = switcher_margin

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title(None)
        header_bar.set_subtitle(None)
        header_bar.set_custom_title(stack_switcher)

        self.set_titlebar(header_bar)
        self.add(stack)

    def _on_destroy(self, window):
        if not self._need_restart: return

        self._need_restart = False
        msg = _(
            'You need to restart the app for the changes to take effect. Restart now?'
        )
        message_dialog = Gtk.MessageDialog(
            None,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.YES_NO,
            version.APP_NAME
        )
        message_dialog.set_position(Gtk.WindowPosition.CENTER)
        message_dialog.set_icon_from_file(common.ICON_PATH)
        message_dialog.props.secondary_text = msg
        response = message_dialog.run()
        message_dialog.destroy()

        if response == Gtk.ResponseType.YES:
            utils.restart_app()

    def _on_button_clicked(self, button):
        dialog = Gtk.Dialog()
        dialog.set_transient_for(self)

        gpaste_settings = GPaste.SettingsUiWidget()

        for child in gpaste_settings.get_children():
            if isinstance(child, Gtk.StackSwitcher):
                toplevel = dialog.get_toplevel()
                if not toplevel: continue

                gpaste_settings.remove(child)

                header_bar = Gtk.HeaderBar()
                header_bar.set_show_close_button(True)
                header_bar.set_title(None)
                header_bar.set_subtitle(None)
                header_bar.set_custom_title(child)

                toplevel.set_titlebar(header_bar)

            if isinstance(child, Gtk.Stack):
                child.set_transition_type(
                    Gtk.StackTransitionType.SLIDE_LEFT_RIGHT
                )
                child.set_transition_duration(self._transition_duration)

        content_area = dialog.get_content_area()
        content_area.add(gpaste_settings)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _on_settings_changed(self, settings, param):
        self._need_restart = True

    def _get_main_page(self):
        name = _('Main')
        page = PrefsGrid(common.SETTINGS)

        page.add_boolean(
            _('Show startup notification:'),
            common.STARTUP_NOTIFICATION
        )
        page.add_boolean(
            _('Show items index number:'),
            common.SHOW_INDEXES
        )
        page.add_boolean(
            _('Show info for text items:'),
            common.SHOW_TEXT_INFO
        )
        page.add_boolean(
            _('Show thumbnails for file/image items:'),
            common.SHOW_THUMBNAILS
        )

        page.add_separator()

        spin_props = {}
        spin_props['lower'] = 10
        spin_props['upper'] = 60
        spin_props['step_increment'] = 5
        page.add_spin(
            _('Items list width(%):'),
            common.WIDTH_PERCENTS,
            spin_props,
            int
        )

        spin_props['lower'] = 1
        spin_props['upper'] = 10
        spin_props['step_increment'] = 1
        page.add_spin(
            _('Item max lines:'),
            common.ITEM_MAX_LINES,
            spin_props,
            int
        )

        spin_props['lower'] = 50
        spin_props['upper'] = 150
        spin_props['step_increment'] = 5
        page.add_spin(
            _('Item max height(px):'),
            common.ITEM_MAX_HEIGHT,
            spin_props,
            int
        )

        page.add_separator()

        spin_props['lower'] = 1
        spin_props['upper'] = 10
        spin_props['step_increment'] = 1
        page.add_spin(
            _('Kind indicator width(px):'),
            common.KIND_INDICATOR_WIDTH,
            spin_props,
            int
        )
        spin_props['lower'] = 200
        spin_props['upper'] = 500
        spin_props['step_increment'] = 50
        page.add_spin(
            _('Search timeout:'),
            common.SEARCH_TIMEOUT,
            spin_props,
            int
        )

        page.add_separator()

        button = Gtk.Button()
        button.set_label(_('GPaste Preferences'))
        button.set_hexpand(True)
        button.connect('clicked', self._on_button_clicked)
        page.add_item(button)

        result = dict(page=page, name=name)
        return result

    def _get_editor_page(self):
        name = _('Editor')
        page = PrefsGrid(common.SETTINGS)

        page.add_boolean(
            _('Wrap text:'),
            common.EDITOR_WRAP_TEXT
        )
        page.add_separator()

        spin_props = {}
        spin_props['lower'] = 200
        spin_props['upper'] = 1000
        spin_props['step_increment'] = 100
        page.add_spin(
            _('Save changes timeout(ms):'),
            common.EDIT_TIMEOUT_MS,
            spin_props,
            int
        )

        spin_props['lower'] = 200
        spin_props['upper'] = 1000
        spin_props['step_increment'] = 100
        page.add_spin(
            _('Show timeout(ms):'),
            common.SHOW_EDITOR_TIMEOUT,
            spin_props,
            int
        )

        spin_props['lower'] = 200
        spin_props['upper'] = 1000
        spin_props['step_increment'] = 100
        page.add_spin(
            _('Hide timeout(ms):'),
            common.HIDE_EDITOR_TIMEOUT,
            spin_props,
            int
        )

        page.add_separator()
        page.add_label(_('Merger'))

        decorators = json.loads(common.SETTINGS[common.MERGE_DECORATORS])
        decorators = [{
            'value': decorator[1],
            'title': decorator[0]
        } for decorator in decorators]
        decorators.append({
            'value': '',
            'title': _('None')
        })
        page.add_combo(
            _('Default decorator:'),
            common.MERGE_DEFAULT_DECORATOR,
            decorators,
            str
        )

        separators = json.loads(common.SETTINGS[common.MERGE_SEPARATORS])
        separators = [{
            'value': separator[1],
            'title': separator[0]
        } for separator in separators]
        separators.append({
            'value': '',
            'title': _('None')
        })
        page.add_combo(
            _('Default separator:'),
            common.MERGE_DEFAULT_SEPARATOR,
            separators,
            str
        )

        result = dict(page=page, name=name)
        return result

    def _get_gpaste_page(self):
        name = _('GPaste')
        page = PrefsGrid(common.SETTINGS)

        gpaste_settings = GPaste.SettingsUiWidget()
        page.add_item(gpaste_settings)

        result = dict(page=page, name=name)
        return result

    def _get_keybindings_page(self):
        name = _('Shortcuts')
        page = PrefsGrid(common.SETTINGS)

        keybindings = {
            common.SHOW_HISTORIES: _('Show histories'),
            common.DELETE_ITEM: _('Delete an item'),
            common.FOCUS_SEARCH: _('Focus search entry'),
            common.EDITOR_WRAP_TEXT_SHORTCUT: _('Toggle text wrap in the editor'),
            common.OPEN_ITEM: _('Open item(file, image, url)'),
            common.BACKUP_HISTORY: _('Backup current history')
        }

        keybindings_widget = KeybindingsWidget(keybindings)
        page.add_item(keybindings_widget)

        result = dict(page=page, name=name)
        return result
