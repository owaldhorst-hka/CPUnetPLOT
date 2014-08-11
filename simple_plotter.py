#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import matplotlib.pyplot as plt

from cnl_library import CNLParser


def append_twice(base_list, extend_list):
    if ( isinstance(extend_list, list) ):
        for x in extend_list:
            base_list.append(x)
            base_list.append(x)
    else:
        base_list.append(extend_list)
        base_list.append(extend_list)



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
    names = ["begin", "end", "eth0.send", "eth0.receive"]
    print( names )

    ### Prepare lists for matplotlib.
    #x_values = list()
    #y1_values = list()
    #y2_values = list()
    #for x in cnl_file.get_csv_iterator(names):
        #x_values.extend( x[0:2] )

        #append_twice( y1_values, x[2] )
        #append_twice( y2_values, x[3] )


    ## Prepare lists for matplotlib.
    x_values = list()
    y1_values = list()
    y2_values = list()
    for x in cnl_file.get_csv_iterator(names):
        x_values.append( x[1] )

        y1_values.append( x[2] )
        y2_values.append( x[3] )

    ## Plot with matplotlib.

    print( x_values )
    print( y1_values )
    print( y2_values )

    plt.plot(x_values, y1_values)
    plt.plot(x_values, y2_values)
    #plt.ylabel('some numbers')
    plt.show()
