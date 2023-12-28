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


class AssettoCorsaWriter:
    out_dir = "."
    sessions=None

    def __init__(self, sessions, outputDirectory=None):
        self.out_dir = outputDirectory or getDocumentDir()
        self.sessions=sessions
        assert sessions

    def write_sessions(self):
        for session in self.sessions:
            self.session = session
            self.write_session()

    def write_session(self):
        outputDirectory = self.out_dir
        session = self.session
        #print(session)
        # dataFile = "trackAttack_from_Alfano6_{}_{}.csv".format(
        session.summary["track"],
        session.summary["date"] + "_" + session.summary["time"].replace(":",""))
        dataFilePath = os.path.join(outputDirectory, dataFile)
        print(dataFilePath)
        self.writeOutputFile(dataFilePath)

    def writeOutputFile(self, ta_file_name):
        #with gzip.open(ta_file_name, 'wt') as dataFile:
        with open(ta_file_name, 'wt') as dataFile:
            dataFileWriter = csv.writer(dataFile,delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            self.writeFileMetaData(dataFileWriter)
            dataFileWriter.writerow([])
            self.writeRaceDataHeader(dataFileWriter)
            self.writeHeaderUnits(dataFileWriter)
            dataFileWriter.writerow([])
            self.writeRaceData(dataFileWriter)
            dataFile.flush()
        dataFile.close()

    def writeFileMetaData(self, dataFileWriter):
        dataFileWriter.writerow(["Format","Assetto Corsa CSV File"])
        dataFileWriter.writerow(["Data Source",self.session.summary["device"]])
        dataFileWriter.writerow(["Date",self.session.summary["date"]])
        dataFileWriter.writerow(["Time",self.session.summary["time"]])
        # dataFileWriter.writerow(["smVersion",info.static._smVersion])
        # dataFileWriter.writerow(["acVersion",info.static._acVersion])
        dataFileWriter.writerow(["numberOfSessions",1])
        dataFileWriter.writerow(["numCars",1])
        #dataFileWriter.writerow(["carModel",info.static.carModel])
        dataFileWriter.writerow(["track",self.session.summary["track"]])
        dataFileWriter.writerow(["playerName",self.session.summary["driver"]])
        dataFileWriter.writerow(["playerNick",self.session.summary["driver"]])
        dataFileWriter.writerow(["playerSurname",self.session.summary["driver"]])
        dataFileWriter.writerow(["sectorCount",self.sectors_found()])

    def sectors_found(self):

        s = 1
        sector_sum = [0]*6
        for s in range(1,7):
            for row in self.session.data_rows[1:]:
                sector_sum[s-1] += int(row[1+s])
        for i in range(0,5):
            if sector_sum[i] == 0:
                return i

    def writeRaceDataHeader(self, dataFileWriter):
        dataFileWriter.writerow([

                #Physics Info
                "accG lat",
                "accG lon",
                "accG vert",
                "brake",
                "camberRAD fl",
                "camberRAD fr",
                "camberRAD rl",
                "camberRAD rr",
                "carDamage1",
                "carDamage2",
                "carDamage3",
                "carDamage4",
                "carDamage5",
                "cgHeight",
                "drs",
                "tc",
                "fuel",
                "gas",
                "gear",
                "numberOfTyresOut",
                "packetId",
                "heading",
                "pitch",
                "roll",
                "rpms",
                "speedKmh",
                "steerAngle",
                "suspensionTravel fl",
                "suspensionTravel fr",
                "suspensionTravel bl",
                "suspensionTravel br",
                "tyreCoreTemperature fl",
                "tyreCoreTemperature fr",
                "tyreCoreTemperature bl",
                "tyreCoreTemperature br",
                "tyreDirtyLevel fl",
                "tyreDirtyLevel fr",
                "tyreDirtyLevel bl",
                "tyreDirtyLevel br",
                "tyreWear fl",
                "tyreWear fr",
                "tyreWear bl",
                "tyreWear br",
                "velocity x",
                "velocity y",
                "velocity z",
                "wheelAngularSpeed fl",
                "wheelAngularSpeed fr",
                "wheelAngularSpeed bl",
                "wheelAngularSpeed br",
                "wheelLoad fl",
                "wheelLoad fr",
                "wheelLoad bl",
                "wheelLoad br",
                "wheelSlip fl",
                "wheelSlip fr",
                "wheelSlip bl",
                "wheelSlip br",
                "wheelsPressure fl",
                "wheelsPressure fr",
                "wheelsPressure bl",
                "wheelsPressure br",

                #Graphics Info
                "packetId",
                "status",
                "session",
                "completedLaps",
                "position",
                "currentTime",
                "iCurrentTime",
                "iLastTime",
                "iBestTime",
                "sessionTimeLeft",
                "distanceTraveled",
                "isInPit",
                "currentSectorIndex",
                "lastSectorTime",
                "numberOfLaps",
                "replayTimeMultiplier",
                "normalizedCarPosition",
                "carCoordinates x",
                "carCoordinates y",
                "carCoordinates z"
        ])

    def writeHeaderUnits(self,dataFileWriter):
        dataFileWriter.writerow([

                #Physics Info
                "g",
                "g",
                "g",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "rpm",
                "km/h",
                "deg",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",

                #Graphics Info
                "",
                "",
                "",
                "",
                "",
                "sec",
                "",
                "",
                "",
                "",
                "m",
                "",
                "",
                "",
                "",
                "",
                "",
                "m",
                "m",
                "m"
        ])

    def writeRaceData(self, dataFileWriter):
        SUMMARY_FIELDS1 = "date,time,laps,some number,track,driver,zeros,apostrophe,fifty,empty string,fifty,device,END,1,0, ,no delete partiel,,10,class,session type,date,time,track,driver,NOT USED,NOT USED".split(',')
        row_header = "Partiel,RPM,Speed GPS,T1,T2,Gf. X,Gf. Y,Orientation,Speed rear,Lat.,Lon.,Altitude"

        num_lap=0
        for lap in self.session.laps():
            num_lap+=1
            for row_UNUSED in lap:
                #print(self.session.get_lap_headers())
                #print(self.session.get_lap(num_lap)[0])
                laprows=self.session.get_lap_map(num_lap)
                for row in laprows:
                    dataFileWriter.writerow([
                    row["Gf. X"],
                    row["Gf. Y"],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    row["Orientation"],
                    0,
                    0,
                    row["RPM"],
                    row["Speed GPS"],

                    0,
                    0,
                    0,
                    0,
                    0,
                    row["T1"],
                    row["T2"],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,

                    0,
                    0,
                    0,
                    num_lap-1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    row["Partiel"],
                    0,
                    num_lap,
                    0,
                    0,
                    row["Lat."],
                    row["Lon."],
                    row["Altitude"]
                ])

