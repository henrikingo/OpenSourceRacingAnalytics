import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from .path_util import getSourceDir, getDocumentDir

"""
Based on the AssettoCorsa Writer, but make it write a file like samples/aim_format_exampl.csv.
This is just a step toward the final goal: upload to Grafana and/or Victoria Metrics.
"""


class Writer:
    out_dir = "."
    sessions=None

    def __init__(self, sessions, outputDirectory=None):
        self.out_dir = outputDirectory or getDocumentDir()
        self.out_dir = os.path.expanduser(self.out_dir)
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
        dataFile = "AIM_from_Alfano6_{}_{}.csv".format(
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
        dataFileWriter.writerow(["Format","AiM CSV File"])
        dataFileWriter.writerow(["Venue",self.session.summary["track"]])
        dataFileWriter.writerow(["Vehicle",0])
        dataFileWriter.writerow(["Racer",self.session.summary["driver"]])
        dataFileWriter.writerow(["Championship",""])
        dataFileWriter.writerow(["Date",self.session.summary["date"]])
        dataFileWriter.writerow(["Time",self.session.summary["time"]])
        dataFileWriter.writerow(["Sample Rate",self.session.summary["samplerate"]])
        dataFileWriter.writerow(["Duration",self.session.total_seconds()])
        dataFileWriter.writerow(["Data Source",self.session.summary["device"]])
        dataFileWriter.writerow(["Comment","File created from Alfano data with Open Source Racing Analytics"])
        dataFileWriter.writerow(["Segment","Session"])

        dataFileWriter.writerow(["Beacon Markers"] + self.session.lap_times_sequence_cumulative())
        dataFileWriter.writerow(["Segment Times"] + self.session.lap_times())

        """
        Format,AiM CSV File,,,,,,,,,,,,,,,,,,,,,,
        Venue,SSKC,,,,,,,,,,,,,,,,,,,,,,
        Vehicle,143,,,,,,,,,,,,,,,,,,,,,,
        Racer,Nicholas Thorne,,,,,,,,,,,,,,,,,,,,,,
        Championship,,,,,,,,,,,,,,,,,,,,,,,
        Comment,,,,,,,,,,,,,,,,,,,,,,,
        Date,"Sunday, June 19, 2022",,,,,,,,,,,,,,,,,,,,,,
        Time,3:42 PM,,,,,,,,,,,,,,,,,,,,,,
        Sample Rate,20,,,,,,,,,,,,,,,,,,,,,,
        Duration,951,,,,,,,,,,,,,,,,,,,,,,
        Segment,Session,,,,,,,,,,,,,,,,,,,,,,
        Beacon Markers,77.2,149.128,211.432,270.088,328.931,387.629,446.908,515.157,574.434,633.224,692.104,750.726,809.236,868.166,932.807,951,,,,,,,
        Segment Times,1:17.200,1:11.928,1:02.304,0:58.656,0:58.843,0:58.698,0:59.279,1:08.249,0:59.277,0:58.790,0:58.880,0:58.622,0:58.510,0:58.930,1:04.641,0:18.193,,,,,,,
        ,,,,,,,,,,,,,,,,,,,,,,,
        Time,GPS Speed,GPS Nsat,GPS LatAcc,GPS LonAcc,GPS Slope,GPS Heading,GPS Gyro,GPS Altitude,GPS PosAccuracy,GPS SpdAccuracy,GPS Radius,GPS Latitude,GPS Longitude,Logger Temperature,Water Temp,AccelerometerX,AccelerometerY,AccelerometerZ,GyroX,GyroY,GyroZ,Int Batt Voltage,RPM
        s,km/h, ,g,g,deg,deg,deg/s,m,m,m/s,m,deg,deg,°C,°C,g,g,g,deg/s,deg/s,deg/s,V,rpm
        """


    def sectors_found(self):

        s = 1
        sector_sum = [0]*6
        for s in range(1,7):
            for row in self.session.lap_summary_rows[1:]:
                sector_sum[s-1] += int(row[1+s])
        for i in range(0,5):
            if sector_sum[i] == 0:
                return i

    def writeRaceDataHeader(self, dataFileWriter):
        dataFileWriter.writerow([
            "Time","GPS Speed","GPS Nsat","GPS LatAcc","GPS LonAcc","GPS Slope","GPS Heading","GPS Gyro","GPS Altitude","GPS PosAccuracy","GPS SpdAccuracy","GPS Radius","GPS Latitude","GPS Longitude","Logger Temperature","Water Temp","AccelerometerX","AccelerometerY","AccelerometerZ","GyroX","GyroY","GyroZ","Int Batt Voltage","RPM"
        ])

    def writeHeaderUnits(self,dataFileWriter):

        dataFileWriter.writerow([
            "","","","msec","s","msec","s",
            "s","km/h"," ","g","g","deg","deg","deg/s","m","m","m/s","m","deg","deg","°C","°C","g","g","g","deg/s","deg/s","deg/s","V","rpm"
        ])

    def writeRaceData(self, dataFileWriter):
        SUMMARY_FIELDS1 = "date,time,laps,some number,track,driver,zeros,apostrophe,fifty,empty string,fifty,device,END,1,0, ,no delete partiel,,samplerate,class,session type,date,time,track,driver,NOT USED,NOT USED".split(',')
        row_header = "Partiel,RPM,Speed_GPS,T1,T2,Gf. X,Gf. Y,Orientation,Speed rear,Lat.,Lon.,Altitude"

        num_lap=0
        for lap in self.session.laps():
            num_lap+=1
            lapdata = self.session.lap_summary_rows[num_lap-1]
            laprows=self.session.get_lap_map(num_lap)
            compheaders=self.session.computed_rows_headers()
            comprows=self.session.computed_rows(num_lap)
            for row, comprow in zip(laprows,comprows):
                dataFileWriter.writerow(
                    comprow + [
#                    [comprow[0],
                    row["Speed_GPS"],
                    lapdata[-1], # "Hdop"
                    0,
                    0, # TODO can also be computed from speed?
                    0,
                    row["Orientation"],
                    0,
                    row["Altitude"],
                    0,
                    0,
                    0,
                    row["Lat"],
                    row["Lon"],
                    row["T1"],    # TODO these are wrong but want to produce exactly the sample file for now.
                    row["T2"],
                    row["GfX"],
                    row["GfY"],
                    0,
                    row["GfX"],
                    row["GfY"],
                    0,
                    lapdata[-3], # "Vbattery"
                    row["RPM"]
                    ])
                """
                Add back later...

                num_lap-1,
                row["Partiel"],
                num_lap,

                wall clock time
                seconds .000 since first lap
                seconds . 000 since lap start
                same but as minutes + seconds?

                automatic sectors?
                """
