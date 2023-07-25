import os
import ROOT
from collections import OrderedDict as od
from CMS_lumi import CMS_lumi

class simpleFit:
    def __init__(self, _data, _xvar, _MH, _MHLow, _MHHigh):
        self.data   = _data     # RooDataset to be fitted
        self.xvar   = _xvar     # RooRealVar to build PDF
        self.MH     = _MH       # central mass point
        self.MHLow  = _MHLow    # lower bound of mass point
        self.MHHigh = _MHHigh   # upper bound of mass point

        # Parameter lookup table for initialisation (DCB + Gaus)
        # gauss shares the same mean as DCB
        _pars = od()
        _pars["DCB"] = od()
        _pars["DCB"]["mean"] = [self.MH, self.MH - 2, self.MHHigh + 2] # nominal, lower, upper (fitting range)
        _pars["DCB"]["sigma"] = [2, 0.1, 5]
        _pars["DCB"]["n1"] = [5, 0.1, 10] # n: normalization
        _pars["DCB"]["n2"] = [3, 0.1, 10]
        _pars["DCB"]["a1"] = [1, 0.1, 15] # a: Gaussian tail
        _pars["DCB"]["a2"] = [2, 0.1, 15]
        _pars["DCB"]["frac"] = [0.9, 0.6, 0.99] # fraction of DCB
        _pars["Gaus"] = od()
        _pars["Gaus"]["sigma"] = [25., 16, 100]

        # _pars["DCB"] = od()
        # _pars["DCB"]["mean"] = [self.MH, self.MH - 3, self.MHHigh + 3] # nominal, lower, upper (fitting range)
        # _pars["DCB"]["sigma"] = [2.5 , 0.1, 5.]
        # _pars["DCB"]["n1"] = [5, 0, 20]
        # _pars["DCB"]["n2"] = [3, 0, 20]
        # _pars["DCB"]["a1"] = [2, 0, 10]
        # _pars["DCB"]["a2"] = [5, 0, 10]
        # _pars["DCB"]["frac"] = [0.9, 0.6, 0.9999999999] # fraction of DCB
        # _pars["Gaus"] = od()
        # _pars["Gaus"]["sigma"] = [25., 16, 100]
        self.pars = _pars

        # Dicts to store all fit vars, polynomials, pdfs
        self.Vars = od()
        self.Pdfs = od()
        self.useDCB = False

        # Fit containers
        self.nBins = 60
        self.FitResult = None

        # setup the xvar
        self.xvar.setUnit("GeV")
        self.xvar.setMin(self.MHLow)
        self.xvar.setMax(self.MHHigh)
        self.xvar.setRange("NormRange", self.MHLow, self.MHHigh)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def buildDCBplusGaussian(self, floatingParm="all"):
        # build double sided crystalball
        for f in ["mean", "sigma", "n1", "n2", "a1", "a2", "frac"]:
            k = "%s_dcb"%f
            self.Vars[k] = ROOT.RooRealVar(k, k, self.pars["DCB"][f][0], self.pars["DCB"][f][1], self.pars["DCB"][f][2])
        self.Pdfs["DCB"] = ROOT.RooDoubleCB("DCB", "DCB", self.xvar, self.Vars["mean_dcb"], self.Vars["sigma_dcb"], self.Vars["a1_dcb"], self.Vars["n1_dcb"], self.Vars["a2_dcb"], self.Vars["n2_dcb"])

        # build gaussian
        self.Vars["sigma_gaus"] = ROOT.RooRealVar("sigma_gaus", "sigma_gaus", self.pars["Gaus"]["sigma"][0], self.pars["Gaus"]["sigma"][1], self.pars["Gaus"]["sigma"][2])
        self.Pdfs["Gaus"] = ROOT.RooGaussian("Gaus", "Gaus", self.xvar, self.Vars["mean_dcb"], self.Vars["sigma_gaus"])

        # dcb + gaus
        self.Pdfs["SigPdf"] = ROOT.RooAddPdf("SigPdf", "SigPdf", self.Pdfs["DCB"], self.Pdfs["Gaus"], self.Vars["frac_dcb"])

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def buildDCB(self, floatingParm="all"):
        for f in ["mean", "sigma", "n1", "n2", "a1", "a2"]:
            k = "%s_dcb"%f
            self.Vars[k] = ROOT.RooRealVar(k, k, self.pars["DCB"][f][0], self.pars["DCB"][f][1], self.pars["DCB"][f][2])
        self.Pdfs["SigPdf"] = ROOT.RooDoubleCB("SigPdf", "SigPdf", self.xvar, self.Vars["mean_dcb"], self.Vars["sigma_dcb"], self.Vars["a1_dcb"], self.Vars["n1_dcb"], self.Vars["a2_dcb"], self.Vars["n2_dcb"])
        self.useDCB = True

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def runFit(self):
        fRes = self.Pdfs["SigPdf"].fitTo(
            self.data,
            ROOT.RooFit.Save(ROOT.kTRUE),
            ROOT.RooFit.Range("NormRange"), ROOT.RooFit.Minimizer("Minuit", "minimize"),
            ROOT.RooFit.SumW2Error(ROOT.kTRUE), ROOT.RooFit.PrintLevel(-1)
        )
        self.FitResults = fRes
        return self.FitResults

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # specify the number of bins used to calculate the chi2 and visualize the fitting distribution
    # default nBins is 60
    def setNBins(self, bins):
        self.nBins = bins

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getChi2(self):
        print("INFO: Binned dataset with {} bins to calculate chi2.".format(self.nBins))
        self.xvar.setBins(self.nBins)
        dh = self.data.binnedClone()
        chi2 =  ROOT.RooChi2Var("chi2", "chi2", self.Pdfs["SigPdf"], dh, ROOT.RooFit.DataError(ROOT.RooAbsData.Expected))
        return chi2.getVal()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # xName: x-axis label
    # catName: name of category put on the plot
    # procName: name of process put on the plot
    # outName: path to save the plot
    def visualize(self, year, xName, catName, procName, outName):
        ROOT.gStyle.SetPadTickX(1)
        ROOT.gStyle.SetPadTickY(1)
        ROOT.gStyle.SetOptStat(0)

        xframe = self.xvar.frame(self.MHLow, self.MHHigh)
        self.data.plotOn(
            xframe, ROOT.RooFit.Name("set"),
            ROOT.RooFit.Binning(self.nBins),
            ROOT.RooFit.MarkerStyle(ROOT.kFullCircle), ROOT.RooFit.MarkerSize(1.5), ROOT.RooFit.XErrorSize(10e-5),
            ROOT.RooFit.DataError(ROOT.RooDataSet.SumW2)
        )

        self.Pdfs["SigPdf"].plotOn(
            xframe, ROOT.RooFit.Name("sigfit"),
            ROOT.RooFit.LineColor(ROOT.TColor.GetColor("#5893D4")), ROOT.RooFit.LineWidth(4)
        )

        if not self.useDCB:
            self.Pdfs["SigPdf"].plotOn(
                xframe, ROOT.RooFit.Components("DCB"), ROOT.RooFit.Name("DCB"),
                ROOT.RooFit.LineColor(ROOT.TColor.GetColor("#1C7747")), ROOT.RooFit.LineWidth(4), ROOT.RooFit.LineStyle(7)
            )

            self.Pdfs["SigPdf"].plotOn(
                xframe, ROOT.RooFit.Components("Gaus"), ROOT.RooFit.Name("Gaus"),
                ROOT.RooFit.LineColor(ROOT.TColor.GetColor("#E23E57")), ROOT.RooFit.LineWidth(4), ROOT.RooFit.LineStyle(7)
            )

        self.data.plotOn(
            xframe, ROOT.RooFit.Name("set"),
            ROOT.RooFit.Binning(self.nBins),
            ROOT.RooFit.MarkerStyle(ROOT.kFullCircle), ROOT.RooFit.MarkerSize(1.5), ROOT.RooFit.XErrorSize(10e-5),
            ROOT.RooFit.DataError(ROOT.RooDataSet.SumW2)
        )

        xframe.SetTitle("")
        xframe.GetXaxis().SetTickSize(0.03)
        xframe.GetXaxis().SetTitleSize(0.04)
        xframe.GetXaxis().SetLabelSize(0.04)
        xframe.GetXaxis().SetLabelOffset(0.02)
        xframe.GetXaxis().SetTitleOffset(1.4)
        xframe.GetXaxis().SetTitle(xName)
        xframe.GetYaxis().SetTitle("Signal shape / ({} GeV)".format((self.MHHigh - self.MHLow)/self.nBins))
        xframe.GetYaxis().SetNdivisions(510)
        xframe.GetYaxis().SetTickSize(0.03)
        xframe.GetYaxis().SetTitleSize(0.04)
        xframe.GetYaxis().SetLabelSize(0.04)
        xframe.GetYaxis().SetTitleOffset(1.6)
        xframe.SetMaximum(xframe.GetMaximum() * 500.)
        xframe.SetMinimum(xframe.GetMaximum() * 0.00000001)

        c = ROOT.TCanvas("c", "", 900, 900)
        c.cd()
        c.SetRightMargin(0.05)
        c.SetTopMargin(0.07)
        c.SetLeftMargin(0.14)
        c.SetBottomMargin(0.12)
        c.SetLogy()
        xframe.Draw()

        CMS_lumi(c, 5, 10, "", year, True, "Simulation", "H #rightarrow #gamma* #gamma #rightarrow ee#gamma", "")
        c.Update()
        c.RedrawAxis()

        ltx = ROOT.TLatex()
        ltx.SetNDC()
        ltx.SetTextFont(42)
        ltx.SetTextSize(0.037)
        ltx.DrawLatex(0.53, 0.86, "{}, {}".format(procName, catName))

        leg1 = ROOT.TLegend(0.53, 0.7, 0.9, 0.83)
        leg1.SetTextFont(42)
        leg1.SetTextSize(0.037)
        leg1.SetFillColor(0)
        leg1.SetLineColor(0)
        leg1.AddEntry(xframe.findObject("set"), "Simulation", "ep")
        leg1.AddEntry(xframe.findObject("sigfit"), "Parametric model", "l")
        leg1.Draw()

        if not self.useDCB:
            leg2 = ROOT.TLegend(0.61, 0.62, 0.9, 0.7)
            leg2.SetTextFont(42)
            leg2.SetTextSize(0.033)
            leg2.SetFillColor(0)
            leg2.SetLineColor(0)
            leg2.AddEntry(xframe.findObject("DCB"), "DCB", "l")
            leg2.AddEntry(xframe.findObject("Gaus"), "Gauss", "l")
            leg2.Draw("same")

        # create the output dir
        outDir = os.path.dirname(outName)
        if not os.path.exists(outDir):
            os.system("mkdir -p %s" %outDir)

        c.Print(outName)
        c.Close()