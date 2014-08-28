# -*- coding:utf-8 -*-

from collections import defaultdict
from operator import itemgetter
from matplotlib import transforms
import numpy
import copy

from cnl_library import merge_lists


CPU_COLORS = defaultdict(lambda : "grey")
CPU_COLORS["usr"] = "green"
CPU_COLORS["system"] = "yellow"
CPU_COLORS["irq"] = "cyan"
CPU_COLORS["softirq"] = "magenta"
CPU_COLORS["util"] = "red"      ## XXX
CPU_COLORS["idle"] = "blue"     ## XXX


def _create_cpu_cols_by_util(cnl_file):
    """
    The actual creation of the "virtual top-cpus" is outsourced to this function:

    For each sample,

    first sort the CPUs by CPU utilization;

    then, for the top-n CPU (n from 1 to num_cpus),
    append the values of the cpu-utilization fields (usr, system, ...).

    Also, stores which CPU was the top-n CPU in the respective sample.
    """
    cpus = cnl_file.get_cpus()
    cpu_fields = cnl_file.get_json_header()["ClassDefinitions"]["CPU"]["Fields"]
    num_samples = len(cnl_file.cols["begin"])

    # init return list (of dicts of lists)
    top_cpus = list()
    for cpu in cpus:
        elem = dict()
        elem["name"] = list()
        for field in cpu_fields:
            elem[field] = list()

        top_cpus.append(elem)


    # Fill return list.
    for i in range(num_samples):
        cpu_utils = [ (cpu, cnl_file.cols[cpu + ".util"][i]) for cpu in cpus ]
        cpus_sorted_by_util = sorted( cpu_utils, key=itemgetter(1), reverse=True)

        for top_cpu, cur_cpu in zip(top_cpus, cpus_sorted_by_util):
            cpu_name = cur_cpu[0]

            top_cpu["name"].append(cpu_name)
            for field in cpu_fields:
                top_cpu[field].append( cnl_file.cols[cpu_name + "." + field][i] )

    return top_cpus



def plot_area_chart(ax, cnl_file, cols, legend_outside=True, legend_title=None):
    """
    Plots an area chart of the CPU utilization (usr, sys, ...).
    """

    cpu_fields = copy.copy( cnl_file.get_json_header()["ClassDefinitions"]["CPU"]["Fields"] )
    cpu_fields.remove("idle")
    cpu_fields.remove("util")

    # Axes
    ax.set_ylim(0,100)
    #ax.set_ylabel('CPU ' + "/".join(cpu_fields) + ' (%)')
    ax.set_ylabel('CPU util (%)')

    # Plot
    y_offsets = numpy.array([0.0] * len(cnl_file.cols["begin"]))
    z = 0
    for field in cpu_fields:
        #values = cols[field]
        v = cols[field] + y_offsets
        values = merge_lists( v, v )

        # as bar chart -- slooooow!!
        #ax.bar(cnl_file.cols["begin"], values, cnl_file.cols["duration"], bottom=y_offsets,
               #color=CPU_COLORS[field], label=field)

        # draw with lines (okay, but not filled..)
        #ax.plot(cnl_file.x_values, values,
               #color=CPU_COLORS[field], label=field, zorder=z)


        # fill (seems to be the best option)
        ax.fill(cnl_file.x_values, values,
               color=CPU_COLORS[field], label=field, zorder=z)


        # NOTE: ax.stackplot could actually be the right choice here..


        #y_offsets += values
        y_offsets += cols[field]

        z -= 1


    # Legend
    if ( legend_outside ):
        offset = transforms.ScaledTranslation(20, 0, transforms.IdentityTransform())
        trans = ax.transAxes + offset

        l = ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.02),fancybox=True, shadow=True, title=legend_title)
    else:
        l = ax.legend(loc=0)

    l.draggable(True)


def plot_top_cpus(cnl_file, axes, indices=[0]):
    """
    This function creates "virtual top-cpus" and plots the utilization fields (usr, system, ...)

    The CPU utilization samples are rearranged as if always the first CPU had the highest load,
    the seconds CPU the second highest load, etc.

    This means, usually each "virtual top-cpus" contains samples from many/all real CPUs.
    Thus, origin of the sample is stored as an extra field and can be plotted as well.
      (Therefore each CPU needs to have an assigned color).

    ***

    Plots the "virtual top-cpus" according to |indices| in the specified |axes|.

    """

    top_cpus = _create_cpu_cols_by_util(cnl_file)

    for ax, i in zip(axes, indices):
        label = "Top #{} CPU".format(i+1)
        cols = top_cpus[i]
        plot_area_chart(ax, cnl_file, cols, True, label)

