#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Copyright (c) 2014,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# This code is provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock


from io import StringIO

import json
import csv
import os


def human_readable_from_seconds(seconds):
    if ( seconds == 0 ):
        return "0"

    if ( seconds <= 5 ):
        return "{:.2}s".format(seconds)

    elif ( seconds <= 2*60 ):
        return "{}s".format(round(seconds))

    elif ( seconds <= 5*60 ):
        return "{}min {}s".format(round(seconds/60), round(seconds%60))

    elif ( seconds <= 2*60*60 ):
        return "{}min".format(round(seconds/60), round(seconds%60))

    else:
        return "{}h {}min".format(round(seconds/3600), round( (seconds/60)%60) )

def merge_lists(first, second):
    """
    Merges two lists alternately.

    E.g.:

    first = [1, 2]
    second = ["A", "B"]

    result = [1, "A", 2, "B"]
    """

    return [item for pair in zip(first, second) for item in pair]


## Exponential moving average
def calc_ema(values, alpha=0.2):
    ret = list()
    beta = 1 - alpha

    ## init
    it = iter(values)
    ema_value = float(next(it))
    ret.append(ema_value)

    ## loop
    for v in it:
        ema_value = alpha * float(v) + beta * ema_value
        ret.append(ema_value)

    return ret



def pretty_json(data):
    return json.dumps(data, sort_keys=True, indent=4)


## Helper functions for CNLParser -- but they could also be handy in other contexts.

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
    class WrongFileFormat_Exception(Exception):
        pass


    def __init__(self, filename):
        self.filename = filename
        #print (filename)

        if ( os.path.isdir(self.filename) ):
            raise self.WrongFileFormat_Exception()

        with open( self.filename ) as in_file:
            try:
                ## Check file format version.
                if ( not in_file.readline() == "%% CPUnetLOGv1\n" ):
                    raise self.WrongFileFormat_Exception()

                ## Read JSON header.
                self.header = read_header(in_file)

                ## Read CSV "header"
                csv_reader = csv.reader( cnl_slice(in_file, "%% Begin_Body", "%% End_Body"), skipinitialspace=True )
                self.csv_header = next(csv_reader)
                self.csv_index = create_csv_index(self.csv_header)
            except UnicodeDecodeError:
                raise self.WrongFileFormat_Exception()


    def get_csv_iterator(self, fields=None):
        """
        Returns an iterator to get the csv-values line by line.

        @param fields [list] Only the "columns" specified in |fields| are included in the returned list (in that order).
                      [None] All "columns" are included (order defined by |self.csv_header|.
        """

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

            ## TODO convert every field to float..?


            ## Yield line by line.
            for line in csv_reader:
                if ( not indices ):
                    #yield line
                    yield [ float( v ) for v in line ]
                else:
                    #yield [ line[ind] for ind in indices ]
                    yield [ float( line[ind] ) for ind in indices ]


    def get_csv_columns(self, fields=None):
        """
        Returns a dictionary holding the CSV values grouped into columns.

        Dict-keys correspond to |self.csv_header|, if |fields| is set only the specified columns are included.
        """

        ## TODO should we really use "get_..." for an I/O and computation intensive function..?

        if ( fields ):
            field_names = fields
        else:
            field_names = self.csv_header

        num_cols = len(field_names)


        ## Create a list for each column.
        cols = [ list() for i in range(num_cols) ]

        ## Read all csv lines and put the values in the corresponding columns,
        for line in self.get_csv_iterator(fields):
            for i in range(num_cols):
                cols[i].append( line[i] )


        ## Create output dictionary.
        ret = dict()
        for i in range(num_cols):
            ret[ field_names[i] ] = cols[i]

        return ret


    ## Convenience functions ##

    def get_json_header(self):
        return self.header

    def print_json_header(self):
        print( json.dumps(self.header, sort_keys=True, indent=4) )

    def get_csv_index_of(self, field_name):
        return self.csv_index[field_name]

    def get_csv_indices_of(self, field_names):
        return [ self.get_csv_index_of(name) for name in field_names ]

    # Specific getters:

    def get_general_header(self):
        return self.header["General"]

    def get_type(self):
        return self.header["General"]["Type"]

    def get_comment(self):
        return self.header["General"]["Comment"]

    def get_cpus(self):
        return self.header["ClassDefinitions"]["CPU"]["Siblings"]

    def get_nics(self):
        return self.header["ClassDefinitions"]["NIC"]["Siblings"]

    def get_sysinfo(self):
        return self.header["General"]["SystemInfo"]

    def get_hostname(self):
        try:
            return self.get_sysinfo()["hostname"]
        except KeyError:
            return "(unknown)"

    def get_environment(self):
        return self.header["General"]["Environment"]

    def get_human_readable_date(self):
        return self.header["General"]["Date"][0]

    def get_machine_readable_date(self):
        return self.header["General"]["Date"][1]


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
