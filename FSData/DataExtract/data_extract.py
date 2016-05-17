# ######################################################
# ##                                                  ##
# ##                    Documentation                 ##
# ##                                                  ##
# ######################################################

# how this script works

# ######################################################
# ##                                                  ##
# ##                      Packages                    ##
# ##                                                  ##
# ######################################################

import csv, os
from os import listdir as LD
from os.path import splitext as ST

if __name__ == "__main__":
    # ######################################################
    # ##                                                  ##
    # ##                 Variable Settings                ##
    # ##                                                  ##
    # ######################################################
    
    input_folder  = "source"
    output_folder = "output"

    # ######################################################
    # ##                                                  ##
    # ##                    Read in Data                  ##
    # ##                                                  ##
    # ######################################################

    for filename in LD(input_folder):
        print filename
        ifname = input_folder + os.sep + filename
        with open(ifname, "r") as file:
            lines = file.readlines()
            file.close()
        # in case files have different format, search for T, S, H, A every time
        (T, S, H, A) = 0, 0, 0, 0
        tabs = lines[1]
        tabs = tabs.split('|')
        ntab = len(tabs)
        for i in range(ntab):
            tab = tabs[i].replace(" ", "")
            if tab == "_totl,_time":
                T = i
            elif tab == "_Vind,_kias":
                S = i
            elif tab == "hding,__mag":
                H = i
            elif tab == "__alt,ftmsl":
                A = i
        ofname = output_folder + os.sep + "t" + ST(filename)[0] + ".csv"
        with open(ofname, "wb") as csvfile:
            fwriter = csv.writer(csvfile, delimiter=',')
            fwriter.writerow(["time", "speed", "heading", "altitude"])
            st = -1
            for line in lines[2:]:
                row = line.split('|')
                if len(row) < ntab:
                    continue
                Tv  = float(row[T].replace(" ", ""))
                Sv  = float(row[S].replace(" ", ""))
                Hv  = float(row[H].replace(" ", ""))
                Av  = float(row[A].replace(" ", ""))
                # prow = ["{0:.5f}".format(Tv), "{0:.5f}".format(Sv), \
                #         "{0:.5f}".format(Hv), "{0:.5f}".format(Av)]
                # fwriter.writerow(prow)
                # fwriter.writerow([Tv, Sv, Hv, Av])
                if st == -1:
                    if Sv > 250 and Av > 30000:
                        st = Tv
                    else:
                        continue
                fwriter.writerow([Tv - st, Sv, Hv, Av])
            csvfile.close()
