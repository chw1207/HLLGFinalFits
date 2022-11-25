# Script to calculate photon systematics
# * Run script once per category per mass point, loops over signal processes
# * Output is pandas dataframe

import os, sys
sys.path.append("./tools")

import ROOT
import pickle
import numpy as np
import pandas as pd
from sigmaEff import sigmaEff
from argparse import ArgumentParser
from commonObjects import inputWSName__, outputNuisanceExtMap, productionModes, swd__


def get_parser():
    parser = ArgumentParser(description="Script to calculate effect of the systematic uncertainties")
    parser.add_argument("-m",   "--mass",            help="Higgs mass point",                                        default="",     type=str)
    parser.add_argument("-c",   "--category",        help="RECO category",                                           default="",     type=str)
    parser.add_argument("-e",   "--ext",             help="Extension",                                               default="",     type=str)
    parser.add_argument("-i",   "--inputWSDir",      help="Input WS directory",                                      default="",     type=str)
    parser.add_argument("-psc", "--phoScales",       help="Photon shape systematics: scales",                        default="",     type=str)
    parser.add_argument("-esc", "--eleScales",       help="Electron shape systematics: scales",                      default="",     type=str)
    parser.add_argument("-psm", "--phoSmears",       help="Photon shape systematics: smears",                        default="",     type=str)
    parser.add_argument("-esm", "--eleSmears",       help="Electron shape systematics: smears",                      default="",     type=str)
    parser.add_argument("-tm",  "--thresholdMean",   help="Reject mean variations if larger than thresholdMean",     default=0.05,   type=float)
    parser.add_argument("-ts",  "--thresholdSigma",  help="Reject mean variations if larger than thresholdSigma",    default=0.5,    type=float)
    parser.add_argument("-tr",  "--thresholdRate",   help="Reject mean variations if larger than thresholdRate",     default=0.05,   type=float)

    return parser

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Function to extact sets from WS
def getDataSets(_ws, _nominalDataName, _sname):
    # Define datasets
    rds_nominal = _ws.data(_nominalDataName)
    if (not rds_nominal):
        print("Fail to get RooDataSet %s" %(_nominalDataName))
        sys.exit(1)
    rds_up = _ws.data("%s_%sUp" %(_nominalDataName, _sname))
    if (not rds_up):
        print("Fail to get RooDataSet %s_%sUp" %(_nominalDataName, _sname))
        sys.exit(1)

    # For Smearing "PhiUp" and "PhiDown" are currently identical so you would have three templates, "RhoUp","RhoDown","PhiUp".
    if "SigmaPhi" in _sname:
        rds_do = _ws.data("%s_%sUp" %(_nominalDataName, _sname))
    else:
        rds_do = _ws.data("%s_%sDo" %(_nominalDataName, _sname))
    if (not rds_do):
        print("Fail to get RooDataSet %s_%sDo" %(_nominalDataName, _sname))
        sys.exit(1)

    _sets = {}
    _sets["nominal"] = rds_nominal
    _sets["Up"] = rds_up
    _sets["Do"] = rds_do
    return _sets

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions to extract mean, sigma and rate variations
def getMeanVar(_sets, _var):
    mu, muVar = {}, {}
    for stype, s in _sets.iteritems():
        mu[stype] = s.mean(_var)
    for stype in ["Up", "Do"]:
        muVar[stype] = (mu[stype] - mu["nominal"]) / mu["nominal"]
    x = (abs(muVar["Up"]) + abs(muVar["Do"])) / 2
    if (np.isnan(x)):
        print("Get NaN mean variation")
        sys.exit(1)
    return min(x, args.thresholdMean)


def getSigmaVar(_sets):
    sigma, sigmaVar = {}, {}
    for stype, s in _sets.iteritems():
        arr = np.array([s.get(i).find("CMS_higgs_mass").getVal() for i in range(s.numEntries())])
        xmin, xmax, sigma_eff = sigmaEff(arr)
        sigma[stype] = sigma_eff
    for stype in ["Up", "Do"]:
        sigmaVar[stype] = (sigma[stype] - sigma["nominal"]) / sigma["nominal"]
    x = (abs(sigmaVar["Up"]) + abs(sigmaVar["Do"])) / 2 # average
    if (np.isnan(x)):
        print("Get NaN sigma variation")
        sys.exit(1)
    return min(x, args.thresholdSigma)


def getRateVar(_sets):
    rate, rateVar = {}, {}
    for stype, s in _sets.iteritems():
        rate[stype] = s.sumEntries()
    for stype in ["Up", "Do"]:
        rateVar[stype] = (rate[stype] - rate["nominal"]) / rate["nominal"]
    x = (abs(rateVar["Up"]) + abs(rateVar["Do"])) / 2
    if (np.isnan(x)):
        print("Get NaN rate variation")
        sys.exit(1)
    return min(x, args.thresholdRate)


def main():
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Define dataFrame
    columns_data = ["proc", "cat", "inputWSFile", "nominalDataName"]
    for stype in ["phoScales","phoSmears", "eleScales", "eleSmears"]:
        for s in getattr(args, stype).split(","):
            if s == "": # no systematic
                continue

            if ("EleScale" in s or "EleSigma" in s) and "Merged" in args.category:
                continue # reject officail calibration's variation

            if ("EleHDAL" in s) and "Resolved" in args.category:
                continue # reject dedicated calibration's variation

            for x in ["mean", "sigma", "rate"]:
                columns_data.append("%s_%s_%s"%(s, outputNuisanceExtMap[stype], x))
    data = pd.DataFrame(columns=columns_data)

    # Loop over processes and add row to dataframe
    for _proc in productionModes:
    # for _proc in ["ggH"]:
        _WSFileName = "%s/signal_%s_%s.root"%(args.inputWSDir, _proc, args.mass)
        _nominalDataName = "set_%s_%s" %(args.mass, args.category)
        data = data.append({"proc":_proc, "cat":args.category, "inputWSFile":_WSFileName, "nominalDataName":_nominalDataName}, ignore_index=True, sort=False)

    for ir, r in data.iterrows():
        print(" --> Processing (%s, %s)" %(r["proc"], args.category))

        # Open ROOT file and extract workspace
        f = ROOT.TFile(r["inputWSFile"])
        if f.IsZombie():
            sys.exit(1)
        inputWS = f.Get(inputWSName__)
        if not inputWS:
            print("Fail to get workspace %s" %(inputWSName__))
            sys.exit(1)

        # Loop over scale and smear systematics
        for stype in ["phoScales", "phoSmears", "eleScales", "eleSmears"]:
            for s in getattr(args, stype).split(","):
                if s == "": # no systematic
                    continue

                if ("EleScale" in s or "EleSigma" in s) and "Merged" in args.category:
                    continue # reject officail calibration's variation

                if ("EleHDAL" in s) and "Resolved" in args.category:
                    continue # reject dedicated calibration's variation

                sets = getDataSets(inputWS, r["nominalDataName"], s)
                # If nominal yield = 0:
                if (sets["nominal"].sumEntries() == 0):
                    _meanVar, _sigmaVar, _rateVar = 0, 0, 0
                else:
                    _sigmaVar = getSigmaVar(sets)
                    _meanVar  = getMeanVar(sets, inputWS.var("CMS_higgs_mass"))
                    _rateVar  = getRateVar(sets)

                # Add values to dataFrame
                data.at[ir, "%s_%s_mean"%(s, outputNuisanceExtMap[stype])] = _meanVar
                data.at[ir, "%s_%s_sigma"%(s, outputNuisanceExtMap[stype])] = _sigmaVar
                data.at[ir, "%s_%s_rate"%(s, outputNuisanceExtMap[stype])] = _rateVar

        # Delete ws and close file
        inputWS.Delete()
        f.Close()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Output dataFrame as pickle file to be read in by signalFit.py
    if not os.path.exists("%s/%s/calcSyst"%(swd__, args.ext)):
        os.system("mkdir -p %s/%s/calcSyst"%(swd__, args.ext))

    with open("%s/%s/calcSyst/%s_%s.pkl"%(swd__, args.ext, args.category, args.mass), "wb") as f:
        pickle.dump(data, f)

    print (" --> Successfully saved photon systematics as pkl file: %s/%s/calcSyst/%s_%s.pkl"%(swd__, args.ext, args.category, args.mass))


if __name__ == "__main__" :
    # Extract information from config file:
    parser = get_parser()
    args = parser.parse_args()

    main()