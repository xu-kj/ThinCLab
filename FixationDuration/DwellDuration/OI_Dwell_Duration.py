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
    TMES_tag = "starttime"
    DUR_tag  = "duration"
    p_mode   = "PUMP"

    # Interval Values to be Tested (in seconds)
    windows = [5, 10, 15, 20, 25, 30, 45, 60, 75, 90, 180] # length of window

    # Test Data Set
    dss               = ["NVP", "BAS", "FOC"]              # name of XML files
    threshold_factors = [0, 0.1, 0.125, 0.25, 0.5, 1]      # list of thresholds

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
        bas_data[seq] = {}

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

        bas_data[seq] = {
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
                mt = int(max_time / iv)
                for i in range(0, mt + 1, 1):
                    if (i * iv + iv) > max_time:
                        focdir[seq]["ts"][iv][i * iv] = max_time
                    else:
                        focdir[seq]["ts"][iv][i * iv] = i * iv + iv
                focdir[seq]["ts"][iv] = OD(sorted(focdir[seq]["ts"][iv].items()))

        # ######################################################
        # ##                                                  ##
        # ##                Calculate Hit Rate                ##
        # ##                                                  ##
        # ######################################################
        pl = intersect(bas_pl, foc_pl)
        for sd in threshold_factors:
            output_filename = "Test on " + ds + "_Avg + " + str(sd) + " Stdv.txt"
            output = open(output_filename, "wb")
            output.write(' ' * 20)
            for iv in windows:
                output.write("{:4.0f}  ".format(iv))
            output.write("\r\n")
            output.write('-' * 78 + "\r\n")

            for par in pl:
                output.write("# Participant " + "{:2.0f}".format(par) + " |  ")
                mark  = bas_data[par]["avg"] + bas_data[par]["std"] * sd
                score = []
                print "par: #" + str(par)

                for iv in windows:
                    # mark = bas_data[par][iv]["avg"] + bas_data[par][iv]["std"] * sd
                    # print iv, mark, bas_data[par][iv]["avg"], bas_data[par][iv]["std"]
                    print iv
                    fv = []
                    ts = focdir[par]["ts"][iv]
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
                    print fv

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
                    score.append(numpy.mean(fv))
                for i in score:
                    output.write("{0:3.2f}  ".format(i))
                output.write("\r\n")
                print ""

            output.close()