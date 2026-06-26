# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * #
# Generates file with solutions to the training instances (MPS format).        #
# Uses Gurobi directly instead of Ecole. Reads MPS files produced by           #
# 01_generate_instances_v2.py and writes results in the same JSON format as    #
# 02_get_instance_solutions.py.                                                 #
# Needs to be run once before training.                                         #
# Usage:                                                                        #
# python 02_get_instance_solutions_v2.py <type> -j <njobs> -n <ninstances>     #
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * #

import glob
import json
import argparse
import threading
import queue

import gurobipy as gp
from gurobipy import GRB


def solve_instance(in_queue, out_queue):
    """
    Worker loop: fetch an MPS instance, solve with Gurobi, record optimal value.

    Parameters
    ----------
    in_queue : queue.Queue
        Input queue from which instance file paths are received.
    out_queue : queue.Queue
        Output queue into which {path: obj_value} dicts are placed.
    """
    while not in_queue.empty():
        instance = in_queue.get()
        try:
            model = gp.read(str(instance))
            model.setParam('OutputFlag', 0)   # suppress Gurobi console output
            model.setParam('LogFile', '')      # suppress log file creation
            model.optimize()
            if model.status == GRB.OPTIMAL:
                solution = model.ObjVal
            else:
                solution = None
        except gp.GurobiError as e:
            print(f'Gurobi error on {instance}: {e}')
            solution = None
        print(f'Solved {instance}  ->  {solution}')
        out_queue.put({str(instance): solution})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'problem',
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
    parser.add_argument(
        '-i', '--instances',
        help='Text file with one instance path per line (overrides directory scan).',
        default=None,
    )
    args = parser.parse_args()

    if args.instances is not None:
        with open(args.instances) as f:
            instances = [line.strip() for line in f if line.strip()]
        import os
        instance_dir = os.path.dirname(os.path.abspath(instances[0]))
        num_inst = min(args.ninst, len(instances))
        orders_queue = queue.Queue()
        answers_queue = queue.Queue()
        for instance in instances[:num_inst]:
            orders_queue.put(instance)
        print(f'{num_inst} instances on queue.')

        workers = []
        for i in range(args.njobs):
            p = threading.Thread(
                    target=solve_instance,
                    args=(orders_queue, answers_queue),
                    daemon=True)
            workers.append(p)
            p.start()

        solutions = {}
        for i in range(num_inst):
            answer = answers_queue.get()
            solutions.update(answer)

        with open(os.path.join(instance_dir, 'instance_solutions.json'), 'w') as f:
            json.dump(solutions, f)

        for p in workers:
            assert not p.is_alive()

        import sys; sys.exit(0)

    # Point to the _mps directories produced by 01_generate_instances_v2.py
    if args.problem == 'setcover':
        instance_dir = 'data/instances/setcover/train_400r_750c_0.05d_mps'
        instances = glob.glob(instance_dir + '/*.mps')
    elif args.problem == 'cauctions':
        instance_dir = 'data/instances/cauctions/train_100_500_mps'
        instances = glob.glob(instance_dir + '/*.mps')
    elif args.problem == 'indset':
        instance_dir = 'data/instances/indset/train_500_4_mps'
        instances = glob.glob(instance_dir + '/*.mps')
    elif args.problem == 'ufacilities':
        instance_dir = 'data/instances/ufacilities/train_35_35_5_mps'
        instances = glob.glob(instance_dir + '/*.mps')
    elif args.problem == 'mknapsack':
        instance_dir = 'data/instances/mknapsack/train_100_6_mps'
        instances = glob.glob(instance_dir + '/*.mps')
    else:
        raise NotImplementedError

    num_inst = min(args.ninst, len(instances))
    orders_queue = queue.Queue()
    answers_queue = queue.Queue()
    for instance in instances[:num_inst]:
        orders_queue.put(instance)
    print(f'{num_inst} instances on queue.')

    workers = []
    for i in range(args.njobs):
        p = threading.Thread(
                target=solve_instance,
                args=(orders_queue, answers_queue),
                daemon=True)
        workers.append(p)
        p.start()

    solutions = {}
    for i in range(num_inst):
        answer = answers_queue.get()
        solutions.update(answer)

    with open(instance_dir + '/instance_solutions.json', 'w') as f:
        json.dump(solutions, f)

    for p in workers:
        assert not p.is_alive()
