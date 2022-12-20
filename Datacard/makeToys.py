import os, sys
import ROOT
from glob import glob
from argparse import ArgumentParser
from contextlib import contextmanager

def get_parser():
    parser = ArgumentParser(description="Script to make toys from inputWS: to be used for making bands in S+B model plot")
    parser.add_argument("-i", "--inputWSFile",  help="Input RooWorkspace file",                                        default="",  type=str)
    parser.add_argument("-e", "--ext",          help="external text (match to makeSplusBPlot.py, usually set to cat)", default="",  type=str)
    parser.add_argument("-n", "--nToys",        help="number of toys",                                                 default=500, type=int)
    
    return parser


# https://stackoverflow.com/a/24176022
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def execute(cmd):
    os.system(cmd)
    

def main():
    # create toy directory
    toys_dir = "./SplusBModels_{}/toys/".format(ext)
    execute("rm -r ./SplusBModels_{}".format(ext))
    execute("mkdir -p {}".format(toys_dir))
    
    # clean the old toys
    if (len(glob("{}/*.root".format(toys_dir))) != 0):
        execute("rm -r {}".format(toys_dir))
    
    # start to gerate toys
    inputWSFile_abs = os.path.abspath(inputWSFile)
    with cd(toys_dir):
        print("Info: change directory to {}".format(os.getcwd()))
        f = ROOT.TFile(inputWSFile_abs)
        w = ROOT.RooWorkspace()
        f.GetObject("w", w)
        mh_bf = w.var("MH").getVal()
        f.Close()
        
        # assuming signal strength = 1 for now
        for itoy in range(nToys):
            # Generate command
            # generate toy ( -t 1 ) dataset from S + B model
            execute("combine {} -m {} -M GenerateOnly --saveWorkspace --toysFrequentist --bypassFrequentistFit -t 1 -s -1 -n _{}_gen_step --setParameters r=1".format(inputWSFile_abs, mh_bf, itoy))

            # Fit command
            # perform S + B fit to toy
            execute("mv higgsCombine_{}_gen_step*.root gen_{}.root".format(itoy, itoy))
            execute("combine gen_{}.root -m 125 -M MultiDimFit -P r --floatOtherPOIs=1 --saveWorkspace --toysFrequentist --bypassFrequentistFit -t 1 -s -1 -n _{}_fit_step --setParameters r=1 --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_freezeDisassociatedParams --X-rtd MINIMIZER_multiMin_hideConstants --X-rtd MINIMIZER_multiMin_maskConstraints --X-rtd MINIMIZER_multiMin_maskChannels=2".format(itoy, itoy))
            
            # Throw command
            # generate asimov ( -t -1 ) B-only dataset from fitted toy
            execute("mv higgsCombine_{}_fit_step*.root fit_{}.root".format(itoy, itoy))
            execute("combine fit_{}.root -m {} --snapshotName MultiDimFit -M GenerateOnly --saveToys --toysFrequentist --bypassFrequentistFit -t -1 -n _{}_throw_step --setParameters r=0".format(itoy, mh_bf, itoy))

            execute("mv higgsCombine_{}_throw_step*.root toy_{}.root".format(itoy, itoy))
            execute("rm gen_{}.root fit_{}.root".format(itoy, itoy))


if __name__ == "__main__" :
    parser = get_parser()
    args = parser.parse_args()
    
    inputWSFile = args.inputWSFile
    ext = args.ext
    nToys = args.nToys

    main()