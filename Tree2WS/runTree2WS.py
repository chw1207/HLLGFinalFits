import ROOT
import os
import subprocess
import json
from tqdm import tqdm
from multiprocessing import Pool
from argparse import ArgumentParser
from commonObjects import massBaseList, years, productionModes
from commonTools import cprint


def get_parser():
    parser = ArgumentParser(description="Script to convert data trees to RooWorkspace (compatible for finalFits)")
    parser.add_argument("-s",  "--script",          help="Which script to run [tree2ws, tree2ws_data]",                 default=None,  type=str)
    parser.add_argument("-c",  "--config",          help="Input config: specify list of variables/analysis categories", default=None,  type=str)
    parser.add_argument("-y",  "--year",            help="Year [2016, 2017, 2018]",                                     default="all", type=str)
    parser.add_argument("-m",  "--mass",            help="mass point [120, 125, 130]",                                  default="all", type=str)
    parser.add_argument("-p",  "--productionMode",  help="Production mode [ggH, VBF, WH, ZH, ttH, bbH]",                default="all", type=str)
    parser.add_argument("-ds", "--doSystematics",   help="Add systematics datasets to output WS",                       default=False, action="store_true")
    parser.add_argument("-n",  "--nCPUs",           help="Number of CPUs used to convert tree to ws(default: 10)",      default=10,    type=int)
    return parser

def convert(cmd):
    log = ROOT.gSystem.GetFromPipe(cmd)
    with open(QUEUE[cmd], "w") as log_file:
        log_file.write(str(log))

def main():
    # create the dir to put log file
    os.makedirs("./logger", exist_ok=True)

    # create the queue to be submitted
    queues = []
    logfiles = []
    if script == "tree2ws":
        for y in year:
            for p in productionMode:
                for m in mass:
                    command_ = f"python3 tree2ws.py --config {config} --year {y} --mass {m} --productionMode {p}"
                    if doSystematics:
                        command_ += " --doSystematics"
                    logfile_ = f"./logger/tree2ws_{y}_{m}_{p}.txt"
                    
                    queues.append(command_)
                    logfiles.append(logfile_)
                    
    if script == "tree2ws_data":
        queues.append(f"python3 tree2ws_data.py --config {config}")
        logfile_ = "./logger/tree2ws_data.txt"
        logfiles.append(logfile_)
                    
    global QUEUE
    QUEUE = dict(zip(queues, logfiles))                
    
    cprint("Executing the following commands", colorStr="green")
    cprint(json.dumps(queues, indent=4))
    
    # submit the process
    pool = Pool(n)
    for i in tqdm(pool.imap_unordered(convert, queues), total=len(queues)):
        pass
    pool.close()
    pool.join()
    

if __name__ == "__main__" :
    # Extract information from config file:
    parser = get_parser()
    args = parser.parse_args()

    if (args.script not in ["tree2ws", "tree2ws_data"]):
        print("Available mass: [tree2ws, tree2ws_data]")
        sys.exit(1)
    if (args.config == None):
        print("Please specify the config file!")
        sys.exit(1)
    if ((args.mass not in massBaseList) and (args.mass != "all")):
        print("Available mass: {}".format(massBaseList))
        sys.exit(1)
    if ((args.year not in years) and (args.year != "all")):
        print("Available year: {}".format(years))
        sys.exit(1)
    if ((args.productionMode not in productionModes) and (args.productionMode != "all")):
        print("Available productionMode: {}".format(productionModes))
        sys.exit(1)

    script          = args.script
    config          = args.config
    mass            = [int(args.mass)] if args.mass != "all" else massBaseList
    year            = [int(args.year)] if args.year != "all" else years
    productionMode  = [args.productionMode] if args.productionMode != "all" else productionModes
    doSystematics   = args.doSystematics
    n               = args.nCPUs

    main()