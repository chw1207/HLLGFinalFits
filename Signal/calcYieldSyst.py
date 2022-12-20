import os, sys
sys.path.append("./tools")

import ROOT
import pickle
import numpy as np
import pandas as pd
from argparse import ArgumentParser
from collections import OrderedDict as od
from commonObjects import productionModes, inputWSName__, massBaseList, swd__


def get_parser():
    parser = ArgumentParser(description="Script to calculate effect of the shape systematic uncertainties")
    parser.add_argument("-c",   "--category",        help="RECO category",                                           default="",     type=str)
    parser.add_argument("-y",   "--year",            help="year",                                                    default="",     type=str)
    parser.add_argument("-i",   "--inputWSDir",      help="Input WS directory",                                      default="",     type=str)
    parser.add_argument("-tr",  "--thresholdRate",   help="Reject mean variations if larger than thresholdRate",     default=0.5,      type=float)

    return parser


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Function to extact sets from WS
# ! FIXEDME: up->UP and do->Do for the same naming method
def getDataSets(_ws, _nominalDataName, _sname):
    # Define datasets
    rds_nominal = _ws.data(_nominalDataName)
    if (not rds_nominal):
        print("Fail to get RooDataSet %s" %(_nominalDataName))
        sys.exit(1)
    rds_up = _ws.data("%s_%sUp" %(_nominalDataName, _sname))
    if (not rds_up):
        print("Fail to get RooDataSet %s_%sup" %(_nominalDataName, _sname))
        sys.exit(1)
    rds_do = _ws.data("%s_%sDo" %(_nominalDataName, _sname))
    if (not rds_do):
        print("Fail to get RooDataSet %s_%sdo" %(_nominalDataName, _sname))
        sys.exit(1)
    _sets = {}
    _sets["nominal"] = rds_nominal
    _sets["Up"] = rds_up
    _sets["Do"] = rds_do
    return _sets


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions to extract rate variations
def getRateVar(_sets):
    rate, rateVar = {}, {}
    for stype, s in _sets.iteritems():
        rate[stype] = s.sumEntries()
    for stype in ["Up", "Do"]:
        rateVar[stype] = (rate[stype] - rate["nominal"]) / rate["nominal"]
    x = np.float64((abs(rateVar["Up"]) + abs(rateVar["Do"])) / 2) # average
    if (np.isnan(x)):
        print("Get NaN rate variation")
        sys.exit(1)
    return min(x, args.thresholdRate)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main(mass):
    global rate_variations
    rate_variations = [
        "puwei",
        "l1pf",
        "hlt",
        "recoE",
        "eleID",
        "phoID",
        "csev",
        "JER",
        "JEC"
    ]

    # Define dataFrame
    columns_data = ["proc", "cat", "mass", "year", "inputWSFile", "nominalDataName"]
    for s in rate_variations:
        columns_data.append(s)
    data = pd.DataFrame(columns=columns_data)

    # Loop over processes and add row to dataframe
    for _proc in productionModes:
        _WSFileName = "%s/signal_%s_%s.root" %(args.inputWSDir, _proc, mass)
        _nominalDataName = "set_%s_%s" %(mass, args.category)
        data = data.append({"proc":_proc, "cat":args.category, "mass":mass, "year":args.year, "inputWSFile":_WSFileName, "nominalDataName":_nominalDataName}, ignore_index=True, sort=False)

    for ir, r in data.iterrows():
        print(" --> Processing ({proc:>4}, {cat}, {m}, {y:<5}) rate uncertainties".format(proc=r["proc"], cat=args.category, m=r["mass"], y=r["year"]))
        # Open ROOT file and extract workspace
        f = ROOT.TFile(r["inputWSFile"], "READ")
        if f.IsZombie():
            sys.exit(1)
        inputWS = f.Get(inputWSName__)
        if not inputWS:
            print("Fail to get workspace %s" %(inputWSName__))
            sys.exit(1)
        # Add values to dataFrame
        for s in rate_variations:
            sets = getDataSets(inputWS, r["nominalDataName"], s)
            _rateVar = getRateVar(sets)
            data.at[ir, s] = _rateVar
        # close file
        f.Close()

    return data

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def calcFactory(df):
    mass_interp = np.linspace(massBaseList[0], massBaseList[-1], 11, endpoint=True).astype(int)
    column_title = ["proc", "cat", "mass", "year"] + rate_variations
    df_data = pd.DataFrame(columns=column_title)

    # for s in rate_variations:
    for proc in df["proc"].unique():
        unc = od([(s, []) for s in rate_variations])
        for ir, r in df.iterrows():
            if proc != r["proc"]:
                continue
            for s in rate_variations:
                unc[s].append(r[s])

        unc_interp = od([(s, []) for s in rate_variations])
        for s, val in unc.iteritems():
            unc_interp[s] = np.interp(mass_interp, np.array(massBaseList), np.array(val))

        for i, _mp in enumerate(mass_interp):
            volumn_val = [proc, args.category, _mp, args.year]
            for s, val in unc_interp.iteritems():
                volumn_val.append(unc_interp[s][i])
            df_data.loc[len(df_data)] = volumn_val

    # Output dataFrame as pickle file
    if not os.path.exists("{}/syst".format(swd__)):
        os.system("mkdir -p {}/syst".format(swd__))
    with open("{}/syst/rate_syst_{}_{}.pkl".format(swd__, args.category, args.year), "wb") as f:
        pickle.dump(df_data, f)
    print(" --> Successfully saved rate systematics as pkl file: {}/syst/rate_syst_{}_{}.pkl".format(swd__, args.category, args.year))


if __name__ == "__main__" :
    parser = get_parser()
    args = parser.parse_args()

    df_list = []
    for _m in massBaseList:
        df = main(_m)
        df_list.append(df)

    df_mass = pd.concat(df_list, ignore_index=True, axis=0, sort=False)
    calcFactory(df_mass)