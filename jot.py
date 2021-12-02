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
snippet_width = 48

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
            print ('attempting to connect to ' + jot_dir)
            sys.exit(_("Connection to sqlite db failed!"))
    return con 

def gen_symbol(gen):
    if gen == 0:
        return ['', '   ']
    elif gen == 1:
        return ['', '|  ']
    elif gen == 2:
        return ['', ' ` ']
    elif gen > 2:
        return ['', ' `' + str(gen)+ '']
    elif gen == -1:
        return ['', ' ? ']

def summary_formatted(row, nlen = snippet_width, gen = 0):
    idWidth = 3
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
    due_str = fore.RED + back.GREY_11 + (row[2] if row[2] else '').center(12) + back.BLACK + ' '
    id_str = fore.HOT_PINK_1B + str(row[0]).rjust(idWidth).ljust(idWidth + 1)
    gen_parts = gen_symbol(gen)
    gen_str = fore.GREY_50 + ' ' + gen_parts[0]
    sts_str = fore.GOLD_1 + (row[7] if row[7] else '').center(3) + fore.GREY_50 + gen_parts[1]
    note_str = fore.CYAN_1 + note_summary + style.RESET
    return(due_str + id_str + gen_str + sts_str + note_str)

def find_children(parent):
    cursor = conn.cursor()
    sql = ''' SELECT child FROM Nest WHERE parent = ? '''
    children = list(sum(cursor.execute(sql, (parent,)).fetchall(), ()))
    nest = [parent, [find_children(child) for child in children]]
    return nest

def family_tree():
    cursor = conn.cursor()
    sql_parents = ' SELECT parent FROM Nest '
    sql_children = ' SELECT child FROM Nest '
    parents = flatten2set(cursor.execute(sql_parents).fetchall())
    children = flatten2set(cursor.execute(sql_children).fetchall())
    last_children = children - parents
    parent_children = children - last_children
    first_parents = parents - parent_children
    circular = 3
    tree = list([find_children(parents) for parents in first_parents])
    return tree, parent_children 

def recursive_list_print(tree, gen = 0, included = []):
    if not tree:
        return included 
    for el in tree:
        if not isinstance(el, list):
            real_gen = int((gen - 1)/2) + 1
            print(summary_formatted(query_row(el), gen = real_gen))
            included.append(el)
        else:
            recursive_list_print(el, gen + 1)
    return included

def print_nested(): 
    tree, parent_children = family_tree()
    included = recursive_list_print(tree)
    circular = parent_children - set(included)
    [print(summary_formatted(query_row(circ), gen = -1)) for circ in circular] 
    included.extend(list(circular))
    cursor = conn.cursor()
    sql2 = ''' SELECT notes_id FROM Notes '''
    all_items = set(sum(cursor.execute(sql2).fetchall(), ()))
    singular = all_items - set(included)
    [print(summary_formatted(query_row(sing), gen = 0)) for sing in singular] 

def flatten2set(object):
    gather = []
    for item in object:
        if isinstance(item, (list, tuple, set)):
            gather.extend(flatten2set(item))            
        else:
            gather.append(item)
    return set(gather)

def print_flat():
    cursor = conn.cursor()
    sql = ''' SELECT * FROM Notes
               LEFT JOIN Status ON Notes.status_id = Status.status_id '''
    rows = cursor.execute(sql)
    conn.commit()
    for row in rows:
        print(summary_formatted(row))

def print_notes(mode = 'nested'):
    if mode == 'flat':
        print_flat()
    elif mode == 'nested':
        print_nested()
    
def query_row(note_id):
    cursor = conn.cursor()
    sql = ''' SELECT * FROM Notes LEFT JOIN Status ON Notes.status_id = Status.status_id WHERE notes_id = ? '''
    cursor.execute(sql, (note_id,))
    row = cursor.fetchone()
    return(row)

def print_note(note_id):
    row = query_row(note_id)
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
    print('Deleting note_id = ' + str(note_id))
    cursor = conn.cursor()
    sql_delete_query = "DELETE FROM Notes where notes_id = ?"
    cursor.execute(sql_delete_query, (str(note_id),))
    conn.commit()
    
    sql_parents = "Select parent FROM Nest where child = ?"
    cursor.execute(sql_parents, (note_id,))
    conn.commit()
    parents = cursor.fetchall()
    parents = set(sum(parents, ())) 
    print(parents)
    
    sql_orphans = "Select child FROM Nest where parent = ?"
    cursor.execute(sql_orphans, (note_id,))
    conn.commit()
    orphans = cursor.fetchall()
    orphans = set(sum(orphans, ())) 
    print(orphans)
    
    sql_delete_nest = "DELETE FROM Nest WHERE parent = ? OR child = ?"
    cursor.execute(sql_delete_nest, (note_id, note_id))
    conn.commit()
    
    if orphans is not None and parents is not None:
        sql_adopt = 'INSERT INTO Nest (parent, child) VALUES (?, ?)'
        for parent in parents:
            for orphan in orphans:
                cursor.execute(sql_adopt, (parent, orphan))
                conn.commit()
                print(str(parent) + ' adopted ' + str(orphan))

def input_note(description, status_id, due, note_id, parent_id):
    longEntryFormat = description == "<long-entry-note>"
    if note_id is None:
        add_note(description, status_id, due, parent_id, longEntryFormat)
    else:
        edit_note(description, status_id, due, note_id, parent_id, longEntryFormat)

def long_entry_note(existingNote):
    f = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    n = f.name
    f.write(existingNote)
    f.close()
    subprocess.call([EDITOR, n])
    with open(n) as f:
        note = f.read()
    return(note.rstrip())

def add_note(description, status_id, due, parent_id, longEntryFormat):
    if longEntryFormat:
        description = long_entry_note('')
    cursor = conn.cursor()
    sql = 'INSERT INTO Notes (description, status_id, due) VALUES (?, ?, ?)'
    cursor.execute(sql, (description, status_id, due))
    conn.commit()
    print('Added note number: ' + fore.HOT_PINK_1B + str(cursor.lastrowid))
    if parent_id is not None:
        sql2 = 'INSERT INTO Nest (parent, child) VALUES (?, ?)'
        cursor.execute(sql2, (parent_id, cursor.lastrowid))
        conn.commit()
        print('Parent defined as: ' + fore.HOT_PINK_1B + str(parent_id))

def edit_note(description, status_id, due, note_id, parent_id, longEntryFormat):
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
    if parent_id is not None:
        sql2 = 'INSERT INTO Nest (parent, child) VALUES (?, ?)'
        cursor.execute(sql2, (parent_id, cursor.lastrowid))
        conn.commit()
        print('Parent defined as: ' + fore.HOT_PINK_1B + str(parent_id))

def valid_date(s):
    try:
        return datetime.strftime(datetime.strptime(s, "%Y-%m-%d"), "%Y-%m-%d")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

def parse_inputs():
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
    parser.add_argument("-p", "--parent", type=int, help="Assign parent by note id")
    parser.add_argument("--code", action = "store_true", help="Open python code for development")
    args = parser.parse_args()
    return(args if args else '')

def main(args):
    if args.code:
        subprocess.call([EDITOR, JOT_DIR + 'jot.py'])
    elif args.note is not None or args.edit is not None or args.status is not None or args.duedate is not None:
        input_note(description=args.note, status_id=args.status, due=args.duedate, note_id=args.edit, parent_id=args.parent)
        if args.verbose:
            print_notes()
    elif args.uncheck is not None:
        input_note(description=None, status_id=2, due=None, note_id=args.uncheck, parent_id=None)
    elif args.check is not None:
        input_note(description=None, status_id=3, due=None, note_id=args.check, parent_id=None)
    elif args.rm is not None:
        remove_note(args.rm)
        if args.verbose:
            print_notes()
    elif args.less is not None:
        print_note(args.less)
    else:
        print_notes()
    
# MAIN SCRIPT
conn = connect()
args = parse_inputs()
main(args)

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
