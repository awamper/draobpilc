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
import os
import signal
import sys
from types import TracebackType
from typing import Any, List, TYPE_CHECKING

from packaging.version import Version

import gi  # type: ignore
gi.require_version('Gtk', '3.0')

from dbus.exceptions import DBusException  # type: ignore
from gi.repository import Gtk  # type: ignore

from draobpilc import common, version
from draobpilc.lib import utils

if TYPE_CHECKING:
    _ = lambda s: s


def check_gpaste_version() -> None:
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
                Version(current_version) <
                Version(version.GPASTE_VERSION)
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
        sys.exit(1)


def install_excepthook() -> None:
    """ Make sure we exit when an unhandled exception occurs. """
    old_hook = sys.excepthook

    def new_hook(etype: type[BaseException], evalue: BaseException, etb: TracebackType | None) -> None:
        old_hook(etype, evalue, etb)

        while Gtk.main_level():
            Gtk.main_quit()

        sys.exit()

    sys.excepthook = new_hook


def run() -> int:
    check_gpaste_version()
    from draobpilc.application import Application
    install_excepthook()

    parser = argparse.ArgumentParser(description='GPaste GUI')
    parser.add_argument('-d', '--debug',
        action='store_true',
        default=False,
        dest='debug'
    )
    parser.add_argument('--preferences',
        action='store_true',
        default=False,
        dest='show_preferences',
        help=_('Show preferences dialog')
    )
    parser.add_argument('--toggle',
        action='store_true',
        default=False,
        dest='toggle',
        help=_('Show/hide the window')
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

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = Application()
    return app.run(sys.argv)

def main() -> None:
    """Main entry point."""
    sys.exit(run())


if __name__ == '__main__':
    main()
