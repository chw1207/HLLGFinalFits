# Script to convert HDalitz trees to RooWorkspace (compatible for finalFits)
# Assumes tree names of the format:
#  * miniTree
# For systematics: requires hist of the format:
#  * cat1_<syst> e.g. cat1_JERUp, cat1_PhoScaleStatDo

import ROOT
import os
import re
import pandas as pd
from pprint import pprint
from argparse import ArgumentParser
from collections import OrderedDict as od
from importlib import import_module
from commonObjects import inputWSName__, category__, productionModes
from commonTools import cprint

def get_parser():
    parser = ArgumentParser(description="Script to convert data trees to RooWorkspace (compatible for finalFits)")
    parser.add_argument("-c",  "--config",          help="Input config: specify list of variables/analysis categories", default=None, type=str)
    parser.add_argument("-y",  "--year",            help="Year",                                                        default=2017, type=int)
    parser.add_argument("-m",  "--mass",            help="mass point",                                                  default=125,  type=int)
    parser.add_argument("-p",  "--productionMode",  help="Production mode [ggH, VBF, WH, ZH, ttH, bbH]",                default="ggH",type=str)
    parser.add_argument("-ds", "--doSystematics",   help="Add systematics datasets to output WS",                       default=False,action="store_true")
    return parser

def main():
    cprint("[INFO] Read file:", colorStr="green")
    pprint(inputTreeFile)
    
    if len(inputTreeFile) > 1: # for 2016 only, combine preVFP and postVFP (trees and histograms)
        # https://root-forum.cern.ch/t/add-histograms-automatically-from-two-files/21561/2
        cmd = f"hadd -f tmp_{year}_{mass}_{productionMode}.root "
        for f2merged in inputTreeFile:
            cmd += f"{f2merged} "
        ROOT.gSystem.Exec(cmd)

    fin = ROOT.TFile(inputTreeFile[0] if len(inputTreeFile) == 1 else f"tmp_{year}_{mass}_{productionMode}.root", "READ")
    intree = fin.Get(inputTreeName)
    ROOT.gROOT.cd() # https://root-forum.cern.ch/t/copytree-with-a-selection/12908/3
    
    # create work space
    ws_dir_name = inputWSName__.split("/")
    ws = ROOT.RooWorkspace(ws_dir_name[1], ws_dir_name[1])
    
    # create variables
    CMS_higgs_mass = ROOT.RooRealVar("CMS_higgs_mass", "CMS_higgs_mass", mass, 110, 170, "GeV") # initial, lower bound, upper bound
    weight = ROOT.RooRealVar("weight", "weight", -100, 100, "")
    ws.Import(CMS_higgs_mass)
    ws.Import(weight)
    
    # convert tree to dataset 
    for cat_name, cat_cut in category__.items():
        outtree = intree.CopyTree(cat_cut)
        aset = ROOT.RooArgSet(CMS_higgs_mass, weight)
        
        # nominal dataset
        dname = f"set_{mass}_{cat_name}"
        dset = ROOT.RooDataSet(dname, dname, outtree, aset, "", "weight")
        cprint("{}".format(dset.sumEntries()), colorStr="red")
        ws.Import(dset)

        if doSystematics:
            for sw in sysWeis: # affect rate 
                hname = f"hist_{mass}_{cat_name}_{sw}"
                dhname = f"dh_{mass}_{cat_name}_{sw}"
                hist_sys = ROOT.TH1D(hname, hname, 60, 110, 170)
                outtree.Draw(f"CMS_higgs_mass >> {hname}", f"({sw})")
                dh = ROOT.RooDataHist(dhname, dhname, CMS_higgs_mass, ROOT.RooFit.Import(hist_sys))
                ws.Import(dh)
                
            for sh in sysHists: # affect shape 
                cat_prefix = cat_cut.replace("category == ", "cat")
                hist_sys = fin.Get(f"{cat_prefix}_{sh}")
                dhname = f"dh_{mass}_{cat_name}_{sh}"
                dh = ROOT.RooDataHist(dhname, dhname, CMS_higgs_mass, ROOT.RooFit.Import(hist_sys))
                ws.Import(dh)
    
    cprint("[INFO] Save WS in :", colorStr="green")
    pprint(outputWSFile)
     
    outputWSDir = ROOT.gSystem.DirName(outputWSFile)
    os.makedirs(outputWSDir, exist_ok=True)
    
    fout = ROOT.TFile(outputWSFile, "RECREATE")
    foutdir = fout.mkdir(ws_dir_name[0])
    foutdir.cd()
    ws.Write()
    fout.Close()
    
    fin.cd()
    fin.Close()
    
    if len(inputTreeFile) > 1:
        ROOT.gSystem.Exec(f"rm tmp_{year}_{mass}_{productionMode}.root")
    

if __name__ == "__main__" :
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
    cfg = import_module(re.sub(".py", "", args.config)).trees2ws_cfg[mass][year]
    inputTreeFile    = cfg["inputTreeFiles"][productionMode]
    inputTreeName    = cfg["inputTreeName"]
    outputWSFile     = cfg["outputWSFiles"][productionMode]
    sysWeis          = cfg["sysWeis"]
    sysHists         = cfg["sysHists"]

    # PyROOT does not display any graphics(root "-b" option)
    ROOT.gROOT.SetBatch()
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    
    main()