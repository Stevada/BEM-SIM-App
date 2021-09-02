# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 11:47:40 2020

@author: xuziang
"""
import computation as C
from simulation_2 import simulation
import opyplus as op 
import numpy as np
import pandas as pd
from numpy import genfromtxt
import matplotlib.pyplot as plt
import threading
import time 
    
#%%
@C.my_timer
def GD(S, dirs, actual, indexs, worked_thetas, dt, parametersRange, nostepsize):
    max_epoch = 100
    # max_epoch = 1
    global epoch 
    global error
    global steps
    global gradients
    global errors

    errors = []
    gradients = {}
    epoch = 1
    while epoch <= max_epoch:
        _, yc = S.simulate()
        error = S.MSE(actual[indexs], yc[indexs])
        print("epoch ",epoch, " error:", error)
        errors.append(error)
        
        """stopping criteria"""
        if epoch >= 2 and abs(errors[-1] - errors[-2])/errors[-1] < 1e-4:
            break 
        
        """parallely get gradient"""
        threads = {}
        
        gradients[epoch] = {}
        for i in worked_thetas:  
            threads[i] = C.training_thread(i, dirs['S'][i], indexs, error, gradients[epoch], dt, actual, parametersRange)
        for i in worked_thetas:
            threads[i].start()
        for i in worked_thetas:
            threads[i].join()
        
        """backtracking line search version3"""
        c = 0.5
        gradientnorm = 0
        for theta in gradients[epoch]:
            gradientnorm += gradients[epoch][theta]**2
        beta = 1
        steps ={}
        threads = {}
        while True:
            for t in range(14): # the indexs for threads are from 1 to 14
                threads[t] = C.searching_thread(t, dirs['S'][t+1], indexs, beta, steps, actual, worked_thetas, gradients[epoch])
            for t in range(14):
                threads[t].start()
            for t in range(14):
                threads[t].join()
            
            """line search stop criteria"""
            alphafound = False
            for t in range(14):
                alpha = beta*0.5**t
                if steps[t] <= error - c*alpha*gradientnorm:
                    alphafound = True
                    break
            if alphafound:
                break
            elif alpha <= 1e-30:
                nostepsize.append(None) 
                break 
            else:
                beta = alpha 
        
        # """line search"""
        # steps ={}
        # threads = {}
        # beta = 0.6
        # for i in range(1,15):
        #     threads[i] = C.searching_thread(i, dirs['S'][i], indexs, beta, steps, actual, worked_thetas, gradients[epoch])
        # for i in range(1,15):
        #     threads[i].start()
        # for i in range(1,15):
        #     threads[i].join()
            
        # best_indexs = 0
        # best_step = 1 
        # for s in steps:
        #     if steps[s] < best_step:
        #         best_step = steps[s]
        #         best_indexs = s
        # alpha = 0.6**best_indexs

        """update mainthread and synchronize all parameters"""
        print("alpha:", alpha)
        for theta in worked_thetas:
            S.par_update(theta, gradients[epoch][theta], alpha)
        pars = S.par_print()
        for i in range(1, 15):
            dirs['S'][i].par_assign(pars)
        
        epoch += 1 
        
    return errors

#%%
# =============================================================================
# Train
# =============================================================================
if __name__ == "__main__":
    all_dir = "C:/Users/xuziang/Downloads/Building Energy Consumption Analysis"
    idfname = '/545_update_part_sim.idf'
    epwfile = "/Austin_weather.epw"
    eplus = '/EnergyPlusV9-3-0'
    epm = op.Epm().load(all_dir + '/EplusModels' + idfname)

    S = simulation(epm, all_dir + '/EplusModels' + epwfile, all_dir + eplus)
    dirs = C.pre_dirs(all_dir, idfname, epwfile, eplus)
    useful_thetas = [1,3,4,5,6,7,9,10,11,13] # no parameters 2, 8, 12, 14
    all_thetas = [i for i in range(1,15)]
    actual = genfromtxt(all_dir + "/Optimizing Algs/Data/ActualEnergyConsumption.csv", delimiter=',')

    S = simulation(epm, all_dir + '/EplusModels' + epwfile, all_dir + eplus)
    dirs = C.pre_dirs(all_dir, idfname, epwfile, eplus)
    useful_thetas = [1,3,4,5,6,7,9,10,11,13] # no parameters 2, 8, 12, 14
    all_thetas = [i for i in range(1,15)]
    actual = genfromtxt(all_dir + "/Optimizing Algs/Data/ActualEnergyConsumption.csv", delimiter=',')

    dt = 1e-4
    parametersRange = {3:400, 4:100, 5:3, 6:48000, 7:20000, 8:0.499, 11:40}
    for i in [1,2,9,10,12,13,14]:
        parametersRange[i] = 1
    # parametersRange = {i:1 for i in range(1, 15)}
    nostepsize = [] # record if no applicable step size found
    all_errors = []
    records_testerror = []
    
    train, test = C.split_dataset_2(1, 0.7)
    C.initialize(all_dir, S, dirs, 'init1')
    errors = GD(S, dirs, actual, train['global'], all_thetas, dt, parametersRange, nostepsize)
    
    _, yc = S.simulate()
    test_error_g = S.MSE(actual[test["global"]], yc[test["global"]])
    test_error_s = S.MSE(actual[test["summer"]], yc[test["summer"]])
    test_error_w = S.MSE(actual[test["winter"]], yc[test["winter"]])
    # print("shit")
# all_errors.append(errors)

# for i in range(1, 11):  
#     train, test = C.split_dataset(i, 0.7, True)
#     C.initialize(all_dir, S, dirs, 'init1')
#     errors = GD(actual, train['global'])
#     all_errors.append(errors)
#      _, yc = S.simulate()
#     train_error = S.MSE(actual[train['global']], yc[train['global']]) 
#     test_error = S.MSE(actual[test['global']], yc[test['global']])
#     test_error_summer = S.MSE(actual[test['summer']], yc[test['summer']])
#     test_error_winter = S.MSE(actual[test['winter']], yc[test['winter']])

#     print("train:", train_error)
#     print("test:", test_error)
#     record = [test_error, test_error_summer, test_error_winter]
#     records_testerror.append(record) 

# records_testerror = np.array(records_testerror)
# print(np.mean(records_testerror, 0))
# print(np.std(records_testerror, 0))
#%%
# for i in range(10):
#     errors = all_errors[i]
#     plt.plot(errors, label="seed:" + str(i))
#     plt.xticks(range(len(errors)))
#     plt.legend()
# plt.show()

# plt.plot(errors, label="seed:1", marker='o')
# plt.legend()
# plt.title("GD, LS1, dt="+str(dt))
# plt.show()#%%

#%%
# =============================================================================
#  save results
# =============================================================================
# import pickle

# with open('results/'+'unisch_GD_all_errors', 'wb') as fp:
#     pickle.dump(all_errors, fp)