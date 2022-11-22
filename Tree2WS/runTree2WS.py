import os, sys
import subprocess
from tqdm import tqdm
from pprint import pprint
from multiprocessing import Pool
from argparse import ArgumentParser
from commonObjects import massBaseList, years, productionModes
from commonTools import color


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
    os.system(cmd)


def main():
    # create the dir to put log file
    if not os.path.exists("./logger"):
        os.system("mkdir ./logger")

    # create the queue to be submitted
    queue = []
    if script == "tree2ws":
        for y in year:
            for p in productionMode:
                for m in mass:
                    if (doSystematics):
                        queue.append("python tree2ws.py --config {} --year {} --productionMode {} --mass {} --doSystematics &> ./logger/tree2ws_{}_{}_{}.txt".format(config, y, p, m, y, p, m))
                    else:
                        queue.append("python tree2ws.py --config {} --year {} --productionMode {} --mass {} &> ./logger/tree2ws_{}_{}_{}.txt".format(config, y, p, m, y, p, m))
    if script == "tree2ws_data":
        queue.append("python tree2ws_data.py --config {} &> ./logger/tree2ws_data.txt".format(config))

    print(color.GREEN + "Executing the following commands" + color.END)
    pprint(queue)

    # submit the process
    pool = Pool(n)
    for i in tqdm(pool.imap_unordered(convert, queue), total=len(queue)):
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