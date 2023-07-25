import os, sys
import re
import ROOT
import math
from glob import glob
from collections import OrderedDict as ods

class color:
   PURPLE = "\033[95m"
   CYAN = "\033[96m"
   DARKCYAN = "\033[36m"
   BLUE = "\033[94m"
   GREEN = "\033[92m"
   YELLOW = "\033[93m"
   RED = "\033[91m"
   BOLD = "\033[1m"
   UNDERLINE = "\033[4m"
   END = "\033[0m"
   
colorDict = {
    "PURPLE": "\033[95m",
    "CYAN": "\033[96m",
    "DARKCYAN": "\033[36m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "END": "\033[0m"
}
def cprint(text, colorStr=""):
    if len(colorStr) == 0:
        print(text, flush=True)
    else:
        print(colorDict[colorStr.upper()] + text + colorDict["END"], flush=True) 

# Function for iterating over ROOT argsets in workspace
# https://root-forum.cern.ch/t/iterating-over-rooargset/16331/2
def rooiter(x):
    iter = x.iterator()
    ret = iter.Next()
    while ret:
        yield ret
        ret = iter.Next()


def extractWSFileNames(_inputWSDir):
    state = False
    if not os.path.isdir(_inputWSDir):
        print("[ERROR] No such directory...")
        return False
    else:
        return glob("{}/*.root".format(_inputWSDir))


# asssume the structure of the file is workspace_HDalitz_sigMC_{mass}_{cat}_{proc}.root
def extractListOfProcs(_listOfWSFileNames):
    procs = []
    for pName in _listOfWSFileNames:
        f = pName.split("/")[-1] # extract the file name (without the directroy name)
        p = f.split("_")[-1].split(".root")[0]
        if p not in procs:
            procs.append(p)
    procs.sort(key = str.lower) # Define list of procs(alphabetically ordered)
    return procs


def extractListOfMass(_listOfWSFileNames):
    mass = []
    for pName in _listOfWSFileNames:
        f = pName.split("/")[-1] # extract the file name (without the directroy name)
        m = f.split("_")[3]
        if m not in mass:
            mass.append(m)
    mass.sort()
    return mass


# function to extract the directory form the full path
# "./test/test.root" -> "./test"
def extractDirectory(fileName):
    vdirs = fileName.split("/")
    del vdirs[-1]
    direc = "/".join(vdirs)
    return direc