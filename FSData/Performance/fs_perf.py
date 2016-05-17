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

import csv, os                         # saving as csv, and iterating dir
import xlrd                            # reading in xlsx
import numpy as np                     # calculating RMS
from os import listdir as LD           # iterate through directory
from os.path import splitext as ST     # find the extension of a file

if __name__ == "__main__":
    # ######################################################
    # ##                                                  ##
    # ##                 Variable Settings                ##
    # ##                                                  ##
    # ######################################################
    
    data_folder   = "data"
    input_folder  = "source"
    output_folder = "output"

    # working with pre-formatted data
    # (CKL, CLN, ACT, TMS) = 2, 3, 8, 13
    data_index_list      = [2, 3, 8, 13]
    (T, S, H, A)         = 0, 1, 2, 3
    (CKL, CLN, ACT, TMS) = 0, 1, 2, 3

    # ######################################################
    # ##                                                  ##
    # ##                    Read in Data                  ##
    # ##                                                  ##
    # ######################################################

    error = False

    for filename in LD(input_folder):
        print "Processing file:", filename
        ifname = input_folder + os.sep + filename
        tdname = data_folder + os.sep + 't' + ST(filename)[0] + ".csv"
        ofname = output_folder + os.sep + 'q' + ST(filename)[0] + ".csv"

        workbook  = xlrd.open_workbook(ifname)
        worksheet = workbook.sheet_by_index(0)
        offset    = 1

        trows = []
        for i, row in enumerate(range(worksheet.nrows)):
            if i < offset:  # (Optionally) skip headers
                continue
            r = []
            # for j, col in enumerate(range(worksheet.ncols)):
            #     r.append(worksheet.cell_value(i, j))
            # for j in data_index_list:
            #     r.append(worksheet.cell_value(i, j))
            r.append(worksheet.cell_value(i, data_index_list[CKL]).upper())
            r.append(worksheet.cell_value(i, data_index_list[CLN]))
            r.append(worksheet.cell_value(i, data_index_list[ACT]).lower())
            r.append(worksheet.cell_value(i, data_index_list[TMS]))
            trows.append(r)

        drows = []
        with open(tdname, "rb") as csvfile:
            # lines = file.readlines()
            lines = csv.reader(csvfile, delimiter = ',')
            for line in lines:
                if line[0] == "time":
                    continue
                r = []
                r.append(float(line[T]))
                r.append(float(line[S]) - 270)
                r.append(float(line[H]) - 140)
                r.append(float(line[A]) - 35000)
                drows.append(r)
            csvfile.close()

        # print "trows"
        # for row in trows:
        #     print row
        # print "drows"
        # for row in drows:
        #     print row

        # 1, calibration
        d = []
        (d5, d9)   = 0, 0
        (CL5, CL9) = -1, -1
        for i in range(1, len(trows), 1):
            # ignore the first "start"
            if trows[i][ACT] == "start":
                # if not trows[i - 1][ACT].startswith("end"):
                #     print "ERROR!"
                #     error = True
                #     break
                    # quit()
                if trows[i][CKL] == "CL":
                    if trows[i][CLN] == 5:
                        CL5 = i
                        d5  = trows[i][TMS] - trows[i - 1][TMS]
                        continue
                    elif trows[i][CLN] == 9:
                        CL9 = i
                        d9  = trows[i][TMS] - trows[i - 1][TMS]
                        continue
                d.append(trows[i][TMS] - trows[i - 1][TMS])
        if error:
            error = False
            continue
        d = np.mean(d)
        print "After Process,", d
        d5 -= d
        d9 -= d
        for i in range(CL5, len(trows), 1):
            trows[i][TMS] -= d5
        for i in range(CL9, len(trows), 1):
            trows[i][TMS] -= d9
        # for row in trows:
        #     print row

        with open(ofname, "wb") as csvfile:
            fwriter = csv.writer(csvfile, delimiter=',')
            fwriter.writerow(["stage", "RMS_spd", "RMS_alt", "RMS_heading"])
            (i, j) = 0, 0
            rest = []
            while i < len(trows):
                if trows[i][ACT] == "start":
                    s  = []
                    a  = []
                    h  = []
                    st = trows[i][TMS]
                elif trows[i][ACT].startswith("end"):
                    while j < len(drows):
                        if drows[j][T] < st:
                            rest.append(j)
                        elif drows[j][T] < trows[i][TMS]:
                            s.append(drows[j][S])
                            a.append(drows[j][A])
                            h.append(drows[j][H])
                        else:
                            break
                        j += 1
                    fwriter.writerow([trows[i][CKL] + \
                                      "{:.0f}".format(trows[i][CLN]), \
                                      np.sqrt(np.mean(np.square(s))), \
                                      np.sqrt(np.mean(np.square(a))), \
                                      np.sqrt(np.mean(np.square(h)))])
                i += 1
            while j < len(drows):
                rest.append(j)
                j += 1
            s = []
            a = []
            h = []
            for r in rest:
                s.append(drows[r][S])
                a.append(drows[r][A])
                h.append(drows[r][H])
            fwriter.writerow(["REST", \
                              np.sqrt(np.mean(np.square(s))), \
                              np.sqrt(np.mean(np.square(a))), \
                              np.sqrt(np.mean(np.square(h)))])
            csvfile.close()
