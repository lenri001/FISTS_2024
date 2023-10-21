def testGaussArriv(time):
    import numpy as np    
    import pandas as pd
    import os
    
    # Creates the Gaussian for number of random arrivals for a day (Scalar value)
    def number_of_arrivals(mean, std_dev, size =1):
        num_arriv = np.array([])
        for i in range(len(mean)):
            num_arriv = np.append(num_arriv, np.random.default_rng().normal(mean[i], std_dev[i], size))
        num_arriv = np.sort(np.absolute(num_arriv))
        return (num_arriv)
    # Creates a compund Gaussian with user imputed size (vector length) 
    # A vector is expected for for the function fir both the mean and std dev
    # [1 ... N] creates an Nth compound Gaussian eg, mean = [10, 20, 30], std_dev = [1, 2, 3]  creates a tri-Gaussian
    def compound_gauss(mean, std_dev, size):
        if len(mean) == len(std_dev):
            cpd_gauss = np.array([])
            for i in range(len(mean)):
                if size[i] <= 1:
                    size[i] = 1
                cpd_gauss = np.append(cpd_gauss, np.random.default_rng().normal(mean[i], std_dev[i], int(size[i])))
            cpd_gauss = np.sort(cpd_gauss)
        return (cpd_gauss)
    # Creates the Guassian for arrival and leave times in minutes in a day
    def random_ev_arrivals_times(arriv_mean, arriv_std_dev, cpd_mean, cpd_std_dev, charge_mean, charge_std_dev):
        # Size (vector length) is determined by number_of_arrivals function
        size = number_of_arrivals(arriv_mean, arriv_std_dev)
        # Input the time when peaks occur
        arriv_time = compound_gauss(cpd_mean, cpd_std_dev, size)
        # Input the average duration of charging for each peak 
        leave_time = compound_gauss(charge_mean, charge_std_dev, size)
        return [arriv_time, leave_time]
    # Creates a datafrrame with the arrival times, and adds a time column 
    # If multiple charging sessions occur they add up
    def date_time_arrival_times(start_date, num_days, arriv_mean, arriv_std_dev, cpd_mean, cpd_std_dev, charge_mean, charge_std_dev):
        # Create a dataframe to be populated 
        df = pd.DataFrame(columns = ['arriv_time', 'leave_time'])
        # Timestamp for each day counter 
        current_date = start_date
        # Populates the dataframe with random arrival for each day
        # Each day is added one at a time in the for loop
        for i in range(num_days):
            # Create temporary dataframe for that day that will be added main dataframe
            temp = pd.DataFrame(columns = ['arriv_time'])
            # Call the random arrival time function for each day
            arriv_time, leave_time = random_ev_arrivals_times(arriv_mean, arriv_std_dev, cpd_mean, cpd_std_dev, charge_mean, charge_std_dev)
            # Converts random arrival times (minutes in a day) into timedeltas which are added to that day's timestamp
            # Converts random arrival times into pandas timestamps 
            temp['arriv_time'] = current_date + pd.to_timedelta(arriv_time, unit = 'min')
            # Converts random leave times (duration) into timestamps by adding arrival time to leave time timedeltas
            temp['leave_time'] = temp['arriv_time'] + pd.to_timedelta(leave_time, unit = 'min')
            # Add daily dataframe to the main dataframe
            df = pd.concat([df,temp])
            # Update the current day timestamp by adding one day
            current_date = current_date + pd.Timedelta(1, "d")
        # Ensures that arrival times are in order
        df = df.sort_values(by=['arriv_time'])
        # Reset dataframe to organized arrival times
        df = df.reset_index(drop = True)
        # Seperate arrival times and leave times to create charging sessions 
        df1 = df[['arriv_time']]
        # Set a charging session to 1
        df1['value'] = 1
        df1['time'] = df1['arriv_time']
        df2 = df[['leave_time']]
        # Set a charging session to -1 to negate a charging to shut it off
        df2['value'] = -1
        df2['time'] = df2['leave_time']
        # Combine the seperated dataframes to create a charging sessions 
        ev = pd.concat([df1, df2])
        # Sort the combined dataframes, by time 
        ev = ev.sort_values(by=['time'])
        # Reset dataframe to organized times
        ev = ev.reset_index(drop = True)
        # Adds the 1 and -1s to get number of charging sessions occuring at every time interval
        ev['fuzz'] = ev.value.cumsum()
        # 0 - 4 charging session can occur since there are 4 charging stations
        ev['fuzz'] = ev['fuzz'].clip(lower=0, upper = 4)
        # Multiply by 5 kW which is the power consumption for each EV charger
        ev['charge'] = ev['fuzz'] * 5 
        # Organize columns 
        ev = ev[['time', 'value', 'fuzz', 'charge']]
        return [df, ev]
        
    def resample(df, time_column = 'time', resample_rate = '5T'):
        df[time_column] = pd.to_datetime(df[time_column])
        df = df.set_index(df[time_column])
        df = df.drop(columns = [time_column])
        df = df.resample(resample_rate).bfill()  #df.groupby(pd.Grouper(key=time_column, freq=resample_rate)).ffill().bfill() 
        df.insert(loc=0, column=time_column, value=df.index) #df.insert(loc=0, column=time_column, value=df.index)
        df = df.reset_index(drop=True)
        #df.fillna(0)
        #df = df.astype(int, errors='ignore')
        #df = df.fillna(0)
        return df
    
    temporaryFile = "df.feather"  
    if os.path.exists(temporaryFile):
        df = pd.read_feather(temporaryFile)
        index = time / 900
        output = df.charge[index].item()
        return output
    else: 
        arriv_mean = [6, 3, 1] # Average number of car arrivals
        arriv_std_dev = [4, 2, 1] # Car arrivals standard deviation
        cpd_mean = [558, 872, 1235] # Arrival times peaks 
        cpd_std_dev = [332, 358, 300] # Arrival times standard deviation
        ev_arriv = np.array([])
        start_date = pd.Timestamp(2023, 1, 1, 0) # Start date for the time deltas
        charge_mean = [90, 90, 90] # Average length of charging session 
        charge_std_dev = [30, 30, 30] # Standard deviation of charging length
        num_days = 365 # Number of outputed random data 
        # Call the function 
        df, ev = date_time_arrival_times(start_date, num_days, arriv_mean, arriv_std_dev,
                                      cpd_mean, cpd_std_dev, charge_mean, charge_std_dev)
        first_row = {'time':pd.Timestamp('2023-01-01 00:00:00'), 'value':0, 'fuzz':0, 'charge':0}
        last_row = {'time':pd.Timestamp('2024-01-01 00:00:00'), 'value':0, 'fuzz':0, 'charge':0}
        ev_pad = ev
        ev_pad = pd.concat([ev_pad, pd.DataFrame([first_row])], ignore_index=True)
        ev_pad = pd.concat([ev_pad, pd.DataFrame([last_row])], ignore_index=True)
        ev_pad = ev_pad.sort_values(by=['time'])
        ev_pad = ev_pad.reset_index(drop = True)
        ev_pad = resample(ev_pad, resample_rate = '15T')
        ev_pad = ev_pad[ev_pad.time.between('2023-01-01 00:00:00', '2023-12-31 23:59:59')].reset_index(drop=True)
        ev_pad.to_feather(temporaryFile)
        return ev_pad.charge[0].item()
