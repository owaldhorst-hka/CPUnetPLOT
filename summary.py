#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import time
import os
from itertools import zip_longest

from cnl_library import CNLParser, pretty_json, human_readable_from_seconds
from split_text import split_proprtionally

## some "constants"/preferences
divisor = 1000000.0
rounding_digits = 2
unit = "MBits"


def format_timestamp(t):
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(t))

def sprint_bold(text):
    return "\033[1m" + text + "\033[0m"

def sprint_inverted(text):
    return "\033[7m" + text + "\033[0m"

def print_inverted(text, **kwargs):
    #print( "\033[7m" + text + "\033[0m", **kwargs )
    print( sprint_inverted(text), **kwargs )


def print_in_two_columns(format_str, left_col, right_col):
    for l, r in zip_longest(left_col, right_col, fillvalue=""):
        print( format_str.format(l, r) )



def show_match(left_file, right_file, env=None):
    """
    Displays a brief summary of two CNL-file next to each other.

    Should be used with two files that belong to the same experiment
    (e.g. sender and receiver).
    """

    left_head, left_rates = left_file.as_column(env)
    right_head, right_rates = right_file.as_column(env)

    ## Head
    print_in_two_columns("{:<50} {}", left_head, right_head)

    ## Rates
    print_in_two_columns("{:<58} {}", left_rates, right_rates)
    #  Note: The escape sequence for the "rate-bar" is counted as characters.. :-/

    print()




class LogAnalyzer:

    def __init__(self, cnl_file):
        self.cnl_file = cnl_file

        ## Get all fields to watch for activity (NIC, send and receive)
        self.nics = cnl_file.get_nics()
        self.watch_fields = list()
        nic_fields = [".send", ".receive"]
        for nic_name in self.nics:
            for nic_field in nic_fields:
                self.watch_fields.append( nic_name + nic_field )

        # important csv indices
        self.watch_indices = cnl_file.get_csv_indices_of(self.watch_fields)
        self.begin_index = cnl_file.get_csv_index_of("begin")
        self.end_index = cnl_file.get_csv_index_of("end")
        self.duration_index = cnl_file.get_csv_index_of("duration")


        ## Result variables
        self.experiment_start_time = None
        self.experiment_end_time = None
        self.recording_start_time = None
        self.recording_end_time = None

        self.sums = [0.0] * len(self.watch_fields)
        self.pause_time = 0

        ## Trigger "summarize"
        self._summarize()


    def _is_activity(self, line):
        for field_name in self.watch_indices:
            if ( float( line[field_name] ) > 0 ):
                return True

        return False

    def _sum_line(self, line):
        # Summarize the values of all watched fields (data send/received).
        for i in range( len(self.sums) ):
            self.sums[i] += line[ self.watch_indices[i] ] * line[self.duration_index]


    def _get_begin(self, line):
        return line[self.begin_index]

    def _get_end(self, line):
        return line[self.end_index]


    def _summarize(self):
        probably_pause_time = 0

        for line in self.cnl_file.get_csv_iterator():
            ## Sum watched columns.
            self._sum_line(line)

            ## Find experiment start and end time.
            if ( self._is_activity(line) ):

                # Find begin of the experiment.
                if ( not self.experiment_start_time ):
                    self.experiment_start_time = self._get_begin(line)

                # Find end of the experiment.
                self.experiment_end_time = self._get_end(line)

                # Since the experiment apparently has started and not finished yet,
                #   the last observed idle time was actually during the experiment.
                #   --> So, track it.
                self.pause_time += probably_pause_time
                probably_pause_time = 0

            ## Keep track of idle states during the experiment.
            else:
                probably_pause_time += line[self.duration_index]


        self.experiment_duration = self.experiment_end_time - self.experiment_start_time



    def show(self):
        print("=== Summary ===")
        #print( "Filename: " + os.path.relpath(self.cnl_file.filename) )
        form_str = "{:<10} {}"
        print( form_str.format("Filename:", os.path.basename(self.cnl_file.filename)) )
        print( form_str.format("Comment:", self.cnl_file.get_comment()) )
        print( form_str.format("Hostname:", self.cnl_file.get_sysinfo()["hostname"]) )
        print( form_str.format("Kernel:", self.cnl_file.get_sysinfo()["kernel"]) )
        print()

        print( form_str.format( "Start:", format_timestamp(self.experiment_start_time) ) )
        print( form_str.format( "End:", format_timestamp(self.experiment_end_time) ) )
        print( form_str.format( "Duration:", round(self.experiment_duration) ) )
        print()

        print( "CPUs: " + ", ".join(self.cnl_file.get_cpus()) )
        print( "NICs: " + ", ".join(self.cnl_file.get_nics()) )
        print()

        # Show average transmission rates.
        print("== Average transmission rates ==")
        for i in range( len(self.sums) ):
            speed = round(self.sums[i] / divisor / self.experiment_duration, rounding_digits)
            print( "{:<13} {:>10} {}/s".format(self.watch_fields[i]+":", speed, unit) )


    def show_brief(self):
        speeds = list()
        for i in range( len(self.sums) ):
            speed = "{:.2f}".format( round(self.sums[i] / divisor / self.experiment_duration, rounding_digits) )
            speeds.append( "{:>8} {}/s".format(speed, unit) )

        speeds_str = " ".join(speeds)
        filename = os.path.basename(self.cnl_file.filename)
        comments = self.cnl_file.get_comment().split(";")

        print( "{:<32} {}".format( filename + ":", speeds_str) )
        for comment in comments:
            print( "{:<32} {}".format( "", comment.strip()) )



    def as_column(self, env=None):
        ## TODO change name?

        ## Head

        head = list()

        filename = os.path.basename(self.cnl_file.filename)
        comments = self.cnl_file.get_comment().split(";")

        # file name
        head.append( filename )

        # comment(s)
        for comment in comments:
            head.append(comment.strip()[:48])

        # duration
        pause = ""
        if ( self.pause_time > 5 ):
            pause = "({} of that idle)".format( human_readable_from_seconds(self.pause_time) )
        head.append( "Duration: {} {}".format(human_readable_from_seconds(self.experiment_duration), pause) )

        # requested environment variables
        if ( env ):
            env_head = self.cnl_file.get_environment()
            for e in env:
                json = env_head.get(e)
                if ( json ):
                    text = pretty_json(json)
                    it = iter(text.split("\n"))

                    # first line
                    head.append( '{}: {}'.format(e, next(it)) )

                    # subsequent lines (if any)
                    for line in it:
                        head.append( line )



        ## Transmission rates

        rates = list()
        for i in range( len(self.sums) ):
            speed = self.sums[i] / (self.experiment_duration-self.pause_time)

            number_str = "{:.2f}".format( round(speed / divisor, rounding_digits) )
            bar_str = "{:<20}".format(number_str + " " + unit + "/s")

            label = "{:<6}".format( self.nics[int(i/2)] + ":" if i%2==0 else "" )

            parts = split_proprtionally(bar_str, [speed, 1000000*10000-speed])
            text = label + "|" + sprint_inverted(parts[0]) + parts[1] + "|"

            rates.append( text )

        return head, rates



    def visualize_brief(self, env=None):
        head, rates = self.as_column(env)

        print_in_two_columns("{:<50} {}", head, rates )



## MAIN ##
if __name__ == "__main__":
    import sys

    filenames = sorted( sys.argv[1:] )

    for filename in filenames:
        ## * Parse input file. *
        cnl_file = CNLParser(filename)

        log = LogAnalyzer(cnl_file)
        #log.summarize()

        if ( len(filenames) > 1 ):
            #log.show_brief()
            log.visualize_brief()
            print()
        else:
            log.show()
