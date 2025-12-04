#!/usr/bin/env python3

# Copyright 2025 Ivan awamper@gmail.com
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

from gi.repository import Gtk  # type: ignore

from draobpilc import common
from draobpilc.widgets.indicator_base import IndicatorBase
from draobpilc.history_item_kind import HistoryItemKind


class ItemKindIndicator(IndicatorBase):

    def __init__(self, kind: HistoryItemKind) -> None:
        super().__init__()

        self.set_name('HistoryItemKindIndicator')
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(False)
        self.set_size_request(common.SETTINGS[common.KIND_INDICATOR_WIDTH], -1)
        self.set_kind(kind)
        self.show()
