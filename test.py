import glob
import json
import sys
import argparse
import threading
import queue
import ecole


if __name__ == '__main__':


    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p',
        default='mknapsack',
        help='MILP instance type to process.',
        choices=['setcover', 'cauctions', 'ufacilities', 'indset', 'mknapsack'],
    )

    parser.add_argument(
        '-j', '--njobs',
        help='Number of parallel jobs.',
        type=int,
        default=1,
    )

    parser.add_argument(
        '-n', '--ninst',
        help='Number of instances to solve.',
        type=int,
        default=10000,
    )
    args = parser.parse_args()
    
    print(vars(args))
    