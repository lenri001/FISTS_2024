import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cvxpy as cp

lg = [31, 16, 25, 20, 4]
pk = ['off', 'mid', 'on', 'mid', 'off']
alpha = np.array([])
for i in range(len(lg)):
    if pk[i] == 'on':
        mult = 0.1079
    elif pk[i] == 'mid':
        mult = 0.0874
    elif pk[i] == 'off':
        mult = 0.0755
    alpha = np.append(alpha, (mult * np.ones(lg[i])))

lg = [31, 16, 25, 20, 4]
pk = ['off', 'mid', 'on', 'mid', 'off']
val = [[0.1709, 0, 0], [0, 0.0874, 0], [0, 0, 0.0755]]
beta = {}
for i in range(len(val)):
    beta_i = np.array([])
    for j in range(len(lg)):
        if pk[j] == 'on':
            mult = val[0][i]
        elif pk[j] == 'mid':
            mult = val[1][i]
        elif pk[j] == 'off':
            mult = val[2][i]
        beta_i = np.append(beta_i, (mult * np.ones(lg[j])))
    beta[i] = beta_i
beta_ON = np.zeros((96, 96))
np.fill_diagonal(beta_ON, beta[0])
beta_MID = np.zeros((96, 96))
np.fill_diagonal(beta_MID, beta[1])
beta_OFF = np.zeros((96, 96))
np.fill_diagonal(beta_OFF, beta[2])

df = pd.read_excel('/home/sigi_laptop/Documents/Research/NAPS_2023/Code/rate_structure_admin_data_06_01.xlsx')

load = df.total_pwr.to_numpy()
solar = df.solar_pwr.to_numpy()
eta_plus=0.96 # charging efficiency
eta_minus=0.96 # discharging efficiency
Emax=450 # SOC upper limit
Emin=100 # SOC lower limit
E_init=250 # initial state of charge
P_B_plus_max=100 # charging power limit
P_B_minus_max=100 # discharging power limit

opt_load=load #declaring optimal load
n=96 #declaring number of timestpes for each optimization
del_t=1/4 #time delta
d=len(load) / n #number of days


# tou demand charge matrix
beta_OFF_val=1.53
beta_MID_val=3.13
beta_ON_val=7.06


P_G = cp.Variable(n)
E_B = cp.Variable(n)
P_B_plus = cp.Variable(n)
P_B_minus = cp.Variable(n)
P_SL = cp.Variable(n)
P_S = cp.Variable(n)
P_L = cp.Variable(n)
obj = cp.Minimize(alpha @ P_G * del_t + cp.max(beta_OFF @ P_G) + cp.max(beta_MID @ P_G) + cp.max(beta_ON @ P_G))


cons = []
for t in range(1,n):
    cons_temp = [
        E_B[t] >= Emin,
        E_B[t] <= Emax,
        P_B_plus[t] >= 0,
        P_B_plus[t] <= P_B_plus_max,
        P_B_minus[t] >= 0,
        P_B_minus[t] <= P_B_minus_max,
        P_SL[t] + P_B_plus[t]/eta_plus == P_S[t],
        P_SL[t] + P_G[t] + P_B_minus[t]*eta_minus == P_L[t],
        P_SL[t] >= 0
    ]
    cons += cons_temp
prob = cp.Problem(obj, cons)

print(prob.solve(solver=cp.SCS))
print(prob.status)
