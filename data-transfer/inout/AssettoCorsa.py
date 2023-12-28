import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from .path_util import getSourceDir, getDocumentDir

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
        dataFile = "trackAttack_from_Alfano6_{}_{}.csv".format(
        session.summary["track"],
        session.summary["date"] + "_" + session.summary["time"].replace(":",""))
        dataFile = dataFile.replace(" ", "_")
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

