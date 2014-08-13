#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import matplotlib
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

    ## Create figure (window/file)
    fig = plt.figure()

    ## Draw comment on the figure.
    t = matplotlib.text.Text(10,10, "Comment: " + cnl_file.get_comment(), figure=fig)
    fig.texts.append(t)

    #plt.title( cnl_file.get_comment() )
    #plt.figtext(0.01, 0.02, "Comment: " + cnl_file.get_comment())


    ax_net = fig.add_subplot(211)
    #ax_net = fig.add_subplot(111)  ## twin


    ax_net.set_ylim(0,10**10)
    ax_net.set_ylabel('Throughput (Bit/s)')

    for col_name in net_cols:
        ax_net.plot(x_values , cols[col_name], label=col_name)
        ax_net.plot(x_values , calc_ema(cols[col_name], 0.2), label=col_name+" (ema)")

    ax_net.legend()


    #ax_cpu = ax_net.twinx()      ## twin
    ax_cpu = fig.add_subplot(212, sharex=ax_net)
    ax_cpu.set_ylim(0,100)
    ax_cpu.set_ylabel('CPU util (%)')

    for col_name in cpu_cols:
        ax_cpu.plot(x_values , cols[col_name], label=col_name)
        #ax2.plot(x_values , calc_ema(cols[col_name], 0.2), label=col_name+" (ema)")

    ax_cpu.legend()

    plt.show()
