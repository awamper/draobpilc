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

import re


class Result():

    def __init__(self, term, original, score, start, end):
        self.term = term
        self.original = original
        self.score = score
        self.start = start
        self.end = end

    def get_highlighted(
        self,
        escape_func=None,
        max_precede_chars=30,
        highlight_template='%s'
    ):
        matched_string = self.original[self.start : self.end]
        new_string = ''

        if self.start > 0:
            start_index = max(0, self.start - max_precede_chars)
            temp_string = self.original[start_index : self.start]
            if escape_func: temp_string = escape_func(temp_string)

            new_string += '...'
            new_string += temp_string

        search_term = self.term.lower()
        next_term_char = None

        for char in matched_string:
            if not char.lower() in search_term:
                if escape_func: char = escape_func(char)
                new_string += char
            else:
                if next_term_char and char != next_term_char:
                    continue

                try:
                    index = search_term.index(char.lower())
                    next_term_char = search_term[index + 1]
                except (IndexError, ValueError):
                    next_term_char = None

                search_term = search_term.replace(char, '', 1)
                if escape_func: char = escape_func(char)
                new_string += highlight_template % (char)

        other_text = self.original[self.end:]
        if escape_func: other_text = escape_func(other_text) 
        new_string += other_text

        return new_string
    

# based on https://github.com/amjith/fuzzyfinder
def match(term, text, max_distance=30):
    result = None
    term = str(term)
    pattern = '.{0,%i}' % max_distance
    pattern = pattern.join(map(re.escape, term))
    regex = re.compile(pattern, re.I)
    match = regex.search(text)

    if match:
        score = len(match.group()) + match.start()
        result = Result(term, text, score, match.start(), score)

    return result
