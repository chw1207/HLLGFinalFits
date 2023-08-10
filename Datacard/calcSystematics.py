import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from collections import OrderedDict as od
from commonObjects import swd__
from glob import glob


# sd = "systematics dataframe"


# Add column to dataFrame with default value for constant systematics:
# eg.
#   1) "name":"QCDscale_VH", "value":"WH:1.005/0.993,ZH:1.038/0.969" -> {WH:1.005/0.993,ZH:1.038/0.969} (proc as key) -> store in valueDict
#   2) "name":"BR_higgs_dalitz", "value":"0.94/1.06" -> {BR_higgs_dalitz:0.94/1.06} (name as key) -> store in onevalueDict
def addConstantSyst(sd, _syst):
    # extract the values map
    valueDict_list = _syst["value"].split(",")
    valueDict, onevalueDict = od(), od()
    for i in valueDict_list:
        key_plus_value = i.split(":")
        if len(key_plus_value) > 1:
            valueDict[key_plus_value[0]] = key_plus_value[1]
        else:
            onevalueDict[_syst["name"]] = key_plus_value[0]

    sd_mupho = sd[~sd["cat"].str.contains("IsoMu")]
    sd_isomu = sd[sd["cat"].str.contains("IsoMu")]
    if _syst["correlateAcrossYears"] == 0:
        for year, v in valueDict.items():
            column_name = "{}_{}".format(_syst["name"], year)
            sd_mupho[column_name] = "-"
            
            # JEC and JER only for VBF categories
            if (_syst["name"] == "CMS_JEC_13TeV" or _syst["name"] == "CMS_JER_13TeV"):
                sd_mupho.loc[(sd_mupho["type"] == "sig") & (sd_mupho["cat"].str.contains("VBF")) & (year == sd_mupho["year"]), column_name] = v

            # R9 reweighting only for R9 related categories
            elif (_syst["name"] == "CMS_R9_13TeV"):
                sd_mupho.loc[(sd_mupho["type"] == "sig") & (sd_mupho["cat"].str.contains("R9")) & (year == sd_mupho["year"]), column_name] = v
                
            else:
                sd_mupho.loc[(sd_mupho["type"] == "sig") & (year == sd_mupho["year"]), column_name] = v
                
        for year, v in valueDict.items():
            if str(year) != "2017":
                continue
            column_name = "{}_{}".format(_syst["name"], year)
            sd_isomu[column_name] = "-"
            
            # JEC and JER only for VBF categories
            if (_syst["name"] == "CMS_JEC_13TeV" or _syst["name"] == "CMS_JER_13TeV"):
                sd_isomu.loc[(sd_isomu["type"] == "sig") & (sd_isomu["cat"].str.contains("VBF")) & (year == sd_isomu["year"]), column_name] = v

            # R9 reweighting only for R9 related categories
            elif (_syst["name"] == "CMS_R9_13TeV"):
                sd_isomu.loc[(sd_isomu["type"] == "sig") & (sd_isomu["cat"].str.contains("R9")) & (year == sd_isomu["year"]), column_name] = v
                
            else:
                sd_isomu.loc[(sd_isomu["type"] == "sig") & (year == sd_isomu["year"]), column_name] = v

    elif _syst["correlateAcrossYears"] == 1:
        sd_mupho[_syst["name"]] = "-" # initial value
        for k, v in valueDict.items():
            sd_mupho.loc[(sd_mupho["type"] == "sig") & (sd_mupho["proc"].str.contains(k)), _syst["name"]] = v
        for k, v in onevalueDict.items():
            sd_mupho.loc[(sd_mupho["type"] == "sig"), k] = v
            
        sd_isomu[_syst["name"]] = "-" # initial value
        for k, v in valueDict.items():
            sd_isomu.loc[(sd_isomu["type"] == "sig") & (sd_isomu["proc"].str.contains(k)) , _syst["name"]] = v
        for k, v in onevalueDict.items():
            sd_isomu.loc[(sd_isomu["type"] == "sig"), k] = v

    else:
        sd_mupho[_syst["name"]] = "-"
        for year, v in valueDict.items():
            # JEC and JER only for VBF categories
            if (_syst["name"] == "CMS_JEC_13TeV" or _syst["name"] == "CMS_JER_13TeV"):
                sd_mupho.loc[(sd_mupho["type"] == "sig") & (sd_mupho["cat"].str.contains("VBF")), _syst["name"]] = v
            # R9 reweighting only for R9 related categories
            elif (_syst["name"] == "CMS_R9_13TeV"):
                sd_mupho.loc[(sd_mupho["type"] == "sig") & (sd_mupho["cat"].str.contains("R9")), _syst["name"]] = v

            else:
                sd_mupho.loc[(sd_mupho["type"] == "sig") & (sd_mupho["year"] == year), _syst["name"]] = v
                
        sd_isomu[_syst["name"]] = "-"
        for year, v in valueDict.items():
            if str(year) != "2017":
                continue
            # JEC and JER only for VBF categories
            if (_syst["name"] == "CMS_JEC_13TeV" or _syst["name"] == "CMS_JER_13TeV"):
                sd_isomu.loc[(sd_isomu["type"] == "sig") & (sd_isomu["cat"].str.contains("VBF")), _syst["name"]] = v
            # R9 reweighting only for R9 related categories
            elif (_syst["name"] == "CMS_R9_13TeV"):
                sd_isomu.loc[(sd_isomu["type"] == "sig") & (sd_isomu["cat"].str.contains("R9")), _syst["name"]] = v

            else:
                sd_isomu.loc[(sd_isomu["type"] == "sig") & (sd_isomu["year"] == year), _syst["name"]] = v
                
    frames = [sd_mupho, sd_isomu]
    result = pd.concat(frames)       
    return result


def addFactorySyst(sd, _syst):
    # read in the shape uncertainties
    df_list = []
    for year in sd["year"].unique():
        if year == "merged":
            continue
        for cat in sd["cat"].unique():
            if ("IsoMu" in cat and str(year) != "2017"):
                continue
            shape_file = ""
            if "resol" in _syst["name"]:
                shape_file = "{}/syst/shape_syst_resol_{}_{}.pkl".format(swd__, cat, year)
            elif "scale" in _syst["name"]:
                shape_file = "{}/syst/shape_syst_scale_{}_{}.pkl".format(swd__, cat, year)
            else:
                print("Error: unknown shape type: {}".format(_syst))
                sys.exit(1)
            df_list.append(pd.read_pickle(shape_file))
    df = pd.concat(df_list, ignore_index=True, axis=0, sort=False)

    # fill shape uncertainties into systematics dataframe
    sd[_syst["name"]] = "-"
    for year in sd["year"].unique():
        if year == "merged":
            continue
        for cat in sd["cat"].unique():
            if ("IsoMu" in cat and str(year) != "2017"):
                continue
            for proc in sd["procOriginal"].unique():
                if ((proc == "data_obs") or (proc == "bkg_mass")):
                    continue
                for mass in sd["mass"].unique():
                    if (mass == "-"):
                        continue
                    col_name = "{}_{}_{}_{}_{}".format(_syst["name"], proc, mass, cat, year)
                    mask = (sd["type"] == "sig") & (sd["year"] == year) & (sd["cat"] == cat) & (sd["procOriginal"] == proc) & (sd["mass"] == mass)
                    try:
                        idx = df.index[(df["factory"] == col_name) & (df["year"] == year)]
                        sd.loc[mask, _syst["name"]] = df.iloc[idx]["value"].item()
                    except:
                        print("Error: unknown col_name = {} or year = {} in shape uncertainties pkl".format(col_name, year))
                        sys.exit(1)
    return sd


def addRateSyst(sd, _syst, _rate_df):
    # fill rate uncertainties into systematics dataframe
    # sd[_syst["name"]] = "-"
    sd_mupho = sd[~sd["cat"].str.contains("IsoMu")]
    sd_isomu = sd[sd["cat"].str.contains("IsoMu")]
    
    if _syst["correlateAcrossYears"] == 0:
        for year in sd_mupho["year"].unique():
            if year == "merged":
                continue
            col_name = "{}_{}".format(_syst["name"], year)
            sd_mupho[col_name] = "-"
            for cat in sd_mupho["cat"].unique():
                for proc in sd_mupho["procOriginal"].unique():
                    if ((proc == "data_obs") or (proc == "bkg_mass")):
                        continue
                    for mass in sd_mupho["mass"].unique():
                        if (mass == "-"):
                            continue
                        mask1 = (_rate_df["year"] == year) & (_rate_df["cat"] == cat) & (_rate_df["proc"] == proc) & (_rate_df["mass"] == mass)
                        idx = _rate_df.index[mask1]

                        mask2 = (sd_mupho["year"] == year) & (sd_mupho["cat"] == cat) & (sd_mupho["procOriginal"] == proc) & (sd_mupho["mass"] == mass)
                        try:
                            sd_mupho.loc[mask2, col_name] = 1+_rate_df.iloc[idx][_syst["title"]].item() # 1 means central value
                        except:
                            print("can only convert an array of size 1 to a Python scalar")
                            print(1+_rate_df.iloc[idx][_syst["title"]])
                            print(cat, year)
                            sys.exit(1)
                            
        for year in sd_isomu["year"].unique():
            if year == "merged":
                continue
            if str(year) != "2017":
                continue
            
            col_name = "{}_{}".format(_syst["name"], year)
            sd_isomu[col_name] = "-"
            for cat in sd_isomu["cat"].unique():
                for proc in sd_isomu["procOriginal"].unique():
                    if ((proc == "data_obs") or (proc == "bkg_mass")):
                        continue
                    for mass in sd_isomu["mass"].unique():
                        if (mass == "-"):
                            continue
                        mask1 = (_rate_df["year"] == year) & (_rate_df["cat"] == cat) & (_rate_df["proc"] == proc) & (_rate_df["mass"] == mass)
                        idx = _rate_df.index[mask1]

                        mask2 = (sd_isomu["year"] == year) & (sd_isomu["cat"] == cat) & (sd_isomu["procOriginal"] == proc) & (sd_isomu["mass"] == mass)
                        try:
                            sd_isomu.loc[mask2, col_name] = 1+_rate_df.iloc[idx][_syst["title"]].item() # 1 means central value
                        except:
                            print("can only convert an array of size 1 to a Python scalar")
                            print(1+_rate_df.iloc[idx][_syst["title"]])
                            print(cat, year)
                            sys.exit(1)
                            

    if _syst["correlateAcrossYears"] == 1:
        sd_mupho[_syst["name"]] = "-"
        for year in sd_mupho["year"].unique():
            if year == "merged":
                continue
            for cat in sd_mupho["cat"].unique():
                for proc in sd_mupho["procOriginal"].unique():
                    if ((proc == "data_obs") or (proc == "bkg_mass")):
                        continue
                    for mass in sd_mupho["mass"].unique():
                        if (mass == "-"):
                            continue
                        mask1 = (_rate_df["year"] == year) & (_rate_df["cat"] == cat) & (_rate_df["proc"] == proc) & (_rate_df["mass"] == mass)
                        idx = _rate_df.index[mask1]

                        mask2 = (sd_mupho["year"] == year) & (sd_mupho["cat"] == cat) & (sd_mupho["procOriginal"] == proc) & (sd_mupho["mass"] == mass)
                        sd_mupho.loc[mask2, _syst["name"]] = 1+_rate_df.iloc[idx][_syst["title"]].item() # 1 means central value
        
        sd_isomu[_syst["name"]] = "-"
        for year in sd_isomu["year"].unique():
            if year == "merged":
                continue
            if str(year) != "2017":
                continue
            
            for cat in sd_isomu["cat"].unique():
                for proc in sd_isomu["procOriginal"].unique():
                    if ((proc == "data_obs") or (proc == "bkg_mass")):
                        continue
                    for mass in sd_isomu["mass"].unique():
                        if (mass == "-"):
                            continue
                        mask1 = (_rate_df["year"] == year) & (_rate_df["cat"] == cat) & (_rate_df["proc"] == proc) & (_rate_df["mass"] == mass)
                        idx = _rate_df.index[mask1]

                        mask2 = (sd_isomu["year"] == year) & (sd_isomu["cat"] == cat) & (sd_isomu["procOriginal"] == proc) & (sd_isomu["mass"] == mass)
                        sd_isomu.loc[mask2, _syst["name"]] = 1+_rate_df.iloc[idx][_syst["title"]].item() # 1 means central value

    frames = [sd_mupho, sd_isomu]
    result = pd.concat(frames)       
    return result