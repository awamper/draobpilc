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

from typing import Optional, Any, Dict, TYPE_CHECKING

from gi.repository import Gtk # type: ignore

from draobpilc import get_data_path
from draobpilc import version
from draobpilc.lib import utils

if TYPE_CHECKING:
    _ = lambda s: s

APPLICATION: Any = None

SETTINGS_SCHEMA_ID: str = version.APP_ID
SETTINGS_SCHEMA_DIR: str = get_data_path('schemas')
SETTINGS: Any = utils.get_settings(
    SETTINGS_SCHEMA_ID,
    SETTINGS_SCHEMA_DIR
)

ICON_PATH: str = get_data_path('draobpilc.png')
CSS_PATH: str = get_data_path('style.css')

# settings keys
WIDTH_PERCENTS: str = 'width-percents'
PROCESSOR_WIDTH_PERCENTS: str = 'processor-width-percents'
PROCESSOR_HEIGHT_PERCENTS: str = 'processor-height-percents'
ITEM_MAX_LINES: str = 'item-max-lines'
ITEM_MAX_HEIGHT: str = 'item-max-height'
ITEM_MAX_DISPLAY_TEXT_CHARS: str = 'item-max-display-text-chars'
KIND_INDICATOR_WIDTH: str = 'kind-indicator-width'
EDIT_TIMEOUT_MS: str = 'edit-timeout-ms'
SHOW_INDEXES: str = 'show-indexes'
SEARCH_TIMEOUT: str = 'search-timeout'
FUZZY_SEARCH_MAX_DISTANCE: str = 'fuzzy-search-max-distance'
STARTUP_NOTIFICATION: str = 'startup-notification'
MERGE_DECORATORS: str = 'merge-decorators'
MERGE_SEPARATORS: str = 'merge-separators'
MERGE_DEFAULT_DECORATOR: str = 'merge-default-decorator'
MERGE_DEFAULT_SEPARATOR: str = 'merge-default-separator'
GPASTE_SCHEMA_ID: str = 'gpaste-schema-id'
GPASTE_DBUS_NAME: str = 'gpaste-dbus-name'
GPASTE_DBUS_PATH: str = 'gpaste-dbus-path'
GPASTE_DBUS_IFACE: str = 'gpaste-dbus-iface'
SHOW_TEXT_INFO: str = 'show-text-info'
SHOW_HISTORIES: str = 'show-histories'
DELETE_ITEM: str = 'delete-item'
SHOW_THUMBNAILS: str = 'show-thumbnails'
FOCUS_SEARCH: str = 'focus-search'
RESET_SEARCH: str = 'reset-search'
EDITOR_WRAP_TEXT: str = 'editor-wrap-text'
EDITOR_WRAP_TEXT_SHORTCUT: str = 'editor-wrap-text-shortcut'
OPEN_ITEM: str = 'open-item'
BACKUP_HISTORY: str = 'backup-history'
PREVIEW_TEXT_FILES: str = 'preview-text-files'
PREVIEW_TEXT_MAX_SIZE_BYTES: str = 'preview-text-max-size-bytes'
KEEP_SEARCH_AND_CLOSE: str = 'keep-search-and-close'
HIDE_APP: str = 'hide-app'
QUIT_APP: str = 'quit-app'
SET_ITEMS_TIMEOUT: str = 'set-items-timeout'
MAX_FILTER_RESULTS: str = 'max-filter-results'
SHOW_HELP: str = 'show-help'
ITEMS_VIEW_LIMIT: str = 'items-view-limit'
LOAD_ALL_HISTORY: str = 'load-all-history'
ENABLE_ACTIVATE_NUMBER_KB: str = 'enable-activate-number-kb'

SHORTCUTS_KEYS: Dict[str, str] = {
    SHOW_HISTORIES: _('Show histories'),
    DELETE_ITEM: _('Delete an item'),
    FOCUS_SEARCH: _('Focus search entry'),
    RESET_SEARCH: _('Reset search'),
    EDITOR_WRAP_TEXT_SHORTCUT: _('Toggle text wrap in the editor'),
    OPEN_ITEM: _('Open selected item(file, image, url)'),
    BACKUP_HISTORY: _('Backup current history'),
    KEEP_SEARCH_AND_CLOSE: _('Keep search and close window'),
    QUIT_APP: _('Quit app'),
    SHOW_HELP: _('Show help'),
    LOAD_ALL_HISTORY: _('Load all history')
}
