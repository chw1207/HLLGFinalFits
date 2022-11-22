from commonObjects import massBaseList, years, twd__

inDir = "/data4/chenghan/electron/miniTree"
trees2ws_cfg = {}
for mass in massBaseList:
    trees2ws_cfg[mass] = {}
    for year in years:
        fdict = {}
        if (year == 2016):
            fdict = {
                "ggH": ["{}/UL{}preVFP/miniTree_HDalitz_ggF_eeg_{}_UL{}preVFP.root".format(inDir, year, mass, year), "{}/UL{}postVFP/miniTree_HDalitz_ggF_eeg_{}_UL{}postVFP.root".format(inDir, year, mass, year)],
                "VBF": ["{}/UL{}preVFP/miniTree_HDalitz_VBF_eeg_{}_UL{}preVFP.root".format(inDir, year, mass, year), "{}/UL{}postVFP/miniTree_HDalitz_VBF_eeg_{}_UL{}postVFP.root".format(inDir, year, mass, year)],
                "WH":  ["{}/UL{}preVFP/miniTree_HDalitz_WH_eeg_{}_UL{}preVFP.root".format(inDir, year, mass, year), "{}/UL{}postVFP/miniTree_HDalitz_WH_eeg_{}_UL{}postVFP.root".format(inDir, year, mass, year)],
                "ZH":  ["{}/UL{}preVFP/miniTree_HDalitz_ZH_eeg_{}_UL{}preVFP.root".format(inDir, year, mass, year), "{}/UL{}postVFP/miniTree_HDalitz_ZH_eeg_{}_UL{}postVFP.root".format(inDir, year, mass, year)],
                "ttH": ["{}/UL{}preVFP/miniTree_HDalitz_ttH_eeg_{}_UL{}preVFP.root".format(inDir, year, mass, year), "{}/UL{}postVFP/miniTree_HDalitz_ttH_eeg_{}_UL{}postVFP.root".format(inDir, year, mass, year)],
                "bbH": ["{}/UL{}preVFP/miniTree_HDalitz_bbH_eeg_{}_UL{}preVFP.root".format(inDir, year, mass, year), "{}/UL{}postVFP/miniTree_HDalitz_bbH_eeg_{}_UL{}postVFP.root".format(inDir, year, mass, year)]
            }
        else:
            fdict = {
                "ggH": ["{}/UL{}/miniTree_HDalitz_ggF_eeg_{}_UL{}.root".format(inDir, year, mass, year)],
                "VBF": ["{}/UL{}/miniTree_HDalitz_VBF_eeg_{}_UL{}.root".format(inDir, year, mass, year)],
                "WH":  ["{}/UL{}/miniTree_HDalitz_WH_eeg_{}_UL{}.root".format(inDir, year, mass, year)],
                "ZH":  ["{}/UL{}/miniTree_HDalitz_ZH_eeg_{}_UL{}.root".format(inDir, year, mass, year)],
                "ttH": ["{}/UL{}/miniTree_HDalitz_ttH_eeg_{}_UL{}.root".format(inDir, year, mass, year)],
                "bbH": ["{}/UL{}/miniTree_HDalitz_bbH_eeg_{}_UL{}.root".format(inDir, year, mass, year)]
            }

        trees2ws_cfg[mass][year] = {
            # Input root files which contain TTree
            "inputTreeFiles": fdict,

            # Name of the input tree
            "inputTreeName":  "miniTree",

            # Output root files which contain WS
            "outputWSFiles": {
                "ggH": "{}/WS/{}/signal_ggH_{}.root".format(twd__, year, mass, year),
                "VBF": "{}/WS/{}/signal_VBF_{}.root".format(twd__, year, mass, year),
                "WH":  "{}/WS/{}/signal_WH_{}.root".format(twd__, year, mass, year),
                "ZH":  "{}/WS/{}/signal_ZH_{}.root".format(twd__, year, mass, year),
                "ttH": "{}/WS/{}/signal_ttH_{}.root".format(twd__, year, mass, year),
                "bbH": "{}/WS/{}/signal_bbH_{}.root".format(twd__, year, mass, year)
            },

            # mass point
            "MassPoint": mass,

            # Vars in the minitree and to be added to workspace
            "TreeVars": ["CMS_higgs_mass", "weight"],

            # Variables to add to sytematic
            "systematicsVars": ["CMS_higgs_mass", "weight"],

            # List of systematics:
            'systematics': [
                "JERUp",
                "JERDo",
                "JECUp",
                "JECDo",
                "PhoScaleStatUp",
                "PhoScaleSystUp",
                "PhoScaleGainUp",
                "PhoScaleStatDo",
                "PhoScaleSystDo",
                "PhoScaleGainDo",
                "PhoSigmaPhiUp",
                "PhoSigmaRhoUp",
                "PhoSigmaRhoDo",
                "EleScaleStatUp",
                "EleScaleSystUp",
                "EleScaleGainUp",
                "EleScaleStatDo",
                "EleScaleSystDo",
                "EleScaleGainDo",
                "EleSigmaPhiUp",
                "EleSigmaRhoUp",
                "EleSigmaRhoDo",
                "EleHDALScaleUp",
                "EleHDALScaleDo",
                "EleHDALSmearUp",
                "EleHDALSmearDo"
            ]
        }