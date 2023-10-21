def output_emissions(dblInp):
#    import pandas as pd
#    [net_load, time] = dblInp
#    df = pd.read_feather('/home/sigi-laptop/Documents/Research/cert_mo_building/peak_shaving/emissions_rate.feather')
#    epoch_timeshift = 1646092800    
#    time += epoch_timeshift
#    er = df['emissions_rate'][df.date == pd.Timestamp(time, unit='s')].astype('float')
#    er = er.iloc[0]
#    if net_load > 0:
#        net_load = 0
#    emissions = -1 * (net_load / 1000 / 12) * (er)
#    return int(emissions)

