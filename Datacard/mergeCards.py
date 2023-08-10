import os
import numpy as np
from ROOT import gSystem
from contextlib import contextmanager
from commonObjects import massBaseList, decayMode, category__, categoryTag


# https://stackoverflow.com/a/24176022
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        

with cd("./cards"):
    opt = "comb_mupho"
    mass_interp = np.linspace(massBaseList[0], massBaseList[-1], 11, endpoint=True).astype(int)
    for mass in mass_interp:
        cards = ""
        for cat in category__.keys():
            cards += "datacard_{}_runII_{}_{}.txt ".format(decayMode, cat, mass)
    
        card_comb = "datacard_{}_runII_{}_{}.txt".format(decayMode, opt, mass)
        print("---> merged card: {}".format(card_comb))
        gSystem.Exec("combineCards.py {} > {} ".format(cards, card_comb))