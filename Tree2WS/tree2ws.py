# Script to convert HDalitz trees to RooWorkspace (compatible for finalFits)
# Assumes tree names of the format:
#  * miniTree
# For systematics: requires trees of the format:
#  * miniTree_<syst> e.g. miniTree_JERUp, miniTree_PhoScaleStatDo

import ROOT
import sys
import os
import re
import pandas as pd
from pprint import pprint
from argparse import ArgumentParser
from collections import OrderedDict as od
from root_numpy import array2tree
from root_pandas import read_root
from importlib import import_module
from commonObjects import inputWSName__, category__, productionModes
from commonTools import color

def get_parser():
    parser = ArgumentParser(description="Script to convert data trees to RooWorkspace (compatible for finalFits)")
    parser.add_argument("-c",  "--config",          help="Input config: specify list of variables/analysis categories", default=None, type=str)
    parser.add_argument("-y",  "--year",            help="Year",                                                        default=2017, type=int)
    parser.add_argument("-m",  "--mass",            help="mass point",                                                  default=125,  type=int)
    parser.add_argument("-p",  "--productionMode",  help="Production mode [ggH, VBF, WH, ZH, ttH, bbH]",                default="ggH",type=str)
    parser.add_argument("-ds", "--doSystematics",   help="Add systematics datasets to output WS",                       default=False,action="store_true")
    return parser


def add_vars_to_workspace(_ws, _var_list):
    # Add intLumi var
    intLumi = ROOT.RooRealVar("intLumi", "intLumi", 1000.,0., 999999999.)
    intLumi.setConstant(True)
    getattr(_ws, "import")(intLumi, ROOT.RooFit.Silence())

    _vars = od()
    for var in _var_list:
        if var in ["type", "category"]:
            continue
        if var == "CMS_higgs_mass":
            _vars[var] = ROOT.RooRealVar(var, var, mass, 110, 170, "GeV") # initial, lower bound, upper bound
            _vars[var].setBins(60)
        elif "weight" in var:
            _vars[var] = ROOT.RooRealVar(var, var, 0.)
        else:
            _vars[var] = ROOT.RooRealVar(var, var, 1., -999999, 999999)
            _vars[var].setBins(1)
        getattr(_ws, "import")(_vars[var], ROOT.RooFit.Silence())
    return _vars.keys()


# Function to make RooArgSet
def make_argset(_ws, _varNames):
    _aset = ROOT.RooArgSet()
    for v in _varNames:
        _aset.add(_ws.var(v))
    return _aset


def main():
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 1) Convert tree to pandas dataframe
    # Create dataframe to store all events in file
    data = pd.DataFrame()
    if doSystematics:
        sdata = pd.DataFrame()
    print("[INFO] Read file:")
    pprint(inputTreeFile)
    data = read_root(inputTreeFile, inputTreeName, columns=TreeVars)
    data["type"] = "nominal"

    # For systematics trees: only for events in experimental phase space
    rate_syst_list = []
    if doSystematics:
        sdf = pd.DataFrame()
        for s in systematics:
            streeName = "{}_{}".format(inputTreeName, s)
            sdf = read_root(inputTreeFile, streeName, columns=TreeVars)
            sdf["type"] = s
            sdata = pd.concat([sdata, sdf], ignore_index=True, axis=0, sort=False)

        for sw in systWeis:
            sdf = read_root(inputTreeFile, inputTreeName, columns=TreeVars+[sw]).drop("weight", axis=1).rename(columns={sw: "weight"})
            rate_syst = sw.replace("weight_", "")
            rate_syst_list.append(rate_syst)
            sdf["type"] = rate_syst
            sdata = pd.concat([sdata, sdf], ignore_index=True, axis=0, sort=False)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 2) Convert pandas dataframe to RooWorkspace
    # Define output workspace file
    outputWSDir = os.path.dirname(outputWSFile)
    if not os.path.exists(outputWSDir):
        os.system("mkdir -p %s" %outputWSDir)
    print("[INFO] Save workspace: {}".format(outputWSFile))
    fout = ROOT.TFile(outputWSFile, "RECREATE")
    foutdir = fout.mkdir(inputWSName__.split("/")[0])
    foutdir.cd()
    ws = ROOT.RooWorkspace(inputWSName__.split("/")[1], inputWSName__.split("/")[1])

    # Add variables to workspace
    varNames = add_vars_to_workspace(ws, data.columns)

    # Loop over cats
    for cat in category__:
        # a) make RooDataSets:
        mask = category__[cat]
        # Convert dataframe to structured array, then to ROOT tree
        sa = data.query(mask).drop("type", axis=1).to_records()
        t = array2tree(sa)
        # Add dataset to worksapce
        dname = "set_%d_%s" %(mass, cat)

        # Make argset
        aset = make_argset(ws, varNames)

        # Convert tree to RooDataset and add to workspace
        dset = ROOT.RooDataSet(dname, dname, t, aset, "", "weight")
        getattr(ws, "import")(dset)

        # Delete trees and RooDataSet from heap
        t.Delete()
        dset.Delete()
        del sa

        if doSystematics:
            for s in systematics:
                # Create mask for systematic variation
                sa = sdata[sdata["type"] == s].query(category__[cat]).drop("type", axis=1).to_records()
                t = array2tree(sa)

                # Make argset
                aset_unc = make_argset(ws, systematicsVars)
                dname_unc = "set_%d_%s_%s" %(mass, cat, s)
                dset_unc = ROOT.RooDataSet(dname_unc, dname_unc, t, aset_unc, "", "weight")

                # Add to workspace
                getattr(ws, "import")(dset_unc)

                # Delete trees and RooDataHist
                t.Delete()
                dset_unc.Delete()
                del sa

            for sw in rate_syst_list:
                # Create mask for systematic variation
                sa = sdata[sdata["type"] == sw].query(category__[cat]).drop("type", axis=1).to_records()
                t = array2tree(sa)

                # Make argset
                aset_unc = make_argset(ws, systematicsVars)
                dname_unc = "set_%d_%s_%s" %(mass, cat, sw)
                dset_unc = ROOT.RooDataSet(dname_unc, dname_unc, t, aset_unc, "", "weight")

                # Add to workspace
                getattr(ws, "import")(dset_unc)

                # Delete trees and RooDataHist
                t.Delete()
                dset_unc.Delete()
                del sa

    # Write WS to file
    ws.Write()
    fout.Close()
    ws.Delete()


if __name__ == "__main__" :
    print(" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HLLG TREE 2 WS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ")
    # Extract information from config file:
    parser = get_parser()
    args = parser.parse_args()

    if args.config is None:
        print("Please specify the config file! eg. config")
        parser.print_help()
        sys.exit(1)

    # Extract arguments
    mass            = args.mass
    year            = args.year
    productionMode  = args.productionMode
    doSystematics   = args.doSystematics
    if productionMode not in productionModes:
        print("Available modes: {}".format(productionModes))
        sys.exit(1)

    # Import config options
    cfg = import_module(re.sub(".py","", args.config)).trees2ws_cfg[mass][year]
    inputTreeFile    = cfg["inputTreeFiles"][productionMode]
    inputTreeName    = cfg["inputTreeName"]
    outputWSFile     = cfg["outputWSFiles"][productionMode]
    TreeVars         = cfg["TreeVars"]
    systWeis         = cfg["systWeis"]
    systematicsVars  = cfg["systematicsVars"]
    systematics      = cfg["systematics"]

    print(color.GREEN + "Converting {} {} @ {}GeV tree to workspace".format(year, productionMode, mass) + color.END)
    main()
    print(" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HLLG TREE 2 WS (END) ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")