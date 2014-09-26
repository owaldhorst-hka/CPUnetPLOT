#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import matplotlib
import matplotlib.ticker as ticker

from cnl_library import CNLParser, calc_ema, merge_lists, pretty_json, human_readable_from_seconds
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



## TODO Maybe this class should be moved to another file..
class TimeLocator(matplotlib.ticker.Locator):
    """
    Place the ticks to be nice seconds/minutes/hours values.
    """

    def __init__(self, numticks=5):
        #self._base = Base(base)
        self.numticks = numticks

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)


    def _shrink_to_a_multiple_of(self, origin, divisor, maxdiff=0):
        diff = origin % divisor

        # BRANCH: external max-diff
        if ( maxdiff > 0 ):
            if ( diff <= maxdiff ):
                origin -= diff

        # BRANCH: automatic max-diff
        elif ( diff < origin * 0.2 ):
            origin -= diff

        return origin


    def _make_nice(self, value, maxdiff=0):
        ## TODO Find out if this approach gets the desired results...

        ## TODO quit loop after it worked?, actually make a loop
        value = self._shrink_to_a_multiple_of(value, 60*60, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 60*30, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 60*15, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 60*10, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 60*5, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 60, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 30, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 15, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 10, maxdiff)
        value = self._shrink_to_a_multiple_of(value, 5, maxdiff)

        return value


    def tick_values(self, vmin, vmax):
        if vmax < vmin:
            vmin, vmax = vmax, vmin


        ## Find a nice stepping for the ticks.

        diff = vmax-vmin

        # If the scale starts almost with 0, concentrate on the positive side.
        if ( vmin <= 0 and 0 < vmax and vmin*-1 < diff / (2*self.numticks)):
            diff = vmax - 0

        step = diff / self.numticks
        nice_step = self._make_nice(step)


        ## Place the ticks.

        locs = list()

        # Tick »0« if it is in range
        if ( vmin <= 0 and 0 < vmax ):
            base = 0
        else:
            base = self._make_nice(vmin)  ## TODO make nice with +, instead - ?

        # ticks to the right
        pos = base
        while ( pos <= vmax ):
            locs.append(pos)
            pos += nice_step

        # ticks to the left
        pos = base - nice_step
        while ( pos >= vmin ):
            locs.append(pos)
            pos -= nice_step


        ## Add an additional (still nice) max label, if appropriate.
        additional_max_tick = self._make_nice(vmax, 0.25 * nice_step)
        if ( additional_max_tick - max(locs) >= 0.5 * nice_step ):
            locs.append(additional_max_tick)


        return self.raise_if_exceeds(locs)


    #def view_limits(self, dmin, dmax):
        #"""
        #Set the view limits to the nearest multiples of base that
        #contain the data
        #"""
        #vmin = self._base.le(dmin)
        #vmax = self._base.ge(dmax)
        #if vmin == vmax:
            #vmin -= 1
            #vmax += 1

        #return mtransforms.nonsingular(vmin, vmax)







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
    ax.set_ylabel('Throughput (Bit/s)', fontsize=args.axis_fontsize)

    plot(ax, cnl_file.x_values, cnl_file.cols, cnl_file.net_col_names, alpha,
         ema_only=True if smooth else False, smooth=smooth)

    # Legend
    if ( legend_outside ):
        offset = matplotlib.transforms.ScaledTranslation(0, -20, matplotlib.transforms.IdentityTransform())
        trans = ax.transAxes + offset

        l = ax.legend( loc='upper left', bbox_to_anchor=(0, 0), ncol=int(len(cnl_file.net_col_names)/2),
                      bbox_transform = trans,
                      fancybox=False, shadow=False, fontsize=args.legend_fontsize)
    else:
        l = ax.legend(loc=0)


def plot_cpu(ax, cnl_file, args):
    # parameters
    legend_outside = True
    alpha = args.opacity if args.transparent_cpu else 1.0
    smooth = args.smooth_cpu

    # axes
    ax.set_ylim(0,100)
    ax.set_ylabel('CPU util (%)', fontsize=args.axis_fontsize)

    # * plot *
    plot(ax, cnl_file.x_values, cnl_file.cols, cnl_file.cpu_col_names, alpha,
         ema_only=True if smooth else False, smooth=smooth)

    # Legend
    if ( legend_outside ):
        offset = matplotlib.transforms.ScaledTranslation(0, -20, matplotlib.transforms.IdentityTransform())
        trans = ax.transAxes + offset

        l = ax.legend( loc='upper left', bbox_to_anchor=(0, 0), ncol=int(len(cnl_file.cpu_col_names)/2),
                      bbox_transform = trans,
                      fancybox=False, shadow=False, fontsize=args.legend_fontsize)
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

    ## font size (there is no cmd-line option for this, [yet?])
    args.axis_fontsize = 12
    args.legend_fontsize = 12


    ## set implicated options
    # --transparent
    if ( args.transparent ):
        args.transparent_cpu = True
        args.transparent_net = True

    # --publication
    if ( args.publication ):
        args.no_comment = True
        args.axis_fontsize = 20
        args.legend_fontsize = 16

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

        # shift x-values  ## TODO find a single base-time for all files?
        #base_time = min_max[0]
        base_time = cnl_file.get_machine_readable_date()
        cnl_file.x_values = [ x - base_time for x in cnl_file.x_values ]

        ## Plot
        plot_net(ax_net, cnl_file, args)
        plot_cpu(ax_cpu, cnl_file, args)

        old_ax_net = ax_net
        old_ax_cpu = ax_cpu


    ## If we have only one input file, plot CPU area charts.
    if ( num_files == 1 ):
        ax1 = fig.add_subplot(2, num_cols, 2, sharex=old_ax_net, sharey=old_ax_cpu)
        ax2 = fig.add_subplot(2, num_cols, 4, sharex=ax_net, sharey=old_ax_cpu)

        plot_top_cpus( cnl_file, args, (ax1, ax2), (0,1) )


    ## Subplot-Layout (margins)
    #  NOTE: This actually works great with a screen resolution of 1920x1200.
    #        Since all space here are in relative size, this might have to be adjusted for other screen resolutions.
    if ( args.publication ):
        ## TODO What about the fontsize? Only increase for slides, or for publication in general..?

        # Narrow layout for publications and presentations
        if ( num_files == 1 ):
            # CPU area charts
            #fig.subplots_adjust(left=0.03, wspace=0.15, right=0.93, top=0.97, hspace=0.3, bottom=0.08) ## small font size
            fig.subplots_adjust(left=0.04, wspace=0.15, right=0.92, top=0.97, hspace=0.3, bottom=0.09) ## large font, legend on the right
            #fig.subplots_adjust(left=0.04, wspace=0.15, right=0.99, top=0.97, hspace=0.3, bottom=0.09) ## large font, legend below
        else:
            # double plot
            #fig.subplots_adjust(left=0.03, wspace=0.15, right=0.99, top=0.97, hspace=0.3, bottom=0.08) ## small font size
            fig.subplots_adjust(left=0.04, wspace=0.15, right=0.99, top=0.97, hspace=0.3, bottom=0.09)
    else:
        # Regular layout (for good readability on screen)
        fig.subplots_adjust(left=0.1, wspace=0.2, right=0.9, top=0.92, hspace=0.4, bottom=0.12)



    ## TODO, maybe the TimeLocator can do this better? (see TimeLocator.view_limits)
    ## set min/max (remember: The x-axis is shared.)
    margin = max( (max_x - min_x) * 0.03, 10 )
    ax_net.set_xlim(min_x - margin - base_time, max_x + margin - base_time)  ## XXX Like that, it's the base-time from the latest file...


    ## Format tick labels TESTING
    def format_ticks(x, pos=None):
        return human_readable_from_seconds(float(x))
    ax_net.xaxis.set_major_formatter( ticker.FuncFormatter(format_ticks) )
    ax_net.xaxis.set_major_locator( TimeLocator() )


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
