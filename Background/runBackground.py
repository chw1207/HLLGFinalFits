import os, sys
from tqdm import tqdm
from pprint import pprint
import json
from multiprocessing import Pool
from commonTools import cprint
from commonObjects import category__, twd__


def execute(cmd):
    os.system(cmd)


def main():
    # create the dir to put log file
    if not os.path.exists("./logger"):
        os.system("mkdir ./logger")

    # setting
    HLLGCatsStr = ",".join(category__.keys())
    infile = "{}/WS/data_obs.root".format(twd__)

    # create the queue to be submitted
    queue = []
    for c in range(len(category__.keys())):
        queue.append("./bin/fTest_v2 --infile {} --runFtestCheckWithToys --singleCat {} --HLLGCats {} &> ./logger/fTest_v2_{}.txt".format(infile, c, HLLGCatsStr, list(category__.keys())[c]))

    n = len(category__.keys())
    cprint("Executing the following commands using {} cores".format(n), colorStr="green")
    
    cprint(json.dumps(queue, indent=4))

    # submit the process
    pool = Pool(n)
    for i in tqdm(pool.imap_unordered(execute, queue), total=len(queue)):
        pass
    pool.close()
    pool.join()


if __name__ == "__main__" :
    main()