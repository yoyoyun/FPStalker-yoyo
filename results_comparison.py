import os
import re

def avg_max_time_func(csv_file):
    flag = int(csv_file.split("_")[-1].split("-")[0])
    all_time = []
    i = 0
    with open(csv_file, 'r') as f:
        for line in f:
            if i == 0:
                i += 1
                continue
            max_chain = int(line.strip('\n').split(',')[-1])
            max_time = (max_chain-1) * flag
            all_time.append(max_time)
            i += 1
    return sum(all_time)/ float(len(all_time))

def avg_id_func(csv_file):
    flag = int(csv_file.split("_")[-1].split("-")[0])
    all_time = []
    i = 0
    with open(csv_file, 'r') as f:
        for line in f:
            if i == 0:
                i += 1
                continue
            nb_id = float(line.strip('\n').split(',')[1])
            all_time.append(nb_id)
            i += 1
    return sum(all_time)/ float(len(all_time))

def avg_track_duration_func(csv_file):
    flag = int(csv_file.split("_")[-1].split("-")[0])
    all_time = []
    i = 0
    with open(csv_file, 'r') as f:
        for line in f:
            if i == 0:
                i += 1
                continue
            nb_original_fp = int(line.strip('\n').split(',')[2])
            nb_assigned_ids = int(line.strip('\n').split(',')[1])
            avg_tracking_duration = ((nb_original_fp - nb_assigned_ids)/nb_assigned_ids)*flag
            all_time.append(avg_tracking_duration)
            i += 1
    return sum(all_time)/ float(len(all_time))

def ownership_func(csv_file):
    flag = int(csv_file.split("_")[-1].split("-")[0])
    all_time = []
    i = 0
    with open(csv_file, 'r') as f:
        for line in f:
            if i == 0:
                i += 1
                continue
            ownership = float(line.strip('\n').split(',')[3])
            all_time.append(ownership)
            i += 1
    return sum(all_time)/ float(len(all_time))

def getFileList(dir, pattern):
    files = os.listdir(dir)

    files = [ff for ff in files if re.match(pattern, ff)]
    files = { int(re.findall(r'_(\d+)\-',ff)[0]):ff for ff in files}
    return files

patterns1 = [r'bidiLSTM-hybridalgo\-6_[\d]+\-res1',
            r'LSTM-hybridalgo\-6_[\d]+\-res1',
            r'myexpname-hybridalgo\-6_[\d]+\-res1',
            r'myexpname-rulebased\-6_[\d]+\-res1',
            r'myexpname-eckersley\-6_[\d]+\-res1']

patterns2 = [r'bidiLSTM-hybridalgo\-6_[\d]+\-res2',
             r'LSTM-hybridalgo\-6_[\d]+\-res2',
             r'myexpname-hybridalgo\-6_[\d]+\-res2',
             r'myexpname-rulebased\-6_[\d]+\-res2',
             r'myexpname-eckersley\-6_[\d]+\-res2']


for value in patterns1:
    name = re.search(r'[a-zA-Z]+-[a-zA-Z]+', value)
    csvs = getFileList('results', value)
    avg_max_time_log = {}
    avg_id_log = {}
    for interval, cf in csvs.items():
        log1 = avg_max_time_func('results/%s' % cf)
        avg_max_time_log[interval] = log1
        log2 = avg_id_func('results/%s'%cf)
        avg_id_log[interval] = log2
    avg_max_time = sorted(avg_max_time_log.items(), key=lambda k:k[0], reverse=False)
    print("avg_max_time:")
    print(avg_max_time)
    avg_id = sorted(avg_id_log.items(), key=lambda k:k[0], reverse=False)
    print("avg_id:")
    print(avg_id)
    with open("analyse/analysis_avg_max_time.csv", "a") as f1:
        f1.write("\n%s\n" % name.group(0))
        for i in avg_max_time:
            f1.write("%s\n" % i[1])
    with open("analyse/analysis_avg_id.csv", "a") as f2:
        f2.write("\n%s\n" % name.group(0))
        for i in avg_id:
            f2.write("%s\n" % i[1])

for value in patterns2:
    name = re.search(r'[a-zA-Z]+-[a-zA-Z]+', value)
    csvs = getFileList('results', value)
    avg_track_duration_log = {}
    ownership_log = {}
    for interval, cf in csvs.items():
        log3 = avg_track_duration_func('results/%s'%cf)
        avg_track_duration_log[interval] = log3
        log4 = ownership_func('results/%s'%cf)
        ownership_log[interval] = log4
    avg_track_duration = sorted(avg_track_duration_log.items(), key=lambda k:k[0], reverse=False)
    print("avg_track_duration:")
    print(avg_track_duration)
    ownership = sorted(ownership_log.items(), key=lambda k:k[0], reverse=False)
    print("ownership:")
    print(ownership)
    with open("analyse/analysis_avg_track_duration.csv", "a") as f3:
        f3.write("\n%s\n" % name.group(0))
        for i in avg_track_duration:
            f3.write("%s\n" % i[1])
    with open("analyse/analysis_ownership.csv", "a") as f4:
        f4.write("\n%s\n" % name.group(0))
        for i in ownership:
            f4.write("%s\n" % i[1])
