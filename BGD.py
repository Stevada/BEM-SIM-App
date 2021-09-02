# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 14:47:06 2021

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
# =============================================================================
# Train
# =============================================================================
# errors = [error]

def optimize(S, dirs, indexs, actual, pre_error, worked_theta, gradients, season, dt, parametersRange, nostepsize):
    worked_errors = []
    iters = 1
    max_iter = 500
    # max_iter = 1
    error = pre_error
    while iters <= max_iter:
        threads = {}
        for theta in worked_theta: 
            threads[theta] = C.training_thread(theta, dirs['S'][theta], indexs[season], error, gradients, dt, actual, parametersRange)            
        for theta in threads:
            threads[theta].start()
        for theta in threads:
            threads[theta].join()
        
        """backtracking line search version3"""
        c = 0.5
        gradientnorm = 0
        for theta in gradients:
            gradientnorm += gradients[theta]**2
        beta = 0.5
        steps ={}
        threads = {}
        while True:
            for t in range(14): # the indexs for threads are from 1 to 14
                threads[t] = C.searching_thread(t, dirs['S'][t+1], indexs[season], beta, steps, actual, worked_theta, gradients)
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
                
        """update mainthread and synchronize all parameters"""
        print("alpha:", alpha)
        for theta in worked_theta:
            S.par_update(theta, gradients[theta], alpha)
            
        pars = S.par_print()
        for i in range(1, 15):
            dirs['S'][i].par_assign(pars)
            
        _, yc = S.simulate()
        error = S.MSE(actual[indexs[season]], yc[indexs[season]])
        worked_errors.append(error)
        
        """record errors for proof of no competing"""
        all_errors_g.append(S.MSE(actual[indexs['global']], yc[indexs['global']]))
        all_errors_s.append(S.MSE(actual[indexs['summer']], yc[indexs['summer']]))
        all_errors_w.append(S.MSE(actual[indexs['winter']], yc[indexs['winter']]))

        """stopping criteria"""
        if iters >= 2 and abs(worked_errors[-1] - worked_errors[-2])/worked_errors[-1] < 1e-4:
            break 
        
        print(season + " error:", error)
        iters += 1 
    return worked_errors 

@C.my_timer
def BGD(S, dirs, actual, indexs, theta_g, theta_s, theta_w, dt, parametersRange, nostepsize):
    global all_errors_g
    global all_errors_s
    global all_errors_w
    global inner_iters
    all_errors_g = []
    all_errors_s = []
    all_errors_w = []
    pre_error_g = 0
    pre_error_s = 0
    pre_error_w = 0
    max_epoch = 100
    # max_epoch = 1
    global epoch
    global steps
    global delta_theta
    global error
    global gradients
    
    epoch = 0
    gradients = {}
    inner_iters = [0]
    
    
    _, yc = S.simulate()
    all_errors_g.append(S.MSE(actual[indexs['global']], yc[indexs['global']]))
    all_errors_s.append(S.MSE(actual[indexs['summer']], yc[indexs['summer']]))
    all_errors_w.append(S.MSE(actual[indexs['winter']], yc[indexs['winter']]))    
    
    while epoch <= max_epoch:
        cur_error_g = all_errors_g[-1]
        cur_error_s = all_errors_s[-1]
        cur_error_w = all_errors_w[-1]
        
        gradients[epoch] = {}
        print("epoch:", epoch, " error_g:", cur_error_g)
        print("epoch:", epoch, " error_s:", cur_error_s)
        print("epoch:", epoch, " error_w:", cur_error_w)
        
        """stopping criteria"""
        if epoch >= 1 and abs(cur_error_g - pre_error_g)/cur_error_g < 1e-4 or abs(cur_error_s - pre_error_s)/cur_error_s < 1e-4 or abs(cur_error_w - pre_error_w)/cur_error_w < 1e-4:
            break 
        
        pre_error_g = cur_error_g
        pre_error_s = cur_error_s
        pre_error_w = cur_error_w
        
        errors_g = optimize(S, dirs, indexs, actual, cur_error_g, theta_g, gradients[epoch], 'global', dt, parametersRange, nostepsize)
        inner_iters.append(inner_iters[-1] + len(errors_g))

        errors_s = optimize(S, dirs, indexs, actual, cur_error_s, theta_s, gradients[epoch], 'summer', dt, parametersRange, nostepsize)
        inner_iters.append(inner_iters[-1] + len(errors_s))

        errors_w = optimize(S, dirs, indexs, actual, cur_error_w, theta_w, gradients[epoch], 'winter', dt, parametersRange, nostepsize)
        inner_iters.append(inner_iters[-1] + len(errors_w))
        
        epoch += 1 

    return inner_iters, all_errors_g, all_errors_s, all_errors_w
        
#%%
# =============================================================================
# Prepare paths and define subthreads
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

    dt = 1e-4
    theta_s = [1,5,6,9]
    theta_w = [7,8,10]
    theta_g = [2,3,4,11,12,13,14]
    records_testerror = []
    nostepsize = []
    parametersRange = {3:400, 4:100, 5:3, 6:48000, 7:20000, 8:0.499, 11:40}
    for i in [1,2,9,10,12,13,14]:
        parametersRange[i] = 1
    # # parametersRange = {i:1 for i in range(1, 15)}
    train, test = C.split_dataset_2(1, 0.7) 
    C.initialize(all_dir, S, dirs, 'init1', changeschedule=False)
    inner_iters, all_errors_g_dt1, all_errors_s_dt1, all_errors_w_dt1 = BGD(S, dirs, actual, train, theta_g, theta_s, theta_w, dt, parametersRange, nostepsize) 
    # inner_iters, all_errors_g_dt1, all_errors_s_dt1 = BGD(actual, train) 
    _, yc = S.simulate()
    test_error_g = S.MSE(actual[test["global"]], yc[test["global"]])
    test_error_s = S.MSE(actual[test["summer"]], yc[test["summer"]])
    test_error_w = S.MSE(actual[test["winter"]], yc[test["winter"]])
# records_testerror = []
# records_allerrorg = {}
# records_allerrors = {}
# records_allerrorw = {}
# records_inneriters = {}

# for i in [1,3,7]:
#     train, test = C.split_dataset(i, 0.7, season=True)
#     C.initialize(all_dir, S, dirs, 'init1', changeschedule=False)
#     inner_iters, all_errors_w, all_errors_s, all_errors_g = BGD(actual, train)
#     _, yc = S.simulate()
#     yc = np.array(yc)
#     train_error = S.MSE(actual[train['global']], yc[train['global']]) 
#     test_error = S.MSE(actual[test['global']], yc[test['global']])
#     test_error_summer = S.MSE(actual[test['summer']], yc[test['summer']])
#     test_error_winter = S.MSE(actual[test['winter']], yc[test['winter']])

#     print("train:", train_error)
#     print("test:", test_error)
#     record = [test_error, test_error_summer, test_error_winter]
#     records_testerror.append(record) 
    
#     """used when we plot no competing proof for all ten seeds"""
#     records_allerrorg[i] = all_errors_g
#     records_allerrors[i] = all_errors_s
#     records_allerrorw[i] = all_errors_w 
#     records_inneriters[i] = inner_iters 
    
# records_testerror = np.array(records_testerror)
# print(np.mean(records_testerror, 0))
# print(np.std(records_testerror, 0))

#%%
# =============================================================================
# Plot erros for all seeds
# =============================================================================
# longest_record = 0
# for i in records_allerrorg:
#     record = records_allerrorg[i]
#     record = np.array(record)
#     inner_iters = records_inneriters[i]
#     plt.plot(record, label = "seed_" + str(i))
#     if len(record) > longest_record:
#         longest_record = len(record)
#     points = np.array(inner_iters)
#     plt.plot(points, record[points], 'r|')
#     plt.xticks(range(longest_record))
# plt.plot(all_errors_g_dt1, label="Lg")
# points = np.array(inner_iters) 
# all_errors_g = np.array(all_errors_g_dt1)
# plt.plot(points, all_errors_g[points], 'r|')
# plt.legend()
# plt.title("BGD, global, LS1, dt="+str(dt))
# plt.show()

# longest_record = 0
# for i in records_allerrors:
#     record = records_allerrors[i]
#     record = np.array(record)
#     inner_iters = records_inneriters[i]
#     plt.plot(record, label = "seed_" + str(i))
#     if len(record) > longest_record:
#         longest_record = len(record)
#     points = np.array(inner_iters)
#     plt.plot(points, record[points], 'r|')
#     plt.xticks(range(longest_record))
# plt.plot(all_errors_s_dt1, label="Ls")
# points = np.array(inner_iters) 
# all_errors_s = np.array(all_errors_s_dt1)
# plt.plot(points, all_errors_s[points], 'r|')
# plt.legend()
# plt.title("BGD, summer, LS1, dt="+str(dt))
# plt.show()

# longest_record = 0
# for i in records_allerrorw:
#     record = records_allerrorw[i]
#     record = np.array(record)
#     inner_iters = records_inneriters[i]
#     plt.plot(record, label = "seed_" + str(i))
#     if len(record) > longest_record:
#         longest_record = len(record)
#     plt.xticks(range(longest_record))
#     points = np.array(inner_iters)
#     plt.plot(points, record[points], 'r|')
# plt.plot(all_errors_w, label="Lw")
# points = np.array(inner_iters) 
# all_errors_w = np.array(all_errors_w)
# plt.plot(points, all_errors_w[points], 'r|')
# plt.legend()
# plt.title("winter_unisch, dt=1e-8")
# plt.title("BGD, winter, LS1, dt="+str(dt))
# plt.show()

    
# # plt.title("BGD_ADAM, train, init_1, error_g")
# # plt.legend()
# # plt.show()
#%%

        

        