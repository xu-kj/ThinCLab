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
    dss               = ["FOC", "NVP", "BAS"] # name of the XML files
    threshold_factor  = 0.25                  # only one value in this script

    # ######################################################
    # ##                                                  ##
    # ##                Processing BAS data               ##
    # ##                                                  ##
    # ######################################################
    with open("BAS.xml", "r") as file:
        bas    = ET.fromstring(file.read())
        bd_d   = {}
        bd_p   = {}
        bas_pl = []
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

        fx  = {}
        # iterating through all the fixation data
        for row in rows[1:]:
            aoiname  = row.findall(cell_tag)[AOI].find(data_tag).text
            starttme = float(row.findall(cell_tag)[TMES].find(data_tag).text)
            if aoiname != p_mode:
                duration = numpy.nan
            else:
                duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            fx[starttme] = duration
        fx = OD(sorted(fx.items()))

        fp = []
        dwell = False
        for t, f in fx.iteritems():
            if len(fp) == 0:
                if math.isnan(f):
                    continue
                else:
                    fp.append(f)
                    dwell = True
            else:
                if dwell:
                    if math.isnan(f):
                        dwell = False
                    else:
                        fp[len(fp) - 1] += f
                elif not math.isnan(f):
                    fp.append(f)
                    dwell = True
        bd_d[seq] = {
            "avg": numpy.mean(fp),
            "std": numpy.std(fp, ddof = 1)
        }

        fx  = {}
        # iterating through all the fixation data
        for row in rows[1:]:
            aoiname  = row.findall(cell_tag)[AOI].find(data_tag).text
            starttme = float(row.findall(cell_tag)[TMES].find(data_tag).text)
            duration = float(row.findall(cell_tag)[DUR].find(data_tag).text)
            if aoiname != p_mode:
                fx[starttme] = - duration
            else:
                fx[starttme] = duration

        fx = OD(sorted(fx.items()))
        # bd_p[seq] = {}
        for iv in windows:
            fp = []
            for t, f in fx.iteritems():
                if f  > 0:
                    et = t + f
                else:
                    et = t - f
                g1 = int(t / iv)
                g2 = int(et / iv)
                while g2 >= len(fp):
                    fp.append([])
                for i in range(g1, g2 + 1, 1):
                    if f > 0:
                        fp[i].append(1)
                    else:
                        fp[i].append(0)
            for i in range(len(fp)):
                if len(fp[i]) == 0:
                    fp[i] = 0
                else:
                    fp[i] = numpy.mean(fp[i])

            bd_p[seq] = {
                "avg": numpy.mean(fp),
                "std": numpy.std(fp, ddof = 1)
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
                timestamp = starttme - 60
                if aoiname != p_mode:
                    dur = - float(row.findall(cell_tag)[DUR].find(data_tag).text)
                else:
                    dur = float(row.findall(cell_tag)[DUR].find(data_tag).text)
                focdir[seq]["dra"][timestamp] = dur
                if timestamp > max_time:
                    max_time = timestamp

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
        for iv in windows:
            for s in speed:
                s = iv * s
                for p in number_of_windows:
                    output.write("{:3.1f}s{:1.0f}p  ".format(s, p))
        output.write("\r\n")
        output.write('-' * 78 + "\r\n")

        for par in pl:
            output.write("# Participant " + "{:2.0f}".format(par) + " |  ")
            score = []
            mark_d = bd_d[par]["avg"] + bd_d[par]["std"] * threshold_factor
            mark_p = bd_p[par]["avg"] + bd_p[par]["avg"] * threshold_factor
            print "par: #" + str(par), mark_d, mark_p
            for iv in windows:
                for ss in speed:
                    ss = iv * ss
                    ts = focdir[par]["ts"][iv][ss]
                    fv = []
                    for i in range(0, len(ts)):
                        fv.append([numpy.nan])
                    for t, f in focdir[par]["dra"].iteritems():
                        if f < 0:
                            et = t - f
                        else:
                            et = t + f
                        cntr = 0
                        for s, e in ts.iteritems():
                            if t < s:
                                if f < 0:
                                    pass
                                elif et < s:
                                    break
                                elif et < e:
                                    if math.isnan(fv[cntr][len(fv[cntr]) - 1]):
                                        fv[cntr][len(fv[cntr]) - 1] = et - s
                                    else:
                                        fv[cntr][len(fv[cntr]) - 1] += et - s
                                else:
                                    fv[cntr] = [iv]
                            elif t >= e:
                                # wait for the next group
                                pass
                            else:
                                if f < 0:
                                    if math.isnan(fv[cntr][len(fv[cntr]) - 1]):
                                        pass
                                    else:
                                        fv[cntr].append(numpy.nan)
                                else:
                                    if et < e:
                                        if math.isnan(fv[cntr][len(fv[cntr]) - 1]):
                                            fv[cntr][len(fv[cntr]) - 1] = f
                                        else:
                                            fv[cntr][len(fv[cntr]) - 1] += f
                                    else:
                                        if math.isnan(fv[cntr][len(fv[cntr]) - 1]):
                                            fv[cntr][len(fv[cntr]) - 1] = e - t
                                        else:
                                            fv[cntr][len(fv[cntr]) - 1] += e - t
                            cntr += 1
                    print "dwell duration array"
                    for v in fv:
                        print v
                    for i in range(len(fv)):
                        if len(fv[i]) == 0:
                            avg = 0
                        else:
                            avg = numpy.nanmean(fv[i])
                            if math.isnan(avg):
                                avg = 0
                        print avg, fv[i]
                        # strictly larger
                        if avg > mark_d:
                            fv[i] = 1
                        else:
                            fv[i] = 0
                    print fv

                    fv2 = []
                    for i in range(0, len(ts)):
                        fv2.append([])
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
                                        fv2[cntr].append(0)
                                    else:
                                        fv2[cntr].append(1)
                                else:
                                    fv2[cntr].append(iv)
                                    # quit()
                            elif t >= e:
                                # wait for the next group
                                pass
                            else:
                                if f < 0:
                                    fv2[cntr].append(0)
                                else:
                                    fv2[cntr].append(1)
                            cntr += 1

                    print "dwell percentage array"
                    for v in fv2:
                        print v

                    for i in range(len(fv2)):
                        if len(fv2[i]) == 0:
                            avg = 0
                        else:
                            avg = numpy.mean(fv2[i])
                            if math.isnan(avg):
                                avg = 0
                        print avg, fv2[i]
                        # strictly larger
                        if avg > mark_p:
                            fv[i] = 1
                        else:
                            pass
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