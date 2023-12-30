import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from inout.Alfano import AlfanoReader
#from inout.AssettoCorsa import AssettoCorsaWriter
from inout.AIM import Writer

if __name__=="__main__":
    reader = AlfanoReader()
    sessions = reader.translate_sessions()
    writer = Writer(sessions)
    writer.write_sessions()
