# -*- coding: utf-8 -*-
"""
Created on Thu May 27 12:19:45 2021

@author: xuziang
"""

from simulation_2 import simulation
import opyplus as op 
import numpy as np
import pandas as pd
from numpy import genfromtxt
#import matplotlib.pyplot as plt
import threading
import time 

# prepare Energy+ models for threads
def pre_dirs(all_dir, idfname, epwfile, eplus):
    threads = ['thread' + str(i) for i in range(1, 15)]
    dirs = {}
    dirs['idfname'] = {}
    dirs['epwfile'] = {}
    dirs['eplus'] = {}
    dirs['epm'] = {}
    dirs['S'] = {}
    
    for i in range(1, 15):
        dirs['idfname'][i] = all_dir + "/" + threads[i-1] + idfname
        dirs['epwfile'][i] = all_dir + "/" + threads[i-1] + epwfile 
        dirs["eplus"][i] = all_dir + "/" + threads[i-1] + eplus
        dirs['epm'][i] = op.Epm().load(dirs['idfname'][i])
        dirs['S'][i] = simulation(dirs["epm"][i], dirs["epwfile"][i], dirs["eplus"][i])
    return dirs 

# thread that takes charge of gradient computation
class training_thread(threading.Thread):
   def __init__(self, parameterID, S, indexs, pre_error, gradients, dt, actual, parametersRange):
      threading.Thread.__init__(self)
      self.parameterID = parameterID
      self.S = S
      self.indexs = indexs
      self.pre_error = pre_error
      self.gradients = gradients
      self.dt = dt
      self.actual = actual
      self.parametersRange = parametersRange
      
   def run(self):
      self.multi_sim()
      
   def multi_sim(self): 
        self.S.par_learn(self.parameterID, self.dt) # make theta := theta + dt
        status, temp_yc = self.S.simulate()
        new_error = self.S.MSE(self.actual[self.indexs], temp_yc[self.indexs])
        # print('new_error:', new_error)
        self.gradients[self.parameterID] = (new_error - self.pre_error) / (self.parametersRange[self.parameterID]*self.dt)
        self.S.par_rec(self.parameterID, self.dt) # recover theta, thta := theta - dt

# thread that takes charge of line search
class searching_thread (threading.Thread):
   def __init__(self, t,  S, epoch, indexs, beta, steps, actual, used_thetas, delta_parameters):
      threading.Thread.__init__(self)
      self.t = t
      self.S = S
      self.epoch = epoch 
      self.indexs = indexs
      self.beta = beta
      self.steps = steps
      self.actual = actual
      self.used_thetas = used_thetas
      self.delta_parameters = delta_parameters
      
   def run(self):
      self.multi_sim()
      
   def multi_sim(self): 
        alpha = self.beta**self.t
        for i in self.used_thetas:
            self.S.par_update(i, self.delta_parameters[i], alpha) # make theta := theta - alpha*delta_theta, it is different with S.par_learn
        _, temp_yc = self.S.simulate()
        temp_yc = np.array(temp_yc)
        self.steps[self.t] = self.S.MSE(self.actual[self.indexs], temp_yc[self.indexs])
        for i in self.used_thetas:
            self.S.par_rec(i, -1*alpha*self.delta_parameters[i]) # recover theta

# initlize calibration parameters
def initialize(all_dir, S, dirs, key, changeschedule=False):
    if key == 'init1':
        init_pars = pd.read_csv(all_dir + '/init_3357.csv', header=None)
    elif key == 'LHS':
        init_pars = pd.read_csv(all_dir + '/LHS_init.csv', header=None)
    else:
        print('wrong initial key')
        return 
    par = {}
    for i in range(1,15):
        par[i] = init_pars[0][i-1]
    
    S.par_assign(par)
    
    if changeschedule:
        S.changeschedule()
    for i in range(1,15):
        dirs['S'][i].par_assign(par)
        if changeschedule:
            dirs['S'][i].changeschedule()
    return 

# split train/test in orignal setting
def split_dataset(s, ratio, season=False):
    np.random.seed(s)
    global_train = []
    summer_train = []
    winter_train = []
    
    global_test = []
    summer_test = []
    winter_test = []
    
    for i in range(8760):
        seed = np.random.rand()
        if seed < ratio:
            global_train.append(i)
            if season:
                if i >= 1416 and i < 8016:
                    summer_train.append(i)
                if i <= 2880 or i < 8761 and i >= 7296:
                    winter_train.append(i)
        else:
            global_test.append(i)
            if season:
                if i >= 1416 and i < 8016:
                    summer_test.append(i)
                if i <= 2880 or i < 8761 and i >= 7296:
                    winter_test.append(i)
    if season:
        train = {'global':global_train, 'summer':summer_train, 'winter':winter_train}
        test = {'global':global_test, 'summer':summer_test, 'winter':winter_test}
        return train, test
    else:
        return global_train, global_test
    
# split train/test for the case of that summer(5~9) and winter(11~3) are not overlapped
def split_dataset_uniformschedule(s, ratio):
    np.random.seed(s)
    global_train = []
    summer_train = []
    winter_train = []
    
    global_test = []
    summer_test = []
    winter_test = []
    
    for i in range(8760):
        seed = np.random.rand()
        if seed < ratio:
            global_train.append(i)
            if i >= 2880 and i < 6552:  #from May to Sep
                summer_train.append(i)
            if i <= 2160 or i < 8761 and i >= 7296:  # from Nov to Mar
                winter_train.append(i)
        else:
            global_test.append(i)
            if i >= 2880 and i < 6552:
                summer_test.append(i)
            if i <= 2160 or i < 8761 and i >= 7296:
                winter_test.append(i)
    
    train = {'global':global_train, 'summer':summer_train, 'winter':winter_train}
    test = {'global':global_test, 'summer':summer_test, 'winter':winter_test}
    
    return train, test

def grid_plot(plot_errors, rows, cols):
    fig, axs = plt.subplots(rows, cols)
    for i in range(rows):
        for j in range(cols):
            axs[i, j].plot(plot_errors[i*cols+j], label = "Lg, seed:" + str(cols*i+j+1))
            axs[i, j].legend()
    return 