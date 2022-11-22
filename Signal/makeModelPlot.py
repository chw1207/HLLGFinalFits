# Script to draw the signal models
# * draw the model per category, proc and mass point, combine all three years

import sys, os
sys.path.append("./tools")
import ROOT
import numpy as np
from argparse import ArgumentParser
from collections import OrderedDict as od
from CMS_lumi import CMS_lumi
from sigmaEff import sigmaEff
from commonObjects import inputWSName__, twd__, swd__, outputWSName__, yearsStr


def get_parser():
    parser = ArgumentParser(description="Script to plot the final signal model")
    parser.add_argument("-c",   "--category",  help="RECO category",                type=str)
    parser.add_argument("-p",   "--process",   help="process",                      type=str)
    parser.add_argument("-m",   "--mass",      help="mass point[120, 125, 130]",    default=125,  type=int)
    parser.add_argument("-n",   "--nBins",     help="number of bins",               default=60,   type=int)

    return parser


def get_ws(fwname, wname):
    fw = ROOT.TFile(fwname, "READ")
    if fw.IsZombie:
        sys.exit(1)
    inWS = ROOT.RooWorkspace()
    fw.GetObject(wname, inWS)
    fw.Close()
    return inWS


def plot_signal(hists, xmin, xmax, eff_sigma, outName, cat, process, offset=0.03):
    ROOT.gStyle.SetPadTickX(1)
    ROOT.gStyle.SetPadTickY(1)
    ROOT.gStyle.SetOptStat(0)

    colorMap = {"2016":38, "2017":30, "2018":46}

    canv = ROOT.TCanvas("canv", "", 850, 800)
    canv.cd()
    canv.SetRightMargin(0.05)
    canv.SetTopMargin(0.07)
    canv.SetLeftMargin(0.13)
    canv.SetBottomMargin(0.12)

    h_axes = hists["data"].Clone()
    h_axes.Reset()
    h_axes.SetMaximum(hists["data"].GetMaximum() * 1.2)
    h_axes.SetMinimum(0.)
    h_axes.GetXaxis().SetLimits(105, 140)
    h_axes.SetTitle("")
    h_axes.GetXaxis().SetTickSize(0.03)
    h_axes.GetXaxis().SetTitleSize(0.04)
    h_axes.GetXaxis().SetLabelSize(0.04)
    h_axes.GetXaxis().SetLabelOffset(0.02)
    h_axes.GetXaxis().SetTitleOffset(1.4)
    h_axes.GetXaxis().SetTitle("M_{ee#gamma} [GeV]")
    # h_axes.GetYaxis().SetTitle("Signal shape / ({} GeV)".format((170 - 105)/Nbins))
    h_axes.GetYaxis().SetNdivisions(510)
    h_axes.GetYaxis().SetTickSize(0.03)
    h_axes.GetYaxis().SetTitleSize(0.04)
    h_axes.GetYaxis().SetLabelSize(0.04)
    h_axes.GetYaxis().SetTitleOffset(1.7)
    h_axes.Draw()

    # Extract effSigma
    effSigma = eff_sigma["all"]
    effSigma_low, effSigma_high = xmin["all"], xmax["all"]
    h_effSigma = hists["pdf"].Clone()
    h_effSigma.GetXaxis().SetRangeUser(effSigma_low, effSigma_high)
    print("eff_sigma = {:.2f} [GeV]".format(effSigma))

    # Set style effSigma
    h_effSigma.SetLineColor(15)
    h_effSigma.SetLineWidth(3)
    h_effSigma.SetFillStyle(1001)
    h_effSigma.SetFillColor(19)
    h_effSigma.Draw("Same Hist F")
    vline_effSigma_low = ROOT.TLine(effSigma_low, 0, effSigma_low, hists["pdf"].GetBinContent(hists["pdf"].FindBin(effSigma_low)))
    vline_effSigma_high = ROOT.TLine(effSigma_high, 0, effSigma_high, hists["pdf"].GetBinContent(hists["pdf"].FindBin(effSigma_high)))
    vline_effSigma_low.SetLineColor(15)
    vline_effSigma_high.SetLineColor(15)
    vline_effSigma_low.SetLineWidth(3)
    vline_effSigma_high.SetLineWidth(3)
    vline_effSigma_low.Draw("Same")
    vline_effSigma_high.Draw("Same")

    # Extract FWHM and set style
    fwhm_low = hists["pdf"].GetBinCenter(hists["pdf"].FindFirstBinAbove(0.5*hists["pdf"].GetMaximum()))
    fwhm_high = hists["pdf"].GetBinCenter(hists["pdf"].FindLastBinAbove(0.5*hists["pdf"].GetMaximum()))
    fwhmArrow = ROOT.TArrow(fwhm_low, 0.5*hists["pdf"].GetMaximum(), fwhm_high,0.5*hists["pdf"].GetMaximum(), 0.02, "<>")
    fwhmArrow.SetLineWidth(2)
    fwhmArrow.Draw("Same <>")

    # Set style pdf
    hists["pdf"].SetLineColor(4)
    hists["pdf"].SetLineWidth(3)
    hists["pdf"].Draw("Same Hist C")

    for year in yearsStr:
        hists["pdf_{}".format(year)].SetLineColor(colorMap[year])
        hists["pdf_{}".format(year)].SetLineStyle(2)
        hists["pdf_{}".format(year)].SetLineWidth(3)
        hists["pdf_{}".format(year)].Draw("Same Hist C")

    # Set style: data
    hists["data"].SetMarkerStyle(25)
    hists["data"].SetMarkerColor(1)
    hists["data"].SetMarkerSize(1.5)
    hists["data"].SetLineColor(1)
    hists["data"].SetLineWidth(2)
    hists["data"].Draw("Same ep X0")

    # legend
    leg0 = ROOT.TLegend(0.14+offset, 0.68, 0.5+offset, 0.82)
    leg0.SetFillStyle(0)
    leg0.SetLineColorAlpha(0,0)
    leg0.SetTextSize(0.033)
    leg0.AddEntry(hists["data"], "Simulation", "ep")
    leg0.AddEntry(hists["pdf"], "#splitline{Parametric}{model}", "l")
    leg0.Draw("Same")

    leg1 = ROOT.TLegend(0.16+offset, 0.52, 0.4+offset, 0.68)
    leg1.SetFillStyle(0)
    leg1.SetLineColorAlpha(0,0)
    leg1.SetTextSize(0.029)
    for year in yearsStr:
        leg1.AddEntry(hists["pdf_{}".format(year)], "%s: #sigma_{eff} = %1.2f GeV" %(year, eff_sigma["{}".format(year)]), "l")
    leg1.Draw("Same")

    leg2 = ROOT.TLegend(0.14+offset, 0.42, 0.4+offset, 0.52)
    leg2.SetFillStyle(0)
    leg2.SetLineColorAlpha(0,0)
    leg2.SetTextSize(0.033)
    leg2.AddEntry(h_effSigma, "#sigma_{eff} = %1.2f GeV" %effSigma, "fl")
    leg2.Draw("Same")

    fwhmText = ROOT.TLatex()
    fwhmText.SetTextFont(42)
    fwhmText.SetTextAlign(11)
    fwhmText.SetNDC()
    fwhmText.SetTextSize(0.033)
    fwhmText.DrawLatex(0.15+offset, 0.37, "FWHM = %1.2f GeV"%(fwhm_high-fwhm_low))

    mode = ROOT.TLatex()
    mode.SetTextFont(42)
    mode.SetNDC()
    mode.SetTextSize(0.04)
    mode.DrawLatex(0.16+offset, 0.86, "H #rightarrow #gamma*#gamma #rightarrow ee#gamma")

    catProc = ROOT.TLatex()
    catProc.SetTextFont(42)
    catProc.SetNDC()
    catProc.SetTextSize(0.035)
    catProc.DrawLatex(0.55+offset, 0.86, "{}, {}".format(process, cat))

    CMS_lumi(canv, 5, 0, "", 2017, True, "Preliminary", "", "")
    canv.Update()
    canv.RedrawAxis()

    canv.SaveAs(outName)
    canv.Close()


def main():
    # container
    hists, hpdfs, data = od(), od(), od()

    # build data histogram
    CMS_higgs_mass = ROOT.RooRealVar("CMS_higgs_mass", "CMS_higgs_mass", 110, 170, "GeV")
    CMS_higgs_mass.setRange("NormRange", 110, 170)
    CMS_higgs_mass.setMin(110)
    CMS_higgs_mass.setMax(170)
    hists["data"] = CMS_higgs_mass.createHistogram("h_data", ROOT.RooFit.Binning(args.nBins)) # create a empty histogram for dataset

    # datasets and eff_sigma
    ScaleNumber = 400 # use to create smooth histogram
    xmin, xmax, eff_sigma = od(), od(), od()
    vall = []
    for year in yearsStr:
        # extract the dataset
        fsetname = "{}/WS/{}/signal_{}_{}.root".format(twd__, year, args.process, args.mass)
        inputWSSet = get_ws(fsetname, inputWSName__)
        dname = "set_{}_{}".format(args.mass, args.category)
        data[year] = inputWSSet.data(dname)
        data[year].fillHistogram(hists["data"], ROOT.RooArgList(CMS_higgs_mass)) # fill the histogram for dataset

        # calculate the effective sigma per year
        v = []
        for i in range(data[year].numEntries()):
            ods_value = data[year].get(i).getRealValue(CMS_higgs_mass.GetName())
            v.append(ods_value)
            vall.append(ods_value)
        xmin["{}".format(year)], xmax["{}".format(year)], eff_sigma["{}".format(year)] = sigmaEff(np.array(v))

        # extract the final models per year
        fpdfname = "{}/WS/Interpolation/{}/CMS_HLLG_Interp_{}_{}_{}_{}.root".format(swd__, year, args.mass, args.process, year, args.category)
        inputWSPdf = get_ws(fpdfname, outputWSName__)
        pdf = inputWSPdf.pdf("SigPdf")
        hpdfs[year] = pdf.createHistogram("h_pdf_%s"%year, CMS_higgs_mass, ROOT.RooFit.Binning(args.nBins * ScaleNumber))

    # calculate the effective sigma for 3 years
    xmin["all"], xmax["all"], eff_sigma["all"] = sigmaEff(np.array(vall))

    # Sum pdf histograms
    for k, p in hpdfs.iteritems():
        if "pdf" not in hists:
            hists["pdf"] = p.Clone("h_pdf")
            hists["pdf"].Reset()
        hists["pdf"] += p
    hists["pdf"].Scale(hists["data"].Integral() * ScaleNumber / hists["pdf"].Integral())

    # Per-year pdf histograms
    for year in yearsStr:
        if "pdf_{}".format(year) not in hists:
            hists["pdf_{}".format(year)] = hists["pdf"].Clone()
            hists["pdf_{}".format(year)].Reset()
        for i, p in hpdfs.iteritems():
            if year == i:
                hists["pdf_{}".format(year)] += p
        hists["pdf_{}".format(year)].Scale(data[year].sumEntries() * ScaleNumber / hists["pdf_{}".format(year)].Integral())

    # draw the signal model
    outPlot = "{}/plots/final".format(swd__)
    if not os.path.exists(outPlot):
        os.makedirs(outPlot)
    outName = "{}/FinalModel_{}_{}_{}.pdf".format(outPlot, args.mass, args.category, args.process)
    plot_signal(hists, xmin, xmax, eff_sigma, outName, args.category, args.process)


if __name__ == "__main__" :
    # get the arguments
    parser = get_parser()
    args = parser.parse_args()

    main()