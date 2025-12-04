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

from typing import Any, Callable, List

import dbus  # type: ignore
import dbus.mainloop.glib  # type: ignore
from gi.repository import Gio  # type: ignore

from draobpilc import common
from draobpilc.lib import utils


class Action():
    REPLACE: str = 'REPLACE'
    REMOVE: str = 'REMOVE'


class Target():
    ALL: str = 'ALL'
    POSITION: str = 'POSITION'


SCHEMA_ID: str = common.SETTINGS[common.GPASTE_SCHEMA_ID]
SETTINGS: Any = None
try:
    SETTINGS = utils.get_settings(SCHEMA_ID)
except utils.SettingsSchemaNotFound:
    pass

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

_bus: Any = dbus.SessionBus()
_gpaste_object: Any = _bus.get_object(
    common.SETTINGS[common.GPASTE_DBUS_NAME],
    common.SETTINGS[common.GPASTE_DBUS_PATH]
)
_client: Any = dbus.Interface(
    _gpaste_object,
    common.SETTINGS[common.GPASTE_DBUS_IFACE]
)


def get_prop(property_name: str) -> Any:
	return _gpaste_object.Get(
        common.SETTINGS[common.GPASTE_DBUS_IFACE],
        property_name,
        dbus_interface='org.freedesktop.DBus.Properties'
    )


def connect(name: str, callback: Callable[..., Any]) -> Any:
    return _client.connect_to_signal(
        name,
        callback,
        dbus_interface=common.SETTINGS[common.GPASTE_DBUS_IFACE]
    )


def disconnect(signal_match: Any) -> None:
    signal_match.remove()


def add(text: str) -> Any:
    return _client.Add(text)


def add_file(path: str) -> Any:
    return _client.AddFile(path)


def get_history() -> List[Any]:
    return _client.GetHistory()


def get_raw_history() -> List[Any]:
    return _client.GetRawHistory()


def get_element(uuid: str) -> str:
    return _client.GetElement(uuid)


def get_raw_element(uuid: str) -> str:
    return _client.GetRawElement(uuid)


def select(uuid: str) -> Any:
    return _client.Select(uuid)


def get_element_kind(uuid: str) -> str:
    return _client.GetElementKind(uuid)


def replace(uuid: str, contents: str) -> Any:
    return _client.Replace(uuid, contents)


def delete(uuid: str) -> Any:
    return _client.Delete(uuid)


def list_histories() -> List[str]:
    histories: List[str] = _client.ListHistories()
    return sorted(histories)


def get_history_size(name: str) -> int:
    return _client.GetHistorySize(name)


def get_history_name() -> str:
    return _client.GetHistoryName()


def switch_history(name: str) -> Any:
    return _client.SwitchHistory(name)


def delete_history(name: str) -> Any:
    return _client.DeleteHistory(name)


def empty_history(name: str) -> Any:
    return _client.EmptyHistory(name)


def track(t: bool) -> Any:
    return _client.Track(t)


def reexecute() -> Any:
    return _client.Reexecute()


def backup_history(history_name: str, backup_name: str) -> Any:
    return _client.BackupHistory(history_name, backup_name)
