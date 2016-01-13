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

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from draobpilc import common
from draobpilc import version


class AboutDialog(Gtk.AboutDialog):

    def __init__(self):
        Gtk.AboutDialog.__init__(self)
        self.connect('response', lambda w, r: self.destroy())

        self.set_modal(True)
        self.set_title(_('About {app_name}').format(
            app_name=version.APP_NAME
        ))
        self.set_program_name(version.APP_NAME)
        self.set_copyright(_('Copyright \xa9 2015 {author}.').format(
            author=version.AUTHOR
        ))
        self.set_website(version.APP_URL)
        self.set_website_label(_('Homepage'))
        self.set_license_type(Gtk.License.GPL_3_0)

        authors = [
            '{author} <{author_email}>'.format(
                author=version.AUTHOR,
                author_email=version.AUTHOR_EMAIL
            )
        ]

        self.set_authors(authors)
        self.set_version(str(version.APP_VERSION))

        logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(common.ICON_PATH)
        self.set_logo(logo_pixbuf)
