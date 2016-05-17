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
    # fmt      = "{urn:schemas-microsoft-com:office:spreadsheet}"
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

    # Interval Values to be Tested (in seconds), Longest is (5-1) = 4 mins
    intervals = [5, 10, 15, 20, 30, 45, 60, 90, 120, 240]

    # ######################################################
    # ##                                                  ##
    # ##                Processing BAS data               ##
    # ##                                                  ##
    # ######################################################
    with open("BAS.xml", "r") as file:
        bas = ET.fromstring(file.read())
        basdir = {}
        bas_data = {}
        file.close()
        bas_pl = []

    for ws in bas.findall(ws_tag):
        name = ws.get(name_tag)
        seq = int(name[:name.find(',')])
        basdir[seq] = {"seq": seq, "dra": {}}
        bas_pl.append(seq)

        table = ws.find(tbl_tag)
        rows = table.findall(row_tag)
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
            starttme = float(row.findall(cell_tag)[TMES].find(data_tag).text)
            duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            basdir[seq]["dra"][starttme] = duration
            fixation_duration.append(duration)

        # Currently, we don't need the values of durations anymore in BAS
        # basdir[seq]["dra"] = OD(sorted(basdir[seq]["dra"].items()))

        avg = numpy.mean(fixation_duration)
        std = numpy.std(fixation_duration)
        bas_data[seq] = {
            "avg": avg,
            "std": std,
            "ulmt": avg + std
        }

    # ######################################################
    # ##                                                  ##
    # ##              Processing Testing data             ##
    # ##                                                  ##
    # ######################################################
    with open("NVP.xml", "r") as file:
        foc = ET.fromstring(file.read())
        focdir = {}
        foc_data = {}
        file.close()
        foc_pl = []

    for ws in foc.findall(ws_tag):
        name = ws.get(name_tag)
        seq = int(name[:name.find(',')])
        focdir[seq] = {"seq": seq, "dra": {}}
        foc_pl.append(seq)

        table = ws.find(tbl_tag)
        rows = table.findall(row_tag)
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
            aoiname = row.findall(cell_tag)[AOI].find(data_tag).text
            if aoiname != p_mode:
                continue
            starttme = float(row.findall(cell_tag)[TMES].find(data_tag).text)
            # ignoring the data in the first minute
            if starttme < 60:
                continue
            duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            focdir[seq]["dra"][starttme - 60] = duration

        focdir[seq]["dra"] = OD(sorted(focdir[seq]["dra"].items()))

    # ######################################################
    # ##                                                  ##
    # ##                Calculate Hit Rate                ##
    # ##                                                  ##
    # ######################################################
    output_filename = "Test on NVP_Avg + 1 Stdv.txt"
    output = open(output_filename, "wb")
    output.write(' ' * 20)
    for iv in intervals:
        output.write("{:4.0f}  ".format(iv))
    output.write("\r\n")
    output.write('-' * 78 + "\r\n")

    pl = intersect(bas_pl, foc_pl)
    for par in pl:
        output.write("# Participant " + "{:2.0f}".format(par) + " |  ")
        mark  = bas_data[par]["avg"] + bas_data[par]["std"] * 1
        score = []
        print "par: #" + str(par), mark, bas_data[par]["avg"], bas_data[par]["std"]
        for iv in intervals:
            fv = []
            for t, f in focdir[par]["dra"].iteritems():
                if int(t / iv) >= len(fv):
                    fv.append([f])
                else:
                    fv[len(fv) - 1].append(f)
            print "interval:", iv
            for i in range(len(fv)):
                avg = numpy.mean(fv[i])
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