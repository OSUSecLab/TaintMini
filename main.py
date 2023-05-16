import json
from taint_mini import taintmini
import argparse
import os


def main():
    parser = argparse.ArgumentParser(prog="taint-mini",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-i", "--input", dest="input", metavar="path", type=str, required=True,
                        help="path of input mini program(s)."
                             "Single mini program directory or index files will both be fine.")
    parser.add_argument("-o", "--output", dest="output", metavar="path", type=str, default="results",
                        help="path of output results."
                             "The output file will be stored outside of the mini program directories.")
    parser.add_argument("-c", "--config", dest="config", metavar="path", type=str,
                        help="path of config file."
                             "See default config file for example. Leave the field empty to include all results.")
    parser.add_argument("-j", "--jobs", dest="workers", metavar="number", type=int, default=None,
                        help="number of workers.")
    parser.add_argument("-b", "--bench", dest="bench", action="store_true",
                        help="enable benchmark data log."
                             "Default: False")

    args = parser.parse_args()
    input_path = args.input
    output_path = args.output
    config_path = args.config
    workers = args.workers
    bench = args.bench

    # test config
    config = None
    if config_path is None:
        # no config given, include all sources and sinks
        config = dict()
    else:
        try:
            config = json.load(open(config_path))
        except FileNotFoundError:
            print(f"[main] error: config not found")
            exit(-1)

    # test input_path
    if os.path.exists(input_path):
        if os.path.isfile(input_path):
            # handle index files
            with open(input_path) as f:
                for i in f.readlines():
                    taintmini.analyze_mini_program(str.strip(i), output_path, config, workers, bench)
        elif os.path.isdir(input_path):
            # handle single mini program
            taintmini.analyze_mini_program(input_path, output_path, config, workers, bench)
    else:
        print(f"[main] error: invalid input path")


if __name__ == "__main__":
    main()
