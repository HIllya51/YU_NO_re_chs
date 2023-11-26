# GUI for this tool. Nothing more, nothing less.

import os
from tkinter import ttk
import tkinter as tk
from tkinter.messagebox import showinfo, showerror
from ai5win_arc import AI5WINArc
from gui import SilkyArcToolGUI  # Truly got in handy.


class AI5WINArcToolGUI(SilkyArcToolGUI):
    _strings_lib = {
        'eng': (
            "AI5WINArcTool by Tester",
            "English",
            "Русский",
            "...",
            "AI5WIN archive file (.arc):",
            "Resources directory:",  # 5
            "Filename choice",
            "Directory choice",
            "*.arc",
            "AI5WIN Archives",
            "*",  # 10
            "All files",
            "Unpack",
            "Pack",
            "Warning",
            "Archive name not stated.",  # 15
            "Directory name not stated.",
            "Error",
            "Help",
            "Choise/input of keys (0xNN...) for packing:",
            "Choise/input of names length for packing:",
        ),
        'rus': (
            "AI5WINArcTool от Tester-а",
            "English",
            "Русский",
            "...",
            "Архивный файл AI5WIN (.arc):",
            "Директория с ресурсами:",  # 5
            "Выбор имени файла",
            "Выбор директории",
            "*.arc",
            "Архивы AI5WIN",
            "*",  # 10
            "Все файлы",
            "Распаковать",
            "Запаковать",
            "Предупреждение",
            "Имя архива не указано.",  # 15
            "Имя директории не указано.",
            "Ошибка",
            "Справка",
            "Выбор/ввод ключей (0xNN...) для запаковки:",
            "Выбор/ввод длины имён для запаковки:",
        )
    }

    program_help = {
        'eng': """
Dual languaged (rus+eng) GUI tool for packing and unpacking archives of AI5WIN engine. Very-very incomplete list of games of the engine thou can see on vndb. It is not the same arc as used in Silky Engine and AI6WIN. For Silky Engine .arc archives use SilkyArcTool instead, for AI6WIN's use AI6WINArcTool!
Important note: the tool is quite slow. It may take several minutes to extract and especially pack even rather small archives.

> Usage:
1. Run the tool (main.py or .exe).
2. Print filename (with extension!!!) or choose it by clicking on button "...".
3. Print directory or choose it by clicking on button "...".
4. If you want to pack, then choose the keys and name size (or enter your data).
5. Push the button pack or "Unpack" to "Pack" or unpack.
6. Just wait until it done.
7. If you unpacked, then in the directory of archive will apeear new ".key" file. Open it with text editor and you will get keys and names size of this archive (hacked authomatically). Enter this data afterwards to repack the archive.
""",
        'rus': """
Двуязычное средство (рус+англ) для распаковки и запаковки архивов движка AI5WIN. Очень-преочень неполный список игр на движке вы можете обозревать здесь. Не стоит путать его с разновидностями .arc, используемым в Silky Engine и AI6WIN. Для них используйте другие средства: SilkyArcTool и AI6WINArcTool соответственно!
Важная заметка: средство достаточно медленное. Для того, чтобы распаковать и запаковать даже достаточно маленький архив, может потребоваться несколько минут.

> Использование:
1. Запустите пакет средств (main.py иль .exe).
2. Введите имя архива (с расширением!!!) или выберите его, нажав на кнопку "...".
3. Введите имя директории файлов или выберите его, нажав на кнопку "...".
4. Если вы хотите запаковать архив, выберите ключи и размер имён (или введите свои данные).
5. Нажмите на кнопку, соответствующую желаемому действию ("Распаковать" и "Запаковать").
6. Ждите завершения.
7. Если вы выполняли распаковку, то в директории архива появится новый файл с расширением ".key". Откройте его с текстовым редактором. Вы сможете увидеть ключи и размер имён данного архива (взломанные автоматически); сии данные вы можете в дальнейшем вводить для перезапаковки архива.
"""
    }

    keys_sep = "      "

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

        self._keyer = tk.StringVar()
        self._keyer.trace_add("write", self._keys_chosen)
        self._first_key = tk.StringVar()
        self._second_key = tk.StringVar()
        self._third_key = tk.StringVar()
        self._name_bytes = tk.StringVar()

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
                font=("Helvetica", 12),
                command=actions[i],
            )
            new_btn.lang_index = 12 + i
            self._action_btns.append(new_btn)

        self._help_btn = tk.Button(
            master=self._bottom_frame,
            background="white",
            font=("Helvetica", 12),
            command=lambda: showinfo(self._strings_lib[self._language][18], self.programm_help[self._language]),
        )
        self._help_btn.lang_index = 18

        good_keys = AI5WINArc.known_keys_triplets
        good_key_values = []
        for i in good_keys:
            good_key_values.append(self.keys_sep.join(map(hex, i)))
        if good_key_values:
            self._keyer.set(good_key_values[0])

        self._keys_lbl = tk.Label(master=self._bottom_frame,
                                  background="white",
                                  font=("Helvetica", 10))
        self._keys_lbl.lang_index = 19
        self._keys_cmb = ttk.Combobox(master=self._bottom_frame,
                                      font=("Helvetica", 12),
                                      textvariable=self._keyer,
                                      values=good_key_values,
                                      state="readonly")

        self._name_lbl = tk.Label(master=self._bottom_frame,
                                  background="white",
                                  font=("Helvetica", 10))
        self._name_lbl.lang_index = 20
        good_name_values = [str(i) for i in AI5WINArc.possible_name_bytes]
        self._name_cmb = ttk.Combobox(master=self._bottom_frame,
                                      font=("Helvetica", 12),
                                      textvariable=self._name_bytes,
                                      values=good_name_values)
        if good_name_values:
            self._name_bytes.set(good_name_values[0])

        keys_vars = (self._first_key, self._second_key, self._third_key)
        self._keys_ent = []
        for key in keys_vars:
            self._keys_ent.append(
                tk.Entry(
                    master=self._bottom_frame,
                    textvariable=key,
                    font=("Helvetica", 12)
                )
            )

        self._init_strings()

        for num, widget in enumerate(self._language_buttons):
            widget.place(relx=0.5 * num, rely=0.0, relwidth=0.5, relheight=1.0)
        self._top_frame.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.1)

        for num, widget_list in enumerate(self._entry_combinations):
            widget_list[0].place(relx=0.0, rely=0.2 * num, relwidth=1.0, relheight=0.1)
            widget_list[1].place(relx=0.0, rely=0.1 + 0.2 * num, relwidth=0.8, relheight=0.1)
            widget_list[2].place(relx=0.8, rely=0.1 + 0.2 * num, relwidth=0.2, relheight=0.1)
        self._keys_lbl.place(relx=0.0, rely=0.4, relwidth=1.0, relheight=0.1)
        self._keys_cmb.place(relx=0.0, rely=0.5, relwidth=1.0, relheight=0.1)
        for num, widget in enumerate(self._keys_ent):
            widget.place(relx=0.33 * num, rely=0.6, relwidth=0.33, relheight=0.1)
        for num, widget in enumerate(self._action_btns):
            widget.place(relx=0.0 + 0.33 * num, rely=0.9, relwidth=0.33 + 0.01 * num, relheight=0.1)
        self._name_lbl.place(relx=0.0, rely=0.7, relwidth=1.0, relheight=0.1)
        self._name_cmb.place(relx=0.0, rely=0.8, relwidth=1.0, relheight=0.1)
        self._help_btn.place(relx=0.67, rely=0.9, relwidth=0.33, relheight=0.1)
        self._bottom_frame.place(relx=0.0, rely=0.1, relwidth=1.0, relheight=0.9)
        self._root.mainloop()

    # Technical methods for packing and unpacking.

    def _unpack_this_archive(self, arc_name, dir_name) -> None:
        """Initializing calling archive unpacking."""
        try:
            self.lock_activity()
            arc_archive = AI5WINArc(arc_name, dir_name, verbose=True, integrity_check=False)
            arc_archive.unpack()
            with open(os.path.join(os.path.dirname(os.path.abspath(arc_name)), arc_name + ".keys"), 'w') as key_file:
                key_file.write("Hacked keys:/Взломанные ключи:\n")
                key_file.write("Key 1/Ключ 1: {}\n".format(hex(arc_archive.first_key)))
                key_file.write("Key 2/Ключ 2: {}\n".format(hex(arc_archive.second_key)))
                key_file.write("Key 3/Ключ 3: {}\n".format(hex(arc_archive.third_key)))
                key_file.write("Длина имён: {}\n".format(hex(arc_archive.name_bytes)))
                self._first_key.set(hex(arc_archive.first_key))
                self._second_key.set(hex(arc_archive.second_key))
                self._third_key.set(hex(arc_archive.third_key))
                self._name_bytes.set(str(arc_archive.name_bytes))
        except Exception as e:
            showerror(self._strings_lib[self._language][17], str(e))
        finally:
            self.unlock_activity()

    def _pack_this_archive(self, arc_name, dir_name) -> None:
        """Initializing calling archive packing."""
        try:
            self.lock_activity()
            arc_archive = AI5WINArc(arc_name, dir_name, verbose=True, integrity_check=False,
                                    first_key=int(self._first_key.get(), 16),
                                    second_key=int(self._second_key.get(), 16),
                                    third_key=int(self._third_key.get(), 16),
                                    name_bytes=int(self._name_bytes.get(), 10))
            arc_archive.pack()
        except Exception as e:
            showerror(self._strings_lib[self._language][17], str(e))
        finally:
            self.unlock_activity()

    # Technocal events methods.

    def _keys_chosen(self, *args) -> None:
        """Change keys variables after changing main text variable."""
        new_keys = self._keyer.get().split(self.keys_sep)
        self._first_key.set(new_keys[0])
        self._second_key.set(new_keys[1])
        self._third_key.set(new_keys[2])
