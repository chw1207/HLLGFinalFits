import ROOT
import sys
import os
import re
from pprint import pprint
from argparse import ArgumentParser
from collections import OrderedDict as od
from root_numpy import array2tree, tree2array
from importlib import import_module
from commonObjects import inputWSName__, category__, productionModes

def get_parser():
    parser = ArgumentParser(description="Script to convert data trees to RooWorkspace (compatible for finalFits)")
    parser.add_argument("-c", "--config", help="Input config: specify list of variables/analysis categories", default=None, type=str)
    return parser


def add_vars_to_workspace(_ws, _var_list):
    # Add intLumi var
    intLumi = ROOT.RooRealVar("intLumi", "intLumi", 1000.,0., 999999999.)
    intLumi.setConstant(True)
    getattr(_ws, "import")(intLumi, ROOT.RooFit.Silence())
    _vars = od()
    for var in _var_list:
        if var == "CMS_higgs_mass":
            _vars[var] = ROOT.RooRealVar(var, var, 125, 110, 170, "GeV") # initial, lower bound, upper bound
            _vars[var].setBins(60)
        elif var == "weight":
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
    # Read the input ROOT files
    print("[INFO] Read file:")
    pprint(inputTreeFiles)
    chain = ROOT.TChain(inputTreeName)
    for i in inputTreeFiles:
        chain.Add(i)

    # Open output ROOT file and initiate workspace to store RooDataSets
    outputWSDir = os.path.dirname(outputWSFile)
    if not os.path.exists(outputWSDir):
        os.system("mkdir %s" %outputWSDir)
    print("[INFO] Save workspace: {}".format(outputWSFile))
    fout = ROOT.TFile(outputWSFile, "RECREATE")
    foutdir = fout.mkdir(inputWSName__.split("/")[0])
    foutdir.cd()
    ws = ROOT.RooWorkspace(inputWSName__.split("/")[1], inputWSName__.split("/")[1])

    # Add variables to workspace
    varNames = add_vars_to_workspace(ws, TreeVars) # Add variables to workspace

    # Make argset
    aset = make_argset(ws, varNames)
    for cat in category__:
        array_cat = tree2array(chain, branches=TreeVars, selection=category__[cat])
        tree_cat = array2tree(array_cat)

        # Define dataset for cat
        dname = "data_obs_{}".format(cat)
        dset = ROOT.RooDataSet(dname, dname, aset, "weight")

        # Loop over events in tree and add to dataset with weight 1
        for ev in range(tree_cat.GetEntries()):
            tree_cat.GetEntry(ev)
            for var in TreeVars:
                if var != "weight":
                    ws.var(var).setVal(getattr(tree_cat, var))
            dset.add(aset, 1.)

        # Add dataset to worksapce
        getattr(ws, "import")(dset)

    # Write workspace to file
    ws.Write()
    ws.Delete()
    fout.Close()


if __name__ == "__main__" :
    print(" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HLLG TREES 2 WS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ")
    # Extract information from config file:
    parser = get_parser()
    args = parser.parse_args()

    if args.config is None:
        print("Please specify the config file! eg. config_data")
        parser.print_help()
        sys.exit(1)

    # Import config options
    cfg = import_module(re.sub(".py","", args.config)).trees2ws_cfg
    inputTreeFiles   = cfg["inputTreeFiles"]
    inputTreeName    = cfg["inputTreeName"]
    outputWSFile     = cfg["outputWSFile"]
    TreeVars         = cfg["TreeVars"]

    main()
    print(" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HLLG TREES 2 WS (END) ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")