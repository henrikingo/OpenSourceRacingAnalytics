Mongodb schema
==============



OSRA.tsMetrics
---------------

{
   "time":
      "$date":
1689264300000"
      }
   },
   "labels":
      "class":"JUNIOR",
      "date":"2023-07-13",
      "device":"ALFANO 6",
      "driver":"ALBERT",
      "fastest_hundreds":"38",
      "fastest_lap":54.38,
      "fastest_minutes":"00",
      "fastest_seconds":"54",
      "lap":"04",
      "laps":"03",
      "samplerate":"10",
      "sessionId":"ALFANO6_LAP_SN10298_130723_16H05_ALBERT_VIHTI_KARTING_3_5438 (1)",
      "session_type":"FREE",
      "some_constant_number":"10298",
      "time":"16:05",
      "track":"VIHTI KARTING"
   },
   "T2":635.7,
   "GfY":0.994,
   "Lat":60.364823,
   "Speed_GPS":92.6,
   "sec_in_lap":0.0,
   "Altitude":96.0,
   "Sector":1.0,
   "msec_cumulative":0,
   "msec_in_lap":0,
   "GfX":1.004,
   "row_in_lap":0,
   "lap":1,
   "row_cumulative":0,
   "T1":35.0,
   "Orientation"::154.6,
   "_id":
      "$oid":"6601f251ba12544269c5c405"
   },
   "sec_cumulative":0.0,
   "Speed rear":0.0,
   "Lon":24.354168,
   "RPM":13413.0
}


OSRA.tsLaps
-----------
{
   "time":
      "$date":
1689264300000"
      }
   },
   "labels":
      "class":"JUNIOR",
      "date":"2023-07-13",
      "device":"ALFANO 6",
      "driver":"ALBERT",
      "fastest_hundreds":"38",
      "fastest_lap":
   54.38"
      },
      "fastest_minutes":"00",
      "fastest_seconds":"54",
      "lap":"01",
      "laps":"03",
      "samplerate":"10",
      "sessionId":"ALFANO6_LAP_SN10298_130723_16H05_ALBERT_VIHTI_KARTING_3_5438 (1)",
      "session_type":"FREE",
      "some_constant_number":"10298",
      "time":"16:05",
      "track":"VIHTI KARTING"
   },
   "time_partiel_3":0.0
   "Max_Speed_GPS":93.7
   "Min_T2":297.5
   "Max_T2":653.9
   "Max_T1":41.4
   "Max_T3":0
   "Max_T4":0.0
   "Min_Speed_sensor":0
   "Max_RPM":1366.7
   "Min_Speed_GPS":38.6
   "lap_start_cumulative_msec":0
   "lap_end_cumulative_sec":56.48
   "time_partiel_6":0.0
   "Min_T1":35.0
   "lap_start_cumulative_sec":0.0
   "Min_T3":0
   "time_lap":56.48
   "lap":1
   "time_partiel_2":0.0
   "lap_end_cumulative_msec":56480
   "time_partiel_1":56.48
   "time_partiel_4":0.0,
   "_id":{"$oid":"6601f251ba12544269c5c401"},
   "Min_T4":0.0
   "time_partiel_5":0.0
   "Min_RPM":608.3"
   }
}


OSRA.tyres
----------
{
   "_id":"TYRECONTROL_001_002_2805281534.csv",
   "source_csv":"TYRECONTROL_001_002_2805281534.csv",
   "cold":{
      "labels":{
         "date":"2023-07-15",
         "time":"15:24",
         "set":"2",
         "immatriculation":"1",
         "track":"",
         "tyre":"",
         "car":"",
         "driver":"",
         "device_serial":"1751"
      },
      "ambient":{
         "auto":"auto",
         "notused":"65535",
         "contains":"froid et chaud",
         "empty":"",
         "empty2":"",
         "T_cold":26,
         "T_hot":26,
         "empty3":""
      },
      "front":{
         "left":{
            "P":0.73
   ,
            "T1":26,
            "T2":27,
            "T3":27,
         "right":{
            "T3":26,
            "T2":26,
            "T1":27,
            "P":0.74

      },
      "rear":{
         "left":{
            "P":0.72,
            "T1":26,
            "T2":27,
            "T3":28,
         "right":{
            "T3":28,
            "T2":28,
            "T1":28,
            "P":0.81

      }
   },
   "hot":{
      "labels":{
         "date":"2023-07-15",
         "time":"15:34",
         "set":"",
         "immatriculation":"",
         "track":"",
         "tyre":"",
         "car":"",
         "driver":"",
         "device_serial":""
      },
      "ambient":{
         "auto":"auto",
         "notused":"65535",
         "contains":"froid et chaud",
         "empty":"",
         "empty2":"",
         "T_cold":26,
         "T_hot":26,
         "empty3":""
      },
      "front":{
         "left":{
            "P":0.78,
            "T1":27,
            "T2":33,
            "T3":37,
         "right":{
            "T3":31,
            "T2":33,
            "T1":34,
            "P":0.86,
      "rear":{
         "left":{
            "P":1.0,
            "T1":28,
            "T2":30,
            "T3":33,
         "right":{
            "T3":31,
            "T2":31,
            "T1":31,
            "P":0.94
      }
   },
   "time":{ "$date":{1689434640000 } },
   "times":[{ "$date":1689434640000},{ "$date":1689435240000 } ]
}
