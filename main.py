import sys
import time
import os

from fingerprint import Fingerprint
from algo import replay_scenario, analyse_scenario_result, ml_based, generate_replay_sequence
from algo import simple_eckersley, rule_based, split_data, optimize_lambda, train_ml
from algo import benchmark_parallel_f_ml, benchmark_parallel_f_rules, parallel_pipe_task_ml_f, parallel_pipe_task_rules_f

# from algoLSTM import replay_scenario, analyse_scenario_result, ml_based, generate_replay_sequence
# from algoLSTM import simple_eckersley, rule_based, split_data, optimize_lambda, train_ml
# from algoLSTM import benchmark_parallel_f_ml, benchmark_parallel_f_rules, parallel_pipe_task_ml_f, parallel_pipe_task_rules_f

from utils import get_consistent_ids, get_fingerprints_experiments
import MySQLdb as mdb

CONSISTENT_IDS = "getids"
REPLAY_ECKERSLEY = "replayeck"
AUTOMATE_REPLAYS = "auto"
RULE_BASED = "rules"
ML_BASED = "ml"
AUTOMATE_ML = "automl"

ALGO_NAME_TO_FUNCTION = {
    "eckersley": simple_eckersley,
    "rulebased": rule_based,
}

def main(argv):
    startTime = time.time()
    con = mdb.connect('localhost', 'root', '!bigbang', 'amiunique')
    cur = con.cursor(mdb.cursors.DictCursor)

    if argv[0] == CONSISTENT_IDS:
        print("Fetching consistent user ids.")
        user_id_consistent = get_consistent_ids(cur)
        with open("./data/consistent_extension_ids.csv", "w") as f:
            f.write("user_id\n")   ##字段名
            for user_id in user_id_consistent:  ##共1455个id
                f.write(user_id+"\n")
    elif argv[0] == AUTOMATE_REPLAYS:  #eckersley/rule_based
        exp_name = argv[1] #
        algo_matching_name = argv[2]  #eckersley/rule_based
        nb_min_fingerprints = int(argv[3])  #6
        exp_name += "-%s-%d" % (algo_matching_name, nb_min_fingerprints)

        attributes = Fingerprint.INFO_ATTRIBUTES + Fingerprint.HTTP_ATTRIBUTES + \
                     Fingerprint.JAVASCRIPT_ATTRIBUTES + Fingerprint.FLASH_ATTRIBUTES

        algo_matching = ALGO_NAME_TO_FUNCTION[algo_matching_name]

        print("Begin automation of scenarios")
        print("Start fetching fingerprints...")
        fingerprint_dataset = get_fingerprints_experiments(cur, nb_min_fingerprints, attributes)
        # 40% train set
        train_data, test_data = split_data(0.40, fingerprint_dataset)
        print("Fetched %d fingerprints." % len(fingerprint_dataset))
        # we iterate on different values of visit_frequency
        visit_frequencies = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        for visit_frequency in visit_frequencies:
            result_scenario = replay_scenario(test_data, visit_frequency,
                                              algo_matching,
                                              filename="./results/"+exp_name+"_"+str(visit_frequency)+"scenario_replay_result.csv")
            analyse_scenario_result(result_scenario, test_data,
                                    fileres1="./results/"+exp_name+"_"+str(visit_frequency)+"-res1.csv",
                                    fileres2="./results/"+exp_name+"_"+str(visit_frequency)+"-res2.csv",
                                   )
    elif argv[0] == AUTOMATE_ML:  #machine learning
        print("Start automating ml based scenario")
        exp_name = argv[1]
        algo_matching_name = "hybridalgo"
        nb_min_fingerprints = int(argv[2])
        exp_name += "-%s-%d" % (algo_matching_name, nb_min_fingerprints)

        attributes = Fingerprint.INFO_ATTRIBUTES + Fingerprint.HTTP_ATTRIBUTES + \
                     Fingerprint.JAVASCRIPT_ATTRIBUTES + Fingerprint.FLASH_ATTRIBUTES

        print("Begin automation of scenarios")
        print("Start fetching fingerprints...")
        fingerprint_dataset = get_fingerprints_experiments(cur, nb_min_fingerprints, attributes)
        print("Fetched %d fingerprints." % len(fingerprint_dataset))
        train_data, test_data = split_data(0.40, fingerprint_dataset)
        model = train_ml(fingerprint_dataset, train_data, load=True)
        # we iterate on different values of visit_frequency
        visit_frequencies = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        for visit_frequency in visit_frequencies:
            result_scenario = replay_scenario(test_data, visit_frequency,
                                              ml_based,
                                              filename="./results/"+exp_name+"_"+str(visit_frequency)+"scenario_replay_result.csv",
                                              model=model, lambda_threshold=0.999)
            analyse_scenario_result(result_scenario, test_data,
                                    fileres1="./results/"+exp_name+"_"+str(visit_frequency)+"-res1.csv",
                                    fileres2="./results/"+exp_name+"_"+str(visit_frequency)+"-res2.csv",
                                   )
    elif argv[0] == "lambda":
        attributes = Fingerprint.INFO_ATTRIBUTES + Fingerprint.HTTP_ATTRIBUTES + \
                     Fingerprint.JAVASCRIPT_ATTRIBUTES + Fingerprint.FLASH_ATTRIBUTES

        nb_min_fingerprints = 6
        print("Start fetching fingerprints...")
        fingerprint_dataset = get_fingerprints_experiments(cur, nb_min_fingerprints, attributes)
        print("Fetched %d fingerprints." % len(fingerprint_dataset))
        train_data, test_data = split_data(0.4, fingerprint_dataset)
        optimize_lambda(fingerprint_dataset, train_data, test_data)
    elif argv[0] == "automlbench":
        prefix_files = argv[1]
        nb_cores = int(argv[2])
        nb_processes = [1, 2, 4, 8]
        nb_fingerprints = [5000, 10000, 15000]
        fn = parallel_pipe_task_ml_f
        with open("./benchres/%s.csv" % prefix_files, "w")as f:
            f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %
                    ("nb_fingerprints",
                     "nb_cores",
                     "nb_processes",
                     "avg",
                     "max",
                     "min",
                     "median",
                     "q1",
                     "q3")
                    )
            for nb_fingerprint in nb_fingerprints:
                for nb_process in nb_processes:
                    mean, min, max, p25, p50, p75 = benchmark_parallel_f_ml(fn, cur, nb_fingerprint, nb_process)
                    f.write("%d,%d,%d,%f,%f,%f,%f,%f,%f\n" % (
                        nb_fingerprint,
                        nb_cores,
                        nb_process,
                        mean,
                        max,
                        min,
                        p50,
                        p25,
                        p75
                    ))
    elif argv[0] == "autorulesbench":
        prefix_files = argv[1]
        nb_cores = int(argv[2])
        nb_processes = [1, 2, 4, 8]
        nb_fingerprints = [5000, 10000, 15000]
        fn = parallel_pipe_task_rules_f
        with open("./benchres/%s.csv" % prefix_files, "w")as f:
            f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %
                    ("nb_fingerprints",
                     "nb_cores",
                     "nb_processes",
                     "avg",
                     "max",
                     "min",
                     "median",
                     "q1",
                     "q3")
                    )
            for nb_fingerprint in nb_fingerprints:
                for nb_process in nb_processes:
                    mean, min, max, p25, p50, p75 = benchmark_parallel_f_rules(fn, cur, nb_fingerprint, nb_process)
                    f.write("%d,%d,%d,%f,%f,%f,%f,%f,%f\n" % (
                        nb_fingerprint,
                        nb_cores,
                        nb_process,
                        mean,
                        max,
                        min,
                        p50,
                        p25,
                        p75
                    ))
    endTime = time.time()
    executeTime = endTime - startTime
    with open("analyse/timerecord.txt","a") as f:
        f.write("%s(test):\n" % argv[1])
        f.write("start: %s\n" % startTime)
        f.write("end: %s\n" % endTime)
        f.write("execute: %s\n" % executeTime)
if __name__ == "__main__":
    main(sys.argv[1:])
