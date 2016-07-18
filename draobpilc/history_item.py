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

import os

import humanize
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GdkPixbuf

from draobpilc import common
from draobpilc.history_item_kind import HistoryItemKind
from draobpilc.lib import utils
from draobpilc.lib import gpaste_client
from draobpilc.lib.signals import Emitter
from draobpilc.widgets.history_item_view import HistoryItemView


class HistoryItem(Emitter):

    FILTER_HIGHLIGHT_TPL = '<span bgcolor="yellow" fgcolor="black"><b>%s</b></span>'

    def __init__(self, index):
        super().__init__()

        self._index = None
        self._raw = None
        self._kind = None
        self._text = None
        self._markup = None
        self._source_markup = None
        self._sort_score = None
        self._n_lines = None
        self._link = None
        self._content_type = None
        self._thumb_path = None
        self._info_string = None
        self._widget = None
        self._app_info = None

        self.add_signal('changed')
        self.load_data(index)

    def __repr__(self):
        text = 'Data not loaded'

        try:
            text = ' '.join(self.text.split())
        except AttributeError:
            pass
        else:
            text = text.strip()[:30]

        return '<HistoryItem: index=%i, "%s">' % (self.index, text)

    def load_data(self, index):
        emit_signal = False
        if self.index: emit_signal = True

        self.index = index
        self._raw = gpaste_client.get_raw_element(self.index)
        self._kind = gpaste_client.get_element_kind(self.index)

        if (self.kind == HistoryItemKind.TEXT and
            utils.is_url(self.raw)
        ):
            self._kind = HistoryItemKind.LINK

        self._n_lines = len(self.raw.split('\n'))
        self._links = self._get_links()
        self._thumb_path = self._get_thumb_path()
        self._app_info = self._get_app_info()
        self._info_string = self._get_info()

        if not self._widget: self._widget = HistoryItemView(self)

        self.text = gpaste_client.get_element(self.index)
        if emit_signal: self.emit('changed')

    def _get_display_text(self, text, escape=True):
        text = ' '.join(text.split())
        text = text.strip()
        if escape: text = GLib.markup_escape_text(text)

        if self.kind == HistoryItemKind.FILE:
            text = text.replace('[Files]', '', 1)
        if self.kind == HistoryItemKind.IMAGE:
            text = text.replace('[Image]', '', 1)

        if common.SETTINGS[common.SHOW_INDEXES]:
            text = '<b>%i</b>. %s' % (self.index, text)

        return text

    def _get_thumb_path(self):
        result = None
        if (
            self.kind != HistoryItemKind.FILE and
            self.kind != HistoryItemKind.IMAGE
        ): return result
        filename = os.path.expanduser(self._raw)
        if not os.path.exists(filename): return result

        uri = 'file://%s' % filename
        file_ = Gio.file_new_for_uri(uri)

        try:
            info = file_.query_info(
                'standard::content-type,thumbnail::path',
                Gio.FileQueryInfoFlags.NONE
            )
            path = info.get_attribute_byte_string('thumbnail::path')
            self._content_type = info.get_content_type()
            is_image = self._content_type.startswith('image')

            if path:
                result = path
            elif is_image:
                try:
                    GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        filename,
                        80,
                        80,
                        False
                    )
                except GLib.Error:
                    pass
                else:
                    result = filename
            else:
                pass
        except GLib.Error:
            pass
        finally:
            return result

    def _get_app_info(self):
        app_info = None
        if (
            self.n_lines > 1 or (
                not self.content_type and
                self.kind != HistoryItemKind.LINK
            )
        ): return app_info

        if self.kind == HistoryItemKind.LINK:
            uri_scheme = self.raw.split(':')[0].strip()
            app_info = Gio.AppInfo.get_default_for_uri_scheme(uri_scheme)
        else:
            app_info = Gio.AppInfo.get_default_for_type(
                self._content_type,
                False
            )

        return app_info

    def _get_links(self):
        result = []
        links = utils.extract_urls(self.raw)

        if links:
            result = links
        
        result = links
        return result

    def _get_info(self):
        result = ''

        if (
            self.kind != HistoryItemKind.FILE and
            self.kind != HistoryItemKind.IMAGE and
            not self.content_type
        ):
            if (
                self.kind != HistoryItemKind.LINK and
                common.SETTINGS[common.SHOW_TEXT_INFO]
            ):
                result = '%i chars, %i lines' % (len(self.raw), self.n_lines)

            return result


        if self.n_lines > 1:
            result += _('%s items') % self.n_lines
        else:
            try:
                size = os.path.getsize(self.raw.strip())
            except FileNotFoundError:
                result += _('No such file or directory')
            else:
                result += humanize.naturalsize(size, gnu=True)

                if self._content_type:
                    result += ', Type: %s' % self._content_type

        return result

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        if not self._index is None: update_label = True
        else: update_label = False

        self._index = value

        if update_label:
            if self._source_markup:
                self.markup = self._source_markup
            else:
                self.markup = None

    @property
    def raw(self):
        return self._raw

    @property
    def kind(self):
        return self._kind

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

        if not self.markup:
            self.widget.set_label(self.display_text)

    @property
    def markup(self):
        return self._markup

    @markup.setter
    def markup(self, value):
        if not value:
            self._markup = None
            self._source_markup = None
            self.widget.set_label(self.display_text)
        else:
            self._source_markup = value
            self._markup = self._get_display_text(value, False)
            self.widget.set_label(self.markup)

    @property
    def display_text(self):
        return self._get_display_text(self._text)

    @property
    def widget(self):
        return self._widget

    @property
    def sort_score(self):
        return self._sort_score

    @sort_score.setter
    def sort_score(self, value):
        self._sort_score = value
    
    @property
    def thumb_path(self):
        return self._thumb_path
    
    @property
    def links(self):
        return self._links

    @property
    def n_lines(self):
        return self._n_lines

    @property
    def info_string(self):
        return self._info_string
    
    @property
    def content_type(self):
        return self._content_type

    @property
    def app_info(self):
        return self._app_info
    