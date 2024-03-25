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

#SUMMARY_FIELDS1 = "date;heure minute;set;immatriculation;Track;Tyre;Vehicule;Driver;SN".split(';')
SUMMARY_FIELDS1 = "date;time;set;immatriculation;track;tyre;car;driver;device_serial".split(';')
SUMMARY_FIELDS2 = "auto;notused;contains;empty;empty2;T_cold;T_hot;empty3".split(';')
TYREDATA = "P;T1;T2;T3; ;T3;T2;T1;P".split(';')

# Alfano produces fixed point values. So we have to add decimal comma into the right place for each.
TYREDATA_DECIMAL= [100,1,1,1,0,1,1,1,100]


class AlfanoTyrecontrolReader:


    def __init__(self, source_dir=None):
        self.source_dir = source_dir or getSourceDir()
        self.source_dir = os.path.expanduser(self.source_dir)
        self._sessions = []

    def list_csv_files(self):
        csvfiles = os.listdir(self.source_dir)
        csvfiles = filter(lambda x: "TYRECONTROL_" == x[:12], csvfiles)
        return csvfiles

    def parse_csv(self):
        for tyrecontrol_file_name in self.list_csv_files():
            tyrecontrol_path = os.path.join(self.source_dir, tyrecontrol_file_name)
            rows=[]
            with open(tyrecontrol_path) as csvfile:
                reader = csv.reader(csvfile, delimiter=";")
                for row in reader:
                    rows.append(row)

                import pprint
                pprint.pprint(rows)
                meta1 = {k:v for k, v in zip(SUMMARY_FIELDS1, rows[1])}
                meta2 = {k:v for k, v in zip(SUMMARY_FIELDS1, rows[2])}
                ambient = {k:v for k, v in zip(SUMMARY_FIELDS2, rows[3])}
                ambient["T_cold"] = int(ambient["T_cold"]) if int(ambient["T_cold"]) < 65535 else -65535
                ambient["T_hot"] = int(ambient["T_hot"]) if int(ambient["T_hot"]) < 65535 else -65535

                for i in range(5,9):
                    rows[i] = [float(v)/float(d) if float(d)>1 else -65535 if v=='65535' else int(v) if v not in ['froid','chaud'] else v
                           for v,d in zip(rows[i],TYREDATA_DECIMAL)]


                tyrecontrol_data = {
                    'source_csv': tyrecontrol_file_name,
                    'cold':{
                        'labels':meta1,
                        'ambient':ambient,
                        'front':{
                            'left':{
                                "P":rows[5][0],
                                "T1":rows[5][1],
                                "T2":rows[5][2],
                                "T3":rows[5][3],
                            },
                            'right':{
                                "T3":rows[5][5],
                                "T2":rows[5][6],
                                "T1":rows[5][7],
                                "P":rows[5][8],
                            },
                        },
                        'rear':{
                            'left':{
                                "P":rows[7][0],
                                "T1":rows[7][1],
                                "T2":rows[7][2],
                                "T3":rows[7][3],
                            },
                            'right':{
                                "T3":rows[7][5],
                                "T2":rows[7][6],
                                "T1":rows[7][7],
                                "P":rows[7][8],
                            },
                        },
                    },
                    'hot':{
                        'labels':meta2,
                        'ambient':ambient,
                        'front':{
                            'left':{
                                "P":rows[6][0],
                                "T1":rows[6][1],
                                "T2":rows[6][2],
                                "T3":rows[6][3],
                            },
                            'right':{
                                "T3":rows[6][5],
                                "T2":rows[6][6],
                                "T1":rows[6][7],
                                "P":rows[6][8],
                            },
                        },
                        'rear':{
                            'left':{
                                "P":rows[8][0],
                                "T1":rows[8][1],
                                "T2":rows[8][2],
                                "T3":rows[8][3],
                            },
                            'right':{
                                "T3":rows[8][5],
                                "T2":rows[8][6],
                                "T1":rows[8][7],
                                "P":rows[8][8],
                            },
                        },
                    },
                }
                print(tyrecontrol_file_name)
                assert rows[3][2] in ["froid et chaud", "froid seulement"]
                assert rows[5][4]=="froid"
                assert rows[6][4]=="chaud"
                assert rows[7][4]=="froid"
                assert rows[8][4]=="chaud"

                # for tyre in [("front","left"),("front","right"),("rear","left"),("rear","right"),]:
                #     for T in ["T1","T2","T3"]:
                #         v = tyrecontrol_data[tyre(0)][tyre(1)][T]
                #         tyrecontrol_data[tyre(0)][tyre(1)][T] = v if v < 65535 else None

                new_session = AlfanoTyrecontrolSession(tyrecontrol_file_name, tyrecontrol_data)

                self._sessions.append(new_session)
            #return "For debugging, just try to get 1 file through first"
        return self._sessions


class AlfanoTyrecontrolSession:
    def __init__(self, filename, tyrecontrol_data):
        self.filename = filename
        self.data = tyrecontrol_data

        date_parts = self.data['cold']['labels']['date'].split("-")
        # Next line is purely to fix a misconfiguration we personally had this one device misconfigured...
        # TODO: Remove before 2028...
        year = date_parts[2] if int(date_parts[2]) < 2028 else "2023"
        isodate = year + "-" +date_parts[1]+ "-" + date_parts[0]
        self.data['cold']['labels']['date'] = isodate

        date_parts = self.data['hot']['labels']['date'].split("-")
        year = date_parts[2] if int(date_parts[2]) < 2028 else "2023"
        isodate = year + "-" +date_parts[1]+ "-" + date_parts[0] if len(date_parts) == 3 else self.data['hot']['labels']['date']
        self.data['hot']['labels']['date'] = isodate

        print(self.data['cold']['labels'])
        print(self.data['hot']['labels'])
        print("")


        self.wallClockUtc = datetime.datetime.strptime(
            self.data['cold']['labels']['date'] + " " + self.data['cold']['labels']['time'],
            '%Y-%m-%d %H:%M'
        )

        if len(self.data['hot']['labels']['time']) == 8:
            self.wallClockUtcHot = datetime.datetime.strptime(
                self.data['hot']['labels']['date'] + " " + self.data['hot']['labels']['time'],
                '%Y-%m-%d %H:%M:%S'
            )
        else:
            self.wallClockUtcHot = datetime.datetime.strptime(
                self.data['hot']['labels']['date'] + " " + self.data['hot']['labels']['time'],
                '%Y-%m-%d %H:%M'
            )

        self.wallClockUtc = self.wallClockUtc+datetime.timedelta(days=48)
        self.wallClockUtcHot = self.wallClockUtcHot+datetime.timedelta(days=48)

        self.data['time']=self.wallClockUtc
        self.data['times']=[self.wallClockUtc, self.wallClockUtcHot]
        self.data['cold']['labels']['date'] = self.wallClockUtc.strftime("%Y-%m-%d")
        self.data['hot']['labels']['date'] = self.wallClockUtcHot.strftime("%Y-%m-%d")
