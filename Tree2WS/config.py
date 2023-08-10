from commonObjects import massBaseList, years, twd__
from glob import glob

inDir = "/data4/chenghan/muon/miniTree/"

# config dict 
trees2ws_cfg = {}
for mass in massBaseList:
    trees2ws_cfg[mass] = {}
    for year in years:
        trees2ws_cfg[mass][year] = {
            # Input root files which contain TTree and TH1D (MuPhoTrig+SingleMuTrig)
            "inputTreeFiles": {
                "ggH": glob(f"{inDir}/UL{year}*/miniTree_HDalitz_ggF_mmg_{mass}_UL{year}*_*.root"),
                "VBF": glob(f"{inDir}/UL{year}*/miniTree_HDalitz_VBF_mmg_{mass}_UL{year}*_*.root"),
                "WH":  glob(f"{inDir}/UL{year}*/miniTree_HDalitz_WH_mmg_{mass}_UL{year}*_*.root"),
                "ZH":  glob(f"{inDir}/UL{year}*/miniTree_HDalitz_ZH_mmg_{mass}_UL{year}*_*.root"),
                "ttH": glob(f"{inDir}/UL{year}*/miniTree_HDalitz_ttH_mmg_{mass}_UL{year}*_*.root"),
                "bbH": glob(f"{inDir}/UL{year}*/miniTree_HDalitz_bbH_mmg_{mass}_UL{year}*_*.root")
            },

            # Name of the input tree
            "inputTreeName":  "miniTree",
            
            # Output root files which contain WS
            "outputWSFiles": {
                "ggH": f"{twd__}/WS/{year}/signal_ggH_{mass}.root",
                "VBF": f"{twd__}/WS/{year}/signal_VBF_{mass}.root",
                "WH":  f"{twd__}/WS/{year}/signal_WH_{mass}.root",
                "ZH":  f"{twd__}/WS/{year}/signal_ZH_{mass}.root",
                "ttH": f"{twd__}/WS/{year}/signal_ttH_{mass}.root",
                "bbH": f"{twd__}/WS/{year}/signal_bbH_{mass}.root"
            },
            
            # weights for systematics
            "sysWeis": [
                "weight_MuIDDo",
                "weight_MuIDUp",
                "weight_HLTDo",
                "weight_HLTUp",
                "weight_L1PFDo",
                "weight_L1PFUp",
                "weight_MuPFDo",
                "weight_MuPFUp",
                "weight_PhoIDDo",
                "weight_PhoIDUp",
                "weight_puweiDo",
                "weight_puweiUp"
            ],
            
            # hists of systematics: 
            "sysHists":[
                "JERUp",
                "JERDo",
                "JECUp",
                "JECDo",
                
                "MuCalibStat",
                "MuCalibZpt",
                "MuCalibEwk",
                "MuCalibdeltaM",
                "MuCalibEwk2",
        
                "PhoNoR9Corr",
                "PhoScaleStatUp",
                "PhoScaleSystUp",
                "PhoScaleGainUp",
                "PhoScaleStatDo",
                "PhoScaleSystDo",
                "PhoScaleGainDo",
                "PhoSigmaPhiUp",
                "PhoSigmaRhoUp",
                "PhoSigmaRhoDo"
            ]
        }