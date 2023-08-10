import os
import re
from collections import OrderedDict as od

# Paths and directory
cwd__ = os.environ["CMSSW_BASE"]+"/src/HLLGFinalFits"
swd__ = "%s/Signal"%cwd__
bwd__ = "%s/Background"%cwd__
dwd__ = "%s/Datacard"%cwd__
fwd__ = "%s/Combine"%cwd__
pwd__ = "%s/Plots"%cwd__
twd__ = "%s/Tree2WS"%cwd__

# Centre of mass energy string
sqrts__ = "13TeV"

# Luminosity map in fb^-1. excluding RunB, C for 2017
# lumiMap = {"2016":36.33, "2017":27.06, "2018":59.82, "combined":137.63, "merged":137.63}
lumiMap = {"2016":36.33, "2017":41.48, "2018":59.82, "combined":123, "merged":123}
lumiScaleFactor = 1000. # Converting from pb to fb

# Base mass point list for signal samples
massBaseList = [120, 125, 130]
years = [
    2016,
    2017,
    2018
]
yearsStr = [
    "2016",
    "2017",
    "2018"
]
eras = ["UL2016preVFP", "UL2016postVFP", "UL2017", "UL2018"]

# Constants
# BR_W_lnu = 3.*10.86*0.01
# BR_Z_ll = 3*3.3658*0.01
# BR_Z_nunu = 20.00*0.01
# BR_Z_qq = 69.91*0.01
# BR_W_qq = 67.41*0.01

# Production modes and decay channel: for extract XS from combine
productionModes = ["ggH", "VBF", "WH", "ZH", "ttH", "bbH"]
decayMode = "hmmg"
massText = "m_{#mu#mu#gamma} (GeV)"
decayText = "H #rightarrow #gamma* #gamma #rightarrow #mu#mu#gamma"

# input WS objects
inputWSName__ = "tagsDumper/cms_hmmg_13TeV"
inputNuisanceExtMap = {"scales":"MCScale", "scalesCorr":"", "smears":"MCSmear"}

# Signal output WS objects
outputWSName__ = "wsig"
outputWSObjectTitle__ = "hmmgpdfsmrel"
outputWSNuisanceTitle__ = "CMS_hmmg_nuisance"

# outputNuisanceExtMap = {"scales":"%sscale"%sqrts__, "scalesCorr":"%sscaleCorr"%sqrts__, "smears":"%ssmear"%sqrts__, "scalesGlobal":"%sscale"%sqrts__}
# outputNuisanceExtMap = {"phoScales":"%sphoScale"%sqrts__, "phoSmears":"%sphoSmear"%sqrts__, "muScales":"%smuScale"%sqrts__, "muSmears":"%smuSmear"%sqrts__}

# Bkg output WS objects
bkgWSName__ = "multipdf"

# Analysis categories
category__ = od()
category__["diMu0.7MuPho_EBHR9"]    = "category == 1"
category__["diMu0.7MuPho_EBLR9"]    = "category == 2"
category__["diMu0.7MuPho_EE"]       = "category == 3"
category__["diMu0.7MuPho_VBF"]      = "category == 4"
category__["diMu0.7MuPho_BST"]      = "category == 5"

category__["diMu9.0MuPho_EBHR9"]    = "category == 6"
category__["diMu9.0MuPho_EBLR9"]    = "category == 7"
category__["diMu9.0MuPho_EE"]       = "category == 8"
category__["diMu9.0MuPho_VBF"]      = "category == 9"
category__["diMu9.0MuPho_BST"]      = "category == 10"

category__["diMu25MuPho_EBHR9"]     = "category == 11"
category__["diMu25MuPho_EBLR9"]     = "category == 12"
category__["diMu25MuPho_EE"]        = "category == 13"
category__["diMu25MuPho_VBF"]       = "category == 14"
category__["diMu25MuPho_BST"]       = "category == 15"
category__["diMu50MuPho"]           = "category == 16"

category__["diMu9.0IsoMu_EBHR9"]    = "category == 17"
category__["diMu9.0IsoMu_EBLR9"]    = "category == 18"
category__["diMu9.0IsoMu_EE"]       = "category == 19"
category__["diMu9.0IsoMu_VBF"]      = "category == 20"
category__["diMu9.0IsoMu_BST"]      = "category == 21"
category__["diMu50IsoMu_EBHR9"]     = "category == 22"
category__["diMu50IsoMu_EBLR9"]     = "category == 23"
category__["diMu50IsoMu_EE"]        = "category == 824"
category__["diMu50IsoMu_VBF"]       = "category == 25"
category__["diMu50IsoMu_BST"]       = "category == 26"

categoryTag = od()
categoryTag["diMu0.7MuPho"] = ["diMu0.7MuPho_EBHR9", "diMu0.7MuPho_EBLR9", "diMu0.7MuPho_EE", "diMu0.7MuPho_VBF", "diMu0.7MuPho_BST"]
categoryTag["diMu9.0MuPho"] = ["diMu9.0MuPho_EBHR9", "diMu9.0MuPho_EBLR9", "diMu9.0MuPho_EE", "diMu9.0MuPho_VBF", "diMu9.0MuPho_BST"]
categoryTag["diMu25MuPho"]  = ["diMu25MuPho_EBHR9", "diMu25MuPho_EBLR9", "diMu25MuPho_EE", "diMu25MuPho_VBF", "diMu25MuPho_BST"]
categoryTag["diMu50MuPho"]  = ["diMu50MuPho"]


# function to converte process to production mode in dataset name
procToDatacardNameMap = od()
procToDatacardNameMap["ggH"] = "ggH"
procToDatacardNameMap["VBF"] = "qqH"
procToDatacardNameMap["WH"]  = "WH"
procToDatacardNameMap["ZH"]  = "ZH"
procToDatacardNameMap["ttH"] = "ttH"
procToDatacardNameMap["bbH"] = "bbH"
def procToDatacardName(_proc):
    k = _proc.split("_")[0]
    if k in procToDatacardNameMap:
        _proc = re.sub(k, procToDatacardNameMap[k], _proc)
    return _proc