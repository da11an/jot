# jot
command line task management interface and database

## Overview

- JOT is a capable task and note manager built as a command-line tool.
- Data is stored in a a sqlite3 database which is created the first time jot is run
- An interface to the database is built in Python
- Long-form editing is available with a text editor. Default is vim on Linux/MacOS and notepad on Windows.
- For easy access, see installation instructions below. Alternatively (Linux/MacOS), add `alias jot='python3 /home/dallan/jot/jot.py'` to your `.bashrc`
- Usage can be accessed by typing `jot --help` or `jot -h`
- Running `jot` without any arguments gives a summary of active items
- Items can be nested by assigning a parent
- Ability to add attachments is envisioned in the database but not yet implemented

## Installation
After cloning the repository, run the following command: `python setup.py install`. `jot` should now be usable without adding an alias.

## Windows

- JOT usage in Windows is similar to Linux, but without color highlighting
- Note that the correct version of Python needs to be used to call JOT: https://stackoverflow.com/questions/55656887/printing-output-of-python-script-to-windows-console-when-running-via-batch-file
- To run python from the cloned directory: `python jot.py [...]`

## MacOS

- Works in MacOS
