import sys, os
import ROOT
import numpy as np
from CMS_lumi import CMS_lumi
from commonObjects import decayMode
from commonTools import rooiter
from collections import OrderedDict as od

class Interpolator:
    def __init__(self, _yields, _fitres, _MHLow, _MHHigh, _year, _proc, _cat):
        self.MHLow      = _MHLow    # lower bound of mass point
        self.MHHigh     = _MHHigh   # upper bound of mass point
        self.yields     = _yields   # dict contains yields @ 120, 125 and 130 GeV
        self.fitres     = _fitres   # dict contains fit results @ 120, 125 and 130 GeV
        if self.yields.keys().sort() != self.fitres.keys().sort():
            print("Error: yields and fit results do not have the same mass points as keys!")
            sys.exit(1)

        self.year       = _year     # year
        self.proc       = _proc     # production modes
        self.cat        = _cat      # category

        # intermediate mass points
        # set num = 11 to have 1 GeV a step: 120, 121, 122 ... 130
        self.xmass      = self.fitres.keys() # 3 mass points (should be 120, 125, 130)
        self.xmass_intp = np.linspace(self.xmass[0], self.xmass[-1], 11, endpoint=True).astype(int)

        # Dicts to store all fit parameters, pdfs
        self.Pars       = od()
        self.ParsErr    = od()
        self.FinalPdfs  = od()

        # store the interpolated yields
        self.norms = []

        # setup the xvar
        self.xvar = ROOT.RooRealVar("CMS_higgs_mass", "CMS_higgs_mass", self.MHLow, self.MHHigh, "GeV")
        self.xvar.setRange("NormRange", self.MHLow, self.MHHigh)
        self.xvar.setMin(self.MHLow)
        self.xvar.setMax(self.MHHigh)
        self.xframe = self.xvar.frame(self.MHLow, self.MHHigh)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def calcPolation(self):
        # extract the parameter from the first fit result
        pars = [i.GetName() for i in rooiter(self.fitres[self.xmass[0]].floatParsFinal())]

        # fill the par values in the fit results into dict
        par_dict = od([(p, [1.]*len(self.xmass)) for p in pars])
        parErr_dict = od([(p, [0.]*len(self.xmass)) for p in pars])
        for imass in range(len(self.xmass)):
            for p in pars:
                par_dict[p][imass] = self.fitres[self.xmass[imass]].floatParsFinal().find(p).getValV()
                parErr_dict[p][imass] = self.fitres[self.xmass[imass]].floatParsFinal().find(p).getError()

        par_dict_intp = od([(p, [1.]*len(self.xmass_intp)) for p in pars])
        parErr_dict_intp = od([(p, [0.]*len(self.xmass_intp)) for p in pars])

        # interpolation: https://numpy.org/doc/stable/reference/generated/numpy.interp.html
        self.norms = np.interp(self.xmass_intp, self.xmass, self.yields.values())
        for p in pars:
            par_dict_intp[p] = np.interp(self.xmass_intp, self.xmass, par_dict[p])
            parErr_dict_intp[p] = np.interp(self.xmass_intp, self.xmass, parErr_dict[p])
        self.Pars = par_dict_intp
        self.ParsErr = parErr_dict_intp

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def buildFinalPdfs(self, outWS="", outWSDir="", save=False, doSystematics=False):
        # create the output dir
        if not os.path.exists(outWSDir):
            os.system("mkdir -p %s" %outWSDir)

        self.FinalPdfs = od()
        for imass, mass in enumerate(self.xmass_intp):
            Vars = od()
            for p in self.Pars.keys():
                Vars[p] = ROOT.RooRealVar(p, p, self.Pars[p][imass])
                Vars[p].setError(self.ParsErr[p][imass])

            dcbPdf = ROOT.RooDoubleCB("DCB", "DCB", self.xvar, Vars["mean_dcb"], Vars["sigma_dcb"], Vars["a1_dcb"], Vars["n1_dcb"], Vars["a2_dcb"], Vars["n2_dcb"])
            gauPdf = ROOT.RooGaussian("Gaus", "Gaus", self.xvar, Vars["mean_dcb"], Vars["sigma_gaus"])
            self.FinalPdfs[mass] = ROOT.RooAddPdf("SigPdf", "SigPdf", dcbPdf, gauPdf, Vars["frac_dcb"])

            if (mass != 120) and (mass != 125) and (mass != 130):
                self.FinalPdfs[mass].plotOn(
                    self.xframe, ROOT.RooFit.Range("NormRange"),
                    ROOT.RooFit.Normalization(self.norms[imass], ROOT.RooAbsReal.NumEvent),
                    ROOT.RooFit.LineColor(ROOT.TColor.GetColorPalette(imass * 20)),
                    ROOT.RooFit.LineStyle(7)
                )
            if mass == 120:
                self.FinalPdfs[mass].plotOn(
                    self.xframe, ROOT.RooFit.Range("NormRange"),
                    ROOT.RooFit.Normalization(self.norms[imass], ROOT.RooAbsReal.NumEvent),
                    ROOT.RooFit.LineColor(ROOT.TColor.GetColor("#0F52BA")),
                    ROOT.RooFit.LineWidth(4), ROOT.RooFit.Name("120")
                )
            if mass == 125:
                self.FinalPdfs[mass].plotOn(
                    self.xframe, ROOT.RooFit.Range("NormRange"),
                    ROOT.RooFit.Normalization(self.norms[imass], ROOT.RooAbsReal.NumEvent),
                    ROOT.RooFit.LineColor(ROOT.TColor.GetColor("#1C7747")),
                    ROOT.RooFit.LineWidth(4), ROOT.RooFit.Name("125")
                )
            if mass == 130:
                self.FinalPdfs[mass].plotOn(
                    self.xframe, ROOT.RooFit.Range("NormRange"),
                    ROOT.RooFit.Normalization(self.norms[imass], ROOT.RooAbsReal.NumEvent),
                    ROOT.RooFit.LineColor(ROOT.TColor.GetColor("#E23E57")),
                    ROOT.RooFit.LineWidth(4), ROOT.RooFit.Name("130")
                )

            if save == True:
                # create the output dir
                if not os.path.exists(outWSDir):
                    os.system("mkdir -p %s" %outWSDir)
                outWSName = "{}/CMS_HLLG_Interp_{}_{}_{}_{}.root".format(outWSDir, mass, self.proc, self.year, self.cat)
                print("INFO: Save the final signal model in {}".format(outWSName))
                fws = ROOT.TFile(outWSName, "RECREATE")
                fws.cd()

                # specify the norm var
                ExpYield = ROOT.RooRealVar("ExpYield", "ExpYield", self.norms[imass], "GeV")
                ExpYield.setConstant(True)

                # create the workspace to save
                ws = ROOT.RooWorkspace(outWS)
                ws.imp = getattr(ws, "import")
                ws.imp(self.FinalPdfs[mass])
                ws.imp(ExpYield)

                # define params set
                aset = ROOT.RooArgSet()
                for p in self.Pars.keys():
                    aset.add(ws.var(p))
                ws.defineSet("SigPdfParams", aset)
                for _var in rooiter(ws.set("SigPdfParams")):
                    _var.setConstant(True)

                # create the factory for the shape uncertainties
                if doSystematics:
                    # set the initial value to be 1 (inside the square brackets are the initial values)
                    scale_var = "CMS_{}_scale_{}_{}_{}[1]".format(decayMode, self.proc, mass, self.cat)
                    resol_var = "CMS_{}_resol_{}_{}_{}[1]".format(decayMode, self.proc, mass, self.cat)
                    ws.factory(scale_var)
                    ws.factory(resol_var)

                    # create RooFormulaVars
                    # * new_mean_dcb = mean_dcb * scale_var
                    # * new_sigma_dcb = sigma_dcb * resol_var
                    ws.factory("prod::new_mean_dcb(mean_dcb, {})".format(scale_var))
                    ws.factory("prod::new_sigma_dcb(sigma_dcb, {})".format(resol_var))

                    # modify the final models
                    ws.factory("EDIT:NewSigPdf(SigPdf, mean_dcb = new_mean_dcb, sigma_dcb = new_sigma_dcb)")

                ws.Write()
                fws.Close()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # xName: x-axis label
    # outName: path to save the plot
    def visualize(self, xName, outName):
        # set up the canvas to draw
        # self.xframe.SetAxisRange(xRange[0], xRange[1], "X")
        self.xframe.SetTitle("")

        self.xframe.GetXaxis().SetTickSize(0.03)
        self.xframe.GetXaxis().SetTitleSize(0.04)
        self.xframe.GetXaxis().SetLabelSize(0.04)
        self.xframe.GetXaxis().SetLabelOffset(0.02)
        self.xframe.GetXaxis().SetTitleOffset(1.4)
        self.xframe.GetXaxis().SetTitle(xName)

        self.xframe.GetYaxis().SetTitle("Signal shape")
        self.xframe.GetYaxis().SetNdivisions(510)
        self.xframe.GetYaxis().SetTickSize(0.03)
        self.xframe.GetYaxis().SetTitleSize(0.04)
        self.xframe.GetYaxis().SetLabelSize(0.04)
        self.xframe.GetYaxis().SetTitleOffset(1.8)

        self.xframe.SetMaximum(self.xframe.GetMaximum() * 500.)
        self.xframe.SetMinimum(self.xframe.GetMaximum() * 0.00000001)

        c = ROOT.TCanvas("c", "", 900, 900)
        c.cd()
        c.SetLogy()
        c.SetRightMargin(0.05)
        c.SetTopMargin(0.07)
        c.SetLeftMargin(0.14)
        c.SetBottomMargin(0.12)
        self.xframe.Draw()

        catProc = ROOT.TLatex()
        catProc.SetTextFont(42)
        catProc.SetNDC()
        catProc.SetTextSize(0.037)
        catProc.DrawLatex(0.53, 0.86, "%s, %s" %(self.proc, self.cat))

        leg1 = ROOT.TLegend(0.53, 0.7, 0.83, 0.84)
        leg1.SetTextFont(42)
        leg1.SetTextSize(0.035)
        leg1.SetFillColor(0)
        leg1.SetLineColor(0)
        leg1.AddEntry(self.xframe.findObject("120"), "PDF-120 GeV ", "l")
        leg1.AddEntry(self.xframe.findObject("125"), "PDF-125 GeV ", "l")
        leg1.AddEntry(self.xframe.findObject("130"), "PDF-130 GeV ", "l")
        leg1.Draw()

        CMS_lumi(c, 4, 11, "", self.year, True, "Simulation", "H #rightarrow #gamma*#gamma #rightarrow ee#gamma", "")

        # create the output dir
        outDir = os.path.dirname(outName)
        if not os.path.exists(outDir):
            os.system("mkdir -p %s" %outDir)

        c.Print(outName)
        c.Close()