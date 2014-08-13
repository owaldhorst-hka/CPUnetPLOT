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





def parse_cnl_file(filename):
    ## * Parse input file. *
    cnl_file = CNLParser(filename)


    ## Display header informations.
    print( cnl_file.get_type() )
    print( cnl_file.get_comment() )

    print( "CPUs: " + str(cnl_file.get_cpus()) )
    print( "NICs: " + str(cnl_file.get_nics()) )


    ## Prepare data for matplotlib

    #nics = cnl_file.get_nics()
    nics = ("eth1", "eth2")  ## XXX
    net_cols = list()
    nic_fields = [".send", ".receive"]
    for nic_name in nics:
        for nic_field in nic_fields:
            net_cols.append( nic_name + nic_field )

    cpu_cols = [ cpu_name + ".util" for cpu_name in cnl_file.get_cpus() ]

    cols = cnl_file.get_csv_columns()
    x_values = cols["end"]
    #print( cols )   ## XXX


    ## Augment cnl_file with processed data.
    cnl_file.cols = cols
    cnl_file.net_col_names = net_cols
    cnl_file.cpu_col_names = cpu_cols
    cnl_file.x_values = x_values

    return cnl_file




def plot_net(ax, x_values, cols, active_cols):
    ax.set_ylim(0,10**10)
    ax.set_ylabel('Throughput (Bit/s)')

    for col_name in active_cols:
        ax.plot(x_values , cols[col_name], label=col_name)
        ax.plot(x_values , calc_ema(cols[col_name], 0.2), label=col_name+" (ema)")

    ax.legend()


def plot_cpu(ax, x_values, cols, active_cols):
    ax.set_ylim(0,100)
    ax.set_ylabel('CPU util (%)')

    for col_name in active_cols:
        ax.plot(x_values , cols[col_name], label=col_name)
        #ax2.plot(x_values , calc_ema(cols[col_name], 0.2), label=col_name+" (ema)")

    ax.legend()




## MAIN ##
if __name__ == "__main__":

    ### DEMO:

    filename = sys.argv[1]
    print( filename )

    cnl_file = parse_cnl_file(filename)

    ## Plot with matplotlib.

    ## Create figure (window/file)
    fig = plt.figure()
    fig.canvas.set_window_title('CPUnetPlot')

    ## Draw comment on the figure (use absolute positioning).
    t = matplotlib.text.Text(10,10, "Comment: " + cnl_file.get_comment(), figure=fig)
    fig.texts.append(t)


    ## Prepare subplots
    ax_net = fig.add_subplot(211)
    ax_cpu = fig.add_subplot(212, sharex=ax_net)
    #ax_net = fig.add_subplot(111)  ## twin
    #ax_cpu = ax_net.twinx()      ## twin


    ## Plot
    plot_net(ax_net, cnl_file.x_values, cnl_file.cols, cnl_file.net_col_names)
    plot_cpu(ax_cpu, cnl_file.x_values, cnl_file.cols, cnl_file.cpu_col_names )

    plt.show()
