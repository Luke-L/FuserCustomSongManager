from manager_classes import Song, ProgramProperties
from program_enums import Genres, SongMode, SongKey, LauncherType
from loader import *
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import filedialog as fd
import tkinter.ttk as ttk
from custom_treeview import MyTreeview
from song_extract import extract_song
from update_checker import check_for_update
from camelot_utils import get_camelot_key # Added import
import shutil
import subprocess
import time
import os
import sys
import re
from configparser import ConfigParser
import webbrowser

# FUSER CUSTOM SONG MANAGER, by Lilly :)
version_number = "1.1.2" # Consider updating if this is a new version with this change

# global debug constant
DEBUG = False

fuser_process_name = "Fuser-Win64-Shipping.exe"
fuser_alt_process_name = "FuserEOS-Win64-Shipping.exe"

startupinfo_hideconsole = subprocess.STARTUPINFO()
startupinfo_hideconsole.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# NEW helper function
def format_camelot_for_display(sortable_key):
    """Converts a sortable Camelot key (e.g., "01A") to a display one (e.g., "1A")."""
    if not sortable_key or sortable_key == "Unknown":
        return sortable_key
    if len(sortable_key) > 1 and sortable_key.startswith('0') and sortable_key[1].isdigit():
        # Check if the part after '0' is indeed a single digit followed by A or B
        if len(sortable_key) == 3 and sortable_key[2] in ('A', 'B'):
             return sortable_key[1:] # "01A" -> "1A"
    return sortable_key # Handles "10A", "11B", "12A", "Unknown", or already formatted


# Helper functions
def rating_to_star_text(rating_int):
    return ("★" * rating_int) + ("☆" * (5 - rating_int))

def text_to_rating_int(rating_text):
    star_count = 0
    for i in range(len(rating_text)):
        if rating_text[i] == "★":
            star_count += 1
    return star_count

def checkbox_to_bool(check_text):
    return True if check_text == "☑" else False

def bool_to_checkbox_text(value):
    return "☑" if value else "☐"

# Taken from https://stackoverflow.com/a/29275361
def process_exists(process_name):
    if DEBUG:
        print("BEGIN process_exists")
    call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call, startupinfo=startupinfo_hideconsole).decode(encoding=sys.stdout.encoding)
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    if DEBUG:
        print("END process_exists")
    return last_line.lower().startswith(process_name.lower())

def process_exists_2(process_name, alt_process_name):
    if DEBUG:
        print("BEGIN process_exists_2")
    progs = str(subprocess.check_output('tasklist', startupinfo=startupinfo_hideconsole))
    if (process_name in progs) or (alt_process_name in progs):
        if DEBUG:
            print("END process_exists_2")
        return True
    else:
        if DEBUG:
            print("END process_exists_2")
        return False

# Song edit dialog window, which appears when editing a song's info (rating, enabled/disabled state, etc)
class SongEditDialog(simpledialog.Dialog):
    def __init__(self, master, song_info):
        self.song_info = song_info
        super(SongEditDialog, self).__init__(master)
        #def __init__(self, *args, **kwargs):

    def body(self, master):
        self.iconbitmap("gui_icons/program_icon.ico")
        # show immutable song info at the top
        width_padding = 5
        height_padding = 5
        ttk.Label(master, text="Filename", anchor=tk.W).grid(row=0, column=0, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Song name", anchor=tk.W).grid(row=0, column=1, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Artist", anchor=tk.W).grid(row=0, column=2, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Year", anchor=tk.W).grid(row=0, column=3, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Genre", anchor=tk.W).grid(row=0, column=4, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Key", anchor=tk.W).grid(row=0, column=5, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Mode", anchor=tk.W).grid(row=0, column=6, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="BPM", anchor=tk.W).grid(row=0, column=7, sticky= 'W', padx=width_padding)

        ttk.Label(master, text=self.song_info[0], anchor=tk.W).grid(row=1, column=0, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[1], anchor=tk.W).grid(row=1, column=1, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[2], anchor=tk.W).grid(row=1, column=2, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[3], anchor=tk.W).grid(row=1, column=3, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[4], anchor=tk.W).grid(row=1, column=4, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[5], anchor=tk.W).grid(row=1, column=5, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[6], anchor=tk.W).grid(row=1, column=6, sticky= 'W', padx=width_padding)
        ttk.Label(master, text=self.song_info[7], anchor=tk.W).grid(row=1, column=7, sticky= 'W', padx=width_padding) # This is BPM (original index 7)

        entry_section = tk.Frame(master)
        #have dropdown for selecting rating and tickbox for whether or not the song should be enabled
        self.is_enabled_var = tk.BooleanVar(value=checkbox_to_bool(self.song_info[8])) # Enabled? (original index 8)
        #print(self.song_info)
        #is_enabled_var.set() #☑☐
        self.is_enabled_checkbutton = ttk.Checkbutton(entry_section, text="Enabled?", variable=self.is_enabled_var)
        if (process_exists_2(fuser_process_name, fuser_alt_process_name)):
            print("Process is currently running")
            self.is_enabled_checkbutton.configure(state=tk.DISABLED)
        else:
            print("Process is not running")
        #is_enabled_checkbutton.select()

        self.is_enabled_checkbutton.grid(row=0, column=0, pady=height_padding)

        self.rating_stringvar = tk.StringVar()
        self.rating_combobox = ttk.Combobox(entry_section, textvariable=self.rating_stringvar, state='readonly', width=10)
        self.rating_combobox['values'] =   ('☆☆☆☆☆',
                                            '★☆☆☆☆',  
                                            '★★☆☆☆', 
                                            '★★★☆☆', 
                                            '★★★★☆', 
                                            '★★★★★')
        ttk.Label(entry_section, text="Rating:", justify="right").grid(row=0, column=1, padx=(10, 0), pady=height_padding, sticky='e')
        self.rating_combobox.grid(row=0, column=2, pady=height_padding, sticky='w')
        self.rating_combobox.current(text_to_rating_int(self.song_info[9])) # Rating (original index 9)

        #notes: self.song_info[10]
        #author: self.song_info[11]

        # have entries at the bottom for entering author and notes
        notes_frame = ttk.Frame(entry_section)
        self.author_entry = ttk.Entry(entry_section)
        self.author_entry.delete(0, tk.END)
        self.author_entry.insert(0, self.song_info[11]) # Author (original index 11)
        ttk.Label(notes_frame, text="Notes:", justify="left").grid(row=0, column=0, sticky='w')
        self.notes_entry = tk.Text(notes_frame)
        self.notes_entry.delete("1.0", tk.END)
        self.notes_entry.insert("1.0", self.song_info[10]) # Notes (original index 10)
        self.notes_entry.grid(row=1, column=0)

        ttk.Label(entry_section, text="Author:", justify="right").grid(row=0, column=3, padx=(10, 0), pady=height_padding, sticky='e')
        self.author_entry.grid(row=0, column=4, pady=height_padding, sticky='w')
        notes_frame.grid(row=2, column=0, columnspan=5)

        entry_section.grid(row=3, column=0, columnspan=8, pady=height_padding)
        return self.author_entry # initial focus

    # Store results from dialog box inside self.result, for other areas to extract results
    def apply(self):
        new_enabled_state = self.is_enabled_var.get()
        #print(new_enabled_state)
        new_rating = self.rating_stringvar.get()
        #print(new_rating)
        new_notes = self.notes_entry.get("1.0", tk.END)[:-1]
        new_author = self.author_entry.get()
        self.result = (new_enabled_state, new_rating, new_notes, new_author)
        print(self.result)

# more helper functions
def paste_folder_name(string_var):

    # potential fix for issue where you can open multiple folder dialogs at once taken from here: https://stackoverflow.com/a/7090747
    temp_window = tk.Toplevel()
    temp_window.withdraw()

    temp_window.overrideredirect(True)
    temp_window.geometry('0x0+0+0')

    # Show window again and lift it to top so it can get focus,
    # otherwise dialogs will end up behind the terminal.
    temp_window.deiconify()
    temp_window.lift()
    temp_window.focus_force()
    temp_window.grab_set()

    folder_name = fd.askdirectory(parent=temp_window)
    temp_window.destroy()
    if (folder_name != ''):
        string_var.set(folder_name)

def paste_file_name(string_var):
    filetypes = (
        ('Executable files', '*.exe'),
        ('Executable files', '*.bat')
    )
    file_name = fd.askopenfilename(filetypes=filetypes)
    if (file_name != ''):
        string_var.set(file_name)

def is_archive(path_to_file):
    return (path_to_file.endswith(".zip") or path_to_file.endswith(".rar") or path_to_file.endswith(".7z"))

def query_array_to_string(query_array):
    return_string = ""
    if len(query_array) == 0:
        return ""
    elif len(query_array) == 1:
        return query_array[0]
    else:
        for i in range(len(query_array) - 1):
            return_string += query_array[i] + " AND "
        return_string += query_array[len(query_array) - 1]
        return return_string
    
def get_two_nums_from_input(var1, var2, search_type_string):
    return_nums = []
    first_num = re.search(r'\d+', var1.get())
    second_num = re.search(r'\d+', var2.get())
    if (len(var1.get()) == 0):
        return None
    if (len(var1.get()) != 0 and first_num == None):
        messagebox.showerror("Entry error", f"First number in {search_type_string} search has no valid numbers!\nIgnoring {search_type_string} search for this query.")
        return None
    first_num = first_num.group()
    if (len(var2.get()) == 0):
        # we only have a single number
        #remaining_query = f"year = {first_num}"
        return_nums.append(first_num)
    else:
        # we have two nums, search for a range
        # ensure second num is valid
        if second_num == None:
            messagebox.showerror("Entry error", f"Second number in {search_type_string} search has no valid numbers!\nIgnoring {search_type_string} search for this query.")
        else:
            second_num = second_num.group()
            larger_num = max(int(first_num), int(second_num))
            smaller_num = min(int(first_num), int(second_num))
            #remaining_query = f"year >= {smaller_num} AND year <= {larger_num}"
            return_nums.append(smaller_num)
            return_nums.append(larger_num)
    return return_nums


# First time popup window, which appears when launching the manager for the first time
class FirstTimePopup(tk.Toplevel):
    def get_data(self):
        if DEBUG:
            print("OK ON FIRST TIME POPUP")
        if (len(self.fuser_path_string.get()) == 0):
            messagebox.showerror("Fuser path missing!", "Fuser install path is left blank.\nPlease try again.")
            return
        if (self.install_type_string.get() == 'Local' and len(self.executable_path_string.get()) == 0):
            messagebox.showerror("Install path missing!", "Install type is set to Local, yet install path is missing.\nPlease try again.")
            return
        
        if (len(self.disabled_path_string.get()) == 0):
            self.result = (self.fuser_path_string.get().replace("/", "\\"), None, self.executable_path_string.get().replace("/", "\\"), self.install_type_string.get())    
        else:
            self.result = (self.fuser_path_string.get().replace("/", "\\"), self.disabled_path_string.get().replace("/", "\\"), self.executable_path_string.get().replace("/", "\\"), self.install_type_string.get())
        if DEBUG:
            print("RESULTS FROM FIRST TIME POPUP:")
            print(self.result)
        messagebox.showinfo("Initial startup", "Since this is the first time the program has been run, it needs to initialize the database with all of your existing songs, if you have any.\nThis may take a moment. The manager may appear momentarily frozen while the database is set up.\nPress OK to continue.")
        self.destroy()

    def __init__(self, root):
        tk.Toplevel.__init__(self, root)
        self.fuser_path_string = tk.StringVar()
        self.disabled_path_string = tk.StringVar()
        self.executable_path_string = tk.StringVar()
        self.install_type_string = tk.StringVar(value='Steam')

        # Info labels
        label = ttk.Label(self, text="Welcome to the Fuser Custom Song Manager!\nIt appears this is your first time running the program.", justify="center")
        label.pack(padx=20, pady=(20, 5), anchor=tk.CENTER)
        label2_text = "Please select the following file paths:\n * Fuser install directory (i.e. C:\\Program Files (x86)\\Steam\\steamapps\\common\\Fuser, the folder containing \"Fuser.exe\")\n * Disabled songs path (where you would like your disabled songs to be placed.)\n    * If left blank, this will default to (your fuser install)\\Fuser\\Content\\Paks\\disabled_songs.\n * Install type\n    * If you purchased the game before it was delisted, select either Steam or Epic depending on where you bought it. Otherwise, select Local.\n * Executable path (optional)\n    * If running locally via an .exe or .bat file, make sure to fill this out. This should be the executable or batch file you use to start the game."
        label2 = ttk.Label(self, text=label2_text, justify="left")
        label2.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # Entry section
        paths_frame = tk.Frame(self)
        ttk.Label(paths_frame, text="Fuser install directory:").grid(row=0, column=0, sticky='W')
        fuser_path_entry = ttk.Entry(paths_frame, textvariable=self.fuser_path_string)
        fuser_path_entry.grid(row=0, column=1)
        fuser_select_button = ttk.Button(paths_frame, text="Select...", style='Centered.TButton', command=lambda: paste_folder_name(self.fuser_path_string))
        fuser_select_button.grid(row=0, column=2)

        ttk.Label(paths_frame, text="Disabled songs directory:").grid(row=1, column=0, sticky='W')
        disabled_path_entry = ttk.Entry(paths_frame, textvariable=self.disabled_path_string)
        disabled_path_entry.grid(row=1, column=1)
        disabled_select_button = ttk.Button(paths_frame, text="Select...", style='Centered.TButton', command=lambda: paste_folder_name(self.disabled_path_string))
        disabled_select_button.grid(row=1, column=2)

        ttk.Label(paths_frame, text="Install type:").grid(row=2, column=0, sticky='W')
        launcher_type_combobox = ttk.Combobox(paths_frame, state='readonly', textvariable=self.install_type_string)
        launcher_type_combobox['values'] = ('Steam', 'Epic', 'Local')
        launcher_type_combobox.grid(row=2, column=1, columnspan=2)
        launcher_type_combobox.current(0)
        launcher_type = LauncherType[launcher_type_combobox.get()]


        ttk.Label(paths_frame, text="Local executable (optional):").grid(row=3, column=0, sticky='W')
        executable_path_entry = ttk.Entry(paths_frame, textvariable=self.executable_path_string)
        executable_path_entry.grid(row=3, column=1)
        executable_select_button = ttk.Button(paths_frame, text="Select...", style='Centered.TButton', command=lambda: paste_file_name(self.executable_path_string))
        executable_select_button.grid(row=3, column=2)

        button = ttk.Button(self, text="Save", command=self.get_data, style='Centered.TButton')
        button.pack(side="bottom", pady=10)
        paths_frame.pack(side='bottom')

        # if fuser install path is empty, show an error
        # if disabled songs path is empty, set to custom_songs/disabled_songs
        # if install type is local and executable path is empty, show error and quit program

        self.result = "uninitialized!"

# Config dialog window, allows user to set various paths
class ConfigDialog(simpledialog.Dialog):
    def __init__(self, master):
        super(ConfigDialog, self).__init__(master)
        #def __init__(self, *args, **kwargs):

    def body(self, master):
        self.result = False
        self.iconbitmap("gui_icons/program_icon.ico")
        self.fuser_path = tk.StringVar(value=prog_properties.fuser_directory)
        #self.database_path = tk.StringVar(value=prog_properties.database_location)
        self.install_type = tk.StringVar(value=prog_properties.launcher_type.name)
        self.executable_path = tk.StringVar(value=prog_properties.executable_path)

        # show immutable song info at the top
        width_padding = 5
        ttk.Label(master, text="Fuser install path", anchor=tk.W).grid(row=0, column=0, sticky= 'W', padx=width_padding)
        #ttk.Label(master, text="Database path", anchor=tk.W).grid(row=1, column=0, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Install Type", anchor=tk.W).grid(row=1, column=0, sticky= 'W', padx=width_padding)
        ttk.Label(master, text="Executable path", anchor=tk.W).grid(row=2, column=0, sticky= 'W', padx=width_padding)

        self.fuser_path_entry = ttk.Entry(master, textvariable=self.fuser_path)
        self.fuser_path_entry.grid(row=0, column=1, padx=width_padding)
        #self.database_path_entry = ttk.Entry(master, textvariable=self.database_path)
        #self.database_path_entry.grid(row=1, column=1, padx=width_padding)
        self.install_type_combobox = ttk.Combobox(master, textvariable=self.install_type, state='readonly')
        self.install_type_combobox['values'] = ('Steam', 'Epic', 'Local')
        self.install_type_combobox.grid(row=1, column=1, padx=width_padding, columnspan=2)
        self.executable_path_entry = ttk.Entry(master, textvariable=self.executable_path)
        self.executable_path_entry.grid(row=2, column=1, padx=width_padding)
        
        fuser_select_button = ttk.Button(master, text="Select...", style='Centered.TButton', command=lambda: paste_folder_name(self.fuser_path))
        fuser_select_button.grid(row=0, column=2)
        #database_select_button = ttk.Button(master, text="Select...", style='Centered.TButton', command=lambda: paste_folder_name(self.database_path))
        #database_select_button.grid(row=1, column=2)
        executable_select_button = ttk.Button(master, text="Select...", style='Centered.TButton', command=lambda: paste_file_name(self.executable_path))
        executable_select_button.grid(row=2, column=2)

        return self.fuser_path_entry # initial focus
        #return True

    def apply(self):
        # Save results from input
        prog_properties.fuser_directory = self.fuser_path.get().replace("/", "\\")
        prog_properties.launcher_type = LauncherType[self.install_type.get()]
        prog_properties.executable_path = self.executable_path.get().replace("/", "\\")

        # return results
        self.result = True

# Search dialog, allowing users to search by various metrics of a song
class SearchDialog(simpledialog.Dialog):
    # what's needed:
    # search box that has tabs at the top to determine search type
    # one tab for each type (search by song name, artist name, year range, bpm range, genre type)

    def __init__(self, master):
        super(SearchDialog, self).__init__(master)

    def body(self, master):
        self.result = False
        self.iconbitmap("gui_icons/program_icon.ico")
        tk.Label(master, text="Search by...", justify="left").pack(anchor='w')
        main_frame = tk.Frame(master)
        main_frame.pack()
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack()

        filename_frame = tk.Frame(self.notebook)
        song_frame = tk.Frame(self.notebook)
        artist_frame = tk.Frame(self.notebook)
        year_frame = tk.Frame(self.notebook)
        genre_frame = tk.Frame(self.notebook)
        keymode_frame = tk.Frame(self.notebook)
        bpm_frame = tk.Frame(self.notebook)
        filename_frame.pack()
        song_frame.pack()
        artist_frame.pack()
        year_frame.pack()
        genre_frame.pack()
        keymode_frame.pack()
        bpm_frame.pack()

        # Filename (short name) search
        tk.Label(filename_frame, text="File name:").grid(row=0, column=0, sticky='w')
        self.search_filename_var = tk.StringVar()
        self.search_filename_entry = ttk.Entry(filename_frame, textvariable=self.search_filename_var)
        self.search_filename_entry.grid(row=0, column=1)

        # Song name search
        tk.Label(song_frame, text="Song name:").grid(row=0, column=0, sticky='w')
        self.search_song_name_var = tk.StringVar()
        self.search_song_name_entry = ttk.Entry(song_frame, textvariable=self.search_song_name_var)
        self.search_song_name_entry.grid(row=0, column=1)

        # Artist name search
        tk.Label(artist_frame, text="Artist name:").grid(row=0, column=0, sticky='w')
        self.search_artist_name_var = tk.StringVar()
        self.search_artist_name_entry = ttk.Entry(artist_frame, textvariable=self.search_artist_name_var)
        self.search_artist_name_entry.grid(row=0, column=1)

        # Year search
        tk.Label(year_frame, text="Released in/From:").grid(row=0, column=0, sticky='w')
        tk.Label(year_frame, text="To (optional):").grid(row=1, column=0, sticky='w')
        self.first_year_var = tk.StringVar()
        self.second_year_var = tk.StringVar()
        self.search_first_year_entry = ttk.Entry(year_frame, textvariable=self.first_year_var)
        self.search_second_year_entry = ttk.Entry(year_frame, textvariable=self.second_year_var)
        self.search_first_year_entry.grid(row=0, column=1)
        self.search_second_year_entry.grid(row=1, column=1)

        # Genre search
        tk.Label(genre_frame, text="Genre:").grid(row=0, column=0, sticky='w')
        self.genre_var = tk.StringVar()
        self.search_genre_combo = ttk.Combobox(genre_frame, state='readonly', textvariable=self.genre_var)
        self.search_genre_combo['values'] = ('', 'Classical', 'Country', 'Rock', 'LatinAndCaribbean', 'Pop', 'RnB', 'HipHop', 'Dance')
        self.search_genre_combo.grid(row=0, column=1)

        # Key/mode search (in single page) using two dropdowns
        tk.Label(keymode_frame, text="Key:").grid(row=0, column=0, sticky='w')
        tk.Label(keymode_frame, text="Mode:").grid(row=1, column=0, sticky='w')
        self.key_var = tk.StringVar()
        self.search_key_combo = ttk.Combobox(keymode_frame, state='readonly', textvariable=self.key_var)
        self.search_key_combo['values'] = ('', 'C', "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
        self.search_key_combo.grid(row=0, column=1)
        self.mode_var = tk.StringVar()
        self.search_mode_combo = ttk.Combobox(keymode_frame, state='readonly', textvariable=self.mode_var)
        self.search_mode_combo['values'] = ('', 'Major', "Minor")
        self.search_mode_combo.grid(row=1, column=1)

        # BPM search
        tk.Label(bpm_frame, text="From:").grid(row=0, column=0, sticky='w')
        tk.Label(bpm_frame, text="To (optional):").grid(row=1, column=0, sticky='w')
        self.first_bpm_var = tk.StringVar()
        self.second_bpm_var = tk.StringVar()
        self.search_first_bpm_entry = ttk.Entry(bpm_frame, textvariable=self.first_bpm_var)
        self.search_second_bpm_entry = ttk.Entry(bpm_frame, textvariable=self.second_bpm_var)
        self.search_first_bpm_entry.grid(row=0, column=1)
        self.search_second_bpm_entry.grid(row=1, column=1)

        #(search by song name, artist name, year range, genre type, key and mode, or bpm range)
        self.notebook.add(filename_frame, text="Filename")
        self.notebook.add(song_frame, text="Song Name")
        self.notebook.add(artist_frame, text="Artist")
        self.notebook.add(year_frame, text="Year")
        self.notebook.add(genre_frame, text="Genre")
        self.notebook.add(keymode_frame, text="Key & Mode")
        self.notebook.add(bpm_frame, text="BPM Range")

        return self.search_song_name_entry # initial focus

    def apply(self):
        if DEBUG:
            print("OK ON SEARCH POPUP")
        query = 'SELECT * from songs WHERE '
        remaining_query = ''

        # make an array that contains all of the subqueries we want to process, then combine them all into a single query, placing " AND " after each query, but not after the last one
        queries = []

        # If these entries have data, add them to the query list
        if (len(self.search_filename_var.get()) != 0):
            queries.append("UPPER(filename) LIKE '%" + self.search_filename_var.get().replace("'", "''").upper() + "%'")
        
        if (len(self.search_song_name_var.get()) != 0):
            queries.append("UPPER(name) LIKE '%" + self.search_song_name_var.get().replace("'", "''").upper() + "%'")

        if (len(self.search_artist_name_var.get()) != 0):
            queries.append("UPPER(artist) LIKE '%" + self.search_artist_name_var.get().replace("'", "''").upper() + "%'")

        if (len(self.first_year_var.get()) != 0):
            nums = get_two_nums_from_input(self.first_year_var, self.second_year_var, "year")
            if nums != None:
                if len(nums) == 1:
                    queries.append(f"year = {nums[0]}")
                elif len(nums) == 2:
                    queries.append(f"year >= {nums[0]} AND year <= {nums[1]}")

        if (len(self.key_var.get()) != 0):
            key_string = self.key_var.get()
            key_int = SongKey[key_string].value
            queries.append(f"key = {key_int}")
        
        if (len(self.mode_var.get()) != 0):
            mode_string = self.mode_var.get()
            mode_int = SongMode[mode_string].value
            queries.append(f"mode = {mode_int}")
        
        if (len(self.first_bpm_var.get()) != 0):
            nums = get_two_nums_from_input(self.first_bpm_var, self.second_bpm_var, "bpm")
            if nums != None:
                if len(nums) == 1:
                    queries.append(f"bpm = {nums[0]}")
                elif len(nums) == 2:
                    queries.append(f"bpm >= {nums[0]} AND bpm <= {nums[1]}")

        if (len(self.genre_var.get()) != 0):
            genre_string = self.genre_var.get()
            genre_int = Genres[genre_string].value
            queries.append(f"genre = {genre_int}")

        # Get the final remaining query and add it onto the beginning query
        remaining_query = query_array_to_string(queries)
        if (len(remaining_query) == 0):
            return
        query += remaining_query
        # Save query result for use later
        self.result = query
        if DEBUG:
            print("SEARCH QUERY:")
            print(self.result)


#--------------------------------
# Main program setup starts here
#--------------------------------

# ensure that current working directory is where the executable is placed
application_path = None
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
#print(application_path)
os.chdir(application_path)

appdata_path = pathlib.Path.home() / 'AppData/Local/FuserCustomSongManager'
config_file_path = appdata_path / 'config.ini'
db_file_path = appdata_path / 'db'

try:
    appdata_path.mkdir(parents=True, exist_ok=True)
    db_file_path.mkdir(parents=True, exist_ok=True)
except PermissionError as e:
    print(f"Permission error in creating the folder {appdata_path} or {db_file_path}")
    print(e)
    sys.exit()
db_file_path = db_file_path / 'songs.sqlite'

window = tk.Tk()
window.iconbitmap("gui_icons/program_icon.ico")
window.title("Fuser Custom Song Manager")
window.resizable(width = 1, height = 1)
window.geometry('1480x720') # Adjusted width slightly for new column
#window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=1)

# Top row button functionality

# Refresh song list on demand
def refresh_list(clear_button):
    # Delete song cache if it exists
    if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak"):
        os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak")
    if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig"):
        os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig")

    # Clear out treeview
    for item in songs_table_tree.get_children():
        songs_table_tree.delete(item)

    clear_button.configure(state='disabled')
    # It's good practice to ensure db_connection is managed (e.g. closed if opened here, or passed if global)
    # Assuming db_connection is available globally or re-established as needed by init_database
    current_db_connection = init_database(prog_properties.database_location, prog_properties.enabled_directory, prog_properties.disabled_directory, False)
    db_songs_raw = execute_db_read_query(current_db_connection, "SELECT * from songs ORDER BY filename")

    # fill out tree view
    processed_songs_for_treeview = []
    for i, original_db_tuple in enumerate(db_songs_raw): # Added enumerate for unique iid
        star_string = rating_to_star_text(original_db_tuple[9])
        enabled_string = "☑" if (original_db_tuple[8] == 1) else "☐"

        key_name_str = SongKey(original_db_tuple[5]).name
        mode_name_str = SongMode(original_db_tuple[6]).name # <<<< We need this
        camelot_input_str = f"{key_name_str} {mode_name_str}"
        
        sortable_camelot_value = get_camelot_key(camelot_input_str)
        display_camelot_value = format_camelot_for_display(sortable_camelot_value)

        song_display_tuple = (
            original_db_tuple[0], original_db_tuple[1], original_db_tuple[2], original_db_tuple[3],
            Genres(original_db_tuple[4]).name, key_name_str, mode_name_str, original_db_tuple[7],
            enabled_string, star_string, original_db_tuple[10], original_db_tuple[11],
            display_camelot_value
        )
        
        current_tags = ()
        if mode_name_str == "Minor":
            current_tags = ('minor_song',)
            
        songs_table_tree.insert(parent="", index='end', iid=i, text="", values=song_display_tuple, tags=current_tags)
    # if current_db_connection was opened here, consider closing it. If global, manage accordingly.

    
    
    

# Launches the game and deletes custom song cache if it exists
def launch_fuser():
    if DEBUG:
        print("BEGIN launch_fuser")
    # delete custom songs cache if it exists
    if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak"):
        os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak")
    if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig"):
        os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig")

    if DEBUG:
        print("LAUNCHER TYPE:")
        print(prog_properties.launcher_type.name)

    if (prog_properties.launcher_type == LauncherType.Steam):
        subprocess.run("cmd /c start steam://run/1331440", startupinfo=startupinfo_hideconsole)
    elif (prog_properties.launcher_type == LauncherType.Epic):
        messagebox.showerror("Fuser on Epic", "Currently, we do not support launching Fuser through this program if it's installed via the Epic Games Launcher.\nPlease launch Fuser through the Epic Games Launcher instead.")
        #subprocess.run("cmd /c start com.epicgames.launcher://apps/" + 2939f4752d4b4ace95a8e1b16e79d3f5 + "?action=launch&silent=true")
        # the above may be correct, have yet to verify this!
    elif (prog_properties.launcher_type == LauncherType.Local):
        if DEBUG:
            print("STARTING FILE " + prog_properties.executable_path)
        #old_cwd = application_path
        os.chdir(os.path.dirname(prog_properties.executable_path))
        subprocess.Popen(prog_properties.executable_path, startupinfo=startupinfo_hideconsole)
        os.chdir(application_path)

# Loops through all songs selected and places them into the enabled songs directory, whether those songs are .pak/.sig files or archives (.zip, .rar, or .7z)
def add_song(treeview, prog_properties):
    if DEBUG:
        print("BEGIN add_song")
    # Preemptive check to see if game is running before allowing songs to be selected
    if (process_exists_2(fuser_process_name, fuser_alt_process_name)):
        messagebox.showerror("Fuser currently running", "Fuser is currently running. Please quit the game to add new songs.")
        return

    filetypes = (
        ('Archive files', '.zip'),
        ('Archive files', '.rar'),
        ('Archive files', '.7z'),
        ('.pak files', '.pak')
    )
    filenames = list(fd.askopenfilenames(filetypes=filetypes))
    #print(filenames)
    # quit early if no songs were selected
    if (len(filenames) == 0):
        return
    
    # check again in case game was launched after selecting files
    if (process_exists_2(fuser_process_name, fuser_alt_process_name)):
        messagebox.showerror("Fuser currently running", "Fuser is currently running. Please quit the game to add new songs.")
        return

    if (len(filenames) > 1 or is_archive(filenames[0])):
        messagebox.showinfo("Multiple songs or archive(s) selected", "You have chosen multiple songs (or an archive/multiple archives) to be added.\nThis may take a moment to complete.")
    #result = list(fd.askopenfilenames())

    for i in range(len(filenames)):
        if filenames[i].endswith(".pak"):
            # TODO: check if file exists in enabled or disabled directories. if so, do NOT try to add it
            # immediately copy into enabled_directory and quit
            # assume .sig file exists next to .pak file
            #print(filenames[i])
            pak_file_path = filenames[i]
            sig_file_path = pak_file_path[:-3] + "sig"
            possible_pak_enabled_path = get_folder_path_to_file(os.path.basename(pak_file_path), prog_properties.enabled_directory)
            possible_sig_enabled_path = get_folder_path_to_file(os.path.basename(sig_file_path), prog_properties.enabled_directory)
            possible_pak_disabled_path = get_folder_path_to_file(os.path.basename(pak_file_path), prog_properties.disabled_directory)
            possible_sig_disabled_path = get_folder_path_to_file(os.path.basename(sig_file_path), prog_properties.disabled_directory)
            dest_pak = ""
            dest_sig = ""

            # check if sig file exists. if not, raise error and skip this file
            if not os.path.exists(sig_file_path):
                messagebox.showwarning(".sig file missing", f"The .sig file that corresponds with the .pak file\n{pak_file_path}\ndoes not exist. Skipping this .pak file.")
                continue
            if (possible_pak_enabled_path != None and possible_sig_enabled_path != None and possible_pak_disabled_path != None and possible_sig_disabled_path != None):
                # if song somehow exists in both enabled path and disabled path, show an error and skip this song
                messagebox.showwarning("Duplicate files exist", f"The .pak and .sig files that corresponds with the .pak file\n{pak_file_path}\nexist in both the enabled and disabled song folders.\nPlease resolve this manually by deleting one or the other.\nSkipping this .pak file for now.")
                continue
            elif (possible_pak_enabled_path == None and possible_sig_enabled_path == None and possible_pak_disabled_path == None and possible_sig_disabled_path == None):
                # If the files don't already exist, set destination to base folder enabled directory
                dest_pak = prog_properties.enabled_directory + "\\" + os.path.basename(pak_file_path)
                dest_sig = prog_properties.enabled_directory + "\\" + os.path.basename(sig_file_path)
            elif (possible_pak_enabled_path != None and possible_sig_enabled_path != None):
                # if the song exists in the enabled path, copy over it
                dest_pak = possible_pak_enabled_path + "\\" + os.path.basename(pak_file_path)
                dest_sig = possible_sig_enabled_path + "\\" + os.path.basename(sig_file_path)
            elif (possible_pak_disabled_path != None and possible_sig_disabled_path != None):
                # if the song exists in the disabled path, copy over it
                dest_pak = possible_pak_disabled_path + "\\" + os.path.basename(pak_file_path)
                dest_sig = possible_sig_disabled_path + "\\" + os.path.basename(sig_file_path)

            try:
                shutil.copyfile(pak_file_path, dest_pak)
                shutil.copyfile(sig_file_path, dest_sig)
            except shutil.SameFileError:
                messagebox.showwarning("Error", f"The .pak file\n{pak_file_path}\nalready exists in the enabled/disabled song folder.\nSkipping this .pak file for now.")
                continue
        else:
            # call song extract, pointing towards file and enabled_directory
            extract_song(filenames[i], prog_properties.enabled_directory, prog_properties.enabled_directory, prog_properties.disabled_directory, prog_properties.pak_directory)
            #pass
    # now the files should exist in the enabled directory
    # add it to the visual tree and the actual database
    # call init on db to add new songs automatically
    # small delay to ensure all files are fully copied
    time.sleep(0.1)
    connection = init_database(prog_properties.database_location, prog_properties.enabled_directory, prog_properties.disabled_directory, True)
    time.sleep(0.1)
    print("finished init database")

    for item in treeview.get_children():
        treeview.delete(item)

    db_songs_raw = execute_db_read_query(connection, "SELECT * from songs ORDER BY filename")
    for i, original_db_tuple in enumerate(db_songs_raw): # Added enumerate
        star_string = rating_to_star_text(original_db_tuple[9])
        enabled_string = "☑" if (original_db_tuple[8] == 1) else "☐"
        key_name_str = SongKey(original_db_tuple[5]).name
        mode_name_str = SongMode(original_db_tuple[6]).name # <<<< We need this
        camelot_input_str = f"{key_name_str} {mode_name_str}"
        sortable_camelot_value = get_camelot_key(camelot_input_str)
        display_camelot_value = format_camelot_for_display(sortable_camelot_value)
        
        song_display_tuple = (
            original_db_tuple[0], original_db_tuple[1], original_db_tuple[2], original_db_tuple[3],
            Genres(original_db_tuple[4]).name, key_name_str, mode_name_str, original_db_tuple[7],
            enabled_string, star_string, original_db_tuple[10], original_db_tuple[11],
            display_camelot_value
        )
        current_tags = ()
        if mode_name_str == "Minor":
            current_tags = ('minor_song',)
        treeview.insert(parent="", index='end', iid=i, text="", values=song_display_tuple, tags=current_tags)
        
    connection.close()
    if DEBUG:
        print("END add_song")

def edit_songs_button_handler():
    selected_items = songs_table_tree.selection()
    if (len(selected_items) == 0):
        return
    if (len(selected_items) == 1):
        edit_song()
    else:
        # special multi-select window
        edit_multiple_songs()
        pass
    # if no songs are selected, do nothing
    # if only one song is selected, show regular popup
    # if multiple songs are selected, show a special popup that just says "multiple songs selected" and have textboxes for author, notes, and a ratings dropdown
    # overwrite contents in database when updating all songs

def delete_songs_button_handler():
    # if no songs are selected, do nothing
    selected_items = songs_table_tree.selection()
    # else (if one or multiple are selected), call the regular delete function for each file that's selected. not sure if this will work
    pass
        
def write_config():
    config.set('main', 'fuser_path', prog_properties.fuser_directory)
    config.set('main', 'database_path', prog_properties.database_location)
    config.set('main', 'install_type', prog_properties.launcher_type.name)
    config.set('main', 'executable_path', prog_properties.executable_path)
    config.write(open(str(config_file_path), 'w'))

# Config window handler function for config button
def config_window():
    # show new popup window
    # load existing values from prog_properties into window
    # on "save" button, close window and write properties to config file
    # also make note in window that mentions program restart being required to apply changes?
    d = ConfigDialog(window)
    if (d.result):
        write_config()
        messagebox.showinfo("Settings saved", "Configuration saved.\nPlease restart the program to use new settings.\nThe program will now quit.")
        sys.exit()
        #quit()

# Search handler function, calls the SearchDialog window and gets appropriate results, filling out visual table with results        
def start_search(clear_button):
    # show search dialog window
    # get query result from dialog window
    
    d = SearchDialog(window)
    if (d.result):
        print(d.result)
        for item in songs_table_tree.get_children():
            songs_table_tree.delete(item)
        
        db_songs_raw = execute_db_read_query(db_connection, d.result) # Assuming db_connection is global and valid
        for i, original_db_tuple in enumerate(db_songs_raw): # Added enumerate
            star_string = rating_to_star_text(original_db_tuple[9])
            enabled_string = "☑" if (original_db_tuple[8] == 1) else "☐"
            key_name_str = SongKey(original_db_tuple[5]).name
            mode_name_str = SongMode(original_db_tuple[6]).name # <<<< We need this
            camelot_input_str = f"{key_name_str} {mode_name_str}"
            sortable_camelot_value = get_camelot_key(camelot_input_str)
            display_camelot_value = format_camelot_for_display(sortable_camelot_value)

            song_display_tuple = (
                original_db_tuple[0], original_db_tuple[1], original_db_tuple[2], original_db_tuple[3],
                Genres(original_db_tuple[4]).name, key_name_str, mode_name_str, original_db_tuple[7],
                enabled_string, star_string, original_db_tuple[10], original_db_tuple[11],
                display_camelot_value
            )
            current_tags = ()
            if mode_name_str == "Minor":
                current_tags = ('minor_song',)
            songs_table_tree.insert(parent="", index='end', iid=i, text="", values=song_display_tuple, tags=current_tags)
        clear_button.configure(state='enabled')
    
# Resets visual table to show all items from database
def clear_search(clear_button):
    for item in songs_table_tree.get_children():
        songs_table_tree.delete(item)
    
    db_songs_raw = execute_db_read_query(db_connection, "SELECT * from songs ORDER BY filename") # Assuming db_connection is global
    for i, original_db_tuple in enumerate(db_songs_raw): # Added enumerate
        star_string = rating_to_star_text(original_db_tuple[9])
        enabled_string = "☑" if (original_db_tuple[8] == 1) else "☐"
        key_name_str = SongKey(original_db_tuple[5]).name
        mode_name_str = SongMode(original_db_tuple[6]).name # <<<< We need this
        camelot_input_str = f"{key_name_str} {mode_name_str}"
        sortable_camelot_value = get_camelot_key(camelot_input_str)
        display_camelot_value = format_camelot_for_display(sortable_camelot_value)

        song_display_tuple = (
            original_db_tuple[0], original_db_tuple[1], original_db_tuple[2], original_db_tuple[3],
            Genres(original_db_tuple[4]).name, key_name_str, mode_name_str, original_db_tuple[7],
            enabled_string, star_string, original_db_tuple[10], original_db_tuple[11],
            display_camelot_value
        )
        current_tags = ()
        if mode_name_str == "Minor":
            current_tags = ('minor_song',)
        songs_table_tree.insert(parent="", index='end', iid=i, text="", values=song_display_tuple, tags=current_tags)
    clear_button.configure(state='disabled')

def manager_update_check(notify_no_update_available = False):
    if DEBUG:
        print("BEGIN manager_update_check")
    new_version_string = check_for_update(version_number)
    if DEBUG:
        print("NEW VERSION:")
        print(new_version_string)
    if new_version_string != None:
        update_text = f"A new version of the Fuser Custom Song Manager, v{new_version_string}, is available! Would you like to view the latest release?"
        result = messagebox.askquestion("Update available!", update_text)
        if (result == 'yes'):
            webbrowser.open_new_tab("https://github.com/N1nDr0id/FuserCustomSongManager/releases/latest")
    elif new_version_string == None and notify_no_update_available:
        messagebox.showinfo("No new updates available", f"You are currently on the latest version of the program, v{version_number}.")
    if DEBUG:
        print("END manager_update_check")

def show_about():
    popup = tk.Toplevel()
    popup.focus_force()
    popup.grab_set()
    popup.title("About")
    popup.iconbitmap("gui_icons/program_icon.ico")

    about_text = f"""Fuser Custom Song Manager, v{version_number}
by N1nDr0id/Lilly.

Made with love for the Fuser community. <3

Built using Python, Tkinter, PyPAKParser, and more.

Special thanks to Narrik Synthfox and riyvk for contributing to this program, 
as well as thanks to those who tested the program."""
    canvas = tk.Canvas(popup, width=64, height=64)
    canvas.pack(padx=20, pady=10)
    popup.logo = tk.PhotoImage(file="gui_icons/program_icon.png").subsample(2, 2)
    canvas.create_image(0, 0, anchor=tk.NW, image=popup.logo)
    ttk.Label(popup, text=about_text, justify=tk.CENTER).pack(padx=20, pady=10)
    buttons_frame = tk.Frame(popup)
    button1 = ttk.Button(buttons_frame, text="Check for updates", command=lambda: manager_update_check(True))
    button2 = ttk.Button(buttons_frame, text="View on GitHub", command=lambda: webbrowser.open_new_tab("https://github.com/N1nDr0id/FuserCustomSongManager"))
    button3 = ttk.Button(buttons_frame, text="Latest release", command=lambda: webbrowser.open_new_tab("https://github.com/N1nDr0id/FuserCustomSongManager/releases/latest"))
    button1.grid(row=0, column=0)
    button2.grid(row=0, column=1)
    button3.grid(row=0, column=2)
    buttons_frame.pack(padx=20, pady=10)

s = ttk.Style()
s.configure('TButton', anchor=tk.W)
s.configure('Centered.TButton', anchor=tk.CENTER)

# Set up top bar
top_bar = ttk.Frame()
add_song_icon = tk.PhotoImage(file="gui_icons/folder.png").subsample(8, 8)
edit_song_icon = tk.PhotoImage(file="gui_icons/edit.png").subsample(8, 8)
delete_song_icon = tk.PhotoImage(file="gui_icons/delete.png").subsample(8, 8)
search_icon = tk.PhotoImage(file="gui_icons/search.png").subsample(8, 8)
clear_icon = tk.PhotoImage(file="gui_icons/close.png").subsample(8, 8)
refresh_icon = tk.PhotoImage(file="gui_icons/arrow-repeat.png").subsample(8, 8)
config_icon = tk.PhotoImage(file="gui_icons/settings.png").subsample(8, 8)
fuser_icon = tk.PhotoImage(file="gui_icons/fuser black.png").subsample(4, 4)
about_icon = tk.PhotoImage(file="gui_icons/information.png").subsample(8, 8)

add_song_button = ttk.Button(text="Add Song(s)", master=top_bar, image=add_song_icon, compound='left')
add_song_button.image = add_song_icon

edit_song_button = ttk.Button(text="Edit Song(s)", master=top_bar, image=edit_song_icon, compound='left', command=edit_songs_button_handler)
edit_song_button.image = edit_song_icon

delete_song_button = ttk.Button(text="Delete Song(s)", master=top_bar, image=delete_song_icon, compound='left')
delete_song_button.image = delete_song_icon

clear_button = ttk.Button(text="Clear Search", master=top_bar, image=clear_icon, compound='left', state='disabled')
clear_button.configure(command=lambda: clear_search(clear_button))
clear_button.image = clear_icon

search_button = ttk.Button(text="Search", master=top_bar, image=search_icon, compound='left', command=lambda: start_search(clear_button))
search_button.image = search_icon

refresh_button = ttk.Button(text="Refresh Song List", master=top_bar, image=refresh_icon, compound='left', command=lambda: refresh_list(clear_button))
refresh_button.image = refresh_icon

launch_button = ttk.Button(text="Launch Fuser", master=top_bar, image=fuser_icon, compound='left', command=launch_fuser)
launch_button.image = fuser_icon

config_button = ttk.Button(text="Configuration", master=top_bar, image=config_icon, compound='left', command=config_window)
config_button.image = config_icon

about_button = ttk.Button(text="About", master=top_bar, image=about_icon, compound='left', command=show_about)
about_button.image = about_icon

add_song_button.grid(row=0, column=0)
edit_song_button.grid(row=0, column=1)
delete_song_button.grid(row=0, column=2)
search_button.grid(row=0, column=3)
clear_button.grid(row=0, column=4)
refresh_button.grid(row=0, column=5)
launch_button.grid(row=0, column=6)
config_button.grid(row=0, column=7)
about_button.grid(row=0, column=8)
top_bar.grid(row=0, column=0, sticky=tk.W)

main_frame = ttk.Frame()
# Set up main window
songs_table_tree = MyTreeview(master=main_frame)
songs_vert_scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=songs_table_tree.yview)
songs_vert_scrollbar.pack(side='right', fill='y')
songs_table_tree.configure(yscrollcommand=songs_vert_scrollbar.set)
songs_hori_scrollbar = ttk.Scrollbar(main_frame, orient='horizontal', command=songs_table_tree.xview)
songs_hori_scrollbar.pack(side='bottom', fill='x')
songs_table_tree.configure(xscrollcommand=songs_hori_scrollbar.set)

songs_table_tree.tag_configure('minor_song', background='#E8E8E8') # A light gray, adjust as preferred


# Defining table columns
songs_table_tree['columns'] = ("Filename", "Song Name", "Artist", "Year", "Genre", "Key", "Mode", "BPM", "Enabled?", "Rating", "Notes", "Author", "Camelot Key") # Added "Camelot Key"
# Column formatting
songs_table_tree.column("#0", width=0, stretch=tk.NO)
songs_table_tree.column("Filename", anchor=tk.W, width=120)
songs_table_tree.column("Song Name", anchor=tk.W, width=240)
songs_table_tree.column("Artist", anchor=tk.W, width=200)
songs_table_tree.column("Year", anchor=tk.CENTER, width=40)
songs_table_tree.column("Genre", anchor=tk.W, width=60)
songs_table_tree.column("Key", anchor=tk.W, width=40)
songs_table_tree.column("Mode", anchor=tk.W, width=40)
songs_table_tree.column("BPM", anchor=tk.E, width=40)
songs_table_tree.column("Enabled?", anchor=tk.CENTER, width=60)
songs_table_tree.column("Rating", anchor=tk.CENTER, width=80)
songs_table_tree.column("Notes", anchor=tk.W, width=200)
songs_table_tree.column("Author", anchor=tk.W, width=120)
songs_table_tree.column("Camelot Key", anchor=tk.W, width=80) # Added definition for Camelot Key column

# Headings for song table
songs_table_tree.heading("#0", text="", anchor=tk.W)
songs_table_tree.heading("Filename", text="Filename", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Song Name", text="Song Name", sort_by='name_ignore_words', anchor=tk.W)
songs_table_tree.heading("Artist", text="Artist", sort_by='name_ignore_words', anchor=tk.W)
songs_table_tree.heading("Year", text="Year", sort_by='num', anchor=tk.W)
songs_table_tree.heading("Genre", text="Genre", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Key", text="Key", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Mode", text="Mode", sort_by='name', anchor=tk.W)
songs_table_tree.heading("BPM", text="BPM", sort_by='num', anchor=tk.W)
songs_table_tree.heading("Enabled?", text="Enabled?", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Rating", text="Rating", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Notes", text="Notes", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Author", text="Author", sort_by='name', anchor=tk.W)
songs_table_tree.heading("Camelot Key", text="Camelot Key", sort_by='camelot', anchor=tk.W) # MODIFIED sort_by

for item in songs_table_tree['columns']: # This loop will now include "Camelot Key"
    songs_table_tree.heading(item, text=item, anchor=tk.W)

#songs_table_tree.insert(parent="", index='end', iid=0, text="", values=("File_name_P", "The Song", "The Artist", 2023, "Dance", "Db", "Major", 120, "☐", "★★★★", "blah blah", "Me :)", "3B")) # Example if needed

# extra window setup for handling inputs
def do_treeview_rmb_popup(e):
    # e is the event that contains info such as which item has been right clicked
    item = songs_table_tree.identify_row(e.y)
    # select item when right clicking
    #print("right clicked item: ", item)
    if item:
        songs_table_tree.selection_set(item)
        songs_table_tree.focus_set()
        songs_table_tree.focus(item)
        if (process_exists_2(fuser_process_name, fuser_alt_process_name)):
            table_rmb_menu.entryconfig(1, state=tk.DISABLED)
            table_rmb_menu.entryconfig(2, state=tk.DISABLED)
        else:
            table_rmb_menu.entryconfig(1, state=tk.NORMAL)
            table_rmb_menu.entryconfig(2, state=tk.NORMAL)
        table_rmb_menu.tk_popup(x=e.x_root, y=e.y_root)
    else:
        pass

# Responsible for updating row visually and moving files as needed
def update_row(iid, song_info, updated_info, check_if_fuser_running):
    new_song_info = list(song_info) # song_info is now the 13-element tuple
    new_song_info[8] = bool_to_checkbox_text(updated_info[0]) # Index 8 is "Enabled?"
    new_song_info[9] = updated_info[1] # Index 9 is "Rating"
    new_song_info[10] = updated_info[2] # Index 10 is "Notes"
    new_song_info[11] = updated_info[3] # Index 11 is "Author"
    # Camelot Key at index 12 is not editable here, so it remains from original song_info

    if (check_if_fuser_running):
        if (process_exists_2(fuser_process_name, fuser_alt_process_name) and checkbox_to_bool(song_info[8]) != checkbox_to_bool(new_song_info[8])):
            # if the user wants to enable the song
            if (checkbox_to_bool(new_song_info[8])):
                messagebox.showerror("Fuser currently running", "Fuser is currently running. This song will not be enabled at this time.\nPlease quit the game to enable this song.")
            else: # If the user wants to disable the song
                messagebox.showerror("Fuser currently running", "Fuser is currently running. This song will not be disabled at this time.\nPlease quit the game to disable this song.")
            new_song_info[8] = song_info[8]

    # function to find song in file path given start folder and filename here
    actual_file_folder_path = None
    song_subfolders = None
    # if file is in enabled directory, find full path to file here
    if (checkbox_to_bool(song_info[8])): # song_info[8] is "Enabled?"
        actual_file_folder_path = get_folder_path_to_file(song_info[0] + ".pak", prog_properties.enabled_directory)
    else:
        actual_file_folder_path = get_folder_path_to_file(song_info[0] + ".pak", prog_properties.disabled_directory)
    
    if (actual_file_folder_path == None):
        messagebox.showwarning("File not found!", "The .pak file for this custom could not be found.")
        # delete song row?
        return
    
    dest_dir = actual_file_folder_path
    if (checkbox_to_bool(song_info[8])):
        song_subfolders = actual_file_folder_path[len(prog_properties.enabled_directory) + 1:]
        # create subfolders in disabled directory for future use
        if (len(song_subfolders) > 0):
            dest_dir = prog_properties.disabled_directory + "\\" + song_subfolders
            pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)
    else:
        song_subfolders = actual_file_folder_path[len(prog_properties.disabled_directory) + 1:]
        # create subfolders in enabled directory for future use
        if (len(song_subfolders) > 0):
            dest_dir = prog_properties.enabled_directory + "\\" + song_subfolders
            pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)

    #print(song_subfolders)
    #print(len(song_subfolders))
    
    #return
    # Early exit in case of sig file missing
    if (not os.path.exists(actual_file_folder_path + "\\" + song_info[0] + ".sig")):
        messagebox.showwarning(".sig file missing", "The .sig file that corresponds with " + song_info[0] + ".pak does not exist alongside the .pak file.\nThis song is now disabled.")
        if (checkbox_to_bool(song_info[8])):
            print("MOVING FILE NOW")
            old_pak_file = actual_file_folder_path + "\\" + song_info[0] + ".pak"
            new_pak_file = prog_properties.disabled_directory + "\\" + song_info[0] + ".pak"
            if (len(song_subfolders) > 0):
                new_pak_file = prog_properties.disabled_directory + "\\" + song_subfolders + "\\" + song_info[0] + ".pak"
            shutil.move(old_pak_file, new_pak_file)
            new_song_info[8] = bool_to_checkbox_text(False)
            new_song_info = tuple(new_song_info)
            songs_table_tree.item(iid, text="", values=new_song_info)
            update_row_in_db(new_song_info) # new_song_info still has 13 elements
        return

    new_song_info = tuple(new_song_info)

    # if song needs to be moved, try moving it before updating table and database
    if (checkbox_to_bool(song_info[8]) != checkbox_to_bool(new_song_info[8])):
        # now we know we need to move, but what should we move?
        # if the song is enabled, move it from disabled to enabled path
        old_pak_file = new_pak_file = old_sig_file = new_sig_file = ""
        old_pak_file = actual_file_folder_path + "\\" + song_info[0] + ".pak"
        old_sig_file = actual_file_folder_path + "\\" + song_info[0] + ".sig"
        if updated_info[0]: # updated_info[0] is the new_enabled_state (boolean)
            # move to enabled folder if it's not already there
            if (len(song_subfolders) > 0):
                new_pak_file = prog_properties.enabled_directory + "\\" + song_subfolders + "\\" + song_info[0] + ".pak"
                new_sig_file = prog_properties.enabled_directory + "\\" + song_subfolders + "\\" + song_info[0] + ".sig"
            else:
                new_pak_file = prog_properties.enabled_directory + "\\" + song_info[0] + ".pak"
                new_sig_file = prog_properties.enabled_directory + "\\" + song_info[0] + ".sig"
        else:
            # move to disabled folder if it's not already there
            if (len(song_subfolders) > 0):
                new_pak_file = prog_properties.disabled_directory + "\\" + song_subfolders + "\\" + song_info[0] + ".pak"
                new_sig_file = prog_properties.disabled_directory + "\\" + song_subfolders + "\\" + song_info[0] + ".sig"
            else:
                new_pak_file = prog_properties.disabled_directory + "\\" + song_info[0] + ".pak"
                new_sig_file = prog_properties.disabled_directory + "\\" + song_info[0] + ".sig"
            pass
        shutil.move(old_pak_file, new_pak_file)
        shutil.move(old_sig_file, new_sig_file)
        # in both cases, delete customSongsUnlocked.pak and .sig if they exist
        if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak"):
            os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak")
        if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig"):
            os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig")

    songs_table_tree.item(iid, text="", values=new_song_info)
    
    # only updates once an item in new_song_info doesn't match with song_info (the old song info)
    # Compare only the editable fields (indices 8, 9, 10, 11 of the 13-element tuple)
    if (song_info[8] != new_song_info[8] or \
        song_info[9] != new_song_info[9] or \
        song_info[10] != new_song_info[10] or \
        song_info[11] != new_song_info[11]):
        update_row_in_db(new_song_info) # new_song_info is the 13-element tuple

# Responsible for updating the row in the database
def update_row_in_db(song_info): # song_info is the 13-element tuple from display
    #rather than updating row by row, we should update all of the new columns respectively
    song_shortname = song_info[0]
    enabled_state = 1 if song_info[8] == "☑" else 0 # Index 8 is "Enabled?"
    rating = text_to_rating_int(song_info[9]) # Index 9 is "Rating"
    new_notes = song_info[10].replace("'", "''") # Index 10 is "Notes"
    new_author = song_info[11].replace("'", "''") # Index 11 is "Author"
    # Camelot key (song_info[12]) is not stored in the DB by this function
    execute_db_query(db_connection, f"UPDATE songs SET enabled = {enabled_state}, rating = {rating}, notes = '{new_notes}', author = '{new_author}' WHERE filename = '{song_shortname}'")
    read = execute_db_read_query(db_connection, f"SELECT * from songs WHERE filename = '{song_shortname}'")
    #print(read)

# Called when editing a song from right click menu
def edit_song():
    # get iid
    selected_song_iid = songs_table_tree.focus()
    # get info for currently selected row
    song_info = songs_table_tree.item(selected_song_iid, 'values') # This will be the 13-element tuple
    # call songeditdialog
    d = SongEditDialog(window, song_info) # Dialog expects indices 0-11 to match old format
    if d.result == None:
        return
    updated_info = d.result # (new_enabled_state, new_rating, new_notes, new_author)
    # update row info
    update_row(selected_song_iid, song_info, updated_info, check_if_fuser_running=True)

def edit_multiple_songs():
    selected_song_iids = songs_table_tree.selection()
    # For the placeholder song_info for the dialog, we only need the first 12 elements
    # as the dialog doesn't use the 13th (Camelot key).
    # However, the number of fields (columns) in the dialog is fixed.
    # The important part is that indices for Enabled, Rating, Notes, Author are consistent.
    placeholder_song_info = ('Multiple Files', 'Multiple Songs', 'Multiple Artists', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', '☑', '☆☆☆☆☆', '', '') 
    # If song_info passed to SongEditDialog had 13 items, it would still work as it only accesses up to index 11.
    d = SongEditDialog(window, placeholder_song_info) # Pass a representative tuple
    if d.result == None:
        return
    updated_info = d.result # (new_enabled_state, new_rating, new_notes, new_author)
    messagebox.showinfo("Edit multiple songs", "The program may appear frozen while the data for each song is being saved. Please wait a moment.")

    for selected_song_iid in selected_song_iids:
        song_info = songs_table_tree.item(selected_song_iid, 'values') # This is the 13-element tuple
        update_row(selected_song_iid, song_info, updated_info, check_if_fuser_running=False) # No individual Fuser check per song in batch

# Deletes a song from the database, the visual database, and from the filesystem
def delete_song():
    selected_song_iids = songs_table_tree.selection()
    if (len(selected_song_iids) == 0):
        return
    
    if (process_exists_2(fuser_process_name, fuser_alt_process_name)):
        messagebox.showerror("Fuser currently running", "Fuser is currently running. This song will not be deleted at this time.\nPlease quit the game to delete this song.")
        return
    
    warning_message_shown = False
    warn_result = 'no'

    for selected_song_iid in selected_song_iids:
        song_info = songs_table_tree.item(selected_song_iid, 'values') # 13-element tuple
        # is_enabled = checkbox_to_bool(song_info[8]) # song_info[8] is "Enabled?"
        if (len(selected_song_iids) == 1):
            warning_msg = f"""WARNING: You are about to delete this song:

Filename: {song_info[0]}
{song_info[1]}
by {song_info[2]}

Are you SURE you want to delete this song? 
Doing so will remove ALL data for this song from your current game installation.
This includes both your custom_songs folder and the local database.

Press YES to delete this song, or NO to cancel this action.
"""
        else:
            warning_msg = f"""WARNING: You are about to delete multiple songs.

Are you SURE you want to delete these songs? 
Doing so will remove ALL data for these songs from your current game installation.
This includes both your custom_songs folder and the local database.

Press YES to delete these songs, or NO to cancel this action.
"""
        if warning_message_shown == False:
            warn_result = messagebox.askquestion("Delete Song", warning_msg, icon='warning')
            print(warn_result)
            warning_message_shown = True
        if (warn_result == 'yes'):
            file_folder_path = None
            if checkbox_to_bool(song_info[8]): # song_info[8] is "Enabled?"
                file_folder_path = get_folder_path_to_file(song_info[0] + ".pak", prog_properties.enabled_directory)
            else:
                file_folder_path = get_folder_path_to_file(song_info[0] + ".pak", prog_properties.disabled_directory)

            # This part of file deletion logic should be okay as it uses song_info[0] for filename
            # and song_info[8] for enabled status, which are consistent.
            if file_folder_path: # Ensure path was found
                pak_file = os.path.join(file_folder_path, f"{song_info[0]}.pak")
                sig_file = os.path.join(file_folder_path, f"{song_info[0]}.sig")
                if os.path.exists(pak_file):
                    os.remove(pak_file)
                if os.path.exists(sig_file):
                    os.remove(sig_file)
            else:
                print(f"Warning: Could not find path for {song_info[0]}.pak to delete.")


            # after ensuring the .pak and .sig files are deleted, also ensure to delete the customSongsUnlocked_P.pak and .sig files
            if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak"):
                os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.pak")
            if os.path.exists(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig"):
                os.remove(prog_properties.pak_directory + "\\customSongsUnlocked_P.sig")
            
            execute_db_query(db_connection, f"DELETE FROM songs WHERE filename = '{song_info[0]}'")
            songs_table_tree.delete(selected_song_iid)

# Input handler for doubleclicking a song row in the table, edits said song
def do_treeview_doubleclick(e):
    item_iid = songs_table_tree.identify_row(e.y)
    if item_iid:
        song_info = songs_table_tree.item(item_iid, 'values') # 13-element tuple
        d = SongEditDialog(window, song_info)
        if d.result == None:
            return
        updated_info = d.result # (new_enabled_state, new_rating, new_notes, new_author)
        update_row(item_iid, song_info, updated_info, check_if_fuser_running=True)
    else:
        pass

# Moves a song to the enabled/disabled path and updates the visual and internal databases
def toggle_song():
    selected_song_iid = songs_table_tree.focus()
    selected_song_values = songs_table_tree.item(selected_song_iid, 'values') # 13-element tuple
    
    song_is_enabled = checkbox_to_bool(selected_song_values[8]) # Index 8 is "Enabled?"
    new_song_state_bool = not song_is_enabled
    
    # Create the 4-tuple that update_row expects for changed info
    # (new_enabled_state_bool, current_rating_str, current_notes_str, current_author_str)
    updated_info_for_toggle = (
        new_song_state_bool, 
        selected_song_values[9], # Rating string
        selected_song_values[10],# Notes string
        selected_song_values[11] # Author string
    )
    update_row(selected_song_iid, selected_song_values, updated_info_for_toggle, check_if_fuser_running=True)
    
# adding right click menu
table_rmb_menu = tk.Menu(tearoff=False)
table_rmb_menu.add_command(label="Edit Song Info", command=edit_song)
table_rmb_menu.add_command(label="Toggle Song", command=toggle_song)
table_rmb_menu.add_command(label="Delete Song", command=delete_song)

# binding mouse clicks
songs_table_tree.bind("<Button-3>", do_treeview_rmb_popup)
songs_table_tree.bind("<Double-1>", do_treeview_doubleclick)

# final UI pack
songs_table_tree.pack(side='left', fill='both')
main_frame.grid(row=1, column=0, sticky="news")

prog_properties = None

config = ConfigParser()
# Attempt to load program properties from config file. If config file doesn't exist, go through first-time setup.
if (not os.path.exists(str(config_file_path))):
    # show first time setup window
    window.withdraw()
    popup = FirstTimePopup(window)
    window.wait_window(popup)
    print(popup.result)

    if (popup.result == "uninitialized!"):
        #quit()
        sys.exit()
    # set up prog_properties with results from popup
    new_prog_properties = ProgramProperties(popup.result[0], str(db_file_path), LauncherType[popup.result[3]], popup.result[2])
    if (popup.result[1] is not None):
        new_prog_properties.disabled_directory = popup.result[1]
    prog_properties = new_prog_properties
    config.add_section('main')
    write_config()
    window.deiconify()
else:
    # read info from config file and use it to load program
    config.read(str(config_file_path))
    #print('"' + config.get('main', 'fuser_path') + '"')
    tmp_fuser_path = config.get('main', 'fuser_path')
    tmp_db_path = config.get('main', 'database_path')
    tmp_install_type = LauncherType[config.get('main', 'install_type')]
    tmp_exe_path = config.get('main', 'executable_path')
    prog_properties = ProgramProperties(tmp_fuser_path, tmp_db_path, tmp_install_type, tmp_exe_path)

# last bit of setup for top row buttons
add_song_button.configure(command=lambda: add_song(songs_table_tree, prog_properties))
delete_song_button.configure(command=delete_song)

# init song tree contents
# init song tree contents
db_connection = init_database(prog_properties.database_location, prog_properties.enabled_directory, prog_properties.disabled_directory, False)
# The global db_connection is initialized here. Other functions use it.
db_songs_raw = execute_db_read_query(db_connection, "SELECT * from songs ORDER BY filename")

for i, original_db_tuple in enumerate(db_songs_raw): # Added enumerate
    star_string = rating_to_star_text(original_db_tuple[9])
    enabled_string = "☑" if (original_db_tuple[8] == 1) else "☐"
    key_name_str = SongKey(original_db_tuple[5]).name
    mode_name_str = SongMode(original_db_tuple[6]).name # <<<< We need this
    camelot_input_str = f"{key_name_str} {mode_name_str}"
    
    sortable_camelot_value = get_camelot_key(camelot_input_str)
    display_camelot_value = format_camelot_for_display(sortable_camelot_value)

    song_display_tuple = (
        original_db_tuple[0], original_db_tuple[1], original_db_tuple[2], original_db_tuple[3],
        Genres(original_db_tuple[4]).name, key_name_str, mode_name_str, original_db_tuple[7],
        enabled_string, star_string, original_db_tuple[10], original_db_tuple[11], 
        display_camelot_value 
    )
    
    current_tags = ()
    if mode_name_str == "Minor":
        current_tags = ('minor_song',)
        
    songs_table_tree.insert(parent="", index='end', iid=i, text="", values=song_display_tuple, tags=current_tags)


manager_update_check()

# Run main loop of program!
window.mainloop()