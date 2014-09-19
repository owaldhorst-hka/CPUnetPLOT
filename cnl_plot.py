#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import matplotlib

from cnl_library import CNLParser, calc_ema, merge_lists, pretty_json
from plot_cpu import plot_top_cpus


## matplotlib.use('QT4Agg')  # override matplotlibrc
import matplotlib.pyplot as plt


def append_twice(base_list, extend_list):
    if ( isinstance(extend_list, list) ):
        for x in extend_list:
            base_list.append(x)
            base_list.append(x)
    else:
        base_list.append(extend_list)
        base_list.append(extend_list)





def parse_cnl_file(filename, nic_fields = [".send", ".receive"]):
    ## * Parse input file. *
    cnl_file = CNLParser(filename)

    ## Prepare data for matplotlib

    #nics = cnl_file.get_nics()
    nics = ("eth1", "eth2")  ## XXX
    net_cols = list()
    for nic_name in nics:
        for nic_field in nic_fields:
            net_cols.append( nic_name + nic_field )

    cpu_cols = [ cpu_name + ".util" for cpu_name in cnl_file.get_cpus() ]
    #cpu_cols = [ cpu_name + ".irq" for cpu_name in cnl_file.get_cpus() ]   ## XXX

    cols = cnl_file.get_csv_columns()
    #x_values = cols["end"]
    #print( cols )   ## XXX


    ## Augment cnl_file with processed data.
    cnl_file.cols = cols
    cnl_file.net_col_names = net_cols
    cnl_file.cpu_col_names = cpu_cols
    #cnl_file.x_values = x_values

    return cnl_file


def get_min_max_x(cnl_file):
    return ( cnl_file.cols["begin"][0], cnl_file.cols["end"][-1] )


def plot(ax, x_values, cols, active_cols, alpha, **kwargs):
    #use_ema = kwargs.get("use_ema")
    ema_only = kwargs.get("ema_only")
    smooth = kwargs.get("smooth")

    for col_name in active_cols:
        data = cols[col_name]
        if ( len(x_values) == len(data)*2 ):
            data = merge_lists( data, data )

        # * plot *
        if ( not ema_only ):
            ax.plot(x_values , data, label=col_name, alpha=alpha)

        ## plot ema
        if ( ema_only and smooth ):
            ax.plot(x_values , calc_ema(data, smooth), label=col_name)


def plot_net(ax, cnl_file, args):
    # parameters
    legend_outside = True
    alpha = args.opacity if args.transparent_net else 1.0
    smooth = args.smooth_net

    # axes
    ax.set_ylim(0,10**10)
    ax.set_ylabel('Throughput (Bit/s)')

    plot(ax, cnl_file.x_values, cnl_file.cols, cnl_file.net_col_names, alpha,
         ema_only=True if smooth else False, smooth=smooth)

    # Legend
    if ( legend_outside ):
        offset = matplotlib.transforms.ScaledTranslation(0, -20, matplotlib.transforms.IdentityTransform())
        trans = ax.transAxes + offset

        l = ax.legend( loc='upper left', bbox_to_anchor=(0, 0), ncol=int(len(cnl_file.net_col_names)/2),
                      bbox_transform = trans,
                      fancybox=False, shadow=False)
    else:
        l = ax.legend(loc=0)


def plot_cpu(ax, cnl_file, args):
    # parameters
    legend_outside = True
    alpha = args.opacity if args.transparent_cpu else 1.0
    smooth = args.smooth_cpu

    # axes
    ax.set_ylim(0,100)
    ax.set_ylabel('CPU util (%)')

    # * plot *
    plot(ax, cnl_file.x_values, cnl_file.cols, cnl_file.cpu_col_names, alpha,
         ema_only=True if smooth else False, smooth=smooth)

    # Legend
    if ( legend_outside ):
        offset = matplotlib.transforms.ScaledTranslation(0, -20, matplotlib.transforms.IdentityTransform())
        trans = ax.transAxes + offset

        l = ax.legend( loc='upper left', bbox_to_anchor=(0, 0), ncol=int(len(cnl_file.cpu_col_names)/2),
                      bbox_transform = trans,
                      fancybox=False, shadow=False)
    else:
        l = ax.legend(loc=0)

    #ax.set_label("Testlabel")

    l.draggable(True)



class NameSuggestor:
    def __init__(self):
        self.date = list()
        self.hostname = list()

    def add(self, cnl_file):
        self.date.append( cnl_file.get_human_readable_date() )
        self.hostname.append( cnl_file.get_hostname() )

    def suggest_filename(self):
        print( "{}_{}".format( self.date[0], "_".join(self.hostname) )  ) ## XXX
        return "{}_{}".format( self.date[0], "_".join(self.hostname) )


## MAIN ##
if __name__ == "__main__":

    ## Command line arguments
    import argparse


    DEFAULT_OPACITY = 0.7
    DEFAULT_ALPHA = 0.1             # alpha for ema, the smaller the smoother

    parser = argparse.ArgumentParser()

    parser.add_argument("files", nargs='*')
    parser.add_argument("-tn", "--transparent-net", action="store_true")
    parser.add_argument("-tc", "--transparent-cpu", action="store_true")
    parser.add_argument("-t", "--transparent", action="store_true",
                        help="Implies --transparent-net and --transparent-cpu")
    parser.add_argument("--opacity", type=float, default=DEFAULT_OPACITY,
                        help="Default: 0.7")
    parser.add_argument("-nc", "--no-comment", action="store_true")
    parser.add_argument("-p", "--publication", action="store_true",
                        help="Reduces the margins so that the output is more suitable for publications and presentations. (Implies --no-comment)")

    parser.add_argument("-sc", "--smooth-cpu", nargs='?', const=DEFAULT_ALPHA, type=float,
                        metavar="ALPHA",
                        help = "Smooth CPU values with exponential moving average. (Disabled by default. When specified without parameter: ALPHA=0.1)" )

    ## XXX experimental..
    parser.add_argument("-sn", "--smooth-net", nargs='?', const=DEFAULT_ALPHA, type=float,
                        metavar="ALPHA",
                        help = "Smooth transmission rates with exponential moving average. (Disabled by default. When specified without parameter: ALPHA=0.1)" )


    # TODO make mutual exclusive
    parser.add_argument("-sr", "--send-receive", action="store_true",
                        help="Plots only outgoing data from the first file, and only incoming data from the second file. (If there's only one file, then the outgoing data is plotted.)")
    parser.add_argument("-rs", "--receive-send", action="store_true",
                        help="Like --send-receive, but the other way round.")

    ## TODO implement (maybe set as default)
    #parser.add_argument("-a", "--all-matches", action="store_true",
                        #help="Finds all matches current directory (or in --files, if specified) and plots them pairwise.")


    args = parser.parse_args()


    ## set implicated options
    # --transparent
    if ( args.transparent ):
        args.transparent_cpu = True
        args.transparent_net = True

    # --publication
    if ( args.publication ):
        args.no_comment = True


    num_files = len(args.files)
    name_suggestor = NameSuggestor()

    ## Create figure (window/file)
    fig = plt.figure()
    fig.canvas.set_window_title('CPUnetPlot')

    num_cols = 2

    min_x = None
    max_x = None

    old_ax_net = None
    old_ax_cpu = None
    for i in range(0, num_files):
        nic_fields = [".send", ".receive"]

        # only send/receive
        if ( args.send_receive ):
            ind = i % 2
            nic_fields = nic_fields[ind:ind+1]
        if ( args.receive_send ):
            ind = (i+1)%2
            nic_fields = nic_fields[ind:ind+1]


        ## Read file
        filename = args.files[i]
        cnl_file = parse_cnl_file(filename, nic_fields)
        name_suggestor.add(cnl_file)

        ## update min_x / max_x
        min_max = get_min_max_x(cnl_file)

        if ( not min_x or min_x > min_max[0] ):
            min_x = min_max[0]

        if ( not max_x or max_x < min_max[1] ):
            max_x = min_max[1]


        ## show some output
        print( filename )
        print( pretty_json(cnl_file.get_general_header()) )
        print()


        ## Plot with matplotlib.

        ## Draw comment on the figure (use absolute positioning).
        if ( not args.no_comment ):
            t = matplotlib.text.Text(10,10, "Comment: " + cnl_file.get_comment(), figure=fig)
            fig.texts.append(t)


        ## Prepare subplots
        ax_net = fig.add_subplot(2, num_cols, i+1, sharex=old_ax_net, sharey=old_ax_net)
        ax_cpu = fig.add_subplot(2, num_cols, i+num_cols+1, sharex=ax_net, sharey=old_ax_cpu)
        #ax_net = fig.add_subplot(111)  ## twin axis
        #ax_cpu = ax_net.twinx()        ## twin axis


        ## Prepare x_values
        plateau = True      ## XXX
        if ( plateau ):
            cnl_file.x_values = merge_lists( cnl_file.cols["begin"], cnl_file.cols["end"] )
        else:
            cnl_file.x_values = cnl_file.cols["end"]

        ## Plot
        plot_net(ax_net, cnl_file, args)
        plot_cpu(ax_cpu, cnl_file, args)

        old_ax_net = ax_net
        old_ax_cpu = ax_cpu


    ## If we have only one input file, plot CPU area charts.
    if ( num_files == 1 ):
        ax1 = fig.add_subplot(2, num_cols, 2, sharex=old_ax_net, sharey=old_ax_cpu)
        ax2 = fig.add_subplot(2, num_cols, 4, sharex=ax_net, sharey=old_ax_cpu)

        plot_top_cpus( cnl_file, (ax1, ax2), (0,1) )


    ## Subplot-Layout (margins)
    #  NOTE: This actually works great with a screen resolution of 1920x1200.
    #        Since all space here are in relative size, this might have to be adjusted for other screen resolutions.
    if ( args.publication ):
        # Narrow layout for publications and presentations
        if ( num_files == 1 ):
            # CPU area charts
            fig.subplots_adjust(left=0.03, wspace=0.15, right=0.93, top=0.97, hspace=0.3, bottom=0.08)
        else:
            # double plot
            fig.subplots_adjust(left=0.03, wspace=0.15, right=0.99, top=0.97, hspace=0.3, bottom=0.08)
    else:
        # Regular layout (for good readability on screen)
        fig.subplots_adjust(left=0.1, wspace=0.2, right=0.9, top=0.92, hspace=0.4, bottom=0.12)



    ## set min/max (remember: The x-axis is shared.)
    margin = max( (max_x - min_x) * 0.03, 10 )
    ax_net.set_xlim(min_x - margin, max_x + margin)



    ## Set the default format for the save-botton to PDF.
    try:
        fig.canvas.get_default_filetype = lambda: "pdf"
        suggested_name = "{}-plot.{}".format( name_suggestor.suggest_filename(), fig.canvas.get_default_filetype() )
        name_func = lambda: suggested_name
        fig.canvas.get_default_filename = name_func
    except:
        print( "[WARNING] Filename suggestion failed!" )

    ## maximize window
    try:
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
    except:
        pass

    # show plot
    plt.show()
