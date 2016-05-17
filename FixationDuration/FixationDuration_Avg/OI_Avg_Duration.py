# ######################################################
# ##                                                  ##
# ##                    Documentation                 ##
# ##                                                  ##
# ######################################################

# In this script, we're trying to find the optimal interval by calculating
# the average of fixation duration in an interval, and compare it with the
# average value + the standard deviation of the data in the BAS condition

# ######################################################
# ##                                                  ##
# ##                      Packages                    ##
# ##                                                  ##
# ######################################################
import numpy
import xml.etree.ElementTree as ET
from collections import OrderedDict as OD

def intersect(a, b):
    return list(set(a) & set(b))

if __name__ == "__main__":
    # ######################################################
    # ##                                                  ##
    # ##                 Variable Settings                ##
    # ##                                                  ##
    # ######################################################

    # Format Tags
    ws_tag   = "{urn:schemas-microsoft-com:office:spreadsheet}Worksheet"
    name_tag = "{urn:schemas-microsoft-com:office:spreadsheet}Name"
    tbl_tag  = "{urn:schemas-microsoft-com:office:spreadsheet}Table"
    row_tag  = "{urn:schemas-microsoft-com:office:spreadsheet}Row"
    cell_tag = "{urn:schemas-microsoft-com:office:spreadsheet}Cell"
    data_tag = "{urn:schemas-microsoft-com:office:spreadsheet}Data"

    # Data Tags
    AOI_tag  = "aoiname"
    TMES_tag = "starttime"
    DUR_tag  = "duration"
    p_mode   = "PUMP"

    # Interval Values to be Tested (in seconds)
    intervals = [5, 10, 15, 20, 25, 30, 45, 60, 75, 90, 180]

    # Test Data Set
    ds  = "NVP"
    sds = [0, 0.1, 0.125, 0.25, 0.5, 1]

    # ######################################################
    # ##                                                  ##
    # ##                Processing BAS data               ##
    # ##                                                  ##
    # ######################################################
    with open("BAS.xml", "r") as file:
        bas      = ET.fromstring(file.read())
        bas_data = {}
        bas_pl   = []
        file.close()

    for ws in bas.findall(ws_tag):
        name = ws.get(name_tag)
        seq  = int(name[:name.find(',')])
        bas_pl.append(seq)

        table = ws.find(tbl_tag)
        rows  = table.findall(row_tag)
        (AOI, TMES, DUR) = 0, 0, 0

        tags = rows[0].findall(cell_tag)
        for i in range(len(tags)):
            data = tags[i].find(data_tag).text.lower()
            if data == AOI_tag:
                AOI = i
            elif data == TMES_tag:
                TMES = i
            elif data == DUR_tag:
                DUR = i
            elif AOI != 0 and TMES != 0 and DUR != 0:
                break

        fixation_duration = []
        for row in rows[1:]:
            aoiname = row.findall(cell_tag)[AOI].find(data_tag).text
            if aoiname != p_mode:
                continue
            # starttme = float(row.findall(cell_tag)[TMES].find(data_tag).text)
            duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            fixation_duration.append(duration)

        avg = numpy.mean(fixation_duration)
        std = numpy.std(fixation_duration)
        bas_data[seq] = {
            "avg": avg,
            "std": std
        }

    # ######################################################
    # ##                                                  ##
    # ##              Processing Testing data             ##
    # ##                                                  ##
    # ######################################################
    with open(ds + ".xml", "r") as file:
        foc      = ET.fromstring(file.read())
        focdir   = {}
        foc_data = {}
        foc_pl   = []
        file.close()

    for ws in foc.findall(ws_tag):
        name = ws.get(name_tag)
        seq  = int(name[:name.find(',')])
        focdir[seq] = {"seq": seq, "dra": {}}
        foc_pl.append(seq)

        table = ws.find(tbl_tag)
        rows  = table.findall(row_tag)
        (AOI, TMES, DUR) = 0, 0, 0

        tags = rows[0].findall(cell_tag)
        for i in range(len(tags)):
            data = tags[i].find(data_tag).text.lower()
            if data == AOI_tag:
                AOI = i
            elif data == TMES_tag:
                TMES = i
            elif data == DUR_tag:
                DUR = i
            elif AOI != 0 and TMES != 0 and DUR != 0:
                break

        for row in rows[1:]:
            starttme = float(row.findall(cell_tag)[TMES].find(data_tag).text)
            # ignoring the data in the first minute
            if starttme < 60:
                continue
            aoiname = row.findall(cell_tag)[AOI].find(data_tag).text
            if aoiname != p_mode:
                duration = numpy.nan
            else:
                duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            focdir[seq]["dra"][starttme - 60] = duration

        focdir[seq]["dra"] = OD(sorted(focdir[seq]["dra"].items()))

    # ######################################################
    # ##                                                  ##
    # ##                Calculate Hit Rate                ##
    # ##                                                  ##
    # ######################################################
    pl = intersect(bas_pl, foc_pl)
    for sd in sds:
        output_filename = "Test on " + ds + "_Avg + " + str(sd) + " Stdv.txt"
        output = open(output_filename, "wb")
        output.write(' ' * 20)
        for iv in intervals:
            output.write("{:4.0f}  ".format(iv))
        output.write("\r\n")
        output.write('-' * 78 + "\r\n")

        for par in pl:
            output.write("# Participant " + "{:2.0f}".format(par) + " |  ")
            mark  = bas_data[par]["avg"] + bas_data[par]["std"] * sd
            score = []
            print "par: #" + str(par), mark, bas_data[par]["avg"], bas_data[par]["std"]
            for iv in intervals:
                fv = []
                for t, f in focdir[par]["dra"].iteritems():
                    group = int(t / iv)
                    while group >= len(fv):
                        fv.append([])
                    fv[group].append(f)
                print "interval:", iv
                for i in range(len(fv)):
                    if len(fv[i]) == 0:
                        avg = 0
                    else:
                        avg = numpy.nanmean(fv[i])
                    print avg, fv[i]
                    # strictly larger
                    if avg > mark:
                        fv[i] = 1
                    else:
                        fv[i] = 0
                score.append(numpy.mean(fv))
            for i in score:
                output.write("{0:3.2f}  ".format(i))
            output.write("\r\n")
            print ""

        output.close()