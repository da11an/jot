# jot
command line task management interface and database

## Overview

- JOT is a capable task and note manager built as a command-line tool.
- Data is stored in a sqlite3 database which is created the first time jot.py is run
- An interface to the database is written in Python
- A long-form note editing mode is available, and the editor is configurable, default depends on os: vim or notepad
- For easy access (Linux): add similar to `alias jot='python3 /PATH/TO/jot/jot/jot.py'` to your `.bashrc`
- Usage can be accessed after installing by typing `jot --help` or `jot -h`
- Typing `jot` (or `python3 jot.py` without the soft link) gives a summary of active items
- Items can be nested by assigning a parent
- Ability to add attachments is envisioned in the database but not yet implemented

## Windows

- JOT usage in Windows is similar to Linux, but without color highlighting
- Note that the correct version of Python needs to be used to call JOT: https://stackoverflow.com/questions/55656887/printing-output-of-python-script-to-windows-console-when-running-via-batch-file
- To run python from the cloned directory: `python jot.py [...]`

## MacOS

- Works in MacOS
