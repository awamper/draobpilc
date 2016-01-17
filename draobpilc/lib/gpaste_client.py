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

import dbus
import dbus.mainloop.glib

from gi.repository import Gio

SCHEMA_ID = 'org.gnome.GPaste'
SETTINGS = Gio.Settings(SCHEMA_ID)


class Action():
    REPLACE = 'REPLACE'
    REMOVE = 'REMOVE'


class Target():
    ALL = 'ALL'
    POSITION = 'POSITION'


class Kind():
    TEXT = 'Text'
    IMAGE = 'Image'
    FILE = 'Uris'
    LINK = 'Link'


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

DBUS_NAME = 'org.gnome.GPaste'
DBUS_PATH = '/org/gnome/GPaste'
DBUS_IFACE = 'org.gnome.GPaste1'

_bus = dbus.SessionBus()
_gpaste_object = _bus.get_object(DBUS_NAME, DBUS_PATH)
_client = dbus.Interface(_gpaste_object, DBUS_IFACE)


def get_prop(property_name):
	return _gpaste_object.Get(
        DBUS_IFACE,
        property_name,
        dbus_interface='org.freedesktop.DBus.Properties'
    )


def connect(name, callback):
	return _client.connect_to_signal(name, callback)


def add(text):
    return _client.Add(text)


def get_history():
    return _client.GetHistory()


def get_raw_history():
    return _client.GetRawHistory()


def get_element(index):
    return _client.GetElement(index)


def get_raw_element(index):
    return _client.GetRawElement(index)


def select(index):
    return _client.Select(index)


def get_element_kind(index):
    return _client.GetElementKind(index)


def replace(index, contents):
    return _client.Replace(index, contents)


def delete(index):
    return _client.Delete(index)


def list_histories():
    histories = _client.ListHistories()
    return sorted(histories)


def get_history_size(name):
    return _client.GetHistorySize(name)


def get_history_name():
    return _client.GetHistoryName()


def switch_history(name):
    return _client.SwitchHistory(name)


def delete_history(name):
    return _client.DeleteHistory(name)


def empty_history(name):
    return _client.EmptyHistory(name)
