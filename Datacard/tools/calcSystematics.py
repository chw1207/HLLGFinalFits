import sys
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

    if _syst["correlateAcrossYears"] == 0:
        for year, v in valueDict.iteritems():
            column_name = "{}_{}".format(_syst["name"], year)
            sd[column_name] = "-"

            # JEC and JER only for VBF categories
            if (_syst["name"] == "CMS_JEC_13TeV" or _syst["name"] == "CMS_JER_13TeV"):
                sd.loc[(sd["type"] == "sig") & (sd["cat"].str.contains("VBF")) & (year == sd["year"]), column_name] = v

            # R9 reweighting only for R9 related categories
            elif (_syst["name"] == "CMS_R9_13TeV"):
                sd.loc[(sd["type"] == "sig") & (sd["cat"].str.contains("R9")) & (year == sd["year"]), column_name] = v

            else:
                sd.loc[(sd["type"] == "sig") & (year == sd["year"]), column_name] = v

    elif _syst["correlateAcrossYears"] == 1:
        sd[_syst["name"]] = "-" # initial value
        for k, v in valueDict.iteritems():
            sd.loc[(sd["type"] == "sig") & (sd["proc"].str.contains(k)), _syst["name"]] = v
        for k, v in onevalueDict.iteritems():
            sd.loc[(sd["type"] == "sig"), k] = v

    else:
        sd[_syst["name"]] = "-"
        for year, v in valueDict.iteritems():
            # JEC and JER only for VBF categories
            if (_syst["name"] == "CMS_JEC_13TeV" or _syst["name"] == "CMS_JER_13TeV"):
                sd.loc[(sd["type"] == "sig") & (sd["cat"].str.contains("VBF")), _syst["name"]] = v
            # R9 reweighting only for R9 related categories
            elif (_syst["name"] == "CMS_R9_13TeV"):
                sd.loc[(sd["type"] == "sig") & (sd["cat"].str.contains("R9")), _syst["name"]] = v

            else:
                sd.loc[(sd["type"] == "sig") & (sd["year"] == year), _syst["name"]] = v
    return sd


def addFactorySyst(sd, _syst):
    # read in the shape uncertainties
    df_list = []
    for year in sd["year"].unique():
        if year == "merged":
            continue
        for cat in sd["cat"].unique():
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
    if _syst["correlateAcrossYears"] == 0:
        for year in sd["year"].unique():
            if year == "merged":
                continue

            col_name = "{}_{}".format(_syst["name"], year)
            sd[col_name] = "-"

            for cat in sd["cat"].unique():
                for proc in sd["procOriginal"].unique():
                    if ((proc == "data_obs") or (proc == "bkg_mass")):
                        continue
                    for mass in sd["mass"].unique():
                        if (mass == "-"):
                            continue
                        mask1 = (_rate_df["year"] == year) & (_rate_df["cat"] == cat) & (_rate_df["proc"] == proc) & (_rate_df["mass"] == mass)
                        idx = _rate_df.index[mask1]

                        mask2 = (sd["year"] == year) & (sd["cat"] == cat) & (sd["procOriginal"] == proc) & (sd["mass"] == mass)
                        sd.loc[mask2, col_name] = 1+_rate_df.iloc[idx][_syst["title"]].item() # 1 means central value

    if _syst["correlateAcrossYears"] == 1:
        sd[_syst["name"]] = "-"
        for year in sd["year"].unique():
            if year == "merged":
                continue
            for cat in sd["cat"].unique():
                for proc in sd["procOriginal"].unique():
                    if ((proc == "data_obs") or (proc == "bkg_mass")):
                        continue
                    for mass in sd["mass"].unique():
                        if (mass == "-"):
                            continue
                        mask1 = (_rate_df["year"] == year) & (_rate_df["cat"] == cat) & (_rate_df["proc"] == proc) & (_rate_df["mass"] == mass)
                        idx = _rate_df.index[mask1]

                        mask2 = (sd["year"] == year) & (sd["cat"] == cat) & (sd["procOriginal"] == proc) & (sd["mass"] == mass)
                        sd.loc[mask2, _syst["name"]] = 1+_rate_df.iloc[idx][_syst["title"]].item() # 1 means central value

    return sd