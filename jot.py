#!/usr/bin/env python3

"""
JOT is a note taking and task management tool 
"""

import sys
import sqlite3
import tempfile
import os
import argparse
from datetime import datetime
import subprocess
from ansi_escape_room import fore, back, style
import pydoc

# Settings ----
JOT_DIR = '/home/dallan/jot/'
EDITOR = 'vim'
DB = JOT_DIR + 'jot.sqlite'

def connect():
    undefined_db = not os.path.exists(DB)
    if undefined_db:
        con = sqlite3.connect(DB)
        cursor = con.cursor()
        sql_file = open("create_db.sql")
        sql_as_string = sql_file.read()
        cursor.executescript(sql_as_string)
        con.commit()
    else:
        try:
            con = sqlite3.connect(DB)
            cursor = con.cursor()
        except:
            print ('attempting to connect to ' + JOT_DIR)
            sys.exit(_("Connection to sqlite db failed!"))
    return con 

def summary_formatted(row):
    nlen = 42
    sym_len = 4
    mlchr = '[+]'.rjust(sym_len)[:sym_len]
    elps = '...'.rjust(sym_len)[:sym_len]
    mlelps = '.+.'.rjust(sym_len)[:sym_len]
    multiline = '\n' in row[3] 
    note_summary = row[3].split('\n')[0]
    nslen0 = len(note_summary)
    tooLong = (nslen0 > (nlen - sym_len)) if multiline else (nslen0 > nlen)
    if tooLong and multiline:
        note_summary = note_summary[:(nlen - sym_len)] + fore.GREEN + mlelps
    elif tooLong: # and not multiline
        note_summary = note_summary[:(nlen - sym_len)] + fore.GREEN + elps
    elif multiline: # and not too long
        note_summary = note_summary + fore.GREEN + mlchr
    
    return(fore.RED + back.GREY_11 + \
           (row[2] if row[2] else '').center(12) + \
           back.BLACK + ' ' + fore.HOT_PINK_1B + \
           str(row[0]).rjust(3).ljust(4) + \
           fore.GOLD_1 + (row[7] if row[7] else '').center(3) + \
           fore.CYAN_1 + ' ' + note_summary + style.RESET)

def print_notes():
    cursor = conn.cursor()
    sql = ''' SELECT * FROM Notes
               LEFT JOIN Status ON Notes.status_id = Status.status_id '''
    rows = cursor.execute(sql)
    conn.commit()
    for row in rows:
        print(summary_formatted(row))

def print_note(note_id):
    cursor = conn.cursor()
    sql = ''' SELECT * FROM Notes LEFT JOIN Status ON Notes.status_id = Status.status_id WHERE notes_id = ? '''
    cursor.execute(sql, (note_id,))
    row = cursor.fetchone()
    if not row:
        print('Note does not exist: ' + fore.HOT_PINK_1B + str(note_id))
    else:
        pydoc.pipepager(
            fore.RED + 'Due Date'.ljust(12) + ' ' + \
            fore.HOT_PINK_1B + 'ID'.ljust(4) + \
            fore.GOLD_1 + 'STS' + fore.CYAN_1 + 'Note Snip' + \
            fore.GREEN + 'pet' + \
            '\n' + style.REVERSE + summary_formatted(row) + \
            '\n' + fore.GREY_62 + 'Created'.ljust(21) + \
            fore.ORANGE_3 + 'Modified'.ljust(21) + \
            '\n' + fore.GREY_62 + style.REVERSE + row[4].center(21) + \
            fore.ORANGE_3 + style.REVERSE + row[5].center(21) + \
            '\n' + '\n' + style.RESET + row[3], cmd='less -R')

def remove_note(note_id):
    # may need to be expanded to check other tables?
    cursor = conn.cursor()
    sql_delete_query = "DELETE FROM Notes where notes_id = ?"
    print('Deleting note_id = ' + str(note_id))
    cursor.execute(sql_delete_query, (str(note_id),))
    conn.commit()
    return cursor.lastrowid

def input_note(description, status_id, due, note_id):
    longEntryFormat = description == "<long-entry-note>"
    if note_id is None:
        add_note(description, status_id, due, longEntryFormat)
    else:
        edit_note(description, status_id, due, note_id, longEntryFormat)

def long_entry_note(existingNote):
    f = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    n = f.name
    f.write(existingNote)
    f.close()
    subprocess.call([EDITOR, n])
    with open(n) as f:
        note = f.read()
    return(note.rstrip())

def add_note(description, status_id, due, longEntryFormat):
    if longEntryFormat:
        description = long_entry_note('')
    cursor = conn.cursor()
    sql = 'INSERT INTO Notes (description, status_id, due) VALUES (?, ?, ?)'
    cursor.execute(sql, (description, status_id, due))
    conn.commit()
    print('Added note number: ' + fore.HOT_PINK_1B + str(cursor.lastrowid))
    return cursor.lastrowid

def edit_note(description, status_id, due, note_id, longEntryFormat):
    cursor = conn.cursor()
    sql_old = 'SELECT * FROM Notes where notes_id = ?'
    cursor.execute(sql_old, (str(note_id),))
    row = cursor.fetchone()
    if longEntryFormat:
        description = long_entry_note(str(row[3]))
    new_row = (
            row[0],
            status_id if status_id is not None else row[1], \
            due if due is not None else row[2], \
            description if description is not None else row[3], \
            row[4],
            datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            )
    sql = 'INSERT or REPLACE into Notes VALUES (?, ?, ?, ?, ?, ?)'
    cursor.execute(sql, new_row)
    conn.commit()
    print('Edited note number: ' + fore.HOT_PINK_1B + str(cursor.lastrowid))
    return cursor.lastrowid

conn = connect()

def valid_date(s):
    try:
        return datetime.strftime(datetime.strptime(s, "%Y-%m-%d"), "%Y-%m-%d")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action = "store_true", help="increase output verbosity")
parser.add_argument("-n", "--note", help="note, add/edit, in quotes if more than a word", nargs='?', const='<long-entry-note>', default=None)
parser.add_argument("-e", "--edit", type=int, help="Edit existing note, argument: ID")
parser.add_argument("-u", "--uncheck", type=int, help="Uncheck existing note, argument: ID")
parser.add_argument("-c", "--check", type=int, help="Check existing note, argument: ID")
parser.add_argument("-l", "--less", type=int, help="Display whole note to `less` [ID]")
parser.add_argument("-s", "--status", type=int, choices=[1, 2, 3, 4], help="set status to 1=plain note, 2=unchecked, 3=checked, 4=cancelled")
parser.add_argument("-d", "--duedate", help="The Due Date - format YYYY-MM-DD", type=valid_date)
parser.add_argument("--rm", type=int, help="remove ID or list of IDs")
args = parser.parse_args()

if args.note is not None or args.edit is not None or args.status is not None or args.duedate is not None:
    input_note(description=args.note, status_id=args.status, due=args.duedate, note_id=args.edit)
    if args.verbose:
        print_notes()
elif args.uncheck is not None:
    input_note(description=args.note, status_id=2, due=args.duedate, note_id=args.uncheck)
elif args.check is not None:
    input_note(description=args.note, status_id=3, due=args.duedate, note_id=args.check)
elif args.rm is not None:
    remove_note(args.rm)
    if args.verbose:
        print_notes()
elif args.less is not None:
    print_note(args.less)
else:
    print_notes()



# def convertToBinaryData(filename):
#     # Convert digital data to binary format
#     with open(filename, 'rb') as file:
#         blobData = file.read()
#     return blobData
# 

# def insertBLOB(empId, name, photo, resumeFile):
#     try:
#         sqliteConnection = sqlite3.connect(DB)
#         cursor = sqliteConnection.cursor()
#         print("Connected to SQLite")
#         sqlite_insert_blob_query = """ INSERT INTO Files
#                                   (id, name, photo, resume) VALUES (?, ?, ?, ?)"""
# 
#         empPhoto = convertToBinaryData(photo)
#         resume = convertToBinaryData(resumeFile)
#         # Convert data into tuple format
#         data_tuple = (empId, name, empPhoto, resume)
#         cursor.execute(sqlite_insert_blob_query, data_tuple)
#         sqliteConnection.commit()
#         print("Image and file inserted successfully as a BLOB into a table")
#         cursor.close()
# 
#     except sqlite3.Error as error:
#         print("Failed to insert blob data into sqlite table", error)
#     finally:
#         if sqliteConnection:
#             sqliteConnection.close()
#             print("the sqlite connection is closed")
# 
# insertBLOB(1, "Smith", "E:\pynative\Python\photos\smith.jpg", "E:\pynative\Python\photos\smith_resume.txt")
# insertBLOB(2, "David", "E:\pynative\Python\photos\david.jpg", "E:\pynative\Python\photos\david_resume.txt")
