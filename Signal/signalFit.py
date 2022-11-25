# Script to perform the signal fit
# * Run script once per category per year, loops over signal processes and mass points(120, 125, 130)

import sys
sys.path.append("./tools")

import ROOT
from simpleFit import simpleFit
from Interpolation import Interpolator
from argparse import ArgumentParser
from collections import OrderedDict as od
from commonObjects import inputWSName__, productionModes, swd__, massBaseList, outputWSName__
from commonTools import color


def get_parser():
    parser = ArgumentParser(description="Script to perform the signal fit")
    parser.add_argument("-c",   "--category",        help="RECO category",                                   default="",     type=str)
    parser.add_argument("-y",   "--year",            help="Year",                                            default="",     type=str)
    parser.add_argument("-i",   "--inputWSDir",      help="Input WS directory",                              default="",     type=str)
    parser.add_argument("-ds",  "--doSystematics",   help="Estimate the shape uncertainties",                default=False,  action="store_true")
    parser.add_argument("-di",  "--doInterpolation", help="Do the interpolation(intermediate signal model)", default=False,  action="store_true")

    return parser


def main():
    for proc in productionModes:
        yields, fitres = od(), od()
        for mass in massBaseList:
            print(color.GREEN + "--> Performing the nominal signal fitting of {} @ {}GeV".format(proc, mass) + color.END)
            # Open ROOT file and extract workspace
            WSFileName = "%s/signal_%s_%d.root" %(args.inputWSDir, proc, mass)
            f = ROOT.TFile(WSFileName)
            if f.IsZombie():
                sys.exit(1)
            inputWS = f.Get(inputWSName__)
            if not inputWS:
                print("Fail to get workspace %s" %(inputWSName__))
                sys.exit(1)

            # Get dataset and var from workspace
            nominalDataName = "set_%d_%s"%(mass, args.category)
            xvar = inputWS.var("CMS_higgs_mass")
            data = inputWS.data(nominalDataName)

            # FIT: unbinned ML fit
            fit = simpleFit(data, xvar, mass, 110, 170)
            fit.buildDCBplusGaussian()
            fitres[mass] = fit.runFit()
            yields[mass] = data.sumEntries()

            # VISUALIZATION: draw the fitting
            outName = "{}/plots/signalFit/{}/CMS_HLLG_sigfit_{}_{}_{}_{}.pdf".format(swd__, args.year, mass, proc, args.year, args.category)
            fit.visualize(args.year, "M_{ee#gamma} [GeV]", args.category, proc, outName)

            # Close the input workspace file
            f.Close()
            print("")

        if args.doInterpolation:
            # INTERPOLATRION: The signal models are gotten from the interpolation of the fittings pdfs @ 120, 125 and 130 GeV
            # specify save=True to save the final signal models
            outWSDir = "{}/WS/Interpolation/{}".format(swd__, args.year)
            interp = Interpolator(yields, fitres, 110, 170, args.year, proc, args.category)
            interp.calcPolation()
            interp.buildFinalPdfs(
                save=True,
                outWS=outputWSName__, outWSDir=outWSDir,
                doSystematics=args.doSystematics
            )

            # VISUALIZATION: draw the fitting
            outPlotName = "{}/plots/Interpolation/{}/CMS_HLLG_Interp_{}_{}_{}.pdf".format(swd__, args.year, proc, args.year, args.category)
            interp.visualize("M_{ee#gamma} [GeV]", outPlotName)


if __name__ == "__main__" :
    # Extract information from config file:
    parser = get_parser()
    args = parser.parse_args()

    main()