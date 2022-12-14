# Script to calculate shape systematics of photon and electron
# * https://twiki.cern.ch/twiki/bin/view/CMS/EgammaMiniAODV2#Energy_Scale_and_Smearing
# * Run script once per category, loops over signal processes.
# * photon shape: uncertainties of standard EGM calibration
# * merged electron shape: uncertainties of dedicated HDALITZ calibration
# * resolved electron shape: uncertainties of standard EGM calibration
# * Outputs are pandas dataframes for scale and resolutions respectively @ all mass points

import os, sys
sys.path.append("./tools")

import ROOT
import pickle
import numpy as np
import pandas as pd
from sigmaEff import sigmaEff
from argparse import ArgumentParser
from commonObjects import productionModes, inputWSName__, swd__, massBaseList, decayMode
from commonTools import color

def get_parser():
    parser = ArgumentParser(description="Script to calculate effect of the shape systematic uncertainties")
    parser.add_argument("-c",   "--category",        help="RECO category",                                           default="",     type=str)
    parser.add_argument("-y",   "--year",            help="year",                                                    default="",     type=str)
    parser.add_argument("-i",   "--inputWSDir",      help="Input WS directory",                                      default="",     type=str)
    parser.add_argument("-tm",  "--thresholdMean",   help="Reject mean variations if larger than thresholdMean",     default=0.05,   type=float)
    parser.add_argument("-ts",  "--thresholdSigma",  help="Reject mean variations if larger than thresholdSigma",    default=0.5,    type=float)

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
# Functions to extract mean and sigma variations
def getMeanVar(_sets, _var):
    mu, muVar = {}, {}
    for stype, s in _sets.iteritems():
        mu[stype] = s.mean(_var)
    for stype in ["Up", "Do"]:
        muVar[stype] = (mu[stype] - mu["nominal"]) / mu["nominal"]
    x = np.float64((abs(muVar["Up"]) + abs(muVar["Do"])) / 2)
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
    x = np.float64((abs(sigmaVar["Up"]) + abs(sigmaVar["Do"])) / 2) # average
    if (np.isnan(x)):
        print("Get NaN sigma variation")
        sys.exit(1)
    return min(x, args.thresholdSigma)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main(mass):
    shape_variations = [
        "PhoScaleStat",
        "PhoScaleSyst",
        "PhoScaleGain",
        "PhoSigmaPhi",
        "PhoSigmaRho",
        "EleScaleStat",
        "EleScaleSyst",
        "EleScaleGain",
        "EleSigmaPhi",
        "EleSigmaRho",
        "EleHDALScale",
        "EleHDALSmear"
    ]

    # Define dataFrame
    columns_data_scale = ["proc", "cat", "mass", "year", "inputWSFile", "nominalDataName"]
    columns_data_resol = ["proc", "cat", "mass", "year", "inputWSFile", "nominalDataName"]
    shape_scale = []
    shape_resol = []
    for s in shape_variations:
        if ("EleScale" in s or "EleSigma" in s) and "Merged" in args.category:
            continue # reject officail calibration's variation
        if ("EleHDAL" in s) and "Resolved" in args.category:
            continue # reject dedicated calibration's variation
        for x in ["scale", "resol"]:
            if (x == "scale" and "Scale" in s):
                columns_data_scale.append(s)
                shape_scale.append(s)
            elif (x == "resol" and ("Sigma" in s or "Smear" in s)):
                columns_data_resol.append(s)
                shape_resol.append(s)
    data_scale = pd.DataFrame(columns=columns_data_scale)
    data_resol = pd.DataFrame(columns=columns_data_resol)

    # Loop over processes and add row to dataframe
    for _proc in productionModes:
        _WSFileName = "%s/signal_%s_%s.root" %(args.inputWSDir, _proc, mass)
        _nominalDataName = "set_%s_%s" %(mass, args.category)
        data_scale = data_scale.append({"proc":_proc, "cat":args.category, "mass":mass, "year":args.year, "inputWSFile":_WSFileName, "nominalDataName":_nominalDataName}, ignore_index=True, sort=False)
        data_resol = data_resol.append({"proc":_proc, "cat":args.category, "mass":mass, "year":args.year, "inputWSFile":_WSFileName, "nominalDataName":_nominalDataName}, ignore_index=True, sort=False)

    # add the scale unc to dataframe
    for ir, r in data_scale.iterrows():
        print(" --> Processing ({proc:>4}, {cat}, {m}, {y:<5}) scale uncertainties".format(proc=r["proc"], cat=args.category, m=r["mass"], y=r["year"]))
        # Open ROOT file and extract workspace
        f = ROOT.TFile(r["inputWSFile"], "READ")
        if f.IsZombie():
            sys.exit(1)
        inputWS = f.Get(inputWSName__)
        if not inputWS:
            print("Fail to get workspace %s" %(inputWSName__))
            sys.exit(1)
        # Add values to dataFrame
        for s in shape_scale:
            sets = getDataSets(inputWS, r["nominalDataName"], s)
            _meanVar = getMeanVar(sets, inputWS.var("CMS_higgs_mass"))
            data_scale.at[ir, s] = _meanVar
        # close file
        f.Close()
    shape_scale_ele = [s for s in shape_scale if "Ele" in s]
    shape_scale_pho = [s for s in shape_scale if "Pho" in s]
    if (len(shape_scale_ele) != 1):
        data_scale["EleTotalScale"] = np.sqrt(np.power(data_scale[shape_scale_ele], 2).sum(axis=1))
    else:
        data_scale["EleTotalScale"] = data_scale[shape_scale_ele[0]]
    if (len(shape_scale_pho) != 1):
        data_scale["PhoTotalScale"] = np.sqrt(np.power(data_scale[shape_scale_pho], 2).sum(axis=1))
    else:
        data_scale["PhoTotalScale"] = data_scale[shape_scale_pho[0]]
    # root of quadrature sum electron and photon
    data_scale["TotalScale"] = np.sqrt(np.power(data_scale[["EleTotalScale", "PhoTotalScale"]], 2).sum(axis=1))

    # add the resolution unc to dataframe
    for ir, r in data_resol.iterrows():
        print(" --> Processing ({proc:>4}, {cat}, {m}, {y:<5}) resol uncertainties".format(proc=r["proc"], cat=args.category, m=r["mass"], y=r["year"]))
        # Open ROOT file and extract workspace
        f = ROOT.TFile(r["inputWSFile"])
        if f.IsZombie():
            sys.exit(1)
        inputWS = f.Get(inputWSName__)
        if not inputWS:
            print("Fail to get workspace %s" %(inputWSName__))
            sys.exit(1)
        # Add values to dataFrame
        for s in shape_resol:
            sets = getDataSets(inputWS, r["nominalDataName"], s)
            _sigmaVar = getSigmaVar(sets)
            data_resol.at[ir, s] = _sigmaVar
        # close file
        f.Close()
    shape_resol_ele = [s for s in shape_resol if "Ele" in s]
    shape_resol_pho = [s for s in shape_resol if "Pho" in s]
    if (len(shape_resol_ele) != 1):
        data_resol["EleTotalResol"] = np.sqrt(np.power(data_resol[shape_resol_ele], 2).sum(axis=1))
    else:
        data_resol["EleTotalResol"] = data_resol[shape_resol_ele[0]]
    if (len(shape_resol_pho) != 1):
        data_resol["PhoTotalResol"] = np.sqrt(np.power(data_resol[shape_resol_pho], 2).sum(axis=1))
    else:
        data_resol["PhoTotalResol"] = data_resol[shape_resol_pho[0]]
    # root of quadrature sum electron and photon
    data_resol["TotalResol"] = np.sqrt(np.power(data_resol[["EleTotalResol", "PhoTotalResol"]], 2).sum(axis=1))

    return data_scale, data_resol


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def calcFactory(df, shape=""):
    if shape not in ["scale", "resol"]:
        print("Error: unknown shape type: {}, available type [scale, resol]".format(shape))
        sys.exit(1)

    mass_interp = np.linspace(massBaseList[0], massBaseList[-1], 11, endpoint=True).astype(int)
    column_title = ["proc", "cat", "mass", "year", "factory", "value"]
    df_data = pd.DataFrame(columns=column_title)

    for proc in df["proc"].unique():
        unc = []
        for ir, r in df.iterrows():
            if proc != r["proc"]:
                continue
            if shape == "scale":
                unc.append(r["TotalScale"])
            else:
                unc.append(r["TotalResol"])
        unc_interp = np.interp(mass_interp, np.array(massBaseList), np.array(unc))

        for i, _mp in enumerate(mass_interp):
            factory_name = "CMS_{}_{}_{}_{}_{}_{}".format(decayMode, shape, proc, _mp, args.category, args.year)
            df_data.loc[len(df_data)] = [proc, args.category, _mp, args.year, factory_name, unc_interp[i]]

    # Output dataFrame as pickle file
    if not os.path.exists("{}/syst".format(swd__)):
        os.system("mkdir -p {}/syst".format(swd__))
    with open("{}/syst/shape_syst_{}_{}_{}.pkl".format(swd__, shape, args.category, args.year), "wb") as f:
        pickle.dump(df_data, f)
    print(" --> Successfully saved {} systematics as pkl file: {}/syst/shape_syst_{}_{}_{}.pkl".format(shape, swd__, shape, args.category, args.year))


if __name__ == "__main__" :
    parser = get_parser()
    args = parser.parse_args()

    df_scale_list, df_resol_list = [], []
    for _m in massBaseList:
        df_scale, df_resol = main(_m)
        df_scale_list.append(df_scale)
        df_resol_list.append(df_resol)

    df_scale_mass = pd.concat(df_scale_list, ignore_index=True, axis=0, sort=False)
    df_resol_mass = pd.concat(df_resol_list, ignore_index=True, axis=0, sort=False)

    calcFactory(df_scale_mass, shape="scale")
    calcFactory(df_resol_mass, shape="resol")