import os, sys
import ROOT
import numpy as np
from TdrStyle import setTDRStyle
from array import array
from collections import OrderedDict as od
from commonObjects import massBaseList, dwd__
from CMS_lumi import CMS_lumi
from pprint import pprint

def GetValuesFromFile(fname):
    fin = ROOT.TFile(fname, "READ")
    if fin.IsZombie():
        sys.exit(1)
    tin = fin.Get("limit")
    res = [ev.limit for ev in tin]
    return res


def LimitVsM():
    Limit = od([("2sigma_do", array("f", [])), ("1sigma_do", array("f", [])), ("mean", array("f", [])), ("1sigma_up", array("f", [])), ("2sigma_up", array("f", [])), ("mass", array("f", []))])
    mass_interp = np.linspace(massBaseList[0], massBaseList[-1], 11, endpoint=True).astype(int)
    for m in mass_interp:
        input_file = "{}/tree/higgsCombine_nom1_{}.AsymptoticLimits.mH{}.root".format(dwd__, m, m)
        _limit = GetValuesFromFile(input_file)
        Limit["2sigma_do"].append(_limit[0])
        Limit["1sigma_do"].append(_limit[1])
        Limit["mean"].append(_limit[2])
        Limit["1sigma_up"].append(_limit[3])
        Limit["2sigma_up"].append(_limit[4])
        Limit["mass"].append(m)

    npoints = len(Limit["mean"])
    xerr = array("f", [0] * npoints)
    sigma2_err_do = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["2sigma_do"])])
    sigma1_err_do = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["1sigma_do"])])
    sigma2_err_up = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["2sigma_up"])])
    sigma1_err_up = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["1sigma_up"])])
    expErr = ROOT.TGraphAsymmErrors(npoints, Limit["mass"], Limit["mean"])
    sigma2 = ROOT.TGraphAsymmErrors(npoints, Limit["mass"], Limit["mean"], xerr, xerr, sigma2_err_do, sigma2_err_up)
    sigma1 = ROOT.TGraphAsymmErrors(npoints, Limit["mass"], Limit["mean"], xerr, xerr, sigma1_err_do, sigma1_err_up)

    c1 = ROOT.TCanvas("c1", "c1", 700, 700)
    c1.SetRightMargin(0.05)
    c1.SetTopMargin(0.07)
    c1.SetBottomMargin(0.14)
    c1.SetLeftMargin(0.14)
    c1.cd()

    mg = ROOT.TMultiGraph()
    mg.SetTitle("")

    sigma2.SetFillColor(ROOT.kOrange)
    sigma1.SetFillColor(ROOT.kGreen+1)
    expErr.SetMarkerColor(ROOT.kBlack)
    expErr.SetLineColor(ROOT.kBlack)
    expErr.SetLineWidth(3)
    expErr.SetLineStyle(7)

    mg.Add(sigma2, "")
    mg.Add(sigma1, "")
    mg.Add(expErr, "")

    mg.Draw("AL3")

    max_element = max(Limit["2sigma_up"])
    mg.GetXaxis().SetTitle("M_{ee#gamma} [GeV]")
    mg.GetXaxis().SetTitleSize(0.05)
    mg.GetXaxis().SetLabelSize(0.05)
    mg.GetYaxis().SetTitleSize(0.05)
    mg.GetYaxis().SetLabelSize(0.05)
    # mg.SetMinimum(0)
    # mg.SetMaximum(15)
    mg.GetXaxis().SetLimits(119.5, 130.5)
    mg.GetYaxis().SetTitle("95% CL limit on #sigma/#sigma_{SM}")
    mg.GetXaxis().SetTitleOffset(1.2)
    mg.GetYaxis().SetTitleOffset(1.2)
    mg.GetYaxis().SetRangeUser(0, max_element * 2.5)
    # mg.GetYaxis().SetRangeUser(0, 12)
    mg.Draw("zE2")
    mg.Draw("AL3")

    leg = ROOT.TLegend(0.6, 0.72, 0.9, 0.89)
    # leg.SetNColumns(2)
    leg.SetTextFont(42)
    leg.SetTextSize(0.04)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)
    leg.AddEntry(expErr, "Expected", "l")
    leg.AddEntry(sigma1, "68% expected", "f")
    leg.AddEntry(sigma2, "95% expected", "f")
    leg.Draw()

    line = ROOT.TLine(119.5, 1, 130.5, 1)
    line.SetLineColor(ROOT.kRed)
    line.SetLineWidth(2)
    line.Draw()

    CMS_lumi(c1, 5, 0, "138 fb^{-1}", 0, True, "Preliminary", "", "")
    c1.RedrawAxis()
    
    if not os.path.exists("./plots"):
        os.system("mkdir ./plots")
    c1.Print("./plots/LimitVSMass.pdf")
    c1.Print("./plots/LimitVSMass.png")
    c1.Close()


def LimitSummary():
    cat_tag = od()
    cat_tag["nom1"]             = "Combined"
    cat_tag["untagm2"]          = "Merged2Gsf Untagged Combined"
    cat_tag["Merged2Gsf_EE"]    = "Merged2Gsf EE"
    cat_tag["Merged2Gsf_EBLR9"] = "Merged2Gsf EB LR9"
    cat_tag["Merged2Gsf_EBHR9"] = "Merged2Gsf EB HR9"
    cat_tag["tagm2"]            = "Merged2Gsf VBF Combined"
    cat_tag["Merged2Gsf_LVBF"]  = "Merged2Gsf LVBF"
    cat_tag["Merged2Gsf_HVBF"]  = "Merged2Gsf HVBF"
    cat_tag["Merged2Gsf_BST"]   = "Merged2Gsf Boost"
    cat_tag["re"]               = "Resolved"
    
    yhigh = [0, 2, 2.8, 3.6, 4.5, 6.5, 7.4, 8.3, 10.3, 12.3]
    Limit = od([("2sigma_do", array("f", [])), ("1sigma_do", array("f", [])), ("mean", array("f", [])), ("1sigma_up", array("f", [])), ("2sigma_up", array("f", [])), ("yaxis", array("f", yhigh))])
    for key, value in cat_tag.iteritems():
        input_file = "{}/tree/higgsCombine_{}_125.AsymptoticLimits.mH125.root".format(dwd__, key)
        _limit = GetValuesFromFile(input_file)
        Limit["2sigma_do"].append(_limit[0])
        Limit["1sigma_do"].append(_limit[1])
        Limit["mean"].append(_limit[2])
        Limit["1sigma_up"].append(_limit[3])
        Limit["2sigma_up"].append(_limit[4])

    npoints = len(Limit["mean"])
    xerr = array("f", [0] * npoints)
    yerr = array("f", [0.09] * npoints)
    sigma2_err_do = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["2sigma_do"])])
    sigma1_err_do = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["1sigma_do"])])
    sigma2_err_up = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["2sigma_up"])])
    sigma1_err_up = array("f", [abs(a - b) for a, b in zip(Limit["mean"], Limit["1sigma_up"])])
    expErr = ROOT.TGraphAsymmErrors(npoints, Limit["mean"], Limit["yaxis"], xerr, xerr, xerr, xerr)
    sigma2 = ROOT.TGraphAsymmErrors(npoints, Limit["mean"], Limit["yaxis"], sigma2_err_do, sigma2_err_up, yerr, yerr)
    sigma1 = ROOT.TGraphAsymmErrors(npoints, Limit["mean"], Limit["yaxis"], sigma1_err_do, sigma1_err_up, yerr, yerr)

    xmin, xmax = 0.5, 500
    mr = 0.04
    mt = 0.06
    mb = 0.13
    ml = 0.45

    c1 = ROOT.TCanvas("c1", "c1", 850, 800)
    c1.cd()
    c1.SetRightMargin(mr)
    c1.SetLeftMargin(ml)
    c1.SetTopMargin(mt)
    c1.SetBottomMargin(mb)
    c1.SetLogx()
    c1.Modified()
    c1.Update()

    sigma1.SetFillColor(ROOT.kGreen+1)
    sigma2.SetFillColor(ROOT.kOrange)
    expErr.SetMarkerStyle(20)
    expErr.SetMarkerSize(1)
    expErr.SetMarkerColor(ROOT.kBlack)
    expErr.SetLineColor(ROOT.kBlack)

    mg = ROOT.TMultiGraph()
    mg.SetTitle("")
    mg.Add(sigma2, "2")
    mg.Add(sigma1, "2")
    mg.Add(expErr, "e1p")
    mg.Draw("ap")
    mg.SetMinimum(yhigh[0] - 1)
    mg.SetMaximum(yhigh[-1]+5)
    
    line = ROOT.TLine(1, yhigh[0] - 1, 1, yhigh[-1]+5)
    line.SetLineColor(ROOT.kRed+1)
    line.SetLineWidth(2)
    line.Draw()
    
    mg.GetYaxis().SetTickLength(0)
    # mg.GetXaxis().SetLimits(1, 20)
    mg.GetYaxis().SetLabelOffset(999)
    # mg.GetXaxis().SetLabelOffset()
    mg.GetXaxis().SetLabelFont(42)
    mg.GetXaxis().SetLabelSize(0.04)
    mg.GetXaxis().SetTitleSize(0.04)
    mg.GetXaxis().SetTitleOffset(1.3)
    mg.GetXaxis().SetLimits(xmin, xmax+50)
    mg.GetXaxis().SetTitle("95% CL upper limit on #sigma/#sigma_{SM}")
    mg.GetXaxis().SetTitleOffset(1.5)

    leg = ROOT.TLegend(0.65, 0.79, 0.92, 0.98*(1-mt))
    leg.SetTextFont(42)
    leg.SetTextSize(0.04)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)
    leg.AddEntry(expErr, "Expected", "p")
    leg.AddEntry(sigma1, "#pm 1#sigma", "f")
    leg.AddEntry(sigma2, "#pm 2#sigma", "f")
    leg.Draw()

    latex = ROOT.TLatex()
    latex.SetTextColor(ROOT.kBlack)
    latex.SetTextSize(0.025)
    latex.SetTextAlign(32)
    i = 0
    for key, value in cat_tag.iteritems():
        latex.SetTextSize(0.025)
        latex.SetTextColor(ROOT.kBlack)
        latex.SetTextSize(0.030)
        if value == "Combined":
            latex.SetTextFont(72)
        else:
            latex.SetTextFont(42)
        latex.DrawLatex(xmin-0.1, Limit["yaxis"][i], value)
        
        i += 1

    latex.SetTextColor(ROOT.kBlack)
    latex.SetTextSize(0.03)
    latex.SetTextAlign(32)
    i = 0
    for i, exp in enumerate(Limit["mean"]):
        latex.DrawLatex(xmax*0.8, Limit["yaxis"][i], "{}".format(round(exp, 2)))
        i += 1

    CMS_lumi(c1, 5, 0, "138 fb^{-1}", 2017, True, "Preliminary", "", "")
    c1.RedrawAxis()
    c1.Update()

    if not os.path.exists("./plots"):
        os.system("mkdir ./plots")
    c1.Print("./plots/LimitSummary.pdf")
    c1.Print("./plots/LimitSummary.png")
    c1.Close()


if __name__ == "__main__" :
    setTDRStyle()
    LimitVsM()
    LimitSummary()