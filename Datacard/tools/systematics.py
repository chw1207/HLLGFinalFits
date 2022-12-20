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
    {"name":"lumi_13TeV_uncorr",  "title":"lumi_13TeV",         "type":"constant",  "prior":"lnN",      "correlateAcrossYears":0,      "value":"2016:1.022,2017:1.020,2018:1.015"},
    {"name":"lumi_13TeV_calib",   "title":"lumi_13TeV_calib",   "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.009,2017:1.008,2018:1.002"},
    {"name":"lumi_13TeV_deflect", "title":"lumi_13TeV_deflect", "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.004,2017:1.004,2018:1.000"},
    {"name":"lumi_13TeV_dynamic", "title":"lumi_13TeV_dynamic", "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.005,2017:1.005,2018:1.000"},
    {"name":"lumi_13TeV_sat",     "title":"lumi_13TeV_sat",     "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.000,2017:1.004,2018:1.001"},
    {"name":"lumi_13TeV_sc",      "title":"lumi_13TeV_sc",      "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.000,2017:1.003,2018:1.002"},
    {"name":"lumi_13TeV_xy",      "title":"lumi_13TeV_xy",      "type":"constant",  "prior":"lnN",      "correlateAcrossYears":1,      "value":"2016:1.009,2017:1.008,2018:1.02"},

    # ! FIXEDME: use 3% to estimate the following experimental uncertainties
    # Todo: HLT eff & Merged ID eff
    {"name":"CMS_HLTeff_13TeV",   "title":"hlt",                "type":"rate",      "prior":"lnN",       "correlateAcrossYears":0,      "value":""},
    {"name":"CMS_Reco_e_13TeV",   "title":"recoE",              "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,      "value":""},
    {"name":"CMS_IDeff_e_13TeV",  "title":"eleID",              "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,      "value":""},
    {"name":"CMS_IDeff_g_13TeV",  "title":"phoID",              "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,      "value":""},
    {"name":"CMS_Vetoeff_13TeV",  "title":"csev",               "type":"rate",      "prior":"lnN",       "correlateAcrossYears":0,      "value":""},

    # L1 prefiring weights, underlying event, parton showering, pileup reweighting
    {"name":"CMS_L1_13TeV",       "title":"l1pf",               "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_PU_13TeV",       "title":"puwei",              "type":"rate",      "prior":"lnN",       "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_UE_13TeV",       "title":"CMS_UE_13TeV",       "type":"constant",  "prior":"lnN",       "correlateAcrossYears":1,       "value":"2016:1.030,2017:1.030,2018:1.030"},
    {"name":"CMS_PS_13TeV",       "title":"CMS_PS_13TeV",       "type":"constant",  "prior":"lnN",       "correlateAcrossYears":1,       "value":"2016:1.030,2017:1.030,2018:1.030"},
    
    # # R9 reweighting: only for EBHR9, LR9 categories
    # {"name":"CMS_R9_13TeV",       "title":"CMS_R9_13TeV",        "type":"constant",  "prior":"lnN",     "correlateAcrossYears":1,     "value":"2016:1.030,2017:1.030,2018:1.030"},

    # # Jet energy scale/resolution: only for VBF categories
    {"name":"CMS_JER_13TeV",      "title":"JER",                "type":"rate",      "prior":"lnN",      "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_JEC_13TeV",      "title":"JEC",                "type":"rate",      "prior":"lnN",      "correlateAcrossYears":1,       "value":""},

    # shape uncertainties
    {"name":"CMS_heeg_scale",      "title":"CMS_heeg_scale",     "type":"factory",   "prior":"param",   "correlateAcrossYears":1,       "value":""},
    {"name":"CMS_heeg_resol",      "title":"CMS_heeg_resol",     "type":"factory",   "prior":"param",   "correlateAcrossYears":1,       "value":""},
]
