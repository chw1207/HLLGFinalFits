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

# Luminosity map in fb^-1
lumiMap = {"2016":36.33, "2017":41.48, "2018":59.82, "combined":137.63, "merged":137.63}
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
BR_W_lnu = 3.*10.86*0.01
BR_Z_ll = 3*3.3658*0.01
BR_Z_nunu = 20.00*0.01
BR_Z_qq = 69.91*0.01
BR_W_qq = 67.41*0.01

# Production modes and decay channel: for extract XS from combine
productionModes = ["ggH", "VBF", "WH", "ZH", "ttH", "bbH"]
decayMode = "heeg"

# flashgg input WS objects
inputWSName__ = "tagsDumper/cms_heeg_13TeV"
inputNuisanceExtMap = {"scales":"MCScale", "scalesCorr":"", "smears":"MCSmear"}
# Signal output WS objects
outputWSName__ = "wsig"
outputWSObjectTitle__ = "heegpdfsmrel"
outputWSNuisanceTitle__ = "CMS_heeg_nuisance"
# outputNuisanceExtMap = {"scales":"%sscale"%sqrts__, "scalesCorr":"%sscaleCorr"%sqrts__, "smears":"%ssmear"%sqrts__, "scalesGlobal":"%sscale"%sqrts__}
outputNuisanceExtMap = {"phoScales":"%sphoScale"%sqrts__, "phoSmears":"%sphoSmear"%sqrts__, "eleScales":"%seleScale"%sqrts__, "eleSmears":"%seleSmear"%sqrts__}

# Bkg output WS objects
bkgWSName__ = "multipdf"

# Analysis categories
category__ = od()
category__["Merged2Gsf_VBF"]    = "category == 1"
category__["Merged2Gsf_BST"]    = "category == 2"
category__["Merged2Gsf_EBHR9"]  = "category == 3"
category__["Merged2Gsf_EBLR9"]  = "category == 4"
category__["Merged2Gsf_EE"]     = "category == 5"
# category__["Resolved"]          = "category == 13"

categoryTag = od()
categoryTag["M2Untag"] = ["Merged2Gsf_EBHR9", "Merged2Gsf_EBLR9", "Merged2Gsf_EE"]
categoryTag["M2tag"]   = ["Merged2Gsf_VBF", "Merged2Gsf_BST"]

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