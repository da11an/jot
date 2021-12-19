# jot
command line task management interface and database

## Overview

- JOT is a capable task and note manager built as a command-line tool.
- Data is stored in a a sqlite3 database which is created the first time jot.py is run
- An interface to the database is built in Python
- A long-form note editing mode is available, and the editor is configurable, default is vim 
- For easy access:
    - Create a softlink in the folder jot is cloned to `ln -s jot.py jot`
    - Add the jot *folder* to your path, e.g. add `export PATH=/my/path/to/jot:$PATH` to end of `.bashrc`
- Usage can be accessed by typing `jot --help` or `jot -h`
- Typing `jot` (or `jot.py` without the soft link) gives a summary of active items
- Items can be nested by assigning a parent
- Ability to add attachments is envisioned in the database but not yet implemented
