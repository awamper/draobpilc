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
import re
import sys
import subprocess

from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import Notify
from gi.repository import GdkPixbuf
from draobpilc import get_data_path
from draobpilc.version import APP_NAME

Notify.init(APP_NAME)

simple_url_re = re.compile(r'^https?://\[?\w', re.IGNORECASE)
simple_url_2_re = re.compile(
    r'^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)($|/.*)$',
    re.IGNORECASE
)


class SettingsSchemaNotFound(Exception):
    """ """


def restart_app():
    from draobpilc.common import APPLICATION
    APPLICATION.quit()
    subprocess.Popen('draobpilc')
    sys.exit()


def notify(summary=None, body=None, icon_name=None):
    if not summary:
        summary = APP_NAME

    notification = Notify.Notification.new(summary, body, icon_name)

    if not icon_name:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(get_data_path('draobpilc.png'))
        notification.set_icon_from_pixbuf(pixbuf)

    notification.show()


def get_settings(schema_id, schema_dir=None):
    if not schema_dir:
        schema_source = Gio.SettingsSchemaSource.get_default()
    else:
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            schema_dir,
            Gio.SettingsSchemaSource.get_default(),
            False
        )

    settings = schema_source.lookup(schema_id, True)

    if not settings:
        raise SettingsSchemaNotFound(
            'Schema "{schema}"" could not be found'.format(schema=schema_id)
        )

    return Gio.Settings(settings_schema=settings)


def is_url(string):
    result = False
    urls = extract_urls(string)

    if len(urls) == 1 and len(urls[0]) == len(string):
        result = True

    return result


# adopted from django
def extract_urls(text):
    def unescape(text, trail):
        """
        If input URL is HTML-escaped, unescape it so as we can safely feed it to
        smart_urlquote. For example:
        http://example.com?x=1&amp;y=&lt;2&gt; => http://example.com?x=1&y=<2>
        """
        unescaped = (text + trail).replace(
            '&amp;', '&').replace('&lt;', '<').replace(
            '&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
        if trail and unescaped.endswith(trail):
            # Remove trail for unescaped if it was not consumed by unescape
            unescaped = unescaped[:-len(trail)]
        elif trail == ';':
            # Trail was consumed by unescape (as end-of-entity marker),
            # move it to text
            text += trail
            trail = ''
        return text, unescaped, trail

    trailing_punctuation = ['.', ',', ':', ';', '.)', '"', '\'', '!']
    wrapping_punctuation = [
        ('(', ')'),
        ('<', '>'),
        ('[', ']'),
        ('&lt;', '&gt;'),
        ('"', '"'),
        ('\'', '\'')
    ]
    word_split_re = re.compile(r'''([\s<>"']+)''')
    result = []
    words = word_split_re.split(text)

    for i, word in enumerate(words):
        if '.' in word or '@' in word or ':' in word:
            # Deal with punctuation.
            lead, middle, trail = '', word, ''

            for punctuation in trailing_punctuation:
                if middle.endswith(punctuation):
                    middle = middle[:-len(punctuation)]
                    trail = punctuation + trail

            for opening, closing in wrapping_punctuation:
                if middle.startswith(opening):
                    middle = middle[len(opening):]
                    lead = lead + opening

                # Keep parentheses at the end only if they're balanced.
                if (
                    middle.endswith(closing)
                    and middle.count(closing) == middle.count(opening) + 1
                ):
                    middle = middle[:-len(closing)]
                    trail = closing + trail

            url = None

            if simple_url_re.match(middle):
                middle, middle_unescaped, trail = unescape(middle, trail)
                url = middle_unescaped
            elif simple_url_2_re.match(middle):
                middle, middle_unescaped, trail = unescape(middle, trail)
                url = 'http://%s' % middle_unescaped

            if url: result.append(url)

    return result


def is_pointer_inside_widget(widget, x=None, y=None):
    result = False
    window = widget.get_window()
    allocation = widget.get_allocation()
    if not allocation or not window: return result

    _, pointer_x, pointer_y, mask  = window.get_pointer()
    if x: pointer_x = x
    if y: pointer_y = y

    if (
        pointer_x >= allocation.x and
        pointer_x <= (allocation.x + allocation.width) and
        pointer_y >= allocation.y and
        pointer_y <= (allocation.y + allocation.height)
    ):
        result = True

    return result


def get_widget_screenshot(widget):
    window = widget.get_window()
    if not window: return None

    allocation = widget.get_allocation()
    pixbuf = Gdk.pixbuf_get_from_window(
        window,
        allocation.x,
        allocation.y,
        allocation.width,
        allocation.height
    )

    if not pixbuf:
        return None
    else:
        return pixbuf
