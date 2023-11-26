# AI5WINArcTool
## English
Dual languaged (rus+eng) GUI tool for packing and unpacking archives of AI5WIN engine. Very-very incomplete list of games of the engine thou can see [on vndb](https://vndb.org/r?q=&o=a&s=title&f=fwAI5WIN-). **It is not the same arc as used in Silky Engine and AI6WIN. For Silky Engine .arc archives use [SilkyArcTool](https://github.com/TesterTesterov/SilkyArcTool) instead, for AI5WIN's use [AI6WINArcTool](https://github.com/TesterTesterov/AI6WINArcTool)!**

You may want to compile and decompile AI5WIN mes script files. For this use [AI5WINScriptTool](https://github.com/TesterTesterov/AI5WINScriptTool).

Important note: the tool is quite slow. It may take several minutes to extract and especially pack even rather small archives.

Versions:
- [AI5WINArcTool 2.2](https://github.com/TesterTesterov/AI5WINArcTool/releases/tag/2.2) -- for using in ustandard archives like in Dokyuusei 2's ones.
- [AI5WINArcTool 2.1](https://github.com/TesterTesterov/AI5WINArcTool/releases/tag/2.1) -- for using in standard archives like in Shangrlia's ones.

## Русский
Двуязычное средство (рус+англ) для распаковки и запаковки архивов движка AI5WIN. Очень-преочень неполный список игр на движке вы можете обозревать [здесь](https://vndb.org/r?f=fwAI6WIN-). **Не стоит путать его с разновидностями .arc, используемым в Silky Engine и AI6WIN. Для них используйте другие средства: [SilkyArcTool](https://github.com/TesterTesterov/SilkyArcTool) и [AI6WINArcTool](https://github.com/TesterTesterov/AI6WINArcTool) соответственно!**

Вам может понадобиться (де)компилировать скрипты mes движка AI5WIN. Для сего используйте средство [AI5WINScriptTool](https://github.com/TesterTesterov/AI5WINScriptTool).

Важная заметка: средство достаточно медленное. Для того, чтобы распаковать и запаковать даже достаточно маленький архив, может потребоваться несколько минут.

Версии:
- [AI5WINArcTool 2.2](https://github.com/TesterTesterov/AI5WINArcTool/releases/tag/2.2) -- для использования в нестандартных архивах, как в Одноклассниках 2.
- [AI5WINArcTool 2.1](https://github.com/TesterTesterov/AI5WINArcTool/releases/tag/2.1) -- для использования в стандартных архивах, как в Шангри-ла.

# Usage
## English
![image](https://user-images.githubusercontent.com/66121918/147419469-1665af28-76a8-4ae5-b5e2-c5bf86303fdf.png)
1. Run the tool (main.py or .exe).
2. Print filename (with extension!!!) or choose it by clicking on button "...".
3. Print directory or choose it by clicking on button "...".
4. If you want to pack, then choose the keys and name size (or enter your data).
5. Push the button pack or "Unpack" to "Pack" or unpack.
6. Just wait until it done.
7. If you unpacked, then in the directory of archive will apeear new ".key" file. Open it with text editor and you will get keys and names size of this archive (hacked authomatically). Enter this data afterwards to repack the archive.

## Русский
![image](https://user-images.githubusercontent.com/66121918/147419462-cd395702-66ce-40d7-b9ec-8bdd5080fcbb.png)
1. Запустите пакет средств (main.py иль .exe).
2. Введите имя архива (с расширением!!!) или выберите его, нажав на кнопку "...".
3. Введите имя директории файлов или выберите его, нажав на кнопку "...".
4. Если вы хотите запаковать архив, выберите ключи и размер имён (или введите свои данные).
5. Нажмите на кнопку, соответствующую желаемому действию ("Распаковать" и "Запаковать").
6. Ждите завершения.
7. Если вы выполняли распаковку, то в директории архива появится новый файл с расширением ".key". Откройте его с текстовым редактором. Вы сможете увидеть ключи и размер имён данного архива (взломанные автоматически); сии данные вы можете в дальнейшем вводить для перезапаковки архива.

# Tested on:

## English
- [Doukyuusei 2](https://vndb.org/v2337).
- [Shangrlia](https://vndb.org/v3182) ([Elf Classics](https://vndb.org/r5220)).
- [Shangrlia](https://vndb.org/v3182) ([Shangrlia Multipack](https://vndb.org/r6255)).

## Русский
- [Одноклассники 2](https://vndb.org/v2337).
- [Шангри-ла](https://vndb.org/v3182) ([Классика от Elf](https://vndb.org/r5220)).
- [Шангри-ла](https://vndb.org/v3182) ([Шангли-ла: Комплексный пакет](https://vndb.org/r6255)).
