#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
from io import StringIO

import json
import csv



def cnl_slice(file, start_delimiter, end_delimiter):

    ## Find beginning
    for line in file:
        if ( line.startswith(start_delimiter) ):
            break

    ## Skip comments and quit on end
    for line in file:
        if ( line.startswith(end_delimiter) ):
            return

        # skip empty or commented lines
        if ( not line or line[0] == "%" or line[0] == "#" ):
            continue

        yield line





def read_header(f):
    str_io = StringIO()

    for line in cnl_slice(f, "%% Begin_Header", "%% End_Header"):
        str_io.write(line)

    str_io.seek(0)
    header = json.load( str_io )

    return header






## MAIN ##
if __name__ == "__main__":

    filename = sys.argv[1]
    print( filename )

    with open( filename ) as in_file:
        assert( in_file.readline() == "%% CPUnetLOGv1\n" )

        header = read_header(in_file)
        print( json.dumps(header, sort_keys=True, indent=4) )  ## XXX

        print ("///")
        print()

        for l in csv.reader( cnl_slice(in_file, "%% Begin_Body", "%% End_Body") ):
            print( l )
            pass




