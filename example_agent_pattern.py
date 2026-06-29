"""
Simple standalone demo of the multi-agent + shared-policy pattern used in agent.py.

Scenario
--------
We have 30 "jobs" (plain integers).  Each job needs the shared Policy to pick
an action for it (here: Policy just squares the number, simulating a neural net).
12 Agent threads process jobs in parallel.  A single PolicySampler thread
batches all pending policy requests and answers them together so the "GPU call"
(here: a print statement + arithmetic) is done once per batch, not 12 times.

Run:
    python example_agent_pattern.py
"""

import threading
import queue
import time
import random


# ---------------------------------------------------------------------------
# The "Policy" (stands in for the GNN / Brain in the real code)
# ---------------------------------------------------------------------------
class Policy:
    def evaluate(self, states):
        """
        Given a list of states (integers here), return one action per state.
        In the real code this is a GPU forward pass through a neural network.
        Here we just square each number.
        """
        print(f"  [Policy] evaluating batch of {len(states)} states: {states}")
        time.sleep(0.05)                       # pretend GPU work takes time
        return [s ** 2 for s in states]        # action = state^2


# ---------------------------------------------------------------------------
# PolicySampler thread  (one thread, shared by all agents)
# ---------------------------------------------------------------------------
class PolicySampler(threading.Thread):
    """
    Sits in a loop waiting for policy requests from agents.
    Collects every request currently in the queue into one batch,
    calls policy.evaluate() once, then sends each answer back.
    """
    def __init__(self, policy, requests_queue):
        super().__init__(name="PolicySampler", daemon=True)
        self.policy = policy
        self.requests_queue = requests_queue

    def run(self):
        while True:
            # Block until at least one request arrives
            requests = []
            req = self.requests_queue.get()

            # Stopping signal: None in the queue
            if req is None:
                self.requests_queue.task_done()
                break

            requests.append(req)

            # Drain any further requests that are already waiting (no block)
            while True:
                try:
                    req = self.requests_queue.get(block=False)
                    if req is None:
                        self.requests_queue.task_done()
                        return          # stop signal arrived mid-drain
                    requests.append(req)
                except queue.Empty:
                    break

            # One batched call to the policy for all waiting agents
            states  = [r['state']    for r in requests]
            actions = self.policy.evaluate(states)

            # Send each agent its answer via its private reply queue
            for r, action in zip(requests, actions):
                r['reply_queue'].put(action)
                self.requests_queue.task_done()


# ---------------------------------------------------------------------------
# Agent thread  (12 of these run in parallel)
# ---------------------------------------------------------------------------
class Agent(threading.Thread):
    def __init__(self, name, jobs_queue, policy_requests_queue):
        super().__init__(name=name, daemon=True)
        self.jobs_queue          = jobs_queue
        self.policy_requests_queue = policy_requests_queue
        self.reply_queue         = queue.Queue()  # private: only this agent reads it

    def run(self):
        while True:
            # Pick up a job_sponsor reference (stopping signal = None)
            job_sponsor = self.jobs_queue.get()
            if job_sponsor is None:
                self.jobs_queue.task_done()
                break

            # Pull the actual task dict from the job_sponsor
            task = job_sponsor.get()

            number       = task['number']
            results      = task['results']       # shared list for this job
            policy_gate  = task['policy_gate']   # threading.Event (the "block_policy" gate)

            # --- simulate some preprocessing work ---
            state = number * 3
            time.sleep(random.uniform(0.01, 0.05))   # pretend SCIP loading time

            # Wait here if the gate is closed (block_policy=True scenario)
            policy_gate.wait()

            # Ask the shared policy for an action
            self.policy_requests_queue.put({'state': state, 'reply_queue': self.reply_queue})
            action = self.reply_queue.get()

            result = {'number': number, 'state': state, 'action': action,
                      'worker': self.name}
            results.append(result)
            print(f"  [{self.name}] job {number}: state={state}, action={action}")

            # Signal completion on both queues
            job_sponsor.task_done()
            self.jobs_queue.task_done()


# ---------------------------------------------------------------------------
# AgentPool  (manages all threads, mirrors AgentPool in agent.py)
# ---------------------------------------------------------------------------
class AgentPool:
    def __init__(self, policy, n_agents=12):
        self.jobs_queue            = queue.Queue()
        self.policy_requests_queue = queue.Queue()
        self.policy_sampler = PolicySampler(policy, self.policy_requests_queue)
        self.agents = [Agent(f"Agent-{i}", self.jobs_queue, self.policy_requests_queue)
                       for i in range(n_agents)]

    def start(self):
        self.policy_sampler.start()
        for a in self.agents:
            a.start()

    def close(self):
        for _ in self.agents:
            self.jobs_queue.put(None)
        self.jobs_queue.join()
        self.policy_requests_queue.put(None)
        self.policy_requests_queue.join()

    def start_job(self, numbers, block_policy=False):
        """
        Submit a list of numbers as a job.
        Returns (results_list, job_sponsor, policy_gate).
        Call policy_gate.set() later if block_policy=True.
        """
        job_sponsor = queue.Queue()
        results     = []

        policy_gate = threading.Event()
        if not block_policy:
            policy_gate.set()           # gate open immediately

        for number in numbers:
            task = {'number': number, 'results': results, 'policy_gate': policy_gate}
            job_sponsor.put(task)
            self.jobs_queue.put(job_sponsor)

        return results, job_sponsor, policy_gate


# ---------------------------------------------------------------------------
# Main: run two jobs (like training + validation in the real code)
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    policy    = Policy()
    pool      = AgentPool(policy, n_agents=12)
    pool.start()

    # --- Job A: submit with gate CLOSED (block_policy=True) ---
    # Agents load their tasks but pause before querying the policy.
    print("\n=== Submitting Job A (gate closed) ===")
    job_a_numbers = list(range(1, 16))   # 15 tasks
    results_a, sponsor_a, gate_a = pool.start_job(job_a_numbers, block_policy=True)

    # Do something else while agents are pre-loading (simulate GPU update)
    print("  [Main] doing other work while agents are paused at the gate...")
    time.sleep(0.3)

    # Now open the gate — all agents that reached policy_gate.wait() proceed
    print("  [Main] opening gate for Job A")
    gate_a.set()
    sponsor_a.join()      # wait for all 15 tasks to finish
    print(f"  [Main] Job A done. {len(results_a)} results collected.")

    # --- Job B: submit with gate OPEN (block_policy=False, the normal case) ---
    print("\n=== Submitting Job B (gate open) ===")
    job_b_numbers = list(range(16, 31))  # another 15 tasks
    results_b, sponsor_b, gate_b = pool.start_job(job_b_numbers, block_policy=False)
    sponsor_b.join()
    print(f"  [Main] Job B done. {len(results_b)} results collected.")

    pool.close()

    # Show a sample of results
    print("\n--- Sample results from Job A ---")
    for r in sorted(results_a, key=lambda x: x['number'])[:5]:
        print(f"  number={r['number']}, state={r['state']}, action={r['action']}, by {r['worker']}")

    print("\n--- Sample results from Job B ---")
    for r in sorted(results_b, key=lambda x: x['number'])[:5]:
        print(f"  number={r['number']}, state={r['state']}, action={r['action']}, by {r['worker']}")
