#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
from collections import defaultdict, deque

from cnl_library import CNLParser
from summary import LogAnalyzer, show_match


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



def merge_comments(left_file, right_file):
    if ( not right_file ):
        return left_file.get_comment()

    c1 = left_file.get_comment()
    c2 = right_file.get_comment()

    if ( c1.find(c2) >= 0 ):
        return c1

    if ( c2.find(c1) >= 0 ):
        return c2

    return c1 + " / " + c2



def print_line(left_file, right_file, long):
    out = ""

    if ( right_file ):
        out = "{}  {}".format(left_file.filename, right_file.filename)
    else:
        out = left_file.filename

    if ( long ):
        out += "   // "
        comm_offset = len(out)

        comments = merge_comments(left_file, right_file).split(";")
        out += comments[0]

        for c in comments[1:]:
            out += ";\n" + " "*comm_offset + c.strip()

    print( out )


def show_summary(left_file, right_file=None):
    ## BRANCH: No match -> fallback to show_brief()
    if ( not right_file ):
        log = LogAnalyzer(left_file)
        log.visualize_brief(args.environment)

    ## BRANCH: Match -> Display both next to each other.
    else:
        log_left = LogAnalyzer(left_file)
        log_right = LogAnalyzer(right_file)

        show_match(log_left, log_right, args.environment)


def show(left_file, right_file, long=False, summary=False):
    if ( summary ):
        show_summary(left_file, right_file)
        print()
    else:
        print_line(left_file, right_file, long)


## MAIN ##
if __name__ == "__main__":
    #import sys

    ## Command line arguments
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("files", nargs='*')
    parser.add_argument("-l", "--long", action="store_true")
    parser.add_argument("-s", "--summary", action="store_true")
    parser.add_argument("-e", "--environment", action='append', metavar="ENV",
                        help="Environment variable that should be displayed. (May be set multiple times.)")

    args = parser.parse_args()


    if ( args.files ):
        filenames = sorted( args.files )
    else:
        filenames = list_files_in_cur_dir()




    cnl_files = defaultdict(deque)

    ## Parse files and store them in a dict (of lists) according to their hostname.
    for filename in filenames:
        try:
            cnl_file = CNLParser(filename)
        except CNLParser.WrongFileFormat_Exception:
            print( "Skipping: {}".format(filename) )
            continue

        hostname = cnl_file.get_hostname()
        cnl_files[hostname].append( cnl_file )


    hostnames = sorted( cnl_files.keys() )

    ## BRANCH: Input from two hosts -> Matching.
    if ( len(hostnames) == 2 ):
        left_files = cnl_files[hostnames[0]]
        right_files = cnl_files[hostnames[1]]

        for left_file in left_files:
            matching_file = find_match(left_file, right_files)
            show(left_file, matching_file, args.long, args.summary)


        ## Print left over right files.
        if ( len(right_files) > 0 ):
            print()
            for f in right_files:
                show(f, None, args.long, args.summary)


    ## BRANCH: Only one (or more than two hosts) -> No matching.
    else:
        for h in hostnames:
            for f in cnl_files[h]:
                show(f, None, args.long, args.summary)



