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

import os
from typing import Any, List, Optional, TYPE_CHECKING

import humanize
from gi.repository import GdkPixbuf, Gio, GLib, GObject  # type: ignore

from draobpilc import common
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.lib import gpaste_client, utils
from draobpilc.widgets.history_item_view import HistoryItemView

if TYPE_CHECKING:
    _ = lambda s: s


class HistoryItem(GObject.Object):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    FILTER_HIGHLIGHT_TPL: str = '<span bgcolor="yellow" fgcolor="black"><b>%s</b></span>'

    def __init__(self, index: int, uuid: str) -> None:
        GObject.Object.__init__(self)

        self._index: Optional[int] = None
        self._uuid: Optional[str] = None
        self._raw: Optional[str] = None
        self._kind: Optional[HistoryItemKind] = None
        self._text: Optional[str] = None
        self._markup: Optional[str] = None
        self._source_markup: Optional[str] = None
        self._sort_score: Optional[int] = None
        self._n_lines: Optional[int] = None
        self._links: Optional[List[str]] = None
        self._content_type: Optional[str] = None
        self._thumb_path: Optional[str] = None
        self._image_path: Optional[str] = None
        self._info_string: Optional[str] = None
        self._widget: Optional[HistoryItemView] = None
        self._app_info: Optional[Gio.AppInfo] = None

        if index >= 0: self.load_data(index, uuid)

    def __repr__(self) -> str:
        text = 'Data not loaded'

        try:
            if self.text:
                text = ' '.join(self.text.split())
        except AttributeError:
            pass
        else:
            text = text.strip()[:30]

        return f'<HistoryItem: index={self.index}, "{text}">'

    def load_data(self, index: int, uuid: str) -> None:
        emit_signal = False
        if self.index is not None: emit_signal = True

        self.index = index
        self._uuid = uuid
        self._raw = gpaste_client.get_raw_element(self._uuid)
        kind_str: str = gpaste_client.get_element_kind(self._uuid)
        
        try:
            # The kind from gpaste is a string, convert it to our enum
            self._kind = HistoryItemKind(kind_str)
        except (ValueError, TypeError):
            # If the kind string is not valid or None, default to TEXT
            self._kind = HistoryItemKind.TEXT
        
        if (self.kind == HistoryItemKind.TEXT and
            self._raw and utils.is_url(self._raw)
        ):
            self._kind = HistoryItemKind.LINK

        # Check if a FILE (Uris) item is actually an image
        if self.kind == HistoryItemKind.FILE and self._raw:
            filename = os.path.expanduser(self._raw.strip())
            if os.path.exists(filename):
                uri = 'file://%s' % filename
                file_ = Gio.file_new_for_uri(uri)
                try:
                    info = file_.query_info(
                        'standard::content-type',
                        Gio.FileQueryInfoFlags.NONE
                    )
                    content_type = info.get_content_type()
                    if content_type and content_type.startswith('image'):
                        self._image_path = filename
                except GLib.Error:
                    pass
        
        self._n_lines = len(self._raw.split('\n')) if self._raw else 0
        self._links = self._get_links()
        self._thumb_path = self._get_thumb_path()
        self._app_info = self._get_app_info()
        self._info_string = self._get_info()

        if not self._widget: self._widget = HistoryItemView(self)

        self.text = gpaste_client.get_element(self._uuid)
        if emit_signal: self.emit('changed')

    def _get_display_text(self, text: str, escape: bool = True) -> str:
        text = ' '.join(text.split())

        if len(text) > common.SETTINGS[common.ITEM_MAX_DISPLAY_TEXT_CHARS]:
            text = text[0:common.SETTINGS[common.ITEM_MAX_DISPLAY_TEXT_CHARS]]

        text = text.strip()
        if escape: text = GLib.markup_escape_text(text)

        if self.kind == HistoryItemKind.FILE:
            text = text.replace('[Files]', '', 1)
        if self.kind == HistoryItemKind.IMAGE:
            text = text.replace('[Image]', '', 1)

        if common.SETTINGS[common.SHOW_INDEXES] and self.index is not None:
            text = '<b>%i</b>. %s' % (self.index, text)

        return text

    def _get_thumb_path(self) -> Optional[str]:
        result = None
        if self.kind != HistoryItemKind.FILE or not self._raw:
            return result
        filename = os.path.expanduser(self._raw.strip())
        if not os.path.exists(filename):
            return result

        uri = 'file://%s' % filename
        file_ = Gio.file_new_for_uri(uri)

        try:
            info = file_.query_info(
                'standard::content-type,thumbnail::path',
                Gio.FileQueryInfoFlags.NONE
            )
            content_type = info.get_content_type()
            if content_type and (content_type.startswith('image') or content_type.startswith('video') or content_type.startswith('audio')):
                path = info.get_attribute_byte_string('thumbnail::path')
                if path:
                    result = path
            self._content_type = content_type
        except GLib.Error:
            pass
        
        return result

    def _get_app_info(self) -> Optional[Gio.AppInfo]:
        app_info = None
        if (
            self.n_lines and self.n_lines > 1 or (
                not self.content_type and
                self.kind != HistoryItemKind.LINK
            )
        ): return app_info

        if self.kind == HistoryItemKind.LINK and self._raw:
            uri_scheme = self._raw.split(':')[0].strip()
            app_info = Gio.AppInfo.get_default_for_uri_scheme(uri_scheme)
        elif self._content_type:
            app_info = Gio.AppInfo.get_default_for_type(
                self._content_type,
                False
            )

        return app_info

    def _get_links(self) -> List[str]:
        result: List[str] = []
        if not self._raw: return result

        links = utils.extract_urls(self._raw)

        if links:
            result = links
        
        return result

    def _get_info(self) -> str:
        result = ''

        if (
            self.kind != HistoryItemKind.FILE and
            self.kind != HistoryItemKind.IMAGE and
            not self.content_type
        ):
            if self.kind != HistoryItemKind.LINK and self._raw and self.n_lines is not None:
                result = '%i chars, %i lines' % (len(self._raw), self.n_lines)

            return result

        if self.n_lines and self.n_lines > 1:
            result += _('%s items') % self.n_lines
        elif self._raw:
            try:
                size = os.path.getsize(self._raw.strip())
            except FileNotFoundError:
                result += _('No such file or directory')
            else:
                result += humanize.naturalsize(size, gnu=True)

                if self._content_type:
                    result += ', Type: %s' % self._content_type

        return result

    @classmethod
    def new_from_raw(cls, raw_content: str, kind: HistoryItemKind = HistoryItemKind.TEXT) -> HistoryItem:
        item = cls(-1, '')
        item._index = -1
        item._raw = raw_content
        item._kind = kind

        if (item.kind == HistoryItemKind.TEXT and item.raw and
            utils.is_url(item.raw)
        ):
            item._kind = HistoryItemKind.LINK

        if item.kind == HistoryItemKind.IMAGE:
            item._image_path = os.path.expanduser(item._raw)

        if item.raw:
            item._n_lines = len(item.raw.split('\n'))
        
        item._links = item._get_links()
        item._thumb_path = item._get_thumb_path()
        item._app_info = item._get_app_info()
        item._info_string = item._get_info()

        if not item._widget: item._widget = HistoryItemView(item)

        if item.kind == HistoryItemKind.FILE: text = '[Files] ' + raw_content
        else: text = raw_content

        item.text = text
        return item

    @property
    def index(self) -> Optional[int]:
        return self._index

    @index.setter
    def index(self, value: int) -> None:
        update_label = False
        if self._index is not None: update_label = True
        
        self._index = value

        if update_label:
            if self._source_markup:
                self.markup = self._source_markup
            else:
                self.markup = None

    @property
    def uuid(self) -> Optional[str]:
        return self._uuid

    @property
    def raw(self) -> Optional[str]:
        return self._raw

    @property
    def kind(self) -> Optional[HistoryItemKind]:
        return self._kind

    @property
    def text(self) -> Optional[str]:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

        if not self.markup:
            self.widget.set_label(self.display_text)

    @property
    def markup(self) -> Optional[str]:
        return self._markup

    @markup.setter
    def markup(self, value: Optional[str]) -> None:
        if not value:
            self._markup = None
            self._source_markup = None
            if self._text:
                self.widget.set_label(self.display_text)
        else:
            self._source_markup = value
            self._markup = self._get_display_text(value, False)
            if self._markup is not None:
                self.widget.set_label(self._markup)

    @property
    def display_text(self) -> str:
        return self._get_display_text(self._text or '')

    @property
    def widget(self) -> HistoryItemView:
        assert self._widget is not None, "Widget accessed before initialization"
        return self._widget

    @property
    def sort_score(self) -> Optional[int]:
        return self._sort_score

    @sort_score.setter
    def sort_score(self, value: Optional[int]) -> None:
        self._sort_score = value
    
    @property
    def thumb_path(self) -> Optional[str]:
        return self._thumb_path
    
    @property
    def image_path(self) -> Optional[str]:
        return self._image_path
    
    @property
    def links(self) -> Optional[List[str]]:
        return self._links

    @property
    def n_lines(self) -> Optional[int]:
        return self._n_lines

    @property
    def info_string(self) -> Optional[str]:
        return self._info_string
    
    @property
    def content_type(self) -> Optional[str]:
        return self._content_type

    @property
    def app_info(self) -> Optional[Gio.AppInfo]:
        return self._app_info
