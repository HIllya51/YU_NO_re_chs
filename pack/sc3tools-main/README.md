# sc3tools

A CLI tool for extracting and modifying text in .scx and .msb scripts found in visual novels based on MAGES. engine. It's meant to be a replacement for the old, overly complicated tool which had the same name and was part of the now-abandoned [SciAdv.Net project](https://github.com/CommitteeOfZero/SciAdv.Net).

## Supported games
- Steins;Gate (Steam)
- Steins;Gate 0
- Robotics;Notes
- Robotics;Notes DaSH

## Usage
Run ``./sc3tools`` with no arguments to see the list of the avaliable commands, as well as the list of the supported games and their aliases (such as ``sg0`` for Steins;Gate 0).

Run ``./sc3tools help <command>`` to see the help message for a specific command.

Here's an example of how you can extract text from the Robotics;Notes scripts:

``./sc3tools extract-text C:/src/CoZ/rne-msb/*.msb rn``

The output files will be placed in a subfolder named ``txt`` (in this case, ``C:/src/CoZ/rne-msb/txt``).