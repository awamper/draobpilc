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

from blinker import Signal


class NameAlreadyExists(Exception):
    """ raise when attempt add signal with already taken name """


class SignalNotFound(Exception):
    """ when attempt to emit/connect/disconnect signal that doesn't exist """


class Emitter():

    def __init__(self):
        self._signals = {}

    def add_signal(self, name):
        signal = self._signals.get(name, False)
        if signal: raise NameAlreadyExists()

        self._signals[name] = Signal()

    def connect(self, name, callback):
        signal = self._signals.get(name, False)
        if not signal: raise SignalNotFound()

        signal.connect(callback, sender=self)

    def disconnect(self, name, callback):
        signal = self._signals.get(name, False)
        if not signal: raise SignalNotFound()

        signal.disconnect(callback, sender=self)

    def emit(self, name, **kwargs):
        signal = self._signals.get(name, False)
        if not signal: raise SignalNotFound()

        signal.send(self, **kwargs)
