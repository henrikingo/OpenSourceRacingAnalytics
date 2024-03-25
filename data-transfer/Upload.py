import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from jsonargparse import ArgumentParser, ActionConfigFile

from inout.Alfano import AlfanoReader
from inout.AlfanoTyrecontrol import AlfanoTyrecontrolReader
from inout.AIM import Writer
from db.mongodb import Mongo

def main(argv):
    config = get_config(argv)
    reader = AlfanoReader(source_dir=config.alfano_incoming)
    sessions = reader.translate_sessions()
    writer = Writer(sessions, outputDirectory=config.output_dir)
    writer.write_sessions()
    tc_reader = AlfanoTyrecontrolReader(source_dir=config.alfano_incoming)
    tc_objects = tc_reader.parse_csv()
    m = Mongo(config)
    m.truncate()
    m.uploadNewSessions(sessions)
    m.uploadTyrecontrol(tc_objects)



def get_config(argv):
    parser = ArgumentParser(
        prog='Upload.py',
        description='Upload racing data to S3(for CSV) and MongoDB (for Grafana).',
        default_config_files=["./Upload.yaml", "~/.OSRA/Upload.yaml"])

    parser.add_argument('--config',
                        '-c',
                        help='Default: ./Upload.yaml. Also ~/.OSRA/Upload.yaml and /etc/OSRA/Upload.yaml will be read.')

    parser.add_argument('--alfano-incoming',
                        '-ai',
                        type=str,
                        default='~/Documents/OSRA/AlfanoIncoming/',
                        help='Directory that contains Alfano 6 and TyreControl 2 data as CSV files.')

    parser.add_argument('--output-dir',
                        '-o',
                        type=str,
                        default='~/Documents/OSRA/AlfanoOutput/',
                        help='Directory where to output AIM format CSV files.')

    parser.add_argument('--output-S3',
                        '-S3',
                        type=str,
                        default='TODO',
                        help='S3 bucket where to output AIM format CSV files.')

    parser.add_argument('--mongodb-uri',
                        type=str,
                        default='mongodb+srv://cluster0.0j0l7bk.mongodb.net/?retryWrites=true',
                        help='MongoDB connection string.')


    return parser.parse_args()


if __name__=="__main__":
    main(sys.argv)
