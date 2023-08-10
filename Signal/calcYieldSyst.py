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
    parser.add_argument("-tr",  "--thresholdRate",   help="Reject mean variations if larger than thresholdRate",     default=0.5,    type=float)

    return parser


# Function to extact hists of systematics from WS
def getDataHists(_ws, _nominalDataName, _sname, _var):
    hname_nominal = _nominalDataName.replace("set", "hist_nominal_{}".format(_sname))
    hname_up = hname_nominal.replace("nominal", "up")
    hname_do = hname_nominal.replace("nominal", "do")
    
    _hists = {
        "nominal": ROOT.TH1F(hname_nominal, "", 60, 110, 170),
        "up"     : ROOT.TH1F(hname_up, "", 60, 110, 170),
        "do"     : ROOT.TH1F(hname_do, "", 60, 110, 170)
    }
    
    # get data
    ds_nominal = _ws.data(_nominalDataName)
    dh_name = _nominalDataName.replace("set", "dh")
    if (_sname == "PhoNoR9Corr"):
        dh_up = _ws.data("%s_%s" %(dh_name, _sname))
        dh_do = _ws.data("%s_%s" %(dh_name, _sname))
    else:
        dh_up = _ws.data("%s_%sUp" %(dh_name, _sname))
        dh_do = _ws.data("%s_%sDo" %(dh_name, _sname))
    
    # convert to TH1
    ds_nominal.fillHistogram(_hists["nominal"], ROOT.RooArgList(_var))
    dh_up.fillHistogram(_hists["up"], ROOT.RooArgList(_var))
    dh_do.fillHistogram(_hists["do"], ROOT.RooArgList(_var))
    
    for b in range(_hists["nominal"].GetNbinsX()+1): # prevent negative events 
        if _hists["nominal"].GetBinContent(b+1) < 0:
            _hists["nominal"].SetBinContent(b+1, 0)

        if _hists["up"].GetBinContent(b+1) < 0:
            _hists["up"].SetBinContent(b+1, 0)

        if _hists["do"].GetBinContent(b+1) < 0:
            _hists["do"].SetBinContent(b+1, 0)


    return _hists


# Functions to extract rate variations
def getRateVar(_hists):
    rate, rateVar = {}, {}   
    for htype, h in _hists.items():
        sumw = 0
        for b in range(h.GetNbinsX()+1):
            sumw += h.GetBinContent(b+1)
        rate[htype] = sumw
    
    for htype in ["up", "do"]:
        rateVar[htype] = (rate[htype] - rate["nominal"]) / rate["nominal"]
    
    x = np.float64((abs(rateVar["up"]) + abs(rateVar["do"])) / 2) # average
    if (np.isnan(x)):
        print("Get NaN rate variation")
        sys.exit(1)
    return min(x, args.thresholdRate)


def main(mass):
    global rate_variations
    rate_variations = [
        "JEC",
        "JER",
        "PhoNoR9Corr",
        "weight_MuID",
        "weight_HLT",
        "weight_L1PF",
        "weight_MuPF",
        "weight_PhoID",
        "weight_puwei"
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
        
        data_proc = pd.DataFrame({"proc":_proc, "cat":args.category, "mass":mass, "year":args.year, "inputWSFile":_WSFileName, "nominalDataName":_nominalDataName}, index=[0])
        data = pd.concat([data, data_proc], ignore_index=True, sort=False)

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
            hists = getDataHists(inputWS, r["nominalDataName"], s, inputWS.var("CMS_higgs_mass"))
            _rateVar = getRateVar(hists)
            data.at[ir, s] = _rateVar
        # close file
        f.Close()
    return data


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
        for s, val in unc.items():
            unc_interp[s] = np.interp(mass_interp, np.array(massBaseList), np.array(val))

        for i, _mp in enumerate(mass_interp):
            volumn_val = [proc, args.category, _mp, args.year]
            for s, val in unc_interp.items():
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
    
    # PyROOT does not display any graphics(root "-b" option)
    ROOT.gROOT.SetBatch()
    ROOT.gErrorIgnoreLevel = ROOT.kWarning

    df_list = []
    for _m in massBaseList:
        df = main(_m)
        df_list.append(df)

    df_mass = pd.concat(df_list, ignore_index=True, axis=0, sort=False)
    calcFactory(df_mass)