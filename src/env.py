import random
import gym

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# from tqdm import tqdm
from gym import spaces
from src.simulation import APL_process


class StockTradingEnv(gym.Env):
    """Environment for agent, consists of __init__, step, and reset functions"""

    def __init__(self, reset_path=False, data_type="mixed"):
        self.asset_price = pd.read_csv(f"data/asset_price_{data_type}_sim.csv").values
        self.option_price = pd.read_csv(f"data/option_price_{data_type}_sim.csv").values
        self.nPaths = self.option_price.shape[0]
        self.nSteps = self.option_price.shape[1]
    
        # user-defined options (path)
        self.reset_path = reset_path
        self.path_choice = int(random.uniform(0, self.nPaths))
        self.path_idx = self.path_choice

        # user-defined options (rewards)
        self.reward_func = APL_process
        self.kappa = 0.0001
        
        # initializing underlying amount
        self.holdings = 0
        self.curr_step = 0

        # Actions of the format hold amount [0,1]
        self.action_space = spaces.Box(low=-1, high=1, dtype=np.float16)

        # agent is given previous action + current asset price and time to maturity (H_i-1, S_i, tau_i)
        self.observation_space = spaces.Box(
            low=np.array([-1, 0, 0]),
            high=np.array([1, np.inf, self.nSteps]),
            shape=(3,),
            dtype=np.float16,
        )

    def step(self, action: float):
        # Execute one time step within the environment
        self.curr_step += 1

        # next call price, call price now, next asset price, asset price now.
        c_next, c_now, s_next, s_now = (
            self.option_price[self.path_idx, self.curr_step],
            self.option_price[self.path_idx, self.curr_step - 1],
            self.asset_price[self.path_idx, self.curr_step],
            self.asset_price[self.path_idx, self.curr_step - 1],
        )

        # R_{t} is Acc PnL 
        reward = (
            c_next
            - c_now
            + self.holdings * (s_next - s_now)
            - self.kappa * np.abs(s_next * action)
        )

        # A_{t}: update the holding info.
        self.holdings += action

        # S_{t+1}: previous action, current asset price and time to maturity (H_i-1, S_i, tau_i)
        next_state = [
            self.holdings,
            s_next,
            self.nSteps - self.curr_step,
        ]
        # done: whether the episode is ended or not
        done = True if self.curr_step + 1 >= self.nSteps else False
        return next_state, reward, done

    def reset(self):
        if self.reset_path:  # if user chose True, sets to his choice, else, random
            self.path_idx = self.path_choice

        # when resetting the env, set current_step and previous holdings equal to 0.
        self.curr_step = 0
        self.holdings = 0
        return [
            self.holdings,
            self.asset_price[self.path_idx, self.curr_step],
            self.nSteps,
          ]  # state0 of new path
