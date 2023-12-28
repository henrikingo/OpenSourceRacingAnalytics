import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from inout.Alfano import AlfanoReader, AssettoCorsaWriter


if __name__=="__main__":
    reader = AlfanoReader()
    sessions = reader.translate_sessions()
    writer = AssettoCorsaWriter(sessions)
    writer.write_sessions()
