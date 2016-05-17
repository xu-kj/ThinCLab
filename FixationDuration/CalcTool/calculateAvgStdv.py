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
import numpy, math, os, csv
from os.path import splitext as ST
from os import listdir as LD
from collections import OrderedDict as OD

if __name__ == "__main__":
    # ######################################################
    # ##                                                  ##
    # ##                 Variable Settings                ##
    # ##                                                  ##
    # ######################################################

    source_folder = "source"
    output_folder = "result"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    (S, D, F) = 2, 3, 4

    iv = 20

    print ">>> Currently the length of the interval is set to be " + \
          str(iv) + " seconds.\n    If that's the desired length, press ENTER."

    iv = raw_input("    Otherwise, please specify the length of the interval: ")
    if iv == "":
        # ENTER Pressed
        iv = 20
    else:
        iv = int(iv)

    print ">>> The length of the interval is set as:", iv
    print ""

    print ">>> Currently the script would process all the csv files from the " + \
          "subfolder\n    named \"" + source_folder + "\". If that's the desired " + \
          "path, press ENTER."
    ip = raw_input("    Otherwise, please specify the path: ")
    if ip == "":
        # ENTER Pressed
        pass
    else:
        source_folder = ip

    # ######################################################
    # ##                                                  ##
    # ##           Processing eyetracking data            ##
    # ##                                                  ##
    # ######################################################

    for filename in LD(source_folder):
        if ST(filename)[1] != ".csv":
            continue
        print ">>> Processing:", filename
        data = {}
        ifname = source_folder + os.sep + filename
        ofname = output_folder + os.sep + 'c_' + filename
        drows = []
        with open(ifname, "rb") as csvfile:
            # lines = file.readlines()
            lines = csv.reader(csvfile, delimiter = ',')
            for line in lines:
                if line[0].lower() == "horizontal_pos":
                    continue
                r = []
                r.append(float(line[S]))
                r.append(float(line[D]))
                r.append(line[F])
                drows.append(r)
            csvfile.close()

        # ######################################################
        # ##                                                  ##
        # ##        Avg and Stdv for Fixation Duration        ##
        # ##                                                  ##
        # ######################################################
        fd = []
        # for row in rows[1:]:
        for row in drows:
            if row[2] != "TRUE":
                continue
            # starttme = row[0]
            duration = row[1]
            fd.append(duration)

        data["fd"] = {
            "avg": numpy.mean(fd),
            "std": numpy.std(fd)
        }

        # ######################################################
        # ##                                                  ##
        # ##          Avg and Stdv for Dwell Duration         ##
        # ##                                                  ##
        # ######################################################
        fp = []
        dwell = False
        for row in drows:
            if len(fp) == 0:
                if row[2] == "FALSE":
                    continue
                else:
                    fp.append(row[1])
                    dwell = True
            else:
                if dwell:
                    if row[2] == "FALSE":
                        dwell = False
                    else:
                        fp[len(fp) - 1] += row[1]
                elif row[2] == "TRUE":
                    fp.append(row[1])
                    dwell = True

        data["dd"] = {
            "avg": numpy.mean(fp),
            "std": numpy.std(fp)
        }

        # ######################################################
        # ##                                                  ##
        # ##       Avg and Stdv for Fixation Percentage       ##
        # ##                                                  ##
        # ######################################################
        fp = []
        for row in drows:
            group = int(row[0] / iv)
            while group >= len(fp):
                fp.append([])
            if row[2] == "TRUE":
                fp[group].append(1)
            else:
                fp[group].append(0)
        for i in range(len(fp)):
            # what if there's no data in the interval?
            if len(fp[i]) == 0:
                fp[i] = 0
            else:
                fp[i] = numpy.mean(fp[i])
        data["fp"] = {
            "avg": numpy.mean(fp),
            "std": numpy.std(fp)
        }

        # ######################################################
        # ##                                                  ##
        # ##                  Output to File                  ##
        # ##                                                  ##
        # ######################################################
        with open(ofname, "wb") as csvfile:
            fwriter = csv.writer(csvfile, delimiter=',')
            fwriter.writerow(["", "avg", "stdv"])
            fwriter.writerow(["Fixation_Duration", \
                              data["fd"]["avg"], data["fd"]["std"]])
            fwriter.writerow(["Dwell_Duration", \
                              data["dd"]["avg"], data["dd"]["std"]])
            fwriter.writerow(["Fixation_Percentage", \
                              data["fp"]["avg"], data["fp"]["std"]])
            csvfile.close()

    c = raw_input(">>> Finished! Press ENTER to quit...")
