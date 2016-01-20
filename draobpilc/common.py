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

from draobpilc import get_data_path
from draobpilc import version
from draobpilc.lib import utils

APPLICATION = None

SETTINGS_SCHEMA_ID = version.APP_ID
SETTINGS_SCHEMA_DIR = get_data_path('schemas')
SETTINGS = utils.get_settings(
    SETTINGS_SCHEMA_ID,
    SETTINGS_SCHEMA_DIR
)

ICON_PATH = get_data_path('draobpilc.png')
CSS_PATH = get_data_path('style.css')

# settings keys
WIDTH_PERCENTS = 'width-percents'
EDITOR_WIDTH_PERCENTS = 'editor-width-percents'
EDITOR_HEIGHT_PERCENTS = 'editor-height-percents'
ITEM_MAX_LINES = 'item-max-lines'
ITEM_MAX_HEIGHT = 'item-max-height'
KIND_INDICATOR_WIDTH = 'kind-indicator-width'
ITEM_PREVIEW_MARGIN = 'item-preview-margin'
EDIT_TIMEOUT_MS = 'edit-timeout-ms'
SHOW_INDEXES = 'show-indexes'
SEARCH_TIMEOUT = 'search-timeout'
FUZZY_SEARCH_MAX_DISTANCE = 'fuzzy-search-max-distance'
STARTUP_NOTIFICATION = 'startup-notification'
MERGE_DECORATORS = 'merge-decorators'
MERGE_SEPARATORS = 'merge-separators'
MERGE_DEFAULT_DECORATOR = 'merge-default-decorator'
MERGE_DEFAULT_SEPARATOR = 'merge-default-separator'
SHOW_EDITOR_TIMEOUT = 'show-editor-timeout'
HIDE_EDITOR_TIMEOUT = 'hide-editor-timeout'
GPASTE_SCHEMA_ID = 'gpaste-schema-id'
GPASTE_DBUS_NAME = 'gpaste-dbus-name'
GPASTE_DBUS_PATH = 'gpaste-dbus-path'
GPASTE_DBUS_IFACE = 'gpaste-dbus-iface'
SHOW_TEXT_INFO = 'show-text-info'
SHOW_HISTORIES = 'show-histories'
DELETE_ITEM = 'delete-item'
SHOW_THUMBNAILS = 'show-thumbnails'
FOCUS_SEARCH = 'focus-search'
