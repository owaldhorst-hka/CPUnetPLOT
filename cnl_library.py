#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from io import StringIO

import json
import csv


## TODO rename file / move to other file..


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



def create_csv_index(csv_header):
    ## Create an index that maps csv_header names to tuple indices.
    csv_field_index = dict()
    i = 0
    for field in csv_header:
        csv_field_index[field] = i
        i += 1

    return csv_field_index



def read_header(f):
    str_io = StringIO()

    for line in cnl_slice(f, "%% Begin_Header", "%% End_Header"):
        str_io.write(line)

    str_io.seek(0)
    header = json.load( str_io )

    return header



class CNLParser:
    def __init__(self, filename):
        self.filename = filename

        with open( self.filename ) as in_file:
            ## Check file format version.
            assert( in_file.readline() == "%% CPUnetLOGv1\n" )

            ## Read JSON header.
            self.header = read_header(in_file)

            ## Read CSV "header"
            csv_reader = csv.reader( cnl_slice(in_file, "%% Begin_Body", "%% End_Body"), skipinitialspace=True )
            self.csv_header = next(csv_reader)
            self.csv_index = create_csv_index(self.csv_header)


    def get_json_header(self):
        return self.header


    def get_csv_iterator(self, fields=None):
        indices = None

        ## Only return selected columns (if the |fields| option is set).
        if ( fields ):
            indices = self.get_csv_indices_of(fields)


        ## Read from file.
        with open( self.filename ) as in_file:
            ## Find start of the CSV part.
            csv_reader = csv.reader( cnl_slice(in_file, "%% Begin_Body", "%% End_Body"), skipinitialspace=True )
            csv_header = next(csv_reader)
            assert( csv_header == self.csv_header )

            ## Yield line by line.
            for line in csv_reader:
                if ( not indices ):
                    yield line
                else:
                    yield [ line[ind] for ind in indices ]


    ## Convenience functions ##

    def print_json_header(self):
        print( json.dumps(self.header, sort_keys=True, indent=4) )

    def get_csv_index_of(self, field_name):
        return self.csv_index[field_name]

    def get_csv_indices_of(self, field_names):
        return [ self.get_csv_index_of(name) for name in field_names ]

    # Specific getters:

    def get_type(self):
        return self.header["General"]["Type"]

    def get_cpus(self):
        return self.header["ClassDefinitions"]["CPU"]["Siblings"]

    def get_nics(self):
        return self.header["ClassDefinitions"]["NIC"]["Siblings"]



## MAIN ##
if __name__ == "__main__":

    ### DEMO:
    import sys

    filename = sys.argv[1]
    print( filename )

    ## * Parse input file. *
    cnl_file = CNLParser(filename)


    ## Display header informations.
    print( cnl_file.get_type() )
    print( json.dumps(cnl_file.get_json_header(), sort_keys=True, indent=4) )

    print( "CPUs: " + str(cnl_file.get_cpus()) )
    print( "NICs: " + str(cnl_file.get_nics()) )

    ## Display some csv/data fields.
    names = None
    names = ["eth0.send", "eth0.receive"]
    print( names )

    for x in cnl_file.get_csv_iterator(names):
        print( ", ".join(x) )
