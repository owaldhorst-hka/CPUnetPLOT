#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from cnl_library import CNLParser
import time

## some "constants"/preferences
divisor = 1000000.0
rounding_digits = 2
unit = "MBits"


def format_timestamp(t):
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(t))


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


        ## Result variables
        self.experiment_start_time = None
        self.experiment_end_time = None
        self.recording_start_time = None
        self.recording_end_time = None

        self.sums = [0.0] * len(self.watch_fields)


    def _is_activity(self, line):
        for field_name in self.watch_indices:
            if ( float( line[field_name] ) > 0 ):
                return True

        return False

    def _sum_line(self, line):
        for i in range( len(self.sums) ):
            self.sums[i] += line[ self.watch_indices[i] ]



    def _get_begin(self, line):
        return line[self.begin_index]

    def _get_end(self, line):
        return line[self.end_index]


    def summarize(self):

        for line in self.cnl_file.get_csv_iterator():
            ## on active samples
            if ( self._is_activity(line) ):

                # Find begin of the experiment.
                if ( not self.experiment_start_time ):
                    self.experiment_start_time = self._get_begin(line)

                # Find end of the experiment.
                self.experiment_end_time = self._get_end(line)

            ## Sum watched columns.
            self._sum_line(line)


        self.experiment_duration = self.experiment_end_time - self.experiment_start_time


    def show(self):
        print( "Comment: " + self.cnl_file.get_comment() )
        print()

        print( "CPUs: " + ", ".join(self.cnl_file.get_cpus()) )
        print( "NICs: " + ", ".join(self.cnl_file.get_nics()) )
        print()

        print( "Start: {}".format( format_timestamp(self.experiment_start_time) ) )
        print( "End:   {}".format( format_timestamp(self.experiment_end_time) ) )
        print( "Duration: {}".format( self.experiment_duration ) )
        print()

        # Show average transmission rates.
        for i in range( len(self.sums) ):
            speed = round(self.sums[i] / divisor / self.experiment_duration, rounding_digits)
            print( "{:<13} {:>8} {}/s".format(self.watch_fields[i]+":", speed, unit) )



## MAIN ##
if __name__ == "__main__":
    import sys

    filename = sys.argv[1]
    print( filename )

    ## * Parse input file. *
    cnl_file = CNLParser(filename)

    log = LogAnalyzer(cnl_file)
    log.summarize()
    log.show()

