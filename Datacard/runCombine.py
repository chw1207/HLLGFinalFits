import os, sys
import ROOT
import numpy as np
from tqdm import tqdm
from glob import glob
from pprint import pprint
from multiprocessing import Pool
from argparse import ArgumentParser
from commonTools import color
from commonObjects import massBaseList, decayMode, category__, categoryTag

def get_parser():
    parser = ArgumentParser(description="Script to run combine tool")
    parser.add_argument("-o", "--option",       help="tagged category option [comb, nom1, untagm2, untagm1, tagm2, tagm1, re or other categories]", default="comb", type=str)
    parser.add_argument("-n", "--nCPUs",        help="Number of CPUs used to submit comebine jobs",                                                 default=11,     type=int)
    parser.add_argument("-v", "--verbose",      help="verbose status",                                                                              default=1,      type=int)
    parser.add_argument("-c", "--combineCards", help="merge several cards",                                                                         default=False,  action="store_true")
    parser.add_argument("-l", "--limit",        help="calculate the limit",                                                                         default=False,  action="store_true")
    parser.add_argument("-s", "--significance", help="calculate the significance",                                                                  default=False,  action="store_true")
    parser.add_argument("-t", "--text2ws",      help="convert text card to root file",                                                              default=False,  action="store_true")
    parser.add_argument("-sb","--splusb",       help="make s + b plots",                                                                            default=False,  action="store_true")
    parser.add_argument("-u", "--unBlind",      help="unblind the results",                                                                         default=False,  action="store_true")
    parser.add_argument("-d", "--doObserved",   help="Fit to data",                                                                                 default=False,  action="store_true")

    return parser


def execute(cmd):
    os.system(cmd)


def submit(_q):
    pool = Pool(n)
    for i in tqdm(pool.imap_unordered(execute, _q), total=len(_q)):
        pass
    pool.close()
    pool.join()


def main():
    # create the dir to put log file
    if not os.path.exists("./logger"):
        os.system("mkdir ./logger")

    # combine the datacrads
    mass_interp = np.linspace(massBaseList[0], massBaseList[-1], 11, endpoint=True).astype(int)
    if combineCards:
        print(color.GREEN + "[INFO] Combine cards for {} categories".format(opt) + color.END)
        for mass in mass_interp:
            cards = ""
            for cat in category__.keys():
                if opt == "nom1" and "1Gsf" in cat:
                    continue
                if opt == "untagm2" and cat not in categoryTag["M2Untag"]:
                    continue
                if opt == "untagm1" and cat not in categoryTag["M1Untag"]:
                    continue
                if opt == "tagm2" and cat not in categoryTag["M2tag"]:
                    continue
                if opt == "tagm1" and cat not in categoryTag["M1tag"]:
                    continue
                if opt == "re":
                    print("Warning: Resolved category do not need to combine cards. ignore...")
                    break

                cards += "./cards/datacard_{}_runII_{}_{}.txt ".format(decayMode, cat, mass)
            if opt == "re":
                break
            card_comb = "./cards/datacard_{}_runII_{}_{}.txt".format(decayMode, opt, mass)
            print("---> merged card: {}".format(card_comb))
            execute("combineCards.py {} > {} ".format(cards, card_comb))

    # calculate the limit
    exp_opt_str = "" if args.doObserved else "--expectSignal 1 -t -1"
    unb_opt_str = "" if args.unBlind else "--run=blind"
    if limit:
        print(color.GREEN + "[INFO] Calculate the limit for {} categories".format(opt) + color.END)
        queue = []
        for mass in mass_interp:
            card_comb = "./cards/datacard_{}_runII_{}_{}.txt".format(decayMode, opt, mass)
            if opt == "re":
                card_comb = "./cards/datacard_{}_runII_Resolved_{}.txt".format(decayMode, mass)
            queue.append("combineTool.py {} -M AsymptoticLimits -n _{}_{} -m {} {} {} -v {} &> ./logger/limit_{}_{}.txt".format(card_comb, opt, mass, mass, exp_opt_str, unb_opt_str, verbose, opt, mass))
        print("---> Executing the following commands using {} cores".format(n))
        pprint(queue)
        submit(queue)

    # calculate the significance
    if significance:
        # Generate post-fit toys 
        print(color.GREEN + "[INFO] Generate the toys to calculate significance for {} categories".format(opt) + color.END)
        queue = []
        for mass in mass_interp:
            card_comb = "./cards/datacard_{}_runII_{}_{}.txt".format(decayMode, opt, mass)
            if opt == "re":
                card_comb = "./cards/datacard_{}_runII_Resolved_{}.txt".format(decayMode, mass)
            queue.append("combine {} -M GenerateOnly -t -1 --expectSignal 1 --toysFrequentist --saveToys -m {} -n _{}_{} -v {} &> ./logger/toys_{}_{}.txt".format(card_comb, mass, opt, mass, verbose, opt, mass))
        print("---> Executing the following commands using {} cores".format(n))
        pprint(queue)
        submit(queue)

        print(color.GREEN + "[INFO] Calculate significance for {} categories".format(opt) + color.END)
        queue = []
        for mass in mass_interp:
            card_comb = "./cards/datacard_{}_runII_{}_{}.txt".format(decayMode, opt, mass)
            if opt == "re":
                card_comb = "./cards/datacard_{}_runII_Resolved_{}.txt".format(decayMode, mass)
            toy_file = "higgsCombine_{}_{}.GenerateOnly.mH{}.123456.root".format(opt, mass, mass)
            # Expected significance
            queue.append("combine {} -M Significance {} --toysFrequentist --toysFile {} -m {} -n _{}_{} -v {} &> ./logger/significance_{}_{}.txt".format(card_comb, exp_opt_str, toy_file, mass, opt, mass, verbose, opt, mass))
            if doObserved:
                # Observed significance
                queue.append("combine {} -M Significance -m {} -n _{}_{}_obs -v {} &> ./logger/significance_obs_{}_{}.txt".format(card_comb, mass, opt, mass, verbose, opt, mass))
        print("---> Executing the following commands using {} cores".format(n))
        pprint(queue)
        submit(queue)

    if text2ws:
        print(color.GREEN + "[INFO] converting the text card to root file" + color.END)
        queue = []
        for mass in mass_interp:
            for cat in category__.keys():
                card2convert = "./cards/datacard_{}_runII_{}_{}.txt".format(decayMode, cat, mass)
                card2root = card2convert.replace(".txt", ".root")
                models = "-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel"
                common_opts = "--PO higgsMassRange=120,130"
                # queue.append("text2workspace.py {} -o {} -m {} {} {} -v {} &> ./logger/text2ws_{}_{}.txt".format(card2convert, card2root, mass, common_opts, models, verbose, cat, mass))
                queue.append("text2workspace.py {} -o {} -m {} -v {} &> ./logger/text2ws_{}_{}.txt".format(card2convert, card2root, mass, verbose, cat, mass))
        print("---> Executing the following commands using {} cores".format(n))
        pprint(queue)
        submit(queue)
    
    if splusb:    
        print(color.GREEN + "[INFO] making toys" + color.END)
        queue = []
        for cat in category__.keys():
            card = "./cards/datacard_{}_runII_{}_125.root".format(decayMode, cat)
            queue.append("python makeToys.py -e {} -i {} &> ./logger/maketoys_{}.txt".format(cat, card, cat))
        pprint(queue)
        submit(queue)    
        print(color.GREEN + "[INFO] making s+b plots" + color.END)
        for cat in category__.keys():
            card = "./cards/datacard_{}_runII_{}_125.root".format(decayMode, cat)
            if args.unBlind:
                execute("python makeSplusBModelPlot.py --inputWSFile {} --cats {} --ext {} --doBands --doToyVeto --unblind".format(card, cat, cat))
            else:
                execute("python makeSplusBModelPlot.py --inputWSFile {} --cats {} --ext {} --doBands --doToyVeto".format(card, cat, cat))

    # create the dir to put all the output file
    if not os.path.exists("./tree"):
        os.system("mkdir ./tree")
    if len(glob("./*.root")) != 0:
        print(color.GREEN + "[INFO] Move output root files to tree dir" + color.END)
        execute("mv *.root ./tree")


if __name__ == "__main__" :
    parser = get_parser()
    args = parser.parse_args()

    opt             = args.option
    n               = args.nCPUs
    verbose         = args.verbose
    combineCards    = args.combineCards
    limit           = args.limit
    significance    = args.significance
    text2ws         = args.text2ws
    splusb          = args.splusb
    unBlind         = args.unBlind
    doObserved      = args.doObserved

    main()