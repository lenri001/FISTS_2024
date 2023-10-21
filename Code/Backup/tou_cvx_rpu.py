def tou_cvx_one_day(dblInp):
    import numpy as np
    import pandas as pd
    import cvxpy as cp
    import os
    
    [net_load, SOC, time] = dblInp
    
    epoch_timeshift = 1646092800
    if time == 0:
        # Create and overwrite microgrid output dataframe for simulation
        ivt_ctrl = 0
        mg_mo_output = pd.DataFrame({'day': [0], 'net_load' : [net_load], 'SOC' : [SOC], 'solar' : [solar]})
        mg_mo_output.to_feather('mg_mo_output.feather')
        return(ivt_ctrl)
    elif time < num_first_iterations:
        # No prior data run optimization as zero
        ivt_ctrl = 0
        num_day =  int(time / 86400)
        mg_mo_output = pd.read_csv('mg_mo_output.feather')
        mg_mo_output.loc[len(mg_mo_output.index)] = [num_day, net_load, SOC, solar]
        mg_mo_output.to_feather('mg_mo_output.feather')
        return(ivt_ctrl)
    
    elif time % num_first_iterations == 0:
        # New iteration (usually a day)
        # Run optimzation run for that day and save output as a feather file
        num_day =  int(time / 86400)
        mg_mo_output = pd.read_csv('mg_mo_output.feather')
        mg_mo_output.loc[len(mg_mo_output.index)] = [num_day, net_load, SOC, solar]
        mg_mo_output.to_feather('mg_mo_output.feather')
        
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

        load = abs(df.building_load.to_numpy() / 1000)
        solar = abs(df.solar.to_numpy() / 1000)
        load = load.astype(int)
        solar = solar.astype(int)

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
        d = int(len(load) / n )#number of days


        # tou demand charge matrix
        beta_OFF_val=1.53
        beta_MID_val=3.13
        beta_ON_val=7.06
        pg = np.array([])
        psl = np.array([])
        eb = np.array([])
        pbp = np.array([])
        pbn = np.array([])

        P_S = mg_mo_output['solar'][mg_mo_output['day'] == num_day - 1]
        P_L = mg_mo_output['net_load'][mg_mo_output['day'] == num_day - 1]

        P_G = cp.Variable(n)
        E_B = cp.Variable(n)
        P_B_plus = cp.Variable(n)
        P_B_minus = cp.Variable(n)
        P_SL = cp.Variable(n)

        obj = cp.Minimize(alpha @ P_G * del_t + cp.max(beta_OFF @ P_G) + cp.max(beta_MID @ P_G) + cp.max(beta_ON @ P_G))
        for t in range(n):
            if t == 0:
               cons_temp = [
                    E_B[t] == E_init,
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
               #print(cons_temp)
            else:
                cons_temp = [
                    E_B[t] == E_B[t - 1] + del_t*(P_B_plus[t - 1] - P_B_minus[t - 1]),
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
            prob.solve(solver=cp.CBC, verbose = True, qcp = True)
            pg = np.append(pg, P_G.value)
            psl = np.append(psl, P_SL.value)
            eb = np.append(eb, E_B.value)
            pbp = np.append(pbp, P_B_plus.value)
            pbn = np.append(pbn, P_B_minus.value)

            E_init  = E_B[n - 1]
            
            opt_output = pd.DataFrame({'opt': pbp + pbn})
            opt_output.to_feather('opt_output.feather')
            ivt_ctrl = opt_output.opt[0]
            
    else:
        # On the same iteration (usually within a day)
        # Read the feather file and output the data
        opt_output = 'opt_output.feather'
        if os.path.exists(opt_output):
            df = pd.read_feather(opt_output)
            iter_day = time % num_first_iterations
            ivt_ctrl =  opt_output.opt[iter_day]
        num_day =  int(time / 86400)
        mg_mo_output = pd.read_csv('mg_mo_output.feather')
        mg_mo_output.loc[len(mg_mo_output.index)] = [num_day, net_load, SOC, solar]
        mg_mo_output.to_feather('mg_mo_output.feather')
        return (ivt_ctrl)
