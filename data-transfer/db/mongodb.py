import datetime
import copy
from collections import OrderedDict
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

NODATE = datetime.date(1970,1,1)


class Mongo:
    def __init__(self, config):
        self.config=config
        self.uri = config.mongodb_uri
        print(self.uri)
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        self.db=self.client["OSRA"]
        self.laps = self.db["tsLaps"]
        self.metrics = self.db["tsMetrics"]
        self.tyres = self.db["tyres"]
        #print("\n\n".join([str(s) for s in [self.client, self.db, self.laps, self.metrics]]))

    def truncate(self):
        self.tyres.delete_many({})
        return
        self.laps.delete_many({})
        self.metrics.delete_many({})

    def uploadNewSessions(self, sessions):
        for s in sessions:
            self.uploadSession(s)

    def uploadSession(self, session):
        meta = self.getMeta(session)
        self.sendLapData(session, meta)
        self.sendMetrics(session, meta)


    def uploadTyrecontrol(self, objects):
        docs=[]
        for o in objects:
            doc = o.data
            doc["_id"] = doc["source_csv"]
            docs.append(doc)

        print("Insert to Mongodb {} Tyrecontrol 2 objects, between {} and {}.".format( len(docs), docs[0]['cold']['labels']['date'], docs[-1]['cold']['labels']['date']))
        self.tyres.insert_many(docs)


    def getMeta(self, s):
        SUMMARY_FIELDS1 = "date,time,laps,some_constant_number,track,driver,fastest_minutes,apostrophe,fastest_seconds,empty_string,fastest_hundreds,device,END,xxx1,xxx0,xxx,no_delete_partiel,yyy,samplerate,class,session_type,date,time,track,driver,NOT_USED,NOT_USED".split(',')

        #meta = OrderedDict(zip(SUMMARY_FIELDS1, copy.copy(s.summary)))
        meta = copy.copy(s.summary)
        meta['sessionId'] = s.dirname
        return meta

    def sendLapData(self, s, meta):
        LAP_FIELDS = "Sector,RPM,Speed GPS,T1,T2,GfX,GfY,Orientation,Speed rear,Lat,Lon,Altitude".split(",")
        SUMMARY_FIELDS2 = "lap,time_lap,time_partiel_1,time_partiel_2,time_partiel_3,time_partiel_4,time_partiel_5,time_partiel_6,Min_RPM,Max_RPM,Min_Speed_GPS,Max_Speed_GPS,Min_T1,Max_T1,Min_T2,Max_T2,Min_T3,Max_T3,Min_T4,Max_T4,Min_Speed_sensor,Max_Speed_sensor,RPM_max_gear,Type_de_champs,Vbattery,max_EGT,Hdop".split(',')

        docs = []

        lapnum = 1
        for _ in s.all_lap_summary_rows():
            m=s.all_lap_summary_maps(lapnum)
            assert all([type(v)!=type("s") for k,v in m.items()])

            cumul_time=datetime.timedelta(milliseconds=m["lap_start_cumulative_msec"])
            doc= {
                'time': s.wallClockUtc+cumul_time,
                'labels':meta
            }
            doc['labels']['lap']=str(lapnum).zfill(2)
            metrics = s.all_lap_summary_maps(lapnum)
            doc.update(metrics)
            docs.append(copy.deepcopy(doc))
            lapnum+=1
        self.laps.insert_many(docs)

    def sendMetrics(self, s, meta):
        docs = []
        start_time = s.wallClockUtc
        lapnum = 1
        for lap in range(1, s.num_laps()+1):
            for row in s.all_rows(lap):
                metrics = OrderedDict(zip(s.all_headers(), row))
                cumul_time=datetime.timedelta(milliseconds=metrics["msec_cumulative"])
                doc= {
                    'time': start_time+cumul_time,
                    'labels':meta
                }
                doc.update(metrics)
                docs.append(doc)
            lapnum+=1
        print("Insert to Mongodb", meta['sessionId'] , start_time, doc['time'])
        self.metrics.insert_many(docs)
