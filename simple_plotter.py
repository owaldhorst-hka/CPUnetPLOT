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



    ## Prepare data for matplotlib

    net_cols = list()
    nic_fields = [".send", ".receive"]
    for nic_name in cnl_file.get_nics():
        for nic_field in nic_fields:
            net_cols.append( nic_name + nic_field )

    cpu_cols = [ cpu_name + ".util" for cpu_name in cnl_file.get_cpus() ]

    cols = cnl_file.get_csv_columns()
    x_values = cols["end"]
    print( cols )


    ## Plot with matplotlib.

    #for col_name in net_cols:
    for col_name in cpu_cols:
        plt.plot(x_values , cols[col_name], label=col_name)

    ## TODO twinx: http://matplotlib.org/examples/api/two_scales.html

    plt.legend()
    plt.show()
