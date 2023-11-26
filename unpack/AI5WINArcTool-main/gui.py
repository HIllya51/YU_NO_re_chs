# GUI for this tool. Nothing more, nothing less.

import os
import ctypes
import locale
import threading
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showinfo, showwarning, showerror
from silky_arc import SilkyArc


class SilkyArcToolGUI:
    default_width = 300
    default_height = 300

    possible_languages = ("eng", "rus")

    _strings_lib = {
        'eng': (
            "SilkyArcTool by Tester",
            "English",
            "Русский",
            "...",
            "Silky archive file (.arc):",
            "Resources directory:",  # 5
            "Filename choice",
            "Directory choice",
            "*.arc",
            "Silky Archives",
            "*",  # 10
            "All files",
            "Unpack archive",
            "Pack archive",
            "Warning",
            "Archive name not stated.",  # 15
            "Directory name not stated.",
            "Error",
            "Help",
        ),
        'rus': (
            "SilkyArcTool от Tester-а",
            "English",
            "Русский",
            "...",
            "Архивный файл Silky (.arc):",
            "Директория с ресурсами:",  # 5
            "Выбор имени файла",
            "Выбор директории",
            "*.arc",
            "Архивы Silky",
            "*",  # 10
            "Все файлы",
            "Распаковать архив",
            "Запаковать архив",
            "Предупреждение",
            "Имя архива не указано.",  # 15
            "Имя директории не указано.",
            "Ошибка",
            "Справка",
        )
    }

    programm_help = {
        'eng': """
Dual languaged (rus+eng) GUI tool for packing and unpacking archives of Silky Engine.
This type of .arc archive also used in Ai6WIN engine (and possibly in Ai5WIN) by Silky.
If you want to work with Silky Engine's .mes scripts, use mesScriptAsseAndDisassembler instead.

Why this tool was created, if there are other tools that can work with this type of archive?
The answer is simple: because there was no actually good enough tools. One tool can only extract the data, other -- only
pack, but without using original compression, that resulting in outrageous big output archives. My tool solves all the
issues -- not only it can extract archives, but also pack them from files, compressing it by algorithm (variation of
LZSS), extraction of which was implemented by Silky Engine. Through the tool has one problem -- it works quite slow,
especially for packing, so you may need to wait for some minutes (due to implementation compression algorithm on
Python).

>>> Usage.

1. Run the tool (main.py or .exe).
2. Print filename (with extension!!!) or choose it by clicking on button "...".
3. Print directory or choose it by clicking on button "...".
4. Print "0", if thou want to unpack, or "1", if thou want to pack.
5. Just wait until it done.
""",
        'rus': """
Двуязычное средство (рус+англ) для распаковки и запаковки архивов Silky Engine. Сей вид архива также используется в
движке Ai6WIN (и, возможно, в Ai5WIN) от Silky. Ежели вам нужно работать со скриптами .mes Silky Engine, используйте
mesScriptAsseAndDisassembler.

Почему же это средство было создано, ежель и так есть средства, что могут работать с сим типом архива? Ответ прост: ни
одно из тех существующих средств не является достаточно хорошим. Одно может только извлекать, другое -- только
запаковывать, однако ж без использования оригинального алгоритма сжатия, из-за чего архивы получаются большими сверх
всякой меры. Но моё средство исправляет эти проблемы: оно может как распаковывать данные, так и запаковывать их, причём
сжимая файлы так, как их хочет видеть Silky Engine (разновидностью LZSS). Единственная, однако, проблема у средства есть
-- несколько медленно работает оно, особенно при запаковке, так что может придётся прождать несколько минут (ввиду
реализации алгоритма сжатия на Python).

>>> Использование.
1. Запустите пакет средств (main.py иль .exe).
2. Введите имя архива (с расширением!!!) или выберите его, нажав на кнопку "...".
3. Введите имя директории файлов или выберите его, нажав на кнопку "...".
4. Введите "0", коли распаковать желаете, али "1", коли запаковать желаете.
5. Ждите завершения.
"""
    }

    def __init__(self, **kwargs):
        """Arguments: width, height, language ("eng", "rus"), ..."""
        self._width = kwargs.get("width", self.default_width)
        self._height = kwargs.get("height", self.default_height)
        self._language = kwargs.get("language", self.init_language())

        self._root = tk.Tk()
        self._root.lang_index = 0

        self._arc_name = tk.StringVar()
        self._arc_name.set("")
        self._dir_name = tk.StringVar()
        self._dir_name.set("")

        self._root.geometry('{}x{}+{}+{}'.format(
            self._width,
            self._height,
            self._root.winfo_screenwidth() // 2 - self._width // 2,
            self._root.winfo_screenheight() // 2 - self._height // 2))
        self._root["bg"] = 'grey'

        self._top_frame = tk.Frame(master=self._root,
                                   background="white",
                                   borderwidth=5,
                                   relief=tk.RAISED)
        self._bottom_frame = tk.Frame(master=self._root,
                                      background="grey",
                                      borderwidth=5,
                                      relief=tk.SUNKEN)

        self._language_buttons = []
        for i in range(2):
            new_button = tk.Button(
                master=self._top_frame,
                background="white",
                font=("Helvetica", 14),
                command=lambda i=i: self.translate(self.possible_languages[i]))
            new_button.lang_index = i + 1
            self._language_buttons.append(new_button)

        self._entry_combinations = []
        entry_btns_commands = (self._choose_file, self._choose_dir)
        entry_vars = (self._arc_name, self._dir_name)
        for i in range(2):
            new_list = []
            new_lbl = tk.Label(master=self._bottom_frame,
                               background="white",
                               font=("Helvetica", 14))
            new_lbl.lang_index = 4 + i
            new_entry = tk.Entry(master=self._bottom_frame,
                                 background="white",
                                 borderwidth=2,
                                 textvariable=entry_vars[i],
                                 font=("Helvetica", 12),
                                 relief=tk.SUNKEN)
            new_btn = tk.Button(master=self._bottom_frame,
                                background="white",
                                command=entry_btns_commands[i],
                                font=("Helvetica", 14))
            new_btn.lang_index = 3
            new_list.append(new_lbl)
            new_list.append(new_entry)
            new_list.append(new_btn)
            self._entry_combinations.append(new_list)
            # Label, Entry, Button.

        self._action_btns = []
        actions = (self._unpack, self._pack)
        for i in range(2):
            new_btn = tk.Button(
                master=self._bottom_frame,
                background="white",
                font=("Helvetica", 14),
                command=actions[i],
            )
            new_btn.lang_index = 12 + i
            self._action_btns.append(new_btn)

        self._help_btn = tk.Button(
            master=self._bottom_frame,
            background="white",
            font=("Helvetica", 14),
            command=lambda: showinfo(self._strings_lib[self._language][18], self.programm_help[self._language]),
        )
        self._help_btn.lang_index = 18

        self._init_strings()

        for num, widget in enumerate(self._language_buttons):
            widget.place(relx=0.5 * num, rely=0.0, relwidth=0.5, relheight=1.0)
        self._top_frame.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.2)

        for num, widget_list in enumerate(self._entry_combinations):
            widget_list[0].place(relx=0.0, rely=0.2 * num, relwidth=1.0, relheight=0.1)
            widget_list[1].place(relx=0.0, rely=0.1 + 0.2 * num, relwidth=0.8, relheight=0.1)
            widget_list[2].place(relx=0.8, rely=0.1 + 0.2 * num, relwidth=0.2, relheight=0.1)
        for num, widget in enumerate(self._action_btns):
            widget.place(relx=0.0, rely=0.4 + 0.2 * num, relwidth=1.0, relheight=0.2)
        self._help_btn.place(relx=0.0, rely=0.8, relwidth=1.0, relheight=0.2)
        self._bottom_frame.place(relx=0.0, rely=0.2, relwidth=1.0, relheight=0.8)

        self._root.mainloop()

    # Getters.

    def get_width(self) -> int:
        """Get the GUI's window width."""
        return self._width

    def get_height(self) -> int:
        """Get the GUI's window height."""
        return self._height

    def get_language(self) -> str:
        """Get the GUI's language."""
        return self._language

    # Technical methods for packing and unpacking.

    def _unpack(self) -> None:
        """Unpack archive."""
        can_i = self.which_problems_i_have()
        if can_i:
            showwarning(title=can_i[0], message=can_i[1])
            return
        unpacking_thread = threading.Thread(daemon=False, target=self._unpack_this_archive,
                                            args=(self._arc_name.get(), self._dir_name.get()))
        unpacking_thread.start()

    def _unpack_this_archive(self, arc_name, dir_name) -> None:
        try:
            self.lock_activity()
            arc_archive = SilkyArc(arc_name, dir_name, verbose=True, integrity_check=False)
            arc_archive.unpack()
        except Exception as e:
            showerror(self._strings_lib[self._language][17], str(e))
        finally:
            self.unlock_activity()

    def _pack(self) -> None:
        """Pack archive."""
        can_i = self.which_problems_i_have()
        if can_i:
            showwarning(title=can_i[0], message=can_i[1])
            return
        packing_thread = threading.Thread(daemon=False, target=self._pack_this_archive,
                                          args=(self._arc_name.get(), self._dir_name.get()))
        packing_thread.start()

    def _pack_this_archive(self, arc_name, dir_name) -> None:
        try:
            self.lock_activity()
            arc_archive = SilkyArc(arc_name, dir_name, verbose=True, integrity_check=False)
            arc_archive.pack()
        except Exception as e:
            showerror(self._strings_lib[self._language][17], str(e))
        finally:
            self.unlock_activity()

    # Technical methods for locking/unlocking activity.

    def lock_activity(self) -> None:
        for btn in self._action_btns:
            btn["state"] = tk.DISABLED

    def unlock_activity(self) -> None:
        for btn in self._action_btns:
            btn["state"] = tk.NORMAL

    # Technical methods for validation.

    def which_problems_i_have(self):
        if self._arc_name.get() == "":
            return (self._strings_lib[self._language][14], self._strings_lib[self._language][15])
        if self._dir_name.get() == "":
            return (self._strings_lib[self._language][14], self._strings_lib[self._language][16])
        return None

    # Technical methods for files and dirs.

    def _choose_file(self) -> None:
        """Choose the archive file."""
        file_types = (
            (self._strings_lib[self._language][9], self._strings_lib[self._language][8]),
            (self._strings_lib[self._language][11], self._strings_lib[self._language][10]),
        )
        file_name = askopenfilename(filetypes=file_types, initialdir=os.getcwd(),
                                    title=self._strings_lib[self._language][6])
        file_name = os.path.normpath(file_name)
        if file_name != "":
            relpath = os.path.relpath(file_name, os.getcwd())
            end_arc = file_name
            if relpath.count(os.sep) < file_name.count(os.sep):
                end_arc = relpath
            self._arc_name.set(end_arc)
            if self._dir_name.get() == "":
                self._dir_name.set(os.path.splitext(end_arc)[0])

    def _choose_dir(self) -> None:
        """Choose the directory."""
        dir_name = askdirectory(initialdir=os.getcwd(), title=self._strings_lib[self._language][7])
        dir_name = os.path.normpath(dir_name)
        if dir_name != "":
            relpath = os.path.relpath(dir_name, os.getcwd())
            end_dir = dir_name
            if relpath.count(os.sep) < dir_name.count(os.sep):
                end_dir = relpath
            self._dir_name.set(end_dir)

    # Language methods.

    def translate(self, language: str) -> None:
        """Change the GUI language on "rus" or "eng"."""
        if language not in self.possible_languages:
            print("Error! Incorrect language!/Ошибка! Некорректный язык!")
            return
        self._language = language
        self._init_strings()

    def _init_strings(self) -> None:
        """Initialize strings of the GUI's widgets."""

        # Quite an elegant solution I through off. Hope this works.
        def _init_all_children_strings(widget):
            for elem in widget.winfo_children():
                if hasattr(elem, "lang_index"):
                    elem["text"] = self._strings_lib[self._language][elem.lang_index]
                if isinstance(elem, tk.Frame):
                    _init_all_children_strings(elem)

        self._root.title(self._strings_lib[self._language][self._root.lang_index])
        _init_all_children_strings(self._root)

    @staticmethod
    def init_language() -> str:
        """Get default language from the system. Works only on Windows."""
        lang_num = 0
        try:
            windll = ctypes.windll.kernel32
            super_locale = locale.windows_locale[windll.GetUserDefaultUILanguage()][:2]
            to_rus_locales = ('ru', 'uk', 'sr', 'bg', 'kk', 'be', 'hy', 'az')
            if super_locale in to_rus_locales:
                lang_num = 1
        except Exception:  # Yes, yes, I know this is a bad practice, but it does not matter here.
            pass
        return SilkyArcToolGUI.possible_languages[lang_num]
