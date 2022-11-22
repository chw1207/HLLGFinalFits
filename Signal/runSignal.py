import os, sys
from tqdm import tqdm
from pprint import pprint
from multiprocessing import Pool
from argparse import ArgumentParser
from collections import OrderedDict as od
from commonTools import color
from commonObjects import massBaseList, years, category__, twd__, productionModes


def get_parser():
    parser = ArgumentParser(description="Script for submitting signal fitting jobs for finalfitslite")
    parser.add_argument("-y",  "--year",            help="specify the year [2016, 2017, 2018, all], default = all",                     default="all", type=str)
    parser.add_argument("-s",  "--script",          help="Which script to run. Options: [signalFit, makeModelPlot, calcShapeSyst]",     default="", type=str)
    parser.add_argument("-n",  "--nCPUs",           help="Number of CPUs used to submit signal jobs(default: 10)",                      default=10, type=int)
    parser.add_argument("-ds", "--doSystematics",   help="Estimate the shape uncertainties",                                            default=False,  action="store_true")

    return parser


def execute(cmd):
    os.system(cmd)


def main():
    # create the dir to put log file
    if not os.path.exists("./logger"):
        os.system("mkdir ./logger")

    # input workspace path
    if year != "all":
        inWS = "%s/WS/%s"%(twd__, year)
    else:
        inWS = ["%s/WS/%s"%(twd__, _y) for _y in years]

    # create the queue to be submitted
    queue = []
    if script == "calcShapeSyst":
        for cat in category__.keys():
            for m in massBaseList:
                if year == "all":
                    for i in range(len(years)):
                        queue.append("python calcShapeSyst.py --mass {} --category {} --inputWSDir {} --year {} &> ./logger/calcSyst_{}_{}_{}.txt".format(m, cat, inWS[i], years[i], cat, m, years[i]))
                else:
                    queue.append("python calcShapeSyst.py --mass {} --category {} --inputWSDir {} --year {} &> ./logger/calcSyst_{}_{}_{}.txt".format(m, cat, inWS[i], years[i], cat, m, years[i]))

    if script == "signalFit":
        for cat in category__.keys():
            if year == "all":
                for i in range(len(years)):
                    if doSystematics:
                        queue.append("python signalFit.py --category {} --year {} --inputWSDir {} --doInterpolation --doSystematics &> ./logger/signalFit_{}_{}.txt".format(cat, years[i], inWS[i], cat, years[i]))
                    else:
                        queue.append("python signalFit.py --category {} --year {} --inputWSDir {} --doInterpolation &> ./logger/signalFit_{}_{}.txt".format(cat, years[i], inWS[i], cat, years[i]))
            else:
                if doSystematics:
                    queue.append("python signalFit.py --category {} --year {} --inputWSDir {} --doInterpolation --doSystematics &> ./logger/signalFit_{}_{}.txt".format(cat, year, inWS, cat, year))
                else:
                    queue.append("python signalFit.py --category {} --year {} --inputWSDir {} --doInterpolation &> ./logger/signalFit_{}_{}.txt".format(cat, year, inWS, cat, year))

    if script == "makeModelPlot":
        for cat in category__.keys():
            for proc in productionModes:
                queue.append("python makeModelPlot.py --category {} --process {} &> ./logger/makeModelPlot_{}_{}.txt".format(cat, proc, cat, proc))

    print(color.GREEN + "Executing the following commands using {} cores".format(n) + color.END)
    pprint(queue)

    # submit the process
    pool = Pool(n)
    for i in tqdm(pool.imap_unordered(execute, queue), total=len(queue)):
        pass
    pool.close()
    pool.join()


if __name__ == "__main__" :
    # Extract information from config file:
    parser = get_parser()
    args = parser.parse_args()

    script          = args.script
    year            = args.year
    doSystematics   = args.doSystematics
    n               = args.nCPUs

    if script not in ["signalFit", "makeModelPlot", "calcShapeSyst"]:
        parser.print_help()
        sys.exit(1)

    main()