
std::vector<float> effSigma(TH1F* hist, double quantile = TMath::Erf(1.0/sqrt(2.0))){    
    std::vector<float> width_vec(3);

    TAxis* xaxis = hist->GetXaxis();
    int nb = xaxis->GetNbins();
    if(nb < 10) {
        cout << "effsigma: Not a valid histo(too few). nbins = " << nb << endl;
        return width_vec;
    }
    for(int i = 0; i < nb+2; i++) {
        if (hist->GetBinContent(i) < 0)
            hist->SetBinContent(i, 0); // prevent negative bin content
    }

    float bwid = xaxis->GetBinWidth(1);
    if(bwid == 0) {
        cout << "effsigma: Not a valid histo. bwid = " << bwid << endl;
        return width_vec;
    }
    // float xmax = xaxis->GetXmax();
    // float xmin = xaxis->GetXmin();
    // float ave = hist->GetMean();
    // float ave = hist->GetBinCenter(hist->GetMaximumBin()); // modified by CH 
    // float rms = hist->GetStdDev();  
    // cout << rms << endl;
    // prevent 0 stdDev
    hist->GetXaxis()->SetRange(1, nb+1); 
    hist->ResetStats();
    float xmax = xaxis->GetXmax();
    float xmin = xaxis->GetXmin();
    // float ave = hist->GetBinCenter(hist->GetMaximumBin()); // modified by CH 
    float ave = hist->GetMean(); 
    float rms = hist->GetStdDev(); // this function may return 0 when having negative weight (https://root.cern.ch/doc/master/TH1_8cxx_source.html#l07530)
    
    float total = 0;
    for(int i = 0; i < nb+2; i++) {
        total += hist->GetBinContent(i);
    }
    if (total < 0){
        width_vec[2] = 0.00001;
        cout << Form(" --> integral of histogram is < 0 in effSigma calc: %s. Returning 0.00001 for effSigma", hist->GetName()) << endl;
        return width_vec;
    }

    // float stddev2 = 0;
    // for (int i = 0; i < nb; i++){
    //     float center = xaxis->GetBinCenter(i+1);
    //     float content = hist->GetBinContent(i+1);
    //     if (content < 0)
    //         content = 0;
    //     stddev2 += content * (center - ave) * (center - ave);
    // }
    // float rms = sqrt(stddev2/total);

    int ierr = 0;
    int ismin = 999;

    // Scan around window of mean: window RMS/binWidth (cannot be bigger than 0.1*number of bins)
    // Determine minimum width of distribution which holds 0.693 of total
    float rlim = quantile*total;
    int nrms = rms/bwid; // Set scan size to +/- rms
    // cout << nrms << ", " << rms << ", "<< nb << ", " << nb/10 << endl;
    if(nrms > nb/10) 
        nrms = nb/10; // Could be tuned...

    float widmin = 9999999.;
    float sigeffmin = -1.;
    float sigeffmax = -1.;
    for(int iscan = -nrms; iscan < nrms+1; iscan++){ // Scan window centre
        int ibm = (ave - xmin)/bwid + 1 + iscan; // Find bin idx in scan: iscan from mean
        float x = (ibm - 0.5)*bwid + xmin; // 0.5 for bin centre
        float xj = x;
        float xk = x;
        int jbm = ibm;
        int kbm = ibm;

        // Define counter for yield in bins: stop when counter > rlim
        float bin = hist->GetBinContent(ibm);
        total = bin;
        for(int j = 1; j < nb; j++){
            if(jbm < nb) {
                jbm++;
                xj += bwid;
                bin = hist->GetBinContent(jbm);
                total += bin;
                if(total > rlim) 
                    break;
            }
            else {
                cout << Form(" --> Reach bin = nBins in effSigma calc: %s. Returning 0.00001 for effSigma", hist->GetName()) << endl;
                width_vec[2] = 0.00001;
                return width_vec;
            }

            if(kbm > 0) {
                kbm--;
                xk -= bwid;
                bin = hist->GetBinContent(kbm);
                total += bin;
                if(total > rlim) 
                    break;
            }
            else {
                cout << Form(" --> Reach bin = 0 in effSigma calc: %s. Returning 0.00001 for effSigma", hist->GetName()) << endl;
                width_vec[2] = 0.00001;
                return width_vec;
            }
        }

        // Calculate fractional width in bin takes above limt (assume linear)
        float dxf = (total-rlim)*bwid/bin;
        float wid = (xj-xk+bwid-dxf)*0.5; // Total width: half of peak
        if(wid < widmin) {
            widmin = wid;
            ismin = iscan;
            sigeffmin = xk+dxf;
            sigeffmax = xj+bwid;
        }
    }
    
    // cout << widmin << endl;
    width_vec[0] = sigeffmin;
    width_vec[1] = sigeffmax;
    width_vec[2] = widmin;
    return width_vec;
}