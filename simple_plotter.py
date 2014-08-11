#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import matplotlib

from cnl_library import CNLParser


## MAIN ##
if __name__ == "__main__":

    ### DEMO:

    filename = sys.argv[1]
    print( filename )

    ## * Parse input file. *
    cnl_file = CNLParser(filename)


    ## Display header informations.
    print( cnl_file.get_type() )

    print( "CPUs: " + str(cnl_file.get_cpus()) )
    print( "NICs: " + str(cnl_file.get_nics()) )

    ## Display some csv/data fields.
    names = None
    names = ["eth0.send", "eth0.receive"]
    print( names )

    for x in cnl_file.get_csv_iterator(names):
        print( ", ".join(x) )
