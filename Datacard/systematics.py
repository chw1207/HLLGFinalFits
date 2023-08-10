# Python file to store systematics: for Higgs Dalitz analysis

# THEORY SYSTEMATICS: The values are extracted from the origional hgg package json file
# ! Things to be checked:
#   1) the value of branching fraction
#   2) should we include alphaS or not?
theory_systematics = [
    {"name":"BR_higgs_dalitz",      "title":"BR_higgs_dalitz",      "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"0.94/1.06"},
    {"name":"pdf_Higgs_ggH",        "title":"pdf_Higgs_ggH",        "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"ggH:1.019"},
    {"name":"pdf_Higgs_qqH",        "title":"pdf_Higgs_qqH",        "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"qqH:1.021"},
    {"name":"pdf_Higgs_VH",         "title":"pdf_Higgs_VH",         "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"WH:1.017,ZH:1.013"},
    {"name":"pdf_Higgs_ttH",        "title":"pdf_Higgs_ttH",        "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"ttH:1.030"},

    {"name":"QCDscale_ggH",         "title":"QCDscale_ggH",         "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"ggH:1.047/0.931"},
    {"name":"QCDscale_qqH",         "title":"QCDscale_qqH",         "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"qqH:1.004/0.997"},
    {"name":"QCDscale_VH",          "title":"QCDscale_VH",          "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"WH:1.005/0.993,ZH:1.038/0.969"},
    {"name":"QCDscale_ttH",         "title":"QCDscale_ttH",         "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"ttH:1.058/0.908"},
    {"name":"QCDscale_bbH",         "title":"QCDscale_bbH",         "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"bbH:1.202/0.761"},

    {"name":"alphaS_ggH",           "title":"alphaS_ggH",           "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"ggH:1.026"},
    {"name":"alphaS_qqH",           "title":"alphaS_qqH",           "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"qqH:1.005"},
    {"name":"alphaS_VH",            "title":"alphaS_VH",            "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"WH:1.009,ZH:1.009"},
    {"name":"alphaS_ttH",           "title":"alphaS_ttH",           "type":"constant",  "prior":"lnN",  "correlateAcrossYears":1,   "value":"ttH:1.020"},
]


# EXPERIMENTAL SYSTEMATICS
# * correlateAcrossYears = 0 : no correlation
# * correlateAcrossYears = 1 : fully correlated
# * correlateAcrossYears = -1 : partially correlated
# ! Things to check:
#   1) estimate the experimaental uncertainties
experimental_systematics = [
    # Integrated luminosity
    #! FIXEDME: Lumi unc
    # https://twiki.cern.ch/twiki/bin/view/CMS/LumiRecommendationsRun2#LumiComb
    {"name":"lumi_13TeV_uncorr",  "title":"lumi_13TeV",         "type":"constant",  "prior":"lnN",      "correlateAcrossYears":0,      "value":"2016:1.022,2017:1.020,2018:1.015"},
    {"name":"lumi_13TeV_corr",    "title":"lumi_13TeV_corr",    "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.006,2017:1.009,2018:1.020"},
    {"name":"lumi_13TeV_corr1718", "title":"lumi_13TeV_corr1718", "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,    "value":"2016:-,2017:1.006,2018:1.002"},

    # ! FIXEDME: use 3% to estimate the following experimental uncertainties
    {"name":"CMS_HLTeff_13TeV",   "title":"weight_HLT",         "type":"rate",      "prior":"lnN",       "correlateAcrossYears":0,      "value":""},
    {"name":"CMS_IDeff_m_13TeV",  "title":"weight_MuID",       "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,      "value":""},
    {"name":"CMS_IDeff_g_13TeV",  "title":"weight_PhoID",       "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,      "value":""},

    # L1 prefiring weights, underlying event, parton showering, pileup reweighting
    {"name":"CMS_L1_13TeV",       "title":"weight_L1PF",       "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_Mu_13TeV",       "title":"weight_MuPF",       "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_PU_13TeV",       "title":"weight_puwei",       "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_UE_13TeV",       "title":"CMS_UE_13TeV",       "type":"constant",  "prior":"lnN",       "correlateAcrossYears":1,       "value":"2016:1.030,2017:1.030,2018:1.030"},
    {"name":"CMS_PS_13TeV",       "title":"CMS_PS_13TeV",       "type":"constant",  "prior":"lnN",       "correlateAcrossYears":1,       "value":"2016:1.030,2017:1.030,2018:1.030"},
    
    # # R9 reweighting: only for EBHR9, LR9 categories
    {"name":"CMS_R9_13TeV",       "title":"PhoNoR9Corr",        "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,       "value":""},

    # # Jet energy scale/resolution: only for VBF categories 
    {"name":"CMS_JER_13TeV",      "title":"JER",                "type":"rate",      "prior":"lnN",      "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_JEC_13TeV",      "title":"JEC",                "type":"rate",      "prior":"lnN",      "correlateAcrossYears":1,       "value":""},

    # shape uncertainties
    {"name":"CMS_hmmg_scale",      "title":"CMS_hmmg_scale",     "type":"factory",   "prior":"param",   "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_hmmg_resol",      "title":"CMS_hmmg_resol",     "type":"factory",   "prior":"param",   "correlateAcrossYears":1,       "value":""},
]
