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
import sys
import signal
import logging
import argparse
from distutils.version import StrictVersion
from dbus.exceptions import DBusException

from gi.repository import Gtk
from draobpilc import get_data_path
from draobpilc import common
from draobpilc import version
from draobpilc.lib import utils

DESKTOP_FILE_PATH = os.path.join(
    os.path.expanduser('~/.local/share/applications'),
    '%s.desktop' % version.APP_NAME
)
DESKTOP_PREFS_FILE_PATH =os.path.join(
    os.path.expanduser('~/.local/share/applications'),
    '%s_prefs.desktop' % version.APP_NAME
)


def check_gpaste_version():
    result = True

    try:
        from draobpilc.lib import gpaste_client
    except DBusException:
        result = False
        current_version = _('Not detected')
    else:
        try:
            gpaste_client.get_history_name()
        except DBusException:
            result = False
            current_version = _('Not detected')
        else:
            current_version = gpaste_client.get_prop('Version')

            if (
                StrictVersion(current_version) <
                StrictVersion(version.GPASTE_VERSION)
            ):
                result = False

    if not result:
        msg = _(
               'GPaste version >= {0} is required, '
               'current version == {1}.'
           ).format(
               version.GPASTE_VERSION,
               current_version
           )
        utils.notify(version.APP_NAME, msg)
        sys.exit(msg)


def install_excepthook():
    """ Make sure we exit when an unhandled exception occurs. """
    old_hook = sys.excepthook

    def new_hook(etype, evalue, etb):
        old_hook(etype, evalue, etb)

        while Gtk.main_level():
            Gtk.main_quit()

        sys.exit()

    sys.excepthook = new_hook


def install_desktop_file():
    desktop_tpl = get_data_path('desktop_file.tpl')
    prefs_tpl = get_data_path('preferences_desktop_file.tpl')

    if os.path.exists(DESKTOP_FILE_PATH):
        print(_('File "%s" already exists.' % DESKTOP_FILE_PATH))
    else:
        print(_('Creating "%s".' % DESKTOP_FILE_PATH))
        with open(desktop_tpl, encoding='utf-8') as tpl_file:
            contents = tpl_file.read()
            contents = contents.replace('{APP_VERSION}', str(version.APP_VERSION))
            contents = contents.replace('{APP_NAME}', version.APP_NAME)
            contents = contents.replace('{COMMENT}', version.APP_DESCRIPTION)
            contents = contents.replace('{EXEC}', 'draobpilc')
            contents = contents.replace('{ICON}', common.ICON_PATH)

            with open(DESKTOP_FILE_PATH, 'w', encoding='utf-8') as desktop_file:
                desktop_file.write(contents)

    if os.path.exists(DESKTOP_PREFS_FILE_PATH):
        print(_('File "%s" already exists.' % DESKTOP_PREFS_FILE_PATH))
    else:
        print(_('Creating "%s".' % DESKTOP_PREFS_FILE_PATH))
        with open(prefs_tpl, encoding='utf-8') as tpl_file:
            contents = tpl_file.read()
            contents = contents.replace('{APP_VERSION}', str(version.APP_VERSION))
            contents = contents.replace('{APP_NAME}', version.APP_NAME)
            contents = contents.replace('{COMMENT}', version.APP_DESCRIPTION)
            contents = contents.replace('{EXEC}', 'draobpilc --preferences')
            contents = contents.replace('{ICON}', common.ICON_PATH)

            with open(DESKTOP_PREFS_FILE_PATH, 'w', encoding='utf-8') as desktop_file:
                desktop_file.write(contents)

    return True


def uninstall_desktop_file():
    if not os.path.exists(DESKTOP_FILE_PATH):
        print(_('File "%s" doesn\'t exits.' % DESKTOP_FILE_PATH))
    else:
        os.remove(DESKTOP_FILE_PATH)
    
    if not os.path.exists(DESKTOP_PREFS_FILE_PATH):
        print(_('File "%s" doesn\'t exits.' % DESKTOP_PREFS_FILE_PATH))
    else:
        os.remove(DESKTOP_PREFS_FILE_PATH)

    return True


def run():
    check_gpaste_version()
    from draobpilc.application import Application
    install_excepthook()

    parser = argparse.ArgumentParser(description='GPaste GUI')
    parser.add_argument('-d', '--debug',
        action='store_true',
        default=False,
        dest='debug'
    )
    parser.add_argument('--install-desktop-file',
        action='store_true',
        default=False,
        dest='install_desktop_file',
        help=_('Add "Draobpilc.desktop" to "~/.local/share/applications"')
    )
    parser.add_argument('--uninstall-desktop-file',
        action='store_true',
        default=False,
        dest='uninstall_desktop_file',
        help=_('Remove "Draobpilc.desktop" from "~/.local/share/applications"')
    )
    parser.add_argument('--preferences',
        action='store_true',
        default=False,
        dest='show_preferences',
        help=_('Show preferences dialog')
    )
    parser.add_argument('--version',
        action='version',
        version=str(version.APP_VERSION_STRING)
    )
    args = parser.parse_args()

    msg_f = '%(asctime)s %(levelname)s\t%(filename)s:%(lineno)d \t%(message)s'
    time_f = '%H:%M:%S'

    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format=msg_f,
            datefmt=time_f
        )

        # Gtk hates "-d" switch, so lets drop it
        if '-d' in sys.argv:
            sys.argv.remove('-d')
        if '--debug' in sys.argv:
            sys.argv.remove('--debug')
    else:
        logging.basicConfig(
            level=logging.WARN,
            format=msg_f,
            datefmt=time_f
        )

    if args.install_desktop_file:
        install_desktop_file()
        sys.exit()
    if args.uninstall_desktop_file:
        uninstall_desktop_file()
        sys.exit()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


if __name__ == '__main__':
    run()
