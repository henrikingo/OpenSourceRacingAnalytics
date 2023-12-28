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
    SUMMARY_FIELDS1 = "date,time,laps,some number,track,driver,zeros,apostrophe,fifty,empty string,fifty,device,END,1,0, ,no delete partiel,,10,class,session type,date,time,track,driver,NOT USED,NOT USED".split(',')
    SUMMARY_FIELDS2 = "lap,time lap,time partiel 1,time partiel 2,time partiel 3,time partiel 4,time partiel 5,time partiel 6,Min RPM,Max RPM,Min Speed GPS,Max Speed GPS,Min T1,Max T1,Min T2,Max T2,Min T3,Max T3,Min T4,Max T4,Min Speed sensor,Max Speed sensor, RPM max gear,Type de champs,Vbattery,max EGT,Hdop".split(',')
    LAP_FIELDS = "Partiel,RPM,Speed GPS,T1,T2,Gf. X,Gf. Y,Orientation,Speed rear,Lat.,Lon.,Altitude".split(",")


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
                    if summary2 is None:
                        summary2 = row
                        continue

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
                for lap_file in list(filter(lambda x: "LAP" == x[:3], os.listdir(session_dir))):
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
                                lap_rows.append(row)
                        assert headers is not None
                        new_session.set_lap(i, lap_rows)
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
        maprows = []
        for row in rows:
            maprows.append(dict(zip(k,row)))
        return maprows

    def set_lap(self, i, data):
        if len(self._laps)>i-1:
            self._laps[i-1] = data
        elif len(self._laps)==i-1:
            self._laps.append(data)
        else:
            raise IndexError("{} > {}".format(i,len(self._laps)))


    def get_lap(self, lap):
        return self._laps[lap-1]

    def laps(self):
        return self._laps

