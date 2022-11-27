# Hold defs of writing functions for datacard
import pandas as pd



class DCWriter:
    def __init__(self, _foutName, _df, _cat, _mass, _years, _auto_space=False):
        self.fout   = open(_foutName, "w")  # output file
        self.df     = _df                   # yields dataframe
        self.cat    = _cat                  # category
        self.mass   = _mass                 # mass points
        self.years  = _years                # years

        self.auto_space = _auto_space
        self.space0 = 9
        self.space1 = 23
        self.space2 = 26
        self.space3 = 136
        self.space4 = 24


    def writePreamble(self):
        self.fout.write("CMS HLLG Datacard\n")
        self.fout.write("Auto-generated by HLLGFinalFits/Datacard/makeDatacard.py\n")
        self.fout.write("Run with: combine\n")
        self.fout.write("---------------------------------------------------------------------------------------------------------------------------------\n")
        self.fout.write("imax 1   number of channels\n")
        self.fout.write("jmax *   number of backgrounds\n")
        self.fout.write("kmax *   number of nuisance parameters (sources of systematic uncertainty)\n")
        self.fout.write("---------------------------------------------------------------------------------------------------------------------------------\n")


    def writeBreak(self):
        self.fout.write("---------------------------------------------------------------------------------------------------------------------------------\n")


    def writeProcesses(self):
        i = 0
        for ir, r in self.df[self.df["cat"] == self.cat].iterrows():
            if ((r["mass"] != self.mass) and (r["mass"] != "-")):
                continue
            if i == 0: # use first element to format the space
                if (self.auto_space):
                    self.space1, self.space2, self.space3, self.space4 = len(r["proc"])+10, len(r["cat"])+10, len(r["modelWSFile"])+10, len(r["model"])+10
                i += 1
            self.fout.write("{0:<{sp0}}{1:<{sp1}}{2:<{sp2}}{3:<{sp3}}{4:<{sp4}}\n".format(
                "shapes", r["proc"], r["cat"], r["modelWSFile"], r["model"],
                sp0=self.space0, sp1=self.space1, sp2=self.space2, sp3=self.space3, sp4=self.space4)
            )

        # Bin, observation and rate lines
        lbreak = "----------------------------------------------------------------------------------------------------------------------------------"
        lbin_cat = "{0:<{sp1}}{1:<{sp2}}".format("bin", self.cat, sp1=self.space0+self.space1, sp2=self.space2)
        lobs_cat = "{0:<{sp1}}{1:<{sp2}}".format("observation", "-1", sp1=self.space0+self.space1, sp2=self.space2)
        lbin_procXcat = "{:<{sp1}}".format("bin", sp1=self.space0+self.space1)
        lproc = "{0:<{sp1}}".format("process", sp1=self.space0+self.space1)
        lprocid = "{0:<{sp1}}".format("process", sp1=self.space0+self.space1)
        lrate = "{0:<{sp1}}".format("rate", sp1=self.space0+self.space1)
        sigID = 0

        # Loop over rows for respective category
        for ir, r in self.df[self.df["cat"] == self.cat].iterrows():
            if (r["proc"] == "data_obs"):
                continue
            if ((r["mass"] != self.mass) and (r["mass"] != "-")):
                continue

            lbin_procXcat += "{:<{sp2}}".format(self.cat, sp2=self.space2)
            lproc += "{:<{sp2}}".format(r["proc"], sp2=self.space2)
            if r["proc"] == "bkg_mass":
                lprocid += "{:<{sp2}}".format("1", sp2=self.space2)
            else:
                lprocid += "{:<{sp2}}".format(str(sigID), sp2=self.space2)
                sigID -= 1

            if r["nominal_yield"] == "-":
                bkgrate = str(round(1.0, 1))
                lrate += "{:<{sp2}}".format(bkgrate, sp2=self.space2)
            else:
                sigrate = str(round(r["nominal_yield"], 7))
                lrate += "{:<{sp2}}".format(sigrate, sp2=self.space2)

        # Remove final space from lines and add to file
        for l in [lbreak, lbin_cat, lobs_cat, lbreak, lbin_procXcat, lproc, lprocid, lrate, lbreak]:
            l = l[:-1]
            self.fout.write("%s\n" %l)


    def writeSystematic(self, s):
        if s["prior"] == "lnN":
            df_iter = pd.DataFrame()
            if ((s["name"] == "CMS_JEC_13TeV") or (s["name"] == "CMS_JER_13TeV")):
                df_iter = self.df[(self.df["cat"] == self.cat) & ((self.df["cat"].str.contains("VBF")) | (self.df["year"].str.contains("merged")))]
                if not pd.Series(self.cat).str.contains("VBF")[0]:
                    return True
            elif (s["name"] == "CMS_R9_13TeV"):
                df_iter = self.df[(self.df["cat"] == self.cat) & ((self.df["cat"].str.contains("R9")) | (self.df["year"].str.contains("merged")))]
                if not pd.Series(self.cat).str.contains("R9")[0]:
                    return True
            else:
                df_iter = self.df[self.df["cat"] == self.cat]

            if (s["correlateAcrossYears"] == 1):
                stitle = s["name"]
                lsyst = "{0:<25}{1:<{sp1}}".format(stitle, s["prior"], sp1=self.space1-(25-self.space0))
                for ir, r in df_iter.iterrows():
                    if r["proc"] == "data_obs":
                        continue
                    if ((r["mass"] != self.mass) and (r["mass"] != "-")):
                        continue
                    sval = r[stitle]
                    lsyst += "{0:<{sp2}}".format(sval, sp2=self.space2)
                self.fout.write("{}\n".format(lsyst[:-1]))
            else:
                for i, y in enumerate(self.years):
                    stitle = "{}_{}".format(s["name"], y)
                    lsyst = "{0:<25}{1:<{sp1}}".format(stitle, s["prior"], sp1=self.space1-(25-self.space0))
                    for ir, r in df_iter.iterrows():
                        if r["proc"] == "data_obs":
                            continue
                        if ((r["mass"] != self.mass) and (r["mass"] != "-")):
                            continue
                        sval = r[stitle]
                        lsyst += "{0:<{sp2}}".format(sval, sp2=self.space2)
                    self.fout.write("{}\n".format(lsyst[:-1]))


    def writeParamSystematic(self, s):
        # self.fout.write("----------------------------------------------------------------------------------------------------------------------------------\n")
        if s["prior"] == "param":
            for proc in self.df["procOriginal"].unique():
                if ((proc == "data_obs") or (proc == "bkg_mass")):
                    continue

                val_years = []
                for year in self.df["year"].unique():
                    if year == "merged":
                        continue
                    mask = (self.df["type"] == "sig") & (self.df["year"] == year) & (self.df["cat"] == self.cat) & (self.df["procOriginal"] == proc) & (self.df["mass"] == self.mass)
                    # try:
                    idx = self.df.index[mask]
                    val = self.df.iloc[idx][s["name"]].item()
                    val_years.append(val)

                col_name = "{}_{}_{}_{}".format(s["name"], proc, self.mass, self.cat)
                self.fout.write("{0:{sp0}}{1:<7}{2:<5}{3:<12}{4:<12}{5:<12}\n".format(col_name, "param", str(1), str(round(val_years[0], 7)), str(round(val_years[1], 7)), str(round(val_years[2], 7)), sp0=self.space0+self.space1+self.space2))


    def writePdfIndex(self, ext="13TeV"):
        self.fout.write("----------------------------------------------------------------------------------------------------------------------------------\n")
        indexStr = "pdfindex_{}_{}".format(self.cat, ext)
        self.fout.write("{0:{sp0}}{1:<10}\n".format(indexStr, "discrete", sp0=self.space0+self.space1+self.space2))


    def close(self):
        self.fout.close()




















































# def writePreamble(f):
#     f.write("CMS HLLG Datacard\n")
#     f.write("Auto-generated by HLLGFinalFits/Datacard/makeDatacard.py\n")
#     f.write("Run with: combine\n")
#     f.write("---------------------------------------------------------------------------------------------------------------------------------\n")
#     f.write("imax 1   number of channels\n")
#     f.write("jmax *   number of backgrounds\n")
#     f.write("kmax *   number of nuisance parameters (sources of systematic uncertainty)\n")
#     f.write("---------------------------------------------------------------------------------------------------------------------------------\n")
#     return True

# def writeProcesses(f, df, cat, mass, outDir): # df = Pandas DataFrame
#     # Shapes
#     # Loop over categories in dataframe
#     sp1, sp2, sp3, sp4 = 0, 0, 0, 0
#     i = 0
#     for ir, r in df[df["cat"] == cat].iterrows():
#         if ((r["mass"] != mass) and (r["mass"] != "-")):
#             continue
#         if i == 0: # use first element to format the space
#             sp1, sp2, sp3, sp4 = len(r["proc"])+10, len(r["cat"])+10, len(r["modelWSFile"])+10, len(r["model"])+10
#             i += 1
#         f.write("shapes   {0:<{sp1}}{1:<{sp2}}{2:<{sp3}}{3:<{sp4}}\n".format(r["proc"], r["cat"], r["modelWSFile"], r["model"], sp1=sp1, sp2=sp2, sp3=sp3, sp4=sp4))

#     # Bin, observation and rate lines
#     lbreak = "----------------------------------------------------------------------------------------------------------------------------------"
#     lbin_cat = "{0:<{sp1}}{1:<{sp2}}".format("bin", cat, sp1=9+sp1, sp2=sp2)
#     lobs_cat = "{0:<{sp1}}{1:<{sp2}}".format("observation", "-1", sp1=9+sp1, sp2=sp2)
#     lbin_procXcat = "{:<{sp1}}".format("bin", sp1=9+sp1)
#     lproc = "{0:<{sp1}}".format("process", sp1=9+sp1)
#     lprocid = "{0:<{sp1}}".format("process", sp1=9+sp1)
#     lrate = "{0:<{sp1}}".format("rate", sp1=9+sp1)
#     sigID = 0

#     # Loop over rows for respective category
#     for ir,r in df[df["cat"] == cat].iterrows():
#         if (r["proc"] == "data_obs"):
#             continue
#         if ((r["mass"] != mass) and (r["mass"] != "-")):
#             continue
#         lbin_procXcat += "{:<{sp2}}".format(cat, sp2=sp2)
#         lproc += "{:<{sp2}}".format(r["proc"], sp2=sp2)
#         if r["proc"] == "bkg_mass":
#             lprocid += "{:<{sp2}}".format("1", sp2=sp2)
#         else:
#             lprocid += "{:<{sp2}}".format(str(sigID), sp2=sp2)
#             sigID -= 1
#         if r["nominal_yield"] == "-":
#             bkgrate = str(round(1.0, 1))
#             lrate += "{:<{sp2}}".format(bkgrate, sp2=sp2)
#         else:
#             sigrate = str(round(r["nominal_yield"], 7))
#             lrate += "{:<{sp2}}".format(sigrate, sp2=sp2)

#     # Remove final space from lines and add to file
#     for l in [lbreak, lbin_cat, lobs_cat, lbreak, lbin_procXcat, lproc, lprocid, lrate, lbreak]:
#         l = l[:-1]
#         f.write("%s\n" %l)

#     return True


# # l-systematic line, v-value, s-systematic title, p-proc, c-cat
# def addSyst(l, v):
#     l += "{0:<15}".format(v)
#     return l

# def writeSystematic(f, df, s, cat, mass, years):
#     df_iter = pd.DataFrame()
#     if ((s["name"] == "CMS_JEC_13TeV") or (s["name"] == "CMS_JER_13TeV")):
#         df_iter = df[(df["cat"] == cat)&((df["cat"].str.contains("VBF"))|(df["year"].str.contains("merged")))]
#         if not pd.Series(cat).str.contains("VBF")[0]:
#             return True
#     elif (s["name"] == "CMS_R9_13TeV"):
#         df_iter = df[(df["cat"] == cat)&((df["cat"].str.contains("R9"))|(df["year"].str.contains("merged")))]
#         if not pd.Series(cat).str.contains("R9")[0]:
#             return True
#     else:
#         df_iter = df[df["cat"] == cat]

#     if (s["correlateAcrossYears"] == 1):
#         stitle = s["name"]
#         lsyst = "{0:<20}{1:<14}".format(stitle, s["prior"])
#         for ir, r in df_iter.iterrows():
#             if r["proc"] == "data_obs":
#                 continue
#             if ((r["mass"] != mass) and (r["mass"] != "-")):
#                 continue

#             sval = r[stitle]
#             lsyst = addSyst(lsyst, sval)

#     # if (s["correlateAcrossYears"] == 1):
#     #     for i, y in enumerate(years):
#     #         stitle = "{}_{}".format(s["name"], y)
#     #         lsyst = "{:30}{:8}".format(stitle, s["prior"])
#     #         for ir, r in df_iter.iterrows():
#     #             if r["proc"] == "data_obs":
#     #                 continue
#     #             if ((r["mass"] != str(mass)) and (r["mass"] != "-")):
#     #                 continue

#     #             sval = r[stitle]
#     #             lsyst = addSyst(lsyst, sval)

#     #         f.write("{}\n".format(lsyst[:-1]))

#     # else:
#     #     stitle = s["name"]
#     #     lsyst = "{:30}{:8}".format(stitle, s["prior"])
#     #     for ir, r in df_iter.iterrows():
#     #         if r["proc"] == "data_obs":
#     #             continue
#     #         if ((r["mass"] != str(mass)) and (r["mass"] != "-")):
#     #             continue

#     #         sval = r[stitle]
#     #         lsyst = addSyst(lsyst, sval)

#         f.write("{}\n".format(lsyst[:-1]))

#     return True