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
import pydoc


class Jot:
    def __init__(self, **kwargs):
        self.defaults()
        self.connect()
        self.parse_inputs()
        self.main()

    def defaults(self):
        # Settings ----
        
        ## Preferences
        self.snippet_width = 48
        self.GREEN = '\x1b[38;5;2m'
        self.YELLOW = '\x1b[38;5;3m'
        self.MAGENTA = '\x1b[38;5;5m'
        self.WHITE = '\x1b[38;5;15m'
        self.CYAN = '\x1b[38;5;6m'
        self.RED = '\x1b[38;5;1m'
        self.BLUE = '\x1b[38;5;4m'
        self.VIOLET = '\x1b[38;5;177m'
        self.DEFAULT = self.WHITE

        ### Defaults
        #### windows config
        if os.name == 'nt':
            self.EDITOR = 'notepad'
            self.colorize = False 
            self.view_note_cmd = "more"
        #### linux config
        else: 
            self.EDITOR = 'nvim'
            self.colorize = True 
            self.view_note_cmd = "less -R"
            
        ## Directories
        self.JOT_DIR = os.path.dirname(sys.argv[0])
        self.DB = os.path.join(self.JOT_DIR, 'jot.sqlite')

    def connect(self):
        undefined_db = not os.path.exists(self.DB)
        if undefined_db:
            self.conn = sqlite3.connect(self.DB)
            self.cursor = self.conn.cursor()
            sql_file = open("create_db.sql")
            sql_as_string = sql_file.read()
            self.cursor.executescript(sql_as_string)
            self.conn.commit()
        else:
            try:
                self.conn = sqlite3.connect(self.DB)
                self.cursor = self.conn.cursor()
            except:
                print ('attempting to connect to ' + self.JOT_DIR)
                sys.exit(_("Connection to sqlite db failed!"))
    
    def gen_symbol(self, gen):
        if gen == 0:
            return ['']
        elif gen == 1:
            return ['#'.ljust(gen, '>') + ' ']
        elif gen > 1:
            return ['>'.rjust(gen, '-') + ' ']
        elif gen == -1:
            return ['? ']
    
    def print_formatted(self, row, gen = 0, status_show = (None, 1, 2, 3, 4, 5)):
        result = self.summary_formatted(row, gen = gen, status_show = status_show)
        if result is not None:
            print(result)
    
    def summary_formatted(self, row, gen = 0, status_show = (None, 1, 2, 3, 4, 5)):
        if row[6] in status_show:
            gen_parts = self.gen_symbol(gen)
            sts_str = (row[7] if row[7] else '').center(3, '|')
            gen_str = gen_parts[0]
            
            idWidth = 3
            sym_len = 0
            multiline = '\n' in row[3] 
            note_summary = gen_str + row[3].split('\n')[0]
            nslen0 = len(note_summary)
            tooLong = nslen0 > self.snippet_width 
            if tooLong and multiline:
                end_chr = '&'
            elif tooLong: # and not multiline
                end_chr = '~' 
            elif multiline: # and not too long
                end_chr = '+' 
            else:
                end_chr = '|'
            note_summary = note_summary[:self.snippet_width].ljust(self.snippet_width) + end_chr
            due_str = (row[2] if row[2] else '').center(10)
            id_str = str(row[0]).rjust(idWidth)
            note_str = note_summary
            plain_summary = '| ' + due_str + ' ' + sts_str + ' ' + id_str + ' | ' + note_str + ' ' 
            return(self.colorize_summary(plain_summary))
    
    def colorize_summary(self, my_str):
        if self.colorize:
            sty = {}
            sty[0] = self.DEFAULT
            sty['date'] = self.RED
            sty['stat'] = self.YELLOW
            sty['ind'] = self.MAGENTA
            sty['note'] = self.CYAN
            sty['end'] = self.GREEN
            spacer = sty[0] + '|'
            mydate = sty['date'] + my_str[1:13]
            mystat = sty['stat'] + my_str[13:16]
            myind = sty['ind'] + my_str[16:21]
            mynote = sty['note'] + my_str[22:23+self.snippet_width]
            myend = sty['end'] + my_str[23+self.snippet_width:24+self.snippet_width] + sty[0]
            return(my_str[0:1] + mydate + mystat + myind + spacer + mynote + myend)
        else:
            return(my_str)
   
    def search_notes(self, term):
        sql = ''' SELECT notes_id FROM Notes WHERE description LIKE ? '''
        found_id = self.cursor.execute(sql, ('%' + term + '%',)).fetchall()
        print(found_id)

    def find_children(self, parent):
        sql = ''' SELECT child FROM Nest WHERE parent = ? '''
        children = list(sum(self.cursor.execute(sql, (parent,)).fetchall(), ()))
        nest = [parent, [self.find_children(child) for child in children]]
        return nest
    
    def family_tree(self):
        sql_parents = ' SELECT parent FROM Nest '
        sql_children = ' SELECT child FROM Nest '
        parents = self.flatten2set(self.cursor.execute(sql_parents).fetchall())
        children = self.flatten2set(self.cursor.execute(sql_children).fetchall())
        last_children = children - parents
        parent_children = children - last_children
        first_parents = parents - parent_children
        circular = 3
        tree = list([self.find_children(parents) for parents in first_parents])
        return tree, parent_children 
    
    def recursive_list_print(self, tree, gen = 0, included = [], status_show = (None,1,2,3,4,5)):
        if not tree:
            return included 
        for el in tree:
            if not isinstance(el, list):
                real_gen = int((gen - 1)/2) + 1
                self.print_formatted(self.query_row(el), gen = real_gen, status_show = status_show)
                included.append(el)
            else:
                self.recursive_list_print(el, gen + 1, status_show = status_show)
        return included
    
    def note_header(self):
        a=self.colorize_summary('+------------+-+-----+-' + ''.ljust(self.snippet_width, '-') + '+')
        b=self.colorize_summary('|     Date   |?| Ind | Note ' + ''.ljust(self.snippet_width-5) + '|')
        c=self.colorize_summary('+------------+-+-----+-' + ''.ljust(self.snippet_width, '-') + '+')
        return(a + '\n' + b + '\n' + c)
    
    def note_footer(self):
        return(self.colorize_summary('+------------+-+-----+-' + ''.ljust(self.snippet_width, '-') + '+'))
    
    def print_nested(self, status_show = (None,1,2,3,4,5)): 
        tree, parent_children = self.family_tree()
        included = self.recursive_list_print(tree, status_show = status_show)
        circular = parent_children - set(included)
        [self.print_formatted(self.query_row(circ), gen = -1, status_show = status_show) for circ in circular] 
        included.extend(list(circular))
        sql2 = ''' SELECT notes_id FROM Notes '''
        all_items = set(sum(self.cursor.execute(sql2).fetchall(), ()))
        singular = all_items - set(included)
        [self.print_formatted(self.query_row(sing), gen = 0, status_show = status_show) for sing in singular] 
    
    def flatten2set(self, object):
        gather = []
        for item in object:
            if isinstance(item, (list, tuple, set)):
                gather.extend(self.flatten2set(item))            
            else:
                gather.append(item)
        return set(gather)
    
    def print_flat(self, status_show = (None,1,2,3,4,5)):
        sql = ''' SELECT * FROM Notes
                   LEFT JOIN Status ON Notes.status_id = Status.status_id '''
        rows = self.cursor.execute(sql)
        self.conn.commit()
        for row in rows:
            myline = self.summary_formatted(row, status_show = status_show)
            if myline:
                print(myline)
    
    def print_notes(self, mode = 'nested', status_show = (None,1,2,3,4,5)):
        print(self.note_header())
        if mode == 'flat':
            self.print_flat(status_show = status_show)
        elif mode == 'nested':
            self.print_nested(status_show = status_show)
        print(self.note_footer())
    
    def query_row(self, note_id):
        sql = ''' SELECT * FROM Notes LEFT JOIN Status ON Notes.status_id = Status.status_id WHERE notes_id = ? '''
        self.cursor.execute(sql, (note_id,))
        row = self.cursor.fetchone()
        return(row)
    
    def print_note(self, note_id):
        row = self.query_row(note_id)
        if not row:
            print('Note does not exist: ' + str(note_id))
        else:
            pydoc.pipepager(
                self.note_header() + \
                '\n' + self.summary_formatted(row) + \
                '\n' + self.note_footer() + \
                '\n' + row[3] + \
                '\n\n' + ('created ' + row[4] + ' & modified ' + row[5]).ljust(self.snippet_width + 17, ">").rjust(self.snippet_width + 24, "<") \
                , cmd=self.view_note_cmd)
    
    def remove_note(self, note_id):
        # may need to be expanded to check other tables?
        print('Deleting note_id = ' + str(note_id))
        sql_delete_query = "DELETE FROM Notes where notes_id = ?"
        self.cursor.execute(sql_delete_query, (str(note_id),))
        self.conn.commit()
        
        sql_parents = "Select parent FROM Nest where child = ?"
        self.cursor.execute(sql_parents, (note_id,))
        self.conn.commit()
        parents = self.cursor.fetchall()
        parents = set(sum(parents, ())) 
        print(parents)
        
        sql_orphans = "Select child FROM Nest where parent = ?"
        self.cursor.execute(sql_orphans, (note_id,))
        self.conn.commit()
        orphans = self.cursor.fetchall()
        orphans = set(sum(orphans, ())) 
        print(orphans)
        
        sql_delete_nest = "DELETE FROM Nest WHERE parent = ? OR child = ?"
        self.cursor.execute(sql_delete_nest, (note_id, note_id))
        self.conn.commit()
        
        if orphans is not None and parents is not None:
            sql_adopt = 'INSERT INTO Nest (parent, child) VALUES (?, ?)'
            for parent in parents:
                for orphan in orphans:
                    self.cursor.execute(sql_adopt, (parent, orphan))
                    self.conn.commit()
                    print(str(parent) + ' adopted ' + str(orphan))
    
    def input_note(self, description, status_id, due, note_id, parent_id):
        longEntryFormat = description == "<long-entry-note>"
        if due == "0001-01-01":
            due = None
        if note_id is None:
            self.add_note(description, status_id, due, parent_id, longEntryFormat)
        else:
            self.edit_note(description, status_id, due, note_id, parent_id, longEntryFormat)
    
    def long_entry_note(self, existingNote):
        f = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
        n = f.name
        f.write(existingNote)
        f.close()
        subprocess.call([self.EDITOR, n])
        with open(n) as f:
            note = f.read()
        return(note.rstrip())
    
    def nest_parent_child(self, parent, child):
        if parent is not None and child is not None:
            print('parent: ' + str(parent))
            if parent > 0 and child > 0:
                sql_nest = 'INSERT INTO Nest (parent, child) VALUES (?, ?)'
                self.cursor.execute(sql_nest, (parent, child))
                self.conn.commit()
                print('Parent defined as: ' + str(parent))
            elif parent < 0 and child > 0: # remove parent link
                sql_unnest = 'DELETE FROM Nest WHERE parent = ? and child = ?'
                self.cursor.execute(sql_unnest, (abs(parent), child))
                self.conn.commit()
                print('Parent removed ' + str(abs(parent)))
            elif parent == 0 and child > 0: # remove all parents
                sql_unnest = 'DELETE FROM Nest WHERE child = ?'
                self.cursor.execute(sql_unnest, (child,))
                self.conn.commit()
                print('All parents removed from note')
    
    
    def add_note(self, description, status_id, due, parent_id, longEntryFormat):
        if longEntryFormat:
            description = self.long_entry_note('')
        sql = 'INSERT INTO Notes (description, status_id, due) VALUES (?, ?, ?)'
        self.cursor.execute(sql, (description, status_id, due))
        self.conn.commit()
        print('Added note number: ' + str(self.cursor.lastrowid))
        self.nest_parent_child(parent_id, self.cursor.lastrowid)
    
    def edit_note(self, description, status_id, due, note_id, parent_id, longEntryFormat):
        sql_old = 'SELECT * FROM Notes where notes_id = ?'
        self.cursor.execute(sql_old, (str(note_id),))
        row = self.cursor.fetchone()
        if longEntryFormat:
            description = self.long_entry_note(str(row[3]))
        new_row = (
                row[0],
                status_id if status_id is not None else row[1], \
                due if due is not None else row[2], \
                description if description is not None else row[3], \
                row[4],
                datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                )
        sql = 'INSERT or REPLACE into Notes VALUES (?, ?, ?, ?, ?, ?)'
        self.cursor.execute(sql, new_row)
        self.conn.commit()
        print('Edited note number: ' + str(self.cursor.lastrowid))
        self.nest_parent_child(parent_id, note_id)
    
    def valid_date(self, s):
        try:
            return datetime.strftime(datetime.strptime(s, "%Y-%m-%d"), "%Y-%m-%d")
        except ValueError:
            msg = "not a valid date: {0!r}".format(s)
            raise argparse.ArgumentTypeError(msg)
    
    def parse_inputs(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbose", action = "store_true", help="increase output verbosity")
        parser.add_argument("-r", "--review", action ='store_true', help="View completed and cancelled items")
        parser.add_argument("-n", "--note", help="note, add/edit, in quotes if more than a word", nargs='?', const='<long-entry-note>', default=None)
        parser.add_argument("-e", "--edit", type=int, help="Edit existing note, argument: ID")
        parser.add_argument("-u", "--uncheck", type=int, help="Uncheck existing note, argument: ID")
        parser.add_argument("-c", "--check", type=int, help="Check existing note, argument: ID")
        parser.add_argument("-l", "--less", type=int, help="Display whole note to `less` [ID]")
        parser.add_argument("-o", "--order", type=str, choices=['nested', 'flat'], help="order to print note summary, if missing defaults to default setting", default = 'nested')
        parser.add_argument("-s", "--status", type=int, choices=[1, 2, 3, 4, 5], help="set status to 1=plain note, 2=unchecked, 3=checked, 4=cancelled")
        parser.add_argument("-d", "--date", help="Key Date - format YYYY-MM-DD", type=self.valid_date, nargs='?', const='0001-01-01', default=None)
        parser.add_argument("--rm", type=int, help="remove ID or list of IDs")
        parser.add_argument("-p", "--parent", nargs='?', const=0, default=None, type=int, help="Assign parent by note id, 0 or blank to remove all, -id to remove specific id")
        parser.add_argument("--code", action = "store_true", help="Open python code for development")
        parser.add_argument("--readme", action = "store_true", help="Open README.md for editing")
        args = parser.parse_args()
        self.args = args if args else ''
    
    def main(self):
        args = self.args
        if args.code:
            subprocess.call([self.EDITOR, os.path.join(self.JOT_DIR, 'jot.py')])
        elif args.readme:
            subprocess.call([self.EDITOR, os.path.join(self.JOT_DIR, 'README.md')])
        elif args.note is not None or args.edit is not None or args.status is not None or args.date is not None:
            self.input_note(description=args.note, status_id=args.status, due=args.date, note_id=args.edit, parent_id=args.parent)
        elif args.uncheck is not None:
            self.input_note(description=None, status_id=2, due=None, note_id=args.uncheck, parent_id=None)
        elif args.check is not None:
            self.input_note(description=None, status_id=3, due=None, note_id=args.check, parent_id=None)
        elif args.rm is not None:
            self.remove_note(args.rm)
        elif args.less is not None:
            self.print_note(args.less)
        elif args.verbose:
            self.print_notes(mode = args.order, status_show = (None,1,2,3,4,5))
        elif args.review:
            self.print_notes(mode = args.order, status_show = (3,4))
        else: # if no options, show active notes
            self.print_notes(mode = args.order, status_show = (None,1,2,5))
    
if __name__ == "__main__":
    jot = Jot()

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
