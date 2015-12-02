#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Copyright (c) 2014,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# This code is provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock

import matplotlib
import matplotlib.pyplot as plt
import os

from cnl_library import CNLParser, calc_ema, merge_lists, pretty_json, get_common_base_time
import cnl_plot
import plot_ticks

## Workaround: "pdf-presenter-console" needs this, otherwise no text is displayed at all.
matplotlib.rc('pdf', fonttype=42)



## TODO the following functions should be shared among cnl_plot and this file

def prepare_x_values(cnl_file, plateau=True):
    if ( plateau ):
        cnl_file.x_values = merge_lists( cnl_file.cols["begin"], cnl_file.cols["end"] )
    else:
        cnl_file.x_values = cnl_file.cols["end"]


def net_fields_to_plot(args):

    # send/ receive
    if ( args.send_only ):
        nic_fields = ["send"]
    elif ( args.receive_only ):
        nic_fields = ["receive"]
    else:
        nic_fields = ["send", "receive"]


    # select nics (and optionally name them properly)
    if ( args.nics ):
        if ( args.nic_labels ):
            nics = dict(zip(args.nics, args.nic_labels))
        else:
            nics = dict(zip(args.nics, args.nics))
    else:
        nics = None

    return nics, nic_fields


def set_tick_labels( ax, x_minutes=True, adapt_net_yticks=True ):
    if ( x_minutes ):
        ax.xaxis.set_major_locator( plot_ticks.TimeLocator() )
        ax.xaxis.set_major_formatter( matplotlib.ticker.FuncFormatter(plot_ticks.format_xticks_minutes) )
    if ( adapt_net_yticks ):
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(plot_ticks.format_yticks))



#######



## NOTE: based on corresponding function in cnl_plot
#
def plot_net(ax, cnl_file, args):
    # parameters
    legend_outside = False
    alpha = args.opacity if args.transparent_net else 1.0
    smooth = args.smooth_net

    # axes
    ax.set_ylim(top=args.net_scale)
    #ax.set_ylabel('Throughput (Bit/s)', fontsize=layout.fontsize.axis_labels)
    ax.set_ylabel('Throughput (Bit/s)')
    ax.set_xlabel('Time (s)')

    cnl_plot.plot(ax, cnl_file.x_values, cnl_file.cols, cnl_file.net_col_names, cnl_file.net_col_labels, alpha,
                  color=args.color, ema_only=True if smooth else False, smooth=smooth)

    # Legend
    if ( legend_outside ):
        offset = matplotlib.transforms.ScaledTranslation(0, -20, matplotlib.transforms.IdentityTransform())
        trans = ax.transAxes + offset

        l = ax.legend( loc='upper left', bbox_to_anchor=(0, 0), ncol=int(len(cnl_file.net_col_names)/2),
                      bbox_transform = trans,
                      fancybox=False, shadow=False#,
                      #fontsize=layout.fontsize.legend
                      )
    else:
        l = ax.legend(loc=args.legend_pos)


    ax.set_xlim(xmin=args.x_min)
    ax.set_xlim(xmax=args.x_max)



def plot(cnl_file, args):
    fig, ax = plt.subplots()

    plot_net(ax, cnl_file, args)


    ## Format tick labels
    set_tick_labels(ax, False, True)


    # Show / hardcopy plot
    if ( args.output == "live" ):
        #plt.title(filename)
        plt.show()
    else:
        if ( args.output_dir ):
            os.makedirs(args.output_dir, exist_ok=True)
            out_filename = args.output_dir + "/" + os.path.basename(filename) #+ "." + args.output
        else:
            out_filename = filename #+ "." + args.output

        out_filename = os.path.splitext(out_filename)[0] + "." + args.output

        plt.savefig(out_filename, format=args.output)
        print(out_filename)






## MAIN ##
if __name__ == "__main__":

    ## Command line arguments
    import argparse

    ## NOTE: most args are copied from cnl_plot

    DEFAULT_OPACITY = 0.7
    DEFAULT_ALPHA = 0.1             # alpha for ema, the smaller the smoother
    DEFAULT_Y_RANGE = 1  # Gbit/s
    DEFAULT_X_MIN = -5.0
    DEFAULT_X_MAX = None

    parser = argparse.ArgumentParser()

    # NOTE: currently only one file is supported...
    parser.add_argument("files", nargs='+')

    parser.add_argument("-ref", "--reference-files", nargs='+', default=list(),
                        help="These files will be used to find a common base time, but will no be plotted.")

    parser.add_argument("-nsc", "--net-scale", type=float, default=DEFAULT_Y_RANGE,
                        help="[Gbit/s]; Default: 10")
    parser.add_argument("--opacity", type=float, default=DEFAULT_OPACITY,
                        help="Default: 0.7")
    parser.add_argument("-tn", "--transparent-net", action="store_true")
    parser.add_argument("-sn", "--smooth-net", nargs='?', const=DEFAULT_ALPHA, type=float,
                        metavar="ALPHA",
                        help = "Smooth transmission rates with exponential moving average. (Disabled by default. When specified without parameter: ALPHA=0.1)" )

    parser.add_argument("-o", "--output", default = "live",
                        help="Set output type. Choices: live, pdf, Default: live")

    parser.add_argument("-d", "--output-dir")



    ## make it pretty
    parser.add_argument("-s", "--send-only", action="store_true")
    parser.add_argument("-r", "--receive-only", action="store_true")
    parser.add_argument("--nics", nargs='*')
    parser.add_argument("-nl", "--nic-labels", nargs='*')

    parser.add_argument("--x-min", type=float, default=DEFAULT_X_MIN)
    parser.add_argument("--x-max", type=float, default=DEFAULT_X_MAX)

    parser.add_argument("-l", "--legend-pos", type=int, default=0,
                        help="see: http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.legend")

    parser.add_argument("-c", "--color", type=str, nargs='*',
                        help="see: http://matplotlib.org/api/colors_api.html")


    args = parser.parse_args()

    ## process argiments
    args.net_scale *= 10**9  # --> multiply by 10**9 to get Gbit/s

    nics, nic_fields = net_fields_to_plot(args)


    ### Preparations
    reference = list(args.files)
    reference.extend(args.reference_files)
    common_base_time = get_common_base_time(reference)



    ## Plot all files (with a common base time)
    #
    for filename in args.files:
        cnl_file = cnl_plot.parse_cnl_file(filename, nic_fields, nics)

        ## show some output
        print( filename )
        print( pretty_json(cnl_file.get_general_header()) )
        print()

        prepare_x_values(cnl_file)
        cnl_file.x_values = [ x - common_base_time for x in cnl_file.x_values ]




        ### Plotting

        plot(cnl_file, args)

