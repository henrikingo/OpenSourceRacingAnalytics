import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from .path_util import getSourceDir, getDocumentDir

class AlfanoReader:
    SUMMARY_FIELDS1 = "date,time,laps,some number,track,driver,zeros,apostrophe,fifty,empty string,fifty,device,END,1,0, ,no delete partiel,,samplerate,class,session type,date,time,track,driver,NOT USED,NOT USED".split(',')
    SUMMARY_FIELDS2 = "lap,time lap,time partiel 1,time partiel 2,time partiel 3,time partiel 4,time partiel 5,time partiel 6,Min RPM,Max RPM,Min Speed GPS,Max Speed GPS,Min T1,Max T1,Min T2,Max T2,Min T3,Max T3,Min T4,Max T4,Min Speed sensor,Max Speed sensor, RPM max gear,Type de champs,Vbattery,max EGT,Hdop".split(',')
    # 3,54340,54340,0,0,0,0,0,6469,14292,406,989,455,460,3530,6623,0,0,0,0,0,0,13271,1,4007,6609,9
    LAP_FIELDS = "Partiel,RPM,Speed GPS,T1,T2,Gf. X,Gf. Y,Orientation,Speed rear,Lat.,Lon.,Altitude".split(",")
    # Alfano produces fixed point values. So we have to add decimal comma into the right place for each.
    LAP_FIELDS_DECIMAL = [1,1,10,10,10,10,10,1,10,1000000,1000000,1]
    SUMMARY_FIELDS_DECIMAL = [1,1000,1000,1000,1000,1000,1000,1000,1,1,10,10,10,10,10,10,1,1,1000,10,1]


    def __init__(self, source_dir=None):
        self.source_dir = source_dir or getSourceDir()
        self._sessions = []


    def session_dirs(self):
        sessions = os.listdir(self.source_dir)
        sessions = filter(lambda x: "ALFANO6_LAP_" == x[:12], sessions)
        return sessions

    def translate_sessions(self):
        for s in self.session_dirs():
            session_dir = os.path.join(self.source_dir, s)
            summary_file = list(filter(lambda x: "SN" == x[:2], os.listdir(session_dir)))
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

                    row = [float(v)/float(d) for v,d in zip(row,self.SUMMARY_FIELDS_DECIMAL)]
                    rows.append(row)

                # Repeat last summary row because there's data for the exit lap until you stop
                rows.append(row)

                #print(rows[0])
                #print(self.SUMMARY_FIELDS2)
                #print(rows[1])

                summary = {k:v for k, v in zip(self.SUMMARY_FIELDS1, summary1)}
                new_session = AlfanoSession(s,summary, rows)
                print(summary)
                print("")
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
            #return "For debugging, just try to get 1 file through first"
        return self._sessions


class AlfanoSession:
    def __init__(self, dirname, summary, data_rows):
        self.dirname = dirname
        self.summary = summary
        self.data_rows = data_rows
        self._laps = []
        self._lap_headers = []

    def set_lap_headers(self,headers):
        self._lap_headers=headers

    def get_lap_headers(self):
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

    def total_seconds(self):
        return sum(self.lap_times_sequence())

    def lap_time_sec(self, lap):
        return self.data_rows[lap-1][1]

    def lap_times_sequence(self):
        return [row[1] for row in self.data_rows]

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

    def real_samplerate(self, lap):
        official_sample_rate=int(self.summary["samplerate"])
        laprows = len(self.get_lap(lap))
        laprows = laprows-1 if lap==1 else laprows
        lap_time_sec = self.lap_time_sec(lap)
        return (laprows)/lap_time_sec if laprows>0 else official_sample_rate

    def computed_rows(self, lap):
        samplerate = self.real_samplerate(lap)   #float(self.summary["samplerate"])
        laprows = self.get_lap(lap)
        COMPUTED_ROWS_HEADERS = ["lap", "row_lap", "row_cumulative", "msec_cumulative", "sec_cumulative", "msec_lap","sec_lap"]
        comprows = []
        msec_lap = 0 #+1000/samplerate
        row_lap=0
        # TODO store the result...
        msec_cumulative = int(0) #+1000/samplerate
        #msec_cumulative = int(self.lap_times_sequence_cumulative(lap-1)*1000)  if lap>1 else 0 # -1 because the end time of previous lap is our start time
        row_cumulative=int(0)
        if lap > 1:
            _, prev_lap = self.computed_rows(lap-1)
            msec_cumulative = int((prev_lap[-1][3]))+1
            #msec_cumulative = int(self.lap_times_sequence_cumulative(lap-1)*1000)  if lap>1 else 0 # -1 because the end time of previous lap is our start time
            row_cumulative=int((prev_lap[-1][2]))

        for row in laprows:
            # Last row of lap 1 is also first row of lap 2. But lap 1 doesn't have that, so skip one tick.
            if True: #row_cumulative > 0:  # Watch out for recursion there
                comprows.append([lap, row_lap, row_cumulative, int(msec_cumulative), int(msec_cumulative)/1000.0, int(msec_lap), int(msec_lap)/1000.0])
                #else:

            msec_cumulative = msec_cumulative + 1000.0/samplerate if samplerate>0 else 0
            msec_lap = msec_lap + 1000.0/samplerate if samplerate>0 else 0
            row_cumulative+=1
            row_lap+=1

        # Hard to assert but these are equal to the next and previous rows on the adjacent lap. For Alfano the rows are duplicated.
        #print(comprows[0],laprows[0])
        #print(comprows[-1],laprows[-1])
        assert len(comprows)==len(laprows)
        #print(round(samplerate,4))
        return COMPUTED_ROWS_HEADERS, comprows
