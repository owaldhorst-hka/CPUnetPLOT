# -*- coding:utf-8 -*-

class Layout:
    def __init__(self, name):
        self.fontsize = fontsize[name]
        self.margin_double_plot = margin_double[name]
        self.margin_area_plot = margin_area[name]

    def set_margins(self, fig, area_plot=False):
        if ( area_plot ):
            self.margin_area_plot.set_margins(fig)
        else:
            self.margin_double_plot.set_margins(fig)


    def set_tick_fontsize(self, plt, *axes):
        for ax in axes:
            plt.setp(ax.get_xticklabels(), fontsize=self.fontsize.ticks)
            plt.setp(ax.get_yticklabels(), fontsize=self.fontsize.ticks)



## TODO Maybe "named tuples" would be more appropriate than classes for Margin and Fontsize?
class Margin:
    def __init__(self, left, wspace, right, top, hspace, bottom):
        self.bottom = float(bottom)
        self.hspace = float(hspace)
        self.left = float(left)
        self.right = float(right)
        self.top = float(top)
        self.wspace = float(wspace)

    def set_margins(self, fig):
        fig.subplots_adjust(left=self.left, wspace=self.wspace, right=self.right,
                            top=self.top, hspace=self.hspace, bottom=self.bottom)


class Fontsize:
    def __init__(self, axis_labels, legend, ticks):
        self.axis_labels = axis_labels
        self.legend = legend
        self.ticks = ticks



## Presets: Fontsize

fontsize = dict()
fontsize["default"] = Fontsize(axis_labels = 18, legend = 14, ticks = 14)
fontsize["presentation"] = Fontsize(axis_labels = 28, legend = 22, ticks = 18)
fontsize["publication"] = fontsize["default"]


## Presets: Subplot-Layout (margins)
#  NOTE: These values actually work great with a screen resolution of 1920x1200.
#        Since all spaces here are in relative size, this might have to be adjusted for other screen resolutions.

margin_double = dict()
margin_area = dict()

# "default": good readability on screen
margin_double["default"] = Margin(left=0.1, wspace=0.2, right=0.9, top=0.92, hspace=0.4, bottom=0.12)
margin_area["default"] = Margin(left=0.1, wspace=0.2, right=0.9, top=0.92, hspace=0.4, bottom=0.12)

# "presentation": large font, small margins
margin_double["presentation"] = Margin(left=0.05, wspace=0.15, right=0.98, top=0.97, hspace=0.33, bottom=0.11)
margin_area["presentation"] = Margin(left=0.05, wspace=0.15, right=0.90, top=0.97, hspace=0.33, bottom=0.11)  # legend on the right
margin_area["presentationX"] = Margin(left=0.04, wspace=0.15, right=0.99, top=0.97, hspace=0.3, bottom=0.09)  # legend below

# "publication": regular font, small margins
margin_double["publication"] = Margin(left=0.03, wspace=0.15, right=0.99, top=0.97, hspace=0.3, bottom=0.08) # small font size
margin_area["publication"] = Margin(left=0.03, wspace=0.15, right=0.93, top=0.97, hspace=0.3, bottom=0.08)   # small font size

