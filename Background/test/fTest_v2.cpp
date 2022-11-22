#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <map>

#include "boost/program_options.hpp"
#include "boost/lexical_cast.hpp"

#include "TFile.h"
#include "TString.h"
#include "TSystem.h"
#include "TMath.h"
#include "TLegend.h"
#include "TCanvas.h"
#include "RooPlot.h"
#include "RooWorkspace.h"
#include "RooDataSet.h"
#include "RooHist.h"
#include "RooAbsData.h"
#include "RooAbsPdf.h"
#include "RooArgSet.h"
#include "RooFitResult.h"
#include "RooMinuit.h"
#include "RooMinimizer.h"
#include "RooMsgService.h"
#include "RooDataHist.h"
#include "RooExtendPdf.h"
#include "TRandom3.h"
#include "TLatex.h"
#include "TMacro.h"
#include "TH1F.h"
#include "TH1I.h"
#include "TArrow.h"
#include "TKey.h"

#include "RooCategory.h"
#include "HiggsAnalysis/CombinedLimit/interface/RooMultiPdf.h"

#include "../interface/PdfModelBuilder.h"
#include <Math/PdfFuncMathCore.h>
#include <Math/ProbFunc.h>
#include <iomanip>
#include "boost/program_options.hpp"
#include "boost/algorithm/string/split.hpp"
#include "boost/algorithm/string/classification.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "../../tdrStyle/tdrstyle.C"
#include "../../tdrStyle/CMS_lumi_mod.C"

#define RESET   "\033[0m"
#define GREEN   "\033[32m"
#define YELLOW  "\033[93m"

using namespace std;
using namespace RooFit;
using namespace boost;

namespace po = program_options;

bool BLIND = true;
bool runFtestCheckWithToys = false;
int mllg_low = 110;
int mllg_high = 170;
int blind_low = 120;
int blind_high = 130;
int nBinsForMass = 60;

// plot setting
string massName = "M_{ee#gamma} [GeV]"; // use to plot the x title
TString extraText_ = "Preliminary";
TString lumitext_ = "138 fb^{-1}";
TString procText_ = "H #rightarrow #gamma*#gamma #rightarrow ee#gamma";


void transferMacros(TFile *inFile, TFile *outFile){
    TIter next(inFile->GetListOfKeys());
    TKey *key;
    while ((key = (TKey*)next())){
        if (string(key->ReadObj()->ClassName()) == "TMacro") {
            //cout << key->ReadObj()->ClassName() << " : " << key->GetName() << endl;
            TMacro *macro = (TMacro*)inFile->Get(key->GetName());
            outFile->cd();
            macro->Write();
        }
    }
}


RooAbsPdf* getPdf(PdfModelBuilder& pdfsModel, string type, int order, const char* ext){
    if (type == "Bernstein")
        return pdfsModel.getBernstein(Form("%s_bern%d", ext, order), order);
    else if (type == "Chebychev")
        return pdfsModel.getChebychev(Form("%s_cheb%d", ext, order), order);
    else if (type == "Exponential")
        return pdfsModel.getExponentialSingle(Form("%s_exp%d", ext, order), order);
    else if (type == "PowerLaw")
        return pdfsModel.getPowerLawSingle(Form("%s_pow%d", ext, order), order);
    else if (type == "Laurent")
        return pdfsModel.getLaurentSeries(Form("%s_lau%d", ext, order), order);
    else {
        cerr << "[ERROR] -- getPdf() -- type " << type << " not recognised." << endl;
        return NULL;
    }
}


void runFit(RooAbsPdf* pdf, RooDataSet* data, double* NLL, int* stat_t, int MaxTries){
    int ntries = 0;
    RooArgSet* params_test = pdf->getParameters((const RooArgSet*)(0));
    int stat = 1;
    double minnll = 10e8;
    while ((stat != 0) && (ntries <= MaxTries)){
        RooFitResult *fitTest = pdf->fitTo(
            *data,
            RooFit::Save(1), RooFit::Minimizer("Minuit2", "minimize"),
            RooFit::SumW2Error(true)
        );
        stat = fitTest->status();
        minnll = fitTest->minNll();
        if (stat != 0)
            params_test->assignValueOnly(fitTest->randomizePars());
        ntries++;
    }
    *stat_t = stat;
	*NLL = minnll;
}


double getProbabilityFtest(double chi2, int ndof, RooAbsPdf* pdfNull, RooAbsPdf* pdfTest, RooRealVar* mass, RooDataSet* data, string name){
    double prob_asym = TMath::Prob(chi2, ndof);
    if (!runFtestCheckWithToys)
        return prob_asym;

    int ndata = data->sumEntries();

    // fit the pdfs to the data and keep this fit Result (for randomizing)
    RooFitResult* fitNullData = pdfNull->fitTo(
        *data,
        RooFit::Save(1), RooFit::Strategy(1),
        RooFit::Minimizer("Minuit2","minimize"), RooFit::SumW2Error(true), RooFit::PrintLevel(-1)
    );
    RooFitResult* fitTestData = pdfTest->fitTo(
        *data,
        RooFit::Save(1), RooFit::Strategy(1),
        RooFit::Minimizer("Minuit2", "minimize"), RooFit::SumW2Error(true), RooFit::PrintLevel(-1)
    );

    // Ok we want to check the distribution in toys then
    // Step 1, cache the parameters of each pdf so as not to upset anything
    RooArgSet* params_null = pdfNull->getParameters((const RooArgSet*)(0));
    RooArgSet preParams_null;
    params_null->snapshot(preParams_null);
    RooArgSet* params_test = pdfTest->getParameters((const RooArgSet*)(0));
    RooArgSet preParams_test;
    params_test->snapshot(preParams_test);

    int ntoys = 1000;
    TCanvas* canv = new TCanvas();
    canv->SetLogy();
    TH1F toyhist(Form("toys_fTest_%s.pdf", pdfNull->GetName()), ";Chi2;", 60, -2, 10);
    TH1I toyhistStatN(Form("Status_%s.pdf", pdfNull->GetName()), ";FitStatus;", 8, -4, 4);
    TH1I toyhistStatT(Form("Status_%s.pdf", pdfTest->GetName()), ";FitStatus;", 8, -4, 4);

    TGraph* gChi2 = new TGraph();
    gChi2->SetLineColor(kGreen + 2);
    double w = toyhist.GetBinWidth(1);

    int ipoint = 0;
    for (int b = 0; b < toyhist.GetNbinsX(); b++){
        double x = toyhist.GetBinCenter(b + 1);
        if (x > 0){
            gChi2->SetPoint(ipoint, x, (ROOT::Math::chisquared_pdf(x, ndof)));
            ipoint++;
        }
    }

    int npass = 0;
    int nsuccesst = 0;
    mass->setBins(nBinsForMass);
    for (int itoy = 0; itoy < ntoys; itoy++){
        params_null->assignValueOnly(preParams_null);
        params_test->assignValueOnly(preParams_test);
        RooDataHist *binnedtoy = pdfNull->generateBinned(RooArgSet(*mass), ndata, 0, 1);

        int stat_n = 1;
        int stat_t = 1;
        int ntries = 0;
        double nllNull, nllTest;
        // Iterate on the fit
        int MaxTries = 2;
        while (stat_n != 0){
            if (ntries >= MaxTries)
                break;
            RooFitResult *fitNull = pdfNull->fitTo(
                *binnedtoy,
                RooFit::Save(1), RooFit::Strategy(1),
                RooFit::Minimizer("Minuit2", "minimize"), RooFit::PrintLevel(-1)
            );
            //,RooFit::Optimize(0));

            nllNull = fitNull->minNll();
            stat_n = fitNull->status();
            if (stat_n != 0)
                params_null->assignValueOnly(fitNullData->randomizePars());
            ntries++;
        }

        ntries = 0;
        while (stat_t != 0){
            if (ntries >= MaxTries)
                break;
            RooFitResult *fitTest = pdfTest->fitTo(
                *binnedtoy,
                RooFit::Save(1), RooFit::Strategy(1), RooFit::SumW2Error(true), //FIXME
                RooFit::Minimizer("Minuit2", "minimize"), RooFit::PrintLevel(-1)
            );
            nllTest = fitTest->minNll();
            stat_t = fitTest->status();
            if (stat_t != 0)
                params_test->assignValueOnly(fitTestData->randomizePars());
            ntries++;
        }

        toyhistStatN.Fill(stat_n);
        toyhistStatT.Fill(stat_t);

        if (stat_t != 0 || stat_n != 0)
            continue;
        nsuccesst++;

        double chi2_t = 2 * (nllNull - nllTest);
        if (chi2_t >= chi2)
            npass++;
        toyhist.Fill(chi2_t);
    }

    double prob = 0;
    if (nsuccesst != 0)
        prob = (double)npass / nsuccesst;

    toyhist.Scale(1. / (w * toyhist.Integral()));
    toyhist.Draw();
    TArrow lData(chi2, toyhist.GetMaximum(), chi2, 0);
    lData.SetLineWidth(2);
    lData.Draw();
    gChi2->Draw("L");
    TLatex* lat = new TLatex();
    lat->SetNDC();
    lat->SetTextFont(42);
    lat->DrawLatex(0.1, 0.91, Form("Prob (asymptotic) = %.4f (%.4f)", prob, prob_asym));
    canv->Print(name.c_str());
    canv->Close();

    TCanvas* stas = new TCanvas();
    toyhistStatN.SetLineColor(2);
    toyhistStatT.SetLineColor(1);
    TLegend* leg = new TLegend(0.2, 0.6, 0.4, 0.87);
    leg->SetFillColor(0);
    leg->SetTextFont(42);
    leg->AddEntry(&toyhistStatN, "Null Hyp", "L");
    leg->AddEntry(&toyhistStatT, "Test Hyp", "L");
    toyhistStatN.Draw();
    toyhistStatT.Draw("same");
    leg->Draw();
    stas->Print(Form("%s_fitstatus.pdf", name.c_str()));
    //reassign params
    params_null->assignValueOnly(preParams_null);
    params_test->assignValueOnly(preParams_test);
    stas->Close();

    delete gChi2;
    delete leg;
    delete lat;

    // flashggFinalFit approach -> I don't know why flashgg choose to return the asymptotic prob
    // I modify this a bit
    //* Still return the asymptotic prob (usually its close to the toys one)
    //* return prob_asym;

    if (!runFtestCheckWithToys)
        return prob_asym;
    else
        return prob;

}


double getGoodnessOfFit(RooRealVar* mass, RooAbsPdf* mpdf, RooDataSet* data, string name){
    double prob;
    int ntoys = 1000;

    // Routine to calculate the goodness of fit.
    name += "_gofTest.pdf";
    RooRealVar norm("norm", "norm", data->sumEntries(), 0, 10e6);
    //norm.removeRange();

    RooExtendPdf* pdf = new RooExtendPdf("ext", "ext", *mpdf, norm);

    // get The Chi2 value from the data
    RooPlot* plot_chi2 = mass->frame();
    data->plotOn(plot_chi2, Binning(nBinsForMass), Name("data"));

    pdf->plotOn(plot_chi2, Name("pdf"));
    int np = pdf->getParameters(*data)->getSize();

    double chi2 = plot_chi2->chiSquare("pdf", "data", np);
    cout << "[INFO] Calculating GOF for pdf " << pdf->GetName() << ", using " << np << " fitted parameters" << endl;

    // The first thing is to check if the number of entries in any bin is < 5
    // if so, we don't rely on asymptotic approximations
    if ((double)data->sumEntries() / nBinsForMass < 5){
        cout << "[INFO] Few entries, running toys for GOF test " << endl;

        // store pre-fit params
        RooArgSet* params = pdf->getParameters(*data);
        RooArgSet preParams;
        params->snapshot(preParams);
        int ndata = data->sumEntries();

        int npass =0;
        vector<double> toy_chi2;
        gRandom->SetSeed(1234);
        for (int itoy = 0; itoy < ntoys ; itoy++){
            params->assignValueOnly(preParams);
            int nToyEvents = gRandom->Poisson(ndata);
            RooDataHist* binnedtoy = pdf->generateBinned(RooArgSet(*mass), nToyEvents, 0, 1);
            pdf->fitTo(
                *binnedtoy,
                RooFit::Minimizer("Minuit2", "minimize"),
                RooFit::PrintLevel(-1)
            );

            RooPlot* plot_t = mass->frame();
            binnedtoy->plotOn(plot_t);
            pdf->plotOn(plot_t); //,RooFit::NormRange("fitdata_1,fitdata_2"));

            double chi2_t = plot_t->chiSquare(np);
            if(chi2_t >= chi2)
                npass++;
            toy_chi2.push_back(chi2_t*(nBinsForMass-np));
            delete plot_t;
        }
        cout << "[INFO] complete" << endl;
        prob = (double)npass / ntoys;

        TCanvas* canv = new TCanvas();
        double medianChi2 = toy_chi2[(int)(((float)ntoys)/2)];
        double rms = TMath::Sqrt(medianChi2);

        TH1F toyhist(Form("gofTest_%s.pdf", pdf->GetName()), ";Chi2;", 50, medianChi2 - 5*rms, medianChi2 + 5*rms);
        for (auto itx = toy_chi2.begin(); itx != toy_chi2.end(); itx++){
            toyhist.Fill((*itx));
        }
        toyhist.Draw();

        TArrow lData(chi2*(nBinsForMass-np), toyhist.GetMaximum(), chi2*(nBinsForMass - np), 0);
        lData.SetLineWidth(2);
        lData.Draw();
        canv->Print(name.c_str());

        // back to best fit
        params->assignValueOnly(preParams);
        canv->Close();
    }
    else{
        prob = TMath::Prob(chi2*(nBinsForMass - np), nBinsForMass - np);
    }

    cout << "[INFO] Chi2 in Observed = " << chi2*(nBinsForMass-np) << endl;
    cout << "[INFO] p-value = " << prob << endl;
    delete pdf;

    return prob;
}

// Plot single fit
void plot_single_fit(RooRealVar* mass, RooAbsPdf* pdf, RooDataSet* data, string name, int status, double* prob){
    // (Originally the Chi2 is taken from full range fit)
    RooPlot* plot_chi2 = mass->frame();
    data->plotOn(plot_chi2, Binning(nBinsForMass));
    pdf->plotOn(plot_chi2);

    int np = pdf->getParameters(*data)->getSize() + 1; //Because this pdf has no extend
    double chi2 = plot_chi2->chiSquare(np);

    *prob = getGoodnessOfFit(mass, pdf, data, name);
    RooPlot* plot = mass->frame();
    plot->GetXaxis()->SetTitle(massName.c_str());

    mass->setRange("unblindReg_1", mllg_low, blind_low);
    mass->setRange("unblindReg_2", blind_high, mllg_high);
    if (BLIND) {
        data->plotOn(plot, Binning(mllg_high - mllg_low), CutRange("unblindReg_1"));
        data->plotOn(plot, Binning(mllg_high - mllg_low), CutRange("unblindReg_2"));
        data->plotOn(plot, Binning(mllg_high - mllg_low), Invisible());
    }
    else data->plotOn(plot, Binning(mllg_high - mllg_low));

    TCanvas* canv = new TCanvas("canv", "", 700, 600);
    pdf->plotOn(plot); //,RooFit::NormRange("fitdata_1,fitdata_2"));
    bool paramoncanv = false;
    if (paramoncanv)
        pdf->paramOn(plot, RooFit::Layout(0.17, 0.93, 0.89), RooFit::Format("NEA", AutoPrecision(1)));
    if (BLIND)
        plot->SetMinimum(0.0001);
    plot->SetTitle("");
    canv->SetLeftMargin(0.15);
    canv->SetRightMargin(0.05);
    canv->SetTopMargin(0.08);
    canv->SetBottomMargin(0.15);
    canv->cd();
    plot->Draw();

    TLatex* lat = new TLatex();
    lat->SetNDC();
    lat->SetTextFont(36);
    lat->DrawLatex(0.60, 0.83, Form("#chi^{2} = %g", chi2 * (nBinsForMass - np)));
    lat->DrawLatex(0.60, 0.76, Form("Prob. = %g", *prob));
    lat->DrawLatex(0.60, 0.70, Form("Fit Status = %d", status));

    canv->Print(Form("%s.pdf", name.c_str()));
    canv->Close();
}


int getBestFitFunction(RooMultiPdf* bkg, RooDataSet* data, RooCategory* cat, bool silent = false){
    double global_minNll = 1e10;
	int best_index = 0;
	int number_of_indeces = cat->numTypes();

	RooArgSet snap,clean;
	RooArgSet* params = bkg->getParameters((const RooArgSet*)0);
	params->remove(*cat);
	params->snapshot(snap);
	params->snapshot(clean);

	for (int id = 0; id < number_of_indeces; id++){
		params->assignValueOnly(clean);
		cat->setIndex(id);

		double minNll = 0; //(nllm->getVal())+bkg->getCorrection();
		int fitStatus = 1;
		runFit(bkg->getCurrentPdf(), data, &minNll, &fitStatus, /*max iterations*/3);

        // Add the penalty
		minNll = minNll + bkg->getCorrection();

		if (!silent) {
			cout << "[INFO] AFTER FITTING" << endl;
			cout << "[INFO] Function was " << bkg->getCurrentPdf()->GetName() <<endl;
			cout << "[INFO] Correction Applied is " << bkg->getCorrection() <<endl;
			cout << "[INFO] NLL + c = " <<  minNll << endl;
			cout << "-----------------------" << endl;
		}
		if (minNll < global_minNll){
        	global_minNll = minNll;
			snap.assignValueOnly(*params);
        	best_index = id;
		}
	}
    cat->setIndex(best_index);
	params->assignValueOnly(snap);

	if (!silent)
		cout << "[INFO] Best fit Function -- " << bkg->getCurrentPdf()->GetName() << " " << cat->getIndex() <<endl;

	return best_index;
}


vector<string> split_string(string instr, string delimiter = "_"){
    // Ref: https://stackoverflow.com/questions/14265581/parse-split-a-string-in-c-using-string-delimiter-standard-c
    vector<string> tokens;
    size_t prev = 0, pos = 0;
    do{
        pos = instr.find(delimiter, prev);
        if (pos == string::npos) pos = instr.length();
        string token = instr.substr(prev, pos-prev);
        if (!token.empty()) tokens.push_back(token);
        prev = pos + delimiter.length();
    }
    while (pos < instr.length() && prev < instr.length());
    return tokens;
}


string ReplaceAll(string str, const string& from, const string& to){
    size_t start_pos = 0;
    while((start_pos = str.find(from, start_pos)) != string::npos){
        str.replace(start_pos, from.length(), to);
        start_pos += to.length(); // Handles case where 'to' is a substring of 'from'
    }
    return str;
}



void plot_best(RooRealVar* mass, RooMultiPdf* pdfs, RooCategory* catIndex, RooDataSet* data, string name, vector<string> HLLGCats, int cat, int bestFitPdf = -1){
    gStyle->SetOptFit(0);

    TLegend* leg = new TLegend(0.42, 0.57, 0.92, 0.86);
    leg->SetFillColor(0);
    leg->SetLineColor(0);
    leg->SetTextSize(0.047);
    leg->SetTextFont(42);

    RooPlot* plot = mass->frame();
    mass->setRange("unblindReg_1", mllg_low, blind_low);
    mass->setRange("unblindReg_2", blind_high, mllg_high);
    if (BLIND){
        data->plotOn(plot, Binning(mllg_high - mllg_low), CutRange("unblindReg_1"), XErrorSize(0.0001));
        data->plotOn(plot, Binning(mllg_high - mllg_low), CutRange("unblindReg_2"), XErrorSize(0.0001));
        data->plotOn(plot, Binning(mllg_high - mllg_low), Invisible());
    }
    else
        data->plotOn(plot, Binning(mllg_high - mllg_low), XErrorSize(0.0001));

    TCanvas* canv = new TCanvas("canv", "", 800, 800);
    canv->SetLeftMargin(0.15);
    canv->SetRightMargin(0.05);
    canv->SetTopMargin(0.1);
    canv->cd();

    ///start extra bit for ratio plot///
    RooHist* plotdata = (RooHist*) plot->getObject(plot->numItems() - 1);
    TPad* pad1 = new TPad("pad1", "pad1", 0, 0.3, 1, 1);
    TPad* pad2 = new TPad("pad2", "pad2", 0, 0, 1, 0.3);
    pad1->SetLeftMargin(0.15);
    pad1->SetRightMargin(0.05);
    pad1->SetBottomMargin(0.02);
    pad1->SetTopMargin(0.11);
    pad2->SetLeftMargin(0.15);
    pad2->SetRightMargin(0.05);
    pad2->SetTopMargin(0.0);
    pad2->SetBottomMargin(0.38);
    pad1->Draw();
    pad2->Draw();
    pad1->cd();
    /// enf extra bit for ratio plot///

    int currentIndex = catIndex->getIndex();
    TObject* datLeg = plot->getObject(int(plot->numItems() - 1));
    leg->AddEntry(datLeg, Form("Data - %s", HLLGCats[cat].c_str()), "EP");
    int style = 1;
    RooAbsPdf* pdf;
    RooCurve* nomBkgCurve;
    int bestcol = -1;
    for (int icat = 0; icat < catIndex->numTypes(); icat++){
        catIndex->setIndex(icat);
        pdfs->getCurrentPdf()->fitTo(*data, RooFit::Minimizer("Minuit2", "minimize"));
        pdfs->getCurrentPdf()->plotOn(plot, LineColor(TColor::GetColorPalette((icat) * (int)(280/catIndex->numTypes() - 1))), LineStyle(style));
        TObject* pdfLeg = plot->getObject(int(plot->numItems() - 1));
        string ext = "";

        if (bestFitPdf == icat){
            ext = " (Best Fit Pdf) ";
            pdf = pdfs->getCurrentPdf();
            nomBkgCurve = (RooCurve*) plot->getObject(plot->numItems() - 1);
            bestcol = icat;
        }
        cout << pdfs->getCurrentPdf()->GetName() << endl;
        vector<string> Pdfname = split_string(pdfs->getCurrentPdf()->GetName());
        leg->AddEntry(pdfLeg, Form("%s%s", Pdfname[Pdfname.size()-1].c_str(), ext.c_str()), "L");
    }
    // make the best pdf be drawn on the top of all pdfs
    pdf->plotOn(plot, LineColor(TColor::GetColorPalette((bestcol) * (int)(280/catIndex->numTypes() - 1))), LineStyle(style));

    if (BLIND){
        data->plotOn(plot, Binning(mllg_high - mllg_low), CutRange("unblindReg_1"), XErrorSize(0.0001));
        data->plotOn(plot, Binning(mllg_high - mllg_low), CutRange("unblindReg_2"), XErrorSize(0.0001));
        data->plotOn(plot, Binning(mllg_high - mllg_low), Invisible());
    }
    else
        data->plotOn(plot, Binning(mllg_high - mllg_low), XErrorSize(0.0001));

    plot->SetTitle(Form("Category %s", HLLGCats[cat].c_str()));

    plot->GetXaxis()->SetLabelOffset(0.05);
    plot->GetXaxis()->SetTickSize(0.03);
    plot->GetYaxis()->SetTitleSize(0.055);
    plot->GetYaxis()->SetTickSize(0.03);
    plot->GetYaxis()->SetLabelSize(0.05);
    plot->GetYaxis()->SetTitleOffset(1.2);

    // plot->GetYaxis()->SetTitleOffset(1.3);
    // plot->GetYaxis()->SetTitleSize(0.05);
    // plot->GetYaxis()->SetLabelSize(0.05);
    if (BLIND)
        plot->SetMinimum(0.0001);
    plot->SetMaximum(plot->GetMaximum() * 1.7);
    plot->Draw();
    leg->Draw("same");

    CMS_lumi(pad1, 5, 11, lumitext_, 2017, true, extraText_, procText_, "");
    pad1->Update();
    canv->cd();

    ///start extra bit for ratio plot///
    TH1D* hbplottmp = (TH1D*) pdf->createHistogram("hbplottmp", *mass, Binning(mllg_high - mllg_low, mllg_low, mllg_high));
    hbplottmp->Scale(plotdata->Integral());
    hbplottmp->Draw("same");
    int npoints = plotdata->GetN();
    double xtmp, ytmp; //
    int point = 0;
    TGraphAsymmErrors* hdatasub = new TGraphAsymmErrors(npoints);
    //hdatasub->SetMarkerSize(defmarkersize);
    for (int ipoint = 0; ipoint < npoints; ipoint++){
        //double bkgval = hbplottmp->GetBinContent(ipoint+1);
        plotdata->GetPoint(ipoint, xtmp, ytmp);
        double bkgval = nomBkgCurve->interpolate(xtmp);
        if (BLIND){
            if ((xtmp > blind_low) && (xtmp < blind_high))
                continue;
        }
        cout << "[INFO] plotdata->Integral() " << plotdata->Integral() << " ( bins " << npoints << ") hbkgplots[i]->Integral() " << hbplottmp->Integral() << " (bins " << hbplottmp->GetNbinsX() << endl;
        double errhi = plotdata->GetErrorYhigh(ipoint);
        double errlow = plotdata->GetErrorYlow(ipoint);

        //cout << "[INFO]  Channel " << name  << " errhi " << errhi << " errlow " << errlow  << endl;
        cout << "[INFO] Channel  " << name << " setting point " << point << " : xtmp " << xtmp << "  ytmp " << ytmp << " bkgval  " << bkgval << " ytmp-bkgval " << ytmp - bkgval << endl;
        bool drawZeroBins_ = 1;
        if (!drawZeroBins_)
            if (fabs(ytmp) < 1e-5)
                continue;
        hdatasub->SetPoint(point, xtmp, ytmp - bkgval);
        hdatasub->SetPointError(point, 0., 0., errlow, errhi);
        point++;
    }

    pad2->cd();
    TH1* hdummy = new TH1D("hdummyweight", "", mllg_high - mllg_low, mllg_low, mllg_high);
    hdummy->SetMaximum(hdatasub->GetHistogram()->GetMaximum() + 1);
    hdummy->SetMinimum(hdatasub->GetHistogram()->GetMinimum() - 1);

    hdummy->GetYaxis()->SetTitle("Data - best fit");
    hdummy->GetYaxis()->SetTitleOffset(0.5);
    hdummy->GetYaxis()->SetTitleSize(0.12);
    hdummy->GetYaxis()->SetLabelSize(0.115);
    hdummy->GetYaxis()->SetNdivisions(505);

    hdummy->GetXaxis()->SetTitle(massName.c_str());
    hdummy->GetXaxis()->SetTitleSize(0.15);
    hdummy->GetXaxis()->SetLabelSize(0.115);
    hdummy->GetXaxis()->SetTitleOffset(1.2);
    hdummy->GetXaxis()->SetTickSize(0.07);
    hdummy->GetXaxis()->SetLabelOffset(0.045);

    hdummy->Draw("HIST");

    TLine* line3 = new TLine(mllg_low, 0., mllg_high, 0.);
    line3->SetLineColor(TColor::GetColorPalette((bestcol) * (int)(256/catIndex->numTypes() - 1)));
    //line3->SetLineStyle(kDashed);
    line3->SetLineWidth(5.0);
    line3->Draw();
    hdatasub->Draw("PESAME");
    // enf extra bit for ratio plot///
    canv->Print(Form("%s.pdf", name.c_str()));
    catIndex->setIndex(currentIndex);
    canv->Close();
}


int main(int argc, char** argv){
    setTDRStyle();

    string fileName; // input file contains workspace
    string WSname = "tagsDumper/cms_heeg_13TeV"; // input workspace name
    string outDir = "plots/fTest"; // out directory for plots
    bool verbose = false;
    string ext = "13TeV";
    string HLLGCatsStr;
    vector<string> HLLGCats;
    int singleCategory; // defalut = -1, if category number is set then run the single category only (i.e. singleCategory = 2, run Merged2Gsf_BST)

    // get the options
    po::options_description desc("Allowed options");
    desc.add_options()
    ("help,h",                                                                              "Show help")
    ("infile",                  po::value<string>(&fileName),                               "In file name")
    ("inWSname",                po::value<string>(&WSname)->default_value(WSname),          "Name of the input WS")
    ("outDir",                  po::value<string>(&outDir)->default_value(outDir),          "Out directory for plots")
    ("singleCat",               po::value<int>(&singleCategory)->default_value(-1),         "Run a single Category only")
    ("HLLGCats",                po::value<string>(&HLLGCatsStr),                            "Higgs Dalitz RECO category")
    ("runFtestCheckWithToys",                                                               "When running the F-test, use toys to calculate p-value (and make plots)")
    ("unblind",  									                                        "Don't blind plots")
    ("verbose,v",                                                                           "Run with more output");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);
    if (vm.count("help")){
        cout << desc << endl;
        exit(1);
    }
    if (vm.count("runFtestCheckWithToys"))
        runFtestCheckWithToys = true;
    if (vm.count("unblind"))
        BLIND = false;
    if (vm.count("verbose"))
        verbose = true;

    if (!verbose) {
        RooMsgService::instance().setGlobalKillBelow(RooFit::ERROR);
        RooMsgService::instance().setSilentMode(true);
        // gErrorIgnoreLevel =kWarning;
    }
    split(HLLGCats, HLLGCatsStr, boost::is_any_of(","));
    int startingCategory = 0;
    int ncats = HLLGCats.size();
    if (singleCategory > -1){
        ncats = singleCategory + 1;
        startingCategory = singleCategory;
    }

    // Setup the output file and ws
    string fmultipdf;
    if (singleCategory > -1){
        fmultipdf = Form("./multipdf/CMS_HLLG_multipdf_%s_%s.root", ext.c_str(), HLLGCats[startingCategory].c_str());
        cout << Form("[INFO] Save multiPdf model: %s", fmultipdf.c_str()) << endl;
    }
    else{
        fmultipdf = Form("./multipdf/CMS_HLLG_multipdf_%s.root", ext.c_str());
        cout << Form("[INFO] Save multiPdf model: %s", fmultipdf.c_str()) << endl;
    }
    const char* multipdfDir = gSystem->DirName(fmultipdf.c_str());
    system(Form("mkdir -p %s", multipdfDir));
    TFile* outputfile = new TFile(fmultipdf.c_str(), "RECREATE");
    RooWorkspace* outputws = new RooWorkspace();
    outputws->SetName("multipdf");

    // Open the infile
    TFile* inFile = TFile::Open(fileName.c_str());
    if (inFile->IsZombie())
        throw runtime_error("TFile::Open() failed");
    RooWorkspace* inWS = (RooWorkspace*) inFile->Get(WSname.c_str());
    transferMacros(inFile, outputfile);
    RooRealVar* intLumi_ = new RooRealVar("IntLumi", "hacked int lumi", 1000);
    RooRealVar* sqrts = new RooRealVar("SqrtS", "SqrtS", 13);
    outputws->import(*intLumi_);
    outputws->import(*sqrts);

    // define the functions used to perform the fTest
    vector<string> functionClasses = {
        "Bernstein",
        "Exponential",
        "PowerLaw",
        "Laurent"
    };
	map<string, string> namingMap;
    namingMap["Bernstein"] = "pol";
    namingMap["Exponential"] = "exp";
    namingMap["PowerLaw"] = "pow";
    namingMap["Laurent"] = "lau";

    // store results here
    system(Form("mkdir -p %s/single_fit", outDir.c_str()));
    FILE* resFile;
    if (singleCategory > -1){
        resFile = fopen(Form("%s/fTestResults_%s.txt", outDir.c_str(), HLLGCats[singleCategory].c_str()), "w");
        cout << Form("[INFO] FitResults file: %s/fTestResults_%s.txt", outDir.c_str(), HLLGCats[singleCategory].c_str()) << endl;
    }
    else{
        resFile = fopen(Form("%s/fTestResults.txt", outDir.c_str()), "w");
        cout << Form("[INFO] FitResults file: %s/fTestResults.txt", outDir.c_str()) << endl;
    }

    vector<map<string, int>> choices_vec;
    vector<map<string, vector<int>>> choices_envelope_vec;
    vector<map<string, RooAbsPdf *>> pdfs_vec;

    PdfModelBuilder pdfsModel;
    RooRealVar* mass = (RooRealVar*) inWS->var("CMS_higgs_mass");
    cout << "[INFO] Got mass from ws: " << mass->GetName() << endl;
    pdfsModel.setObsVar(mass);
    double upperEnvThreshold = 0.1; // upper threshold on delta(chi2) to include function in envelope (looser than truth function)

    fprintf(resFile, "Truth Model & d.o.f & $\\Delta NLL_{N+1}$ & $p(\\chi^{2}>\\chi^{2}_{(N\\rightarrow N+1)})$ \\\\\n");
    fprintf(resFile, "\\hline\n");

    for (int cat = startingCategory; cat < ncats; cat++){
        map<string, int> choices;
        map<string, vector<int>> choices_envelope;
        map<string, RooAbsPdf*> pdfs;
        map<string, RooAbsPdf*> allPdfs;
        string catname = HLLGCats[cat];

        // extract the dataset to perferm fTest
        RooDataSet* dataFull = (RooDataSet*) inWS->data(Form("data_obs_%s", catname.c_str()));
        cout << "[INFO] Open data for " << dataFull->GetName() << ". Sum of entries: " << dataFull->sumEntries() << endl;
        mass->setBins(nBinsForMass);

        // binned dataset
        RooDataSet* data;
        string thisdataBinned_name = Form("roohist_data_mass_%s", catname.c_str());
        RooDataHist thisdataBinned(thisdataBinned_name.c_str(), "data", *mass, *dataFull);
        data = (RooDataSet*) &thisdataBinned;
        RooArgList storedPdfs("store");

        double MinimimNLLSoFar = 1e10;
		int simplebestFitPdfIndex = 0;
        // Standard F-Test to find the truth functions
        for (auto funcType = functionClasses.begin(); funcType != functionClasses.end(); funcType++){
            double thisNll = 0., prevNll = 0., chi2 = 0., prob = 0.;
            int order = 1, prev_order = 0, cache_order = 0;

            RooAbsPdf* prev_pdf = NULL;
            RooAbsPdf* cache_pdf = NULL;
            vector<int> pdforders;

            int counter = 0;
            while (prob < 0.05 && order < 7){
                RooAbsPdf* bkgPdf = getPdf(pdfsModel, *funcType, order, Form("ftest_pdf_%s_%s", catname.c_str(), ext.c_str()));
                if (!bkgPdf)
                    order += 1;
                else{
                    int fitStatus = 0;
                    cout << "[INFO] Perform the F-test on: " << " category " << HLLGCats[cat] << ", " << bkgPdf->GetName() << endl;
                    // bkgPdf->Print();

                    runFit(bkgPdf, data, &thisNll, &fitStatus, /*max iterations*/3);
                    if (fitStatus != 0)
                        cout << "[WARNING] Warning -- Fit status for " << bkgPdf->GetName() << " at " << fitStatus <<endl;

                    chi2 = 2. * (prevNll - thisNll);
					if (chi2 < 0. && order > 1)
                        chi2 = 0.;

                    if (prev_pdf != NULL){
                        prob = getProbabilityFtest(
                            chi2, order - prev_order, prev_pdf, bkgPdf, mass, data,
                            Form("%s/Ftest_from_%s%d_%s_%s.pdf", outDir.c_str(), funcType->c_str(), order, catname.c_str(), ext.c_str())
                        );
                        cout << "[INFO] F-test Prob(chi2>chi2(data)) == " << prob << endl;
                    }
                    else
                        prob = 0;

                    cout << "[INFO] Function: " << *funcType << ", order: " << order << ", prevNll: " << prevNll << ", thisNll: " << thisNll << ", chi2: " << chi2 << ", prob: " << prob << endl;

                    prevNll = thisNll;
                    cache_order = prev_order;
                    cache_pdf = prev_pdf;
                    prev_order = order;
                    prev_pdf = bkgPdf;
                    order++;
                }
                counter += 1;
            }

            fprintf(resFile, "%15s & %d & %5.2f & %5.2f \\\\\n", funcType->c_str(), cache_order + 1, chi2, prob);
            choices.insert(pair<string, int>(*funcType, cache_order));
            pdfs.insert(pair<string, RooAbsPdf*>(Form("%s%d", funcType->c_str(), cache_order), cache_pdf));
            int truthOrder = cache_order;

            // Now run loop to determine functions inside envelope
            chi2 = 0.;
            thisNll = 0.;
            prevNll = 0.;
            prob = 0.;
            order = 1;
            prev_order = 0;
            cache_order = 0;

            cout << "[INFO] Determining Envelope Functions for Family: " << *funcType << ", cat: " << catname << endl;
            cout << "[INFO] Upper end Threshold for highest order function " << upperEnvThreshold <<endl;
            while (prob < upperEnvThreshold){
                RooAbsPdf *bkgPdf = getPdf(pdfsModel, *funcType, order, Form("env_pdf_%s_%s", catname.c_str(), ext.c_str()));
                if (!bkgPdf){
                    // assume this order is not allowed
                    if (order > 6){
                        cout << "[WARNING] could not add ] " << endl;
                        break ;
                    }
                    order++;
                }
                else{
                    //RooFitResult *fitRes;
                    int fitStatus = 0;
                    runFit(bkgPdf, data, &thisNll, &fitStatus, /*max iterations*/3);//bkgPdf->fitTo(*data,Save(true),RooFit::Minimizer("Minuit2","minimize"));
                    //thisNll = fitRes->minNll();
                    if (fitStatus != 0)
                    cout << "[WARNING] Warning -- Fit status for " << bkgPdf->GetName() << " at " << fitStatus <<endl;

                    double myNll = 2.*thisNll;
                    chi2 = 2. * (prevNll - thisNll);

                    if (chi2 < 0. && order > 1)
                        chi2 = 0.;
                    prob = TMath::Prob(chi2, order - prev_order);

                    cout << "[INFO] Function: " << *funcType << ", order: " << order << ", prevNll: " << prevNll << ", thisNll: " << thisNll << ", chi2: " << chi2 << ", prob: " << prob << endl;

                    prevNll = thisNll;
                    cache_order = prev_order;
                    cache_pdf = prev_pdf;

                    // Calculate goodness of fit for the thing to be included (will use toys for lowstats)!
                    double gofProb = 0;
                    plot_single_fit(
                        mass, bkgPdf, data,
                        Form("%s/single_fit/%s%d_%s_%s", outDir.c_str(), funcType->c_str(), order, catname.c_str(), ext.c_str()),
                        fitStatus, &gofProb
                    );

                    // Looser requirements for the envelope
                    if (prob < upperEnvThreshold){
                        // Good looking fit or one of our regular truth functions
                        if (gofProb > 0.01 || order == truthOrder){
                            cout << "[INFO] Adding to Envelope " << bkgPdf->GetName() << " " << gofProb
                                 << " 2xNLL + c is " << myNll + bkgPdf->getVariables()->getSize()
                                 << endl;
                            allPdfs.insert(pair<string,RooAbsPdf*>(Form("%s%d", funcType->c_str(), order), bkgPdf));
                            storedPdfs.add(*bkgPdf);
                            pdforders.push_back(order);

                            // Keep track but we shall redo this later
                            if ((myNll + bkgPdf->getVariables()->getSize()) < MinimimNLLSoFar) {
                                simplebestFitPdfIndex = storedPdfs.getSize() - 1;
                                MinimimNLLSoFar = myNll + bkgPdf->getVariables()->getSize();
                            }
                        }
                        prev_order=order;
						prev_pdf=bkgPdf;
						order++;
                    }
                }
                fprintf(resFile, "%15s & %d & %5.2f & %5.2f \\\\\n", funcType->c_str(), cache_order + 1, chi2, prob);
                choices_envelope.insert(pair<string, vector<int>>(*funcType, pdforders));
            }
        }
        fprintf(resFile, "\\hline\n");
		choices_vec.push_back(choices);
		choices_envelope_vec.push_back(choices_envelope);
		pdfs_vec.push_back(pdfs);

        // Put selectedModels into a MultiPdf
        string catindexname = Form("pdfindex_%s_%s", catname.c_str(), ext.c_str());
        RooCategory catIndex(catindexname.c_str(), "c");
        RooMultiPdf *pdf = new RooMultiPdf(Form("CMS_higgs_%s_%s_bkgshape", catname.c_str(), ext.c_str()), "all pdfs", catIndex, storedPdfs);
        RooRealVar nBackground(Form("CMS_higgs_%s_%s_bkgshape_norm", catname.c_str(), ext.c_str()), "nbkg", data->sumEntries(), 0, 3 * data->sumEntries());

        //double check the best pdf!
        int bestFitPdfIndex = getBestFitFunction(pdf, data, &catIndex, !verbose);
        catIndex.setIndex(bestFitPdfIndex);
        cout << "// ------------------------------------------------------------------------- //" << endl;
        cout << "[INFO] Created MultiPdf " << pdf->GetName() << ", in Category " << cat << " with a total of " << catIndex.numTypes() << " pdfs"<< endl;
        storedPdfs.Print();
        cout << "[INFO] Best Fit Pdf = " << bestFitPdfIndex << ", " << storedPdfs.at(bestFitPdfIndex)->GetName() << endl;
        cout << "// ------------------------------------------------------------------------- //" << endl;
        cout << "[INFO] Simple check of index "<< simplebestFitPdfIndex << endl;

        mass->setBins(nBinsForMass);
        RooDataHist dataBinned(Form("roohist_data_mass_%s", catname.c_str()), "data", *mass, *dataFull);

        // Save it (also a binned version of the dataset
        outputws->import(*pdf);
        outputws->import(nBackground);
        // outputws->import(catIndex);
        outputws->import(dataBinned);
        // outputws->import(*data);
        outputws->import(*dataFull, Rename(Form("data_mass_%s", catname.c_str())));
        plot_best(
            mass, pdf, &catIndex, data,
            Form("%s/multipdf_%s_%s", outDir.c_str(), catname.c_str(), ext.c_str()),
            HLLGCats, cat, bestFitPdfIndex
        );

        outputfile->cd();
        outputws->Write();
        outputfile->Close();
    }

    FILE* dfile;
    if (singleCategory > -1){
        dfile = fopen(Form("./dat/fTest_%s.dat", HLLGCats[startingCategory].c_str()), "w");
        cout << Form("[INFO] datfile for BiasStudy: ./dat/fTest_%s.dat", HLLGCats[startingCategory].c_str()) << endl;
    }
    else{
        resFile = fopen("./dat/fTest.dat", "w");
        cout << "[INFO] datfile for BiasStudy: ./dat/fTest.dat" << endl;
    }
    cout << "[RESULT] Recommended options" << endl;
    for (int cat = startingCategory; cat < ncats; cat++){
        cout << "Cat [" << HLLGCats[cat].c_str() << ", " << cat << "]" << endl;

        fprintf(dfile, "cat = [%s, %d]\n", HLLGCats[cat].c_str(), cat);
        for (auto it = choices_vec[cat - startingCategory].begin(); it != choices_vec[cat - startingCategory].end(); it++){
            cout << "\t" << it->first << " - " << it->second << endl;
            fprintf(dfile, "truth = %s:%d:%s%d\n", it->first.c_str(), it->second, namingMap[it->first].c_str(), it->second);
        }
        for (auto it = choices_envelope_vec[cat - startingCategory].begin(); it != choices_envelope_vec[cat - startingCategory].end(); it++){
            vector<int> ords = it->second;
            for (vector<int>::iterator ordit = ords.begin(); ordit != ords.end(); ordit++){
                fprintf(dfile, "paul = %s:%d:%s%d\n", it->first.c_str(), *ordit, namingMap[it->first].c_str(), *ordit);
            }
        }
        fprintf(dfile, "\n");
    }
    outputfile->Close();

    return 0;
}