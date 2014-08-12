#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import matplotlib.pyplot as plt

from cnl_library import CNLParser, calc_ema


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
    print( cnl_file.get_comment() )

    print( "CPUs: " + str(cnl_file.get_cpus()) )
    print( "NICs: " + str(cnl_file.get_nics()) )



    ## Prepare data for matplotlib

    #nics = cnl_file.get_nics()
    nics = ("eth1", "eth2")
    net_cols = list()
    nic_fields = [".send", ".receive"]
    for nic_name in nics:
        for nic_field in nic_fields:
            net_cols.append( nic_name + nic_field )

    cpu_cols = [ cpu_name + ".util" for cpu_name in cnl_file.get_cpus() ]

    cols = cnl_file.get_csv_columns()
    x_values = cols["end"]
    #print( cols )   ## XXX


    ## Plot with matplotlib.

    # Twin plot
    #   (see http://matplotlib.org/examples/api/two_scales.html)

    #fig, ax1 = plt.subplots()  ## twin
    fig, axes = plt.subplots(2, 1, sharex=True)
    (ax1, ax2) = axes

    #plt.title( cnl_file.get_comment() )
    plt.figtext(0.01, 0.02, "Comment: " + cnl_file.get_comment())
    #plt.figtext(0.01, 0.99, "Hallo ;-)")


    plt.ylim(0,10**10)
    ax1.set_ylabel('Throughput (Bit/s)')

    for col_name in net_cols:
        ax1.plot(x_values , cols[col_name], label=col_name)
        ax1.plot(x_values , calc_ema(cols[col_name], 0.2), label=col_name+" (ema)")

    ax1.legend()

    #ax2 = ax1.twinx()      ## twin
    plt.ylim(0,100)
    ax2.set_ylabel('CPU util (%)')

    for col_name in cpu_cols:
        ax2.plot(x_values , cols[col_name], label=col_name)
        #ax2.plot(x_values , calc_ema(cols[col_name], 0.2), label=col_name+" (ema)")

    ax2.legend()

    plt.show()
