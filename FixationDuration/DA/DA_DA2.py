# ######################################################
# ##                                                  ##
# ##                    Documentation                 ##
# ##                                                  ##
# ######################################################

#

# ######################################################
# ##                                                  ##
# ##                      Packages                    ##
# ##                                                  ##
# ######################################################
import numpy, math
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
    tbl_tag  = "{urn:schemas-microsoft-com:office:spreadsheet}Table"
    row_tag  = "{urn:schemas-microsoft-com:office:spreadsheet}Row"
    name_tag = "{urn:schemas-microsoft-com:office:spreadsheet}Name"
    cell_tag = "{urn:schemas-microsoft-com:office:spreadsheet}Cell"
    data_tag = "{urn:schemas-microsoft-com:office:spreadsheet}Data"

    # Data Tags
    AOI_tag  = "aoiname"
    DUR_tag  = "duration"
    TMES_tag = "starttime"
    p_mode   = "PUMP"

    # Interval Values to be Tested (in seconds)
    windows           = [10]                  # only one value in this script
    speed             = [0.25, 0.5, 0.75, 1]  # speed is value * window
    number_of_windows = [1, 2, 3]             # number of windows

    # Test Data Set
    dss               = ["FOC", "NVP", "BAS"] # name of the XML files to be tested
    threshold_factor  = 0.1                   # only one value in this script

    # ######################################################
    # ##                                                  ##
    # ##                Processing BAS data               ##
    # ##                                                  ##
    # ######################################################
    with open("BAS.xml", "r") as file:
        bas      = ET.fromstring(file.read())
        bas_pl   = []
        bas_data = {}
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
            duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            fixation_duration.append(duration)

        bas_data[seq] = {
            "avg": numpy.mean(fixation_duration),
            "std": numpy.std(fixation_duration, ddof = 1)
        }

    # ######################################################
    # ##                                                  ##
    # ##              Processing Testing data             ##
    # ##                                                  ##
    # ######################################################
    for ds in dss:
        with open(ds + ".xml", "r") as file:
            foc    = ET.fromstring(file.read())
            focdir = {}
            foc_pl = []
            file.close()

        for ws in foc.findall(ws_tag):
            name = ws.get(name_tag)
            seq  = int(name[:name.find(',')])
            focdir[seq] = {"seq": seq, "dra": {}, "ts": {}}
            foc_pl.append(seq)

            table = ws.find(tbl_tag)
            rows  = table.findall(row_tag)
            (AOI, TMES, DUR) = 0, 0, 0

            max_time = 0

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
                    # duration = numpy.nan
                    duration = - float(row.findall(cell_tag)[DUR].find(data_tag).text)
                else:
                    duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
                focdir[seq]["dra"][starttme - 60] = duration
                if (starttme - 60) > max_time:
                    max_time = starttme - 60

            focdir[seq]["dra"] = OD(sorted(focdir[seq]["dra"].items()))

            for iv in windows:
                focdir[seq]["ts"][iv] = {}
                for s in speed:
                    s = s * iv
                    focdir[seq]["ts"][iv][s] = {}
                    mt = int((max_time - iv) / s) + 1
                    for i in range(0, mt + 1, 1):
                        if (i * s + iv) > max_time:
                            focdir[seq]["ts"][iv][s][i * s] = max_time
                        else:
                            focdir[seq]["ts"][iv][s][i * s] = i * s + iv
                    focdir[seq]["ts"][iv][s] = OD(sorted(focdir[seq]["ts"][iv][s].items()))

        # ######################################################
        # ##                                                  ##
        # ##                Calculate Hit Rate                ##
        # ##                                                  ##
        # ######################################################
        pl = intersect(bas_pl, foc_pl)
        output_filename = "Test on " + ds + "_Avg + " + \
                          str(threshold_factor) + " Stdv.txt"
        output = open(output_filename, "wb")
        output.write(' ' * 20)
        # for iv in windows:
        #     output.write("{:4.0f}  ".format(iv))
        for iv in windows:
            for s in speed:
                s = iv * s
                for p in number_of_windows:
                    output.write("{:3.1f}s{:1.0f}p  ".format(s, p))
        output.write("\r\n")
        output.write('-' * 78 + "\r\n")

        for par in pl:
            output.write("# Participant " + "{:2.0f}".format(par) + " |  ")
            mark  = bas_data[par]["avg"] + bas_data[par]["std"] * threshold_factor
            score = []
            print "par: #" + str(par), mark, bas_data[par]["avg"], bas_data[par]["std"]
            for iv in windows:
                for ss in speed:
                    ss = iv * ss
                    ts = focdir[par]["ts"][iv][ss]
                    print ts
                    fv = []
                    for i in range(0, len(ts)):
                        fv.append([])
                    for t, f in focdir[par]["dra"].iteritems():
                        if f < 0:
                            et = t - f
                        else:
                            et = t + f
                        cntr = 0
                        for s, e in ts.iteritems():
                            if t < s:
                                if et < s:
                                    break
                                elif et < e:
                                    if f < 0:
                                        fv[cntr].append(numpy.nan)
                                    else:
                                        fv[cntr].append(et - s)
                                else:
                                    fv[cntr].append(iv)
                            elif t >= e:
                                # wait for the next group
                                pass
                            else:
                                if et < e:
                                    if f < 0:
                                        fv[cntr].append(numpy.nan)
                                    else:
                                        fv[cntr].append(f)
                                else:
                                    if f < 0:
                                        fv[cntr].append(numpy.nan)
                                    else:
                                        fv[cntr].append(e - t)
                            cntr += 1

                    print cntr
                    # for v in fv:
                    #     print v

                    for i in range(len(fv)):
                        if len(fv[i]) == 0:
                            avg = 0
                        else:
                            avg = numpy.nanmean(fv[i])
                            if math.isnan(avg):
                                avg = 0
                        print avg, fv[i]
                        # strictly larger
                        if avg > mark:
                            fv[i] = 1
                        else:
                            fv[i] = 0
                    print fv
                    for p in number_of_windows:
                        fp = []
                        fm = [1] * p
                        for i in range(0, len(fv) - p + 1, 1):
                            if fv[i:i + p] == fm:
                                fp.append(1)
                            else:
                                fp.append(0)
                        print fp
                        score.append(numpy.mean(fp))
            for i in score:
                output.write("{0:5.4f}  ".format(i))
            output.write("\r\n")

        output.close()