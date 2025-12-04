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
import locale
import gettext
from typing import Optional, TYPE_CHECKING

from draobpilc import version

if TYPE_CHECKING:
    _ = lambda s: s

locale.setlocale(locale.LC_ALL)
gettext.install(version.APP_NAME, names=('gettext', 'ngettext'))

_ROOT: str = os.path.abspath(os.path.dirname(__file__))
def get_data_path(path: Optional[str] = None) -> str:
    file_name = _ROOT
    if not path: return file_name

    file_name = os.path.join(_ROOT, 'data', path)
    return file_name
