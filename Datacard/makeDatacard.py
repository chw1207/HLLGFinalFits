# Datacard making script: https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/part2/settinguptheanalysis/
# * Uses output pkl files of makeYields.py and calcShapeSyst.py (one for yields, and the other one for shape uncertainties)
# * Systematics which have different names will be assumed to be uncorrelated, and the ones with the same name will be assumed 100% correlated.
# * A systematic correlated across channels must have the same p.d.f. in all cards (i.e. always lnN, or all gmN with same N)

import os, sys
sys.path.append("./tools")

import numpy as np
import pandas as pd
from glob import glob
from argparse import ArgumentParser
from collections import OrderedDict as od
from commonTools import color
from commonObjects import category__, massBaseList, dwd__, swd__, decayMode, years
from calcSystematics import addConstantSyst, addFactorySyst, addRateSyst
from writeToDatacard import DCWriter
from systematics import theory_systematics, experimental_systematics


def main():
    infiles = glob("./yields/*.pkl")
    infiles.sort(key=str.lower)
    df_data = pd.DataFrame()
    for f in infiles:
        df_data = pd.concat([df_data, pd.read_pickle(f)], ignore_index=True, axis=0, sort=False)

    # Theory:
    print(" --> Adding theory systematics variations to dataFrame")
    for s in theory_systematics:
        if (s["type"] == "constant"):
            df_data = addConstantSyst(df_data, s)

    # Experimental:
    print(" --> Opening rate variations pkl files")
    rate_list = []
    for year in years:
        for cat in category__.keys():
            try:
                if ("IsoMu" in cat and year != 2017): 
                    continue
                rate_file = "{}/syst/rate_syst_{}_{}.pkl".format(swd__, cat, year)
                rate_list.append(pd.read_pickle(rate_file))
            except:
                print("Error: unable to read the pkl file {}".format(rate_file))
                sys.exit(1)
    df_rate = pd.concat(rate_list, ignore_index=True, axis=0, sort=False)
    
    print(" --> Adding experimental systematics variations to dataFrame")
    # Add constant systematics to dataFrame
    for s in experimental_systematics:
        if (s["type"] == "constant"):
            df_data = addConstantSyst(df_data, s)
        if (s["type"] == "factory"):
            df_data = addFactorySyst(df_data, s)
        if (s["type"] == "rate"):
            df_data = addRateSyst(df_data, s, df_rate)
    
    mass_interp = np.linspace(massBaseList[0], massBaseList[-1], 11, endpoint=True).astype(int)
    outDir = "{}/cards".format(dwd__)
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    for cat in category__.keys():
    # for cat in ["Merged2Gsf_EBHR9"]:
        for mass in mass_interp:
        # for mass in [125]:
            fdataName = "{}/datacard_{}_runII_{}_{}.txt".format(outDir, decayMode, cat, mass)
            print("[INFO] Creating the data card {}".format(fdataName))

            dcw = DCWriter(fdataName, df_data, cat, mass, years, _auto_space=True)
            dcw.writePreamble()
            dcw.writeProcesses()
            for syst in theory_systematics:
                dcw.writeSystematic(syst)
            for syst in experimental_systematics:
                dcw.writeSystematic(syst)
            dcw.writeBreak()
            for syst in experimental_systematics:
                dcw.writeParamSystematic(syst)
            dcw.writePdfIndex()
            dcw.close()


if __name__ == "__main__" :
    main()