import sys
import os
import platform
import threading
import time
import csv
import math
import gzip

from inout.Alfano import AlfanoReader


if __name__=="__main__":
    reader = AlfanoReader()
    reader.translate_sessions()
    reader.write_sessions()
