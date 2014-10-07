# -*- coding:utf-8 -*-

# Copyright (c) 2014,
# Karlsruhe Institute of Technology, Institute of Telematics
#
# This code is provided under the BSD 2-Clause License.
# Please refer to the LICENSE.txt file for further information.
#
# Author: Mario Hock


import matplotlib.ticker as ticker
from cnl_library import human_readable_from_seconds


## tick positions ##

class TimeLocator(ticker.Locator):
    """
    Place the x-axis ticks to be nice seconds/minutes/hours values.
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

        steps = (60*60, 60*30, 60*15, 60*10, 60*5,
                 60, 30, 15, 10, 5)

        nice_value = value
        for step in steps:
            nice_value = self._shrink_to_a_multiple_of(value, step, maxdiff)

            if ( nice_value != value ):
                break

        return nice_value


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
            ## TODO make nice with +, instead - ?
            base = self._make_nice(vmin)

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




## tick labels ##

def format_xticks_time(x, pos=None):
    return human_readable_from_seconds(float(x))

def format_xticks_minutes(x, pos=None):
    return "0" if x == 0 else "{:.0f}min".format(float(x)/60)

def format_yticks_10G(y, pos=None):
    return "0" if y == 0 else "{:.0f}G ".format(y / 1000000000)

