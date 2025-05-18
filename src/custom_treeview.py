# From https://stackoverflow.com/questions/1966929/tk-treeview-column-sort

# NOTE: This script is part of the Fuser Custom Song Manager program. Its contents are here for both reference and for use within that program.

import tkinter as tk
import tkinter.ttk as ttk
from functools import partial
import list_ops

class MyTreeview(ttk.Treeview):
    def heading(self, column, sort_by=None, **kwargs):
        if sort_by and not hasattr(kwargs, 'command'):
            func = getattr(self, f"_sort_by_{sort_by}", None)
            if func:
                kwargs['command'] = partial(func, column, False)
        return super().heading(column, **kwargs)

    def _sort(self, column, reverse, data_type, callback):
        # Handles case where "The " and "A " should be ignored from the title of a song or artist name, similar to how Fuser itself handles sorting by song or artist name.
        if (data_type == "remove_the_a"):   
            # songs that start with "the"
            songs_the = [(self.set(k, column).casefold().replace('the ', '', 1), k) for k in self.get_children('') if self.set(k, column).casefold().startswith("the ")]
            # songs that start with "a"
            songs_a = [(self.set(k, column).casefold().replace('a ', '', 1), k) for k in self.get_children('') if self.set(k, column).casefold().startswith("a ")]
            # songs that simultaneously don't start with the and a
            songs_not_the_a =[(self.set(k, column).casefold(), k) for k in self.get_children('') if (not self.set(k, column).casefold().startswith("a ") and not self.set(k, column).casefold().startswith("the "))]
            # all songs, with the first occurances of "the " and "a " removed from their starts, depending on which one comes first
            l = list_ops.union(list_ops.union(songs_a, songs_the), songs_not_the_a)
            data_type = str.casefold
        else:
            l = [(self.set(k, column), k) for k in self.get_children('')]
        
        #print(l)
        l.sort(key=lambda t: data_type(t[0]), reverse=reverse)
        #print("SORT")
        for index, (_, k) in enumerate(l):
            #print(_, k)
            self.move(k, '', index)
        self.heading(column, command=partial(callback, column, not reverse))

    def _sort_by_num(self, column, reverse):
        self._sort(column, reverse, int, self._sort_by_num)

    def _sort_by_name(self, column, reverse):
        self._sort(column, reverse, str.casefold, self._sort_by_name)

    def _sort_by_name_ignore_words(self, column, reverse):
        self._sort(column, reverse, "remove_the_a", self._sort_by_name_ignore_words)
        
    def _convert_camelot_display_to_sort_val(self, display_val):
        """Converts a display Camelot key (e.g., "1A") to a sortable one (e.g., "01A")."""
        if not display_val or display_val == "Unknown":
            return display_val 

        num_part_str = ""
        letter_part_str = ""
        is_num_part = True
        for char_idx, char in enumerate(display_val):
            if char.isdigit() and is_num_part:
                num_part_str += char
            else:
                is_num_part = False # Once a non-digit is hit, the rest is letter part
                letter_part_str += char
        
        if not num_part_str or not letter_part_str: # Malformed (e.g. "A", "1", "")
             # Check if it's something like "10", "11", "12" without A/B, unlikely for Camelot
            if num_part_str and not letter_part_str: # e.g. "10"
                try:
                    num_only = int(num_part_str)
                    if 1 <= num_only <= 9: return f"0{num_only}"
                    return num_part_str # "10", "11", "12"
                except ValueError: return display_val # Should not happen
            return display_val 

        try:
            num = int(num_part_str)
            # Standard Camelot keys are 1-12 followed by A or B
            if letter_part_str in ("A", "B"):
                if 1 <= num <= 9:
                    return f"0{num}{letter_part_str}" # e.g., "01A"
                elif 10 <= num <= 12:
                    return f"{num}{letter_part_str}" # e.g., "10A"
            return display_val # If letter part is not A or B, or num out of range
        except ValueError:
            return display_val # num_part_str wasn't purely digits

    def _sort_by_camelot(self, column, reverse):
        """Sorts the column by Camelot key, converting display version to sortable version."""
        l_to_sort = []
        for k_child in self.get_children(''):
            display_value = self.set(k_child, column)
            sort_key = self._convert_camelot_display_to_sort_val(display_value)
            l_to_sort.append((sort_key, k_child))

        # Sort by the generated sort_key
        l_to_sort.sort(key=lambda t: t[0], reverse=reverse)
        
        # Reorder items in the treeview
        for index, (_, k) in enumerate(l_to_sort):
            self.move(k, '', index)
        
        # Update the heading command for the next sort
        self.heading(column, command=partial(self._sort_by_camelot, column, not reverse))