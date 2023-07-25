import ROOT
import os
import re
from pprint import pprint
from argparse import ArgumentParser
from collections import OrderedDict as od
from importlib import import_module
from commonObjects import inputWSName__, category__, productionModes
from commonTools import cprint

def get_parser():
    parser = ArgumentParser(description="Script to convert data trees to RooWorkspace (compatible for finalFits)")
    parser.add_argument("-c", "--config", help="Input config: specify list of variables/analysis categories", default=None, type=str)
    return parser


def main():
    # Read the input ROOT files
    cprint("[INFO] Read file:", colorStr="green")
    pprint(inputTreeFiles)
    
    cmd = f"hadd -f tmp_data.root "
    for f2merged in inputTreeFiles:
        cmd += f"{f2merged} "
    ROOT.gSystem.Exec(cmd)
    
    fin = ROOT.TFile("tmp_data.root", "READ")
    intree = fin.Get(inputTreeName)
    ROOT.gROOT.cd() # https://root-forum.cern.ch/t/copytree-with-a-selection/12908/3
    
    # create work space
    ws_dir_name = inputWSName__.split("/")
    ws = ROOT.RooWorkspace(ws_dir_name[1], ws_dir_name[1])
    
    # create variables
    CMS_higgs_mass = ROOT.RooRealVar("CMS_higgs_mass", "CMS_higgs_mass", 125, 110, 170, "GeV") # initial, lower bound, upper bound
    weight = ROOT.RooRealVar("weight", "weight", 1., "")
    ws.Import(CMS_higgs_mass)
    ws.Import(weight)
    
    # convert tree to dataset 
    for cat_name, cat_cut in category__.items():
        outtree = intree.CopyTree(cat_cut)
        aset = ROOT.RooArgSet(CMS_higgs_mass, weight)
        
        # nominal dataset
        dname = f"data_obs_{cat_name}"
        dset = ROOT.RooDataSet(dname, dname, outtree, aset, "", "weight")
        ws.Import(dset)
    
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
    
    ROOT.gSystem.Exec(f"rm tmp_data.root")

if __name__ == "__main__" :
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

    main()