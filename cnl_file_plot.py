#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Copyright (c) 2015,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# This code is provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock

import matplotlib
import matplotlib.pyplot as plt
import os
import copy

from cnl_library import CNLParser, calc_ema, merge_lists, pretty_json, get_common_base_time, get_base_times
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
    legend_outside = False   # TODO make no legend and legend outside possible
    alpha = args.opacity if args.transparent_net else 1.0
    smooth = args.smooth_net

    # axes
    ax.set_ylim(top=args.net_scale)
    #ax.set_ylabel('Throughput (Bit/s)', fontsize=layout.fontsize.axis_labels)  ## TODO make fontsize choosable
    ax.set_ylabel('Throughput (Bit/s)')
    ax.set_xlabel('Time (s)')

    cnl_plot.plot(ax, cnl_file.x_values, cnl_file.cols, cnl_file.net_col_names, cnl_file.net_col_labels, alpha,
                  color=args.color, ema_only=True if smooth else False, smooth=smooth)

    # Legend
    if ( args.legend_pos != None ):
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





def plot(subplot_args, base_times=0):
    """
    [base_times] can either be a single nummer,
        this is treated as common base time for all subplots
        or a list
        with the individual base times (same order as args.files)

    """

    fig, ax = plt.subplots()
    i=0
    current_base_time = base_times   # makes sense if a common base_time is used

    for args in subplot_args:

        nics, nic_fields = net_fields_to_plot(args)

        ## Plot all files (with a common base time)
        #
        for filename in args.files:
            cnl_file = cnl_plot.parse_cnl_file(filename, nic_fields, nics)

            # if individual base_times are used, get the next one
            if isinstance(base_times, list):
                current_base_time = base_times[i]
                i += 1

            ## show some output
            print( filename )
            #print( pretty_json(cnl_file.get_general_header()) )
            #print()

            prepare_x_values(cnl_file)
            cnl_file.x_values = [ x - current_base_time for x in cnl_file.x_values ]


            ## * Plot *
            plot_net(ax, cnl_file, args)



    ## Format tick labels
    set_tick_labels(ax, False, True)




    ## output ##

    args = subplot_args[0]

    # Show / hardcopy plot
    if ( args.output == "live" ):
        #plt.title(filename)
        plt.show()
    else:
        ## output-filename is given explicitly
        if ( args.output_filename ):
            filename = args.output_filename
        ## otherwise, the original filename is used (with adapted filename extension)
        else:
            filename = args.files[0]

        ## if output_dir is given, strip the original path from the filename (if there is any)
        if ( args.output_dir ):
            os.makedirs(args.output_dir, exist_ok=True)
            out_filename = args.output_dir + "/" + os.path.basename(filename) #+ "." + args.output
        else:
            out_filename = filename #+ "." + args.output

        ## replace filename extension to the output format
        out_filename = os.path.splitext(out_filename)[0] + "." + args.output

        ## * save file *
        plt.savefig(out_filename, format=args.output)
        print(out_filename)







def merge_args(sub_args, args):
    """
      merges [sub_args] over [args] into [merged_args]:

        For every element that exist in both, the one from [sub_args] is used
    """
    merged_args = copy.copy(args)
    merged_args.subplots = None

    merged_args_dict = merged_args.__dict__
    sub_args_dict = sub_args.__dict__


    for key in sub_args_dict:
        #print( key, sub_args_dict[key] )

        if ( sub_args_dict[key] != None ):
            merged_args_dict[key] = sub_args_dict[key]

    return merged_args



## MAIN ##
if __name__ == "__main__":

    ### Command line arguments

    import argparse
    import shlex

    ## NOTE: most args are copied from cnl_plot

    DEFAULT_OPACITY = 0.7
    DEFAULT_ALPHA = 0.1             # alpha for ema, the smaller the smoother
    DEFAULT_Y_RANGE = 1  # Gbit/s
    DEFAULT_X_MIN = -5.0
    DEFAULT_X_MAX = None



    ## These arguments can be given within a "--subplots"-argument as well as when "--subplots" isn't used at all
    def add_subplot_args(parser):
        ## NOTE: The merging algorithm could get confused, if arguments with default-values are put in here!
        #    (Maybe "nargs='?'" can be used in this case...)

        parser.add_argument("files", nargs='*')
        #parser.add_argument("files")

        ## make it pretty
        parser.add_argument("-s", "--send-only", action="store_true")
        parser.add_argument("-r", "--receive-only", action="store_true")
        parser.add_argument("--nics", nargs='*')
        parser.add_argument("-nl", "--nic-labels", nargs='*')

        parser.add_argument("-c", "--color", type=str, nargs='*',
                            help="see: http://matplotlib.org/api/colors_api.html")


    ## These arguments can't be given within "--subplots"
    def add_unique_args(parser):
        parser.add_argument("-ref", "--reference-files", nargs='+', default=list(),
                            help="These files will be used to find a common base time, but will not be plotted.")

        parser.add_argument("-nsc", "--net-scale", type=float, default=DEFAULT_Y_RANGE,
                            help="[Gbit/s]; Default: 10")
        parser.add_argument("--opacity", type=float, default=DEFAULT_OPACITY,
                            help="Default: 0.7")
        parser.add_argument("-tn", "--transparent-net", action="store_true")
        ## TODO smoothing could be interesting for individual subplots, too..
        parser.add_argument("-sn", "--smooth-net", nargs='?', const=DEFAULT_ALPHA, type=float,
                            metavar="ALPHA",
                            help = "Smooth transmission rates with exponential moving average. (Disabled by default. When specified without parameter: ALPHA=0.1)" )

        parser.add_argument("-o", "--output", default = "live",
                            help="Set output type. Choices: live, pdf, Default: live")

        parser.add_argument("-of", "--output-filename",
                    help="Sets the filename of output explicitly (helpful when subplots are used).")

        parser.add_argument("-d", "--output-dir")

        parser.add_argument("--rel-base-time", action="store_true",
                            help="Do NOT use a common base time, but begin every line at 0. (Do not in conjunction with --reference-files)")



        ## make it pretty
        parser.add_argument("--x-min", type=float, default=DEFAULT_X_MIN)
        parser.add_argument("--x-max", type=float, default=DEFAULT_X_MAX)

        parser.add_argument("-l", "--legend-pos", type=int,
                            help="see: http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.legend")


        ## subplots
        parser.add_argument("-sub", "--subplots", type=str, nargs='*',
                            help="Use this if you want to draw multiple plots into the same image. (Arguments must not start with '-'.)")


    # Create general parser
    parser = argparse.ArgumentParser()
    add_subplot_args(parser)
    add_unique_args(parser)

    args = parser.parse_args()

    ## adjust arguments
    args.net_scale *= 10**9  # --> multiply by 10**9 to get Gbit/s


    ## Subplots: Read the arguments given as argument to "--subplots" and merge the result
    subplot_args = list()
    subplot_args.append(args)


    if args.subplots:
        # Create subplot parser
        subplot_parser = argparse.ArgumentParser()
        add_subplot_args(subplot_parser)

        for subcmd in args.subplots:
            sub_argv = shlex.split(subcmd)
            sub_args = subplot_parser.parse_args(sub_argv)

            merged_args = merge_args(sub_args, args)

            subplot_args.append(merged_args)
            # XXX debug
            #print( sub_args )
            #print()
            #print( merged_args )




    ## Find common base time
    if ( not args.rel_base_time ):
        reference = list()
        reference.extend(args.reference_files)
        for args in subplot_args:
            reference.extend(args.files)

        base_time = get_common_base_time(reference)

    ## Rel base time, find a base-time for each plot
    else:
        reference = list()
#        reference.extend(args.reference_files)
        for args in subplot_args:
            reference.extend(args.files)

        base_time = get_base_times(reference)



    ### Plotting

    plot(subplot_args, base_time)


