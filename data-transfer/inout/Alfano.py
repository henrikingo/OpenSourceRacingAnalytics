import copy
import datetime
import sys
import os
import platform
import threading
import time
import csv
import math
import gzip
from collections import OrderedDict

from .path_util import getSourceDir, getDocumentDir

NODATE = datetime.date(1970,1,1)
NODATETIME = datetime.datetime(1970,1,1,0,0,0,0)

class AlfanoReader:
    SUMMARY_FIELDS1 = "date,time,laps,some_constant_number,track,driver,fastest_minutes,apostrophe,fastest_seconds,empty_string,fastest_hundreds,device,END,1,0,_,no_delete_partiel,,samplerate,class,session_type,date2,time2,track2,driver2,NOT_USED,NOT_USED2".split(',')
    SUMMARY_FIELDS2 = "lap,time_lap,time_partiel_1,time_partiel_2,time_partiel_3,time_partiel_4,time_partiel_5,time_partiel_6,Min_RPM,Max_RPM,Min_Speed_GPS,Max_Speed_GPS,Min_T1,Max_T1,Min_T2,Max_T2,Min_T3,Max_T3,Min_T4,Max_T4,Min_Speed_sensor,Max_Speed_sensor,RPM_max_gear,Type_de_champs,Vbattery,max_EGT,Hdop".split(',')
    # 3,54340,54340,0,0,0,0,0,6469,14292,406,989,455,460,3530,6623,0,0,0,0,0,0,13271,1,4007,6609,9
    LAP_FIELDS = "Partiel,RPM,Speed GPS,T1,T2,Gf. X,Gf. Y,Orientation,Speed rear,Lat.,Lon.,Altitude".split(",")
    # Alfano produces fixed point values. So we have to add decimal comma into the right place for each.
    LAP_FIELDS_DECIMAL = [1,1,10,10,10,1000,1000,100,10,1000000,1000000,10]
    SUMMARY_FIELDS_DECIMAL = [1,1000,1000,1000,1000,1000,1000,1000,10,10,10,10,10,10,10,10,1,1,1000,10,1]


    def __init__(self, source_dir=None):
        self.source_dir = source_dir or getSourceDir()
        self.source_dir = os.path.expanduser(self.source_dir)
        self._sessions = []


    def session_dirs(self):
        sessions = os.listdir(self.source_dir)
        sessions = filter(lambda x: "ALFANO6_LAP_" == x[:12], sessions)
        return sessions

    def translate_sessions(self):
        for s in self.session_dirs():
            session_dir = os.path.join(self.source_dir, s)
            summary_file = list(filter(lambda x: "SN" == x[:2], os.listdir(session_dir)))
            print(summary_file, session_dir)
            assert len(summary_file)==1
            summary_file_path = os.path.join(session_dir,summary_file[0])
            with open(summary_file_path) as csvfile:
                reader = csv.reader(csvfile)
                summary1 = None
                summary2 = None
                rows = []
                for row in reader:
                    if summary1 is None:
                        summary1 = row
                        continue
                    if summary2 is None:
                        summary2 = row
                        continue

                    row = [float(v)/float(d) if d>1 else int(v)
                           for v,d in zip(row,self.SUMMARY_FIELDS_DECIMAL)]
                    rows.append(row)

                # Repeat last summary row because there's data for the exit lap until you stop
                rows.append(row)

                #print(rows[0])
                #print(self.SUMMARY_FIELDS2)
                #print(rows[1])

                summary = {k:v for k, v in zip(self.SUMMARY_FIELDS1, summary1)}
                new_session = AlfanoSession(s,summary, rows)

                self._sessions.append(new_session)
                #assert ",".join(rows[0]) == ",".join(self.SUMMARY_FIELDS2)

                i = 1
                lap_files = list(filter(lambda x: "LAP" == x[:3], os.listdir(session_dir)))
                lap_files.sort()
                for lap_file in lap_files:
                    lap_file_path = os.path.join(session_dir,lap_file)
                    with open(lap_file_path) as lap:
                        reader = csv.reader(lap)
                        headers = None
                        lap_rows = []
                        for row in reader:
                            if headers is None:
                                headers = row
                                new_session.set_lap_headers(headers)
                            else:
                                row = [float(v)/float(d) for v,d in zip(row,self.LAP_FIELDS_DECIMAL)]
                                lap_rows.append(row)
                        assert headers is not None
                        new_session.set_lap(i, lap_rows)
                        #print(len(lap_rows))
                        i += 1

                #new_session.session_end()
            #return "For debugging, just try to get 1 file through first"
        return self._sessions


class AlfanoSession:
    def __init__(self, dirname, summary, lap_summary_rows):
        self.dirname = dirname
        self.summary_orig = summary
        KEEP = "date,time,laps,some_constant_number,track,driver,fastest_minutes,fastest_seconds,fastest_hundreds,device,samplerate,class,session_type".split(',')

        self.summary = {k:summary[k] for k in KEEP}
        self.wallClockUtc = datetime.datetime.strptime(self.summary['date'] + " " + self.summary['time'],'%d-%m-%Y %H:%M')
        date_parts = self.summary['date'].split("-")
        isodate = date_parts[2] + "-" +date_parts[1]+ "-" + date_parts[0]
        self.summary ["date"] = isodate
        #self.summary['fastest_lap'] = datetime.datetime.combine(NODATE, datetime.time(0,int(summary['fastest_minutes']),
        #int(summary['fastest_seconds']), int(summary['fastest_hundreds'])))


        print(self.summary)
        print("")
        self.lap_summary_rows = lap_summary_rows
        self._laps = []
        self._lap_headers = []


        fastest = datetime.timedelta(minutes=int(summary['fastest_minutes']), seconds=int(summary['fastest_seconds']),     milliseconds=int(summary['fastest_hundreds'])*10)
        self.summary['fastest_lap'] = fastest.total_seconds()

        self.lap_times_array = [row[1] for row in self.lap_summary_rows]

    def set_lap_headers(self,headers):
        self._lap_headers=headers

    def get_lap_headers(self):
        return "Sector,RPM,Speed_GPS,T1,T2,GfX,GfY,Orientation,Speed rear,Lat,Lon,Altitude".split(",")

    def get_lap_headers_real(self):
        return self._lap_headers

    def get_lap_map(self,i):
        rows = self.get_lap(i)
        k = self.get_lap_headers()
        return [dict(zip(k,row)) for row in rows]

    def set_lap(self, i, rows):
        if len(self._laps)>i-1:
            self._laps[i-1] = rows
        elif len(self._laps)==i-1:
            self._laps.append(rows)
        else:
            raise IndexError("{} > {}".format(i,len(self._laps)))


    def get_lap(self, lap):
        return self._laps[lap-1]

    def laps(self):
        return self._laps

    def num_laps(self):
        return len(self._laps)

    def total_seconds(self):
        return sum(self.lap_times_sequence())

    def lap_time_sec(self, lap):
        return self.lap_summary_rows[lap-1][1]

    def lap_times_sequence(self):
        return self.lap_times_array

    def lap_times_sequence_cumulative(self,lap=None):
        laps = []
        cumulus = 0.0
        for v in self.lap_times_sequence():
            cumulus += v
            laps.append(cumulus)
        if lap is None:
            #print(laps)
            return laps
        else:
            return laps[lap-1]

    def lap_times(self):
        times_strings = []
        for lap_seconds in self.lap_times_sequence():
            full_seconds = int(lap_seconds)
            msec = int((lap_seconds - full_seconds)*1000)
            minutes = str(full_seconds//60)
            fs = float(full_seconds%60)+(float(msec)/1000.0)
            seconds = str(fs) if fs>=10 else "0"+str(fs)
            timestr = minutes+":"+seconds
            times_strings.append(timestr)
        return times_strings

    def computed_lap_summary_rows_headers(self):
        SUMMARY_ROWS_HEADERS = ["lap_start_cumulative_sec","lap_end_cumulative_sec","lap_start_cumulative_msec","lap_end_cumulative_msec"]
        return SUMMARY_ROWS_HEADERS

    def computed_lap_summary_rows(self, lap):
        prev_lap_time = self.lap_times_sequence_cumulative(lap-1) if lap > 1 else 0.0
        this_lap_time = self.lap_times_sequence_cumulative(lap)


        therow=[
            prev_lap_time,
            this_lap_time,
            int(prev_lap_time*1000),
            int(this_lap_time*1000)
        ]
        return therow


    def all_lap_summary_rows(self, _lap=None):
        if _lap is None:
            return [self.all_lap_summary_rows(lap) for lap in range(1,self.num_laps()+1)]

        return self.computed_lap_summary_rows(_lap) + self.lap_summary_rows[_lap-1]

    def all_lap_summary_headers(self):
        return self.computed_lap_summary_rows_headers() + AlfanoReader.SUMMARY_FIELDS2

    def all_lap_summary_maps(self, _lap=None):
        if _lap is None:
            return [self.all_lap_summary_maps(lap) for lap in range(1,self.num_laps()+1)]
        h=self.all_lap_summary_headers()
        r=self.all_lap_summary_rows(_lap)

        d= OrderedDict([(k,v) for k,v in zip(h,r)])

        return d















    def real_samplerate(self, lap):
        official_sample_rate=int(self.summary["samplerate"])
        laprows = len(self.get_lap(lap))
        laprows = laprows-1 if lap==1 else laprows
        lap_time_sec = self.lap_time_sec(lap)
        return (laprows)/lap_time_sec if laprows>0 and lap_time_sec>0 else official_sample_rate

    def session_end(self):
        # Add a row of zero values to the end. It is useful for some vizualisations.
        last_lap = self.get_lap(self.num_laps())
        null_row = [0] * len(last_lap[-1])
        self.set_lap(self.num_laps()+1, [null_row])
        lap_data_null_row = [0] * len(self.lap_summary_rows[-1])
        self.lap_summary_rows.append(lap_data_null_row)


    def computed_rows_headers(self):
        COMPUTED_ROWS_HEADERS = ["lap", "row_in_lap", "row_cumulative", "msec_cumulative", "sec_cumulative", "msec_in_lap","sec_in_lap"]
        return COMPUTED_ROWS_HEADERS

    def computed_rows(self, lap):
        samplerate = self.real_samplerate(lap)   #float(self.summary["samplerate"])
        laprows = self.get_lap(lap)
        COMPUTED_ROWS_HEADERS = self.computed_rows_headers()
        comprows = []
        msec_lap = 0 #+1000/samplerate
        row_lap=0
        # TODO store the result...
        msec_cumulative = int(0) #+1000/samplerate
        #msec_cumulative = int(self.lap_times_sequence_cumulative(lap-1)*1000)  if lap>1 else 0 # -1 because the end time of previous lap is our start time
        row_cumulative=int(0)
        # Last row of lap 1 is also first row of lap 2. Therefore want to keep rownr the same but time can skip a msec to distinguish otherwise identical rows.
        if lap > 1:
            prev_lap = self.computed_rows(lap-1)
            msec_cumulative = int((prev_lap[-1][3]))+1
            #msec_cumulative = int(self.lap_times_sequence_cumulative(lap-1)*1000)  if lap>1 else 0 # -1 because the end time of previous lap is our start time
            row_cumulative=int((prev_lap[-1][2]))

        for row in laprows:
            comprows.append([lap, row_lap, row_cumulative, int(msec_cumulative), int(msec_cumulative)/1000.0, int(msec_lap), int(msec_lap)/1000.0])

            msec_cumulative = msec_cumulative + 1000.0/samplerate if samplerate>0 else 0
            msec_lap = msec_lap + 1000.0/samplerate if samplerate>0 else 0
            row_cumulative+=1
            row_lap+=1

        # Hard to assert but these are equal to the next and previous rows on the adjacent lap. For Alfano the rows are duplicated.
        #print(comprows[0],laprows[0])
        #print(comprows[-1],laprows[-1])
        assert len(comprows)==len(laprows)
        #print(round(samplerate,4))
        return comprows

    def all_rows(self, _lap=None):
        for lap in [_lap] if _lap is not None else range(1,self.num_laps()+1):
            for comp, real in zip(self.computed_rows(lap), self.get_lap(lap)):
                yield comp + real

    def all_headers(self):
        return self.computed_rows_headers() + self.get_lap_headers()
