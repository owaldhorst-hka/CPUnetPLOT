#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os

from cnl_library import CNLParser
from collections import defaultdict, deque


def list_files_in_cur_dir():
    raw_list = os.listdir()
    no_invisible = filter(lambda filename: not filename.startswith("."), raw_list)

    return sorted( no_invisible )


def get_begin(cnl_file):
    return cnl_file.get_general_header()["Date"][1]

def are_close(cnl_file1, cnl_file2):
    t1 = get_begin(cnl_file1)
    t2 = get_begin(cnl_file2)

    return abs(t1 - t2) < 2


def find_match(cnl_file, list_of_files):
    for f in list_of_files:
        if ( are_close(cnl_file, f) ):
            list_of_files.remove(f)
            return f

    return None


## MAIN ##
if __name__ == "__main__":
    import sys

    if ( len(sys.argv) > 1 ):
        filenames = sorted( sys.argv[1:] )
    else:
        filenames = list_files_in_cur_dir()




    cnl_files = defaultdict(deque)

    ## Parse files and store them in a dict (of lists) according to their hostname.
    for filename in filenames:
        cnl_file = CNLParser(filename)
        hostname = cnl_file.get_hostname()
        cnl_files[hostname].append( cnl_file )


    ## Match.
    hostnames = sorted( cnl_files.keys() )
    left_files = cnl_files[hostnames[0]]
    right_files = cnl_files[hostnames[1]]

    for left_file in left_files:
        matching_file = find_match(left_file, right_files)

        if ( matching_file ):
            print( "{}  {}".format(left_file.filename, matching_file.filename) )
        else:
            print( left_file.filename )


    ## Print left over right files.
    if ( len(right_files) > 0 ):
        print()
        for f in right_files:
            print( f.filename )




