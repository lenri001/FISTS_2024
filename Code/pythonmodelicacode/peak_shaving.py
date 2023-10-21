def peak_shaving(dblInp):
    [net_load, SOC] = dblInp
    if ((net_load <= -15000) and (SOC > 0.20) and (net_load >= -100000)):
        ivt_ctrl = -1 * abs(net_load + 15000)
    elif ((net_load <= -100000) and (SOC > 0.20)):
        ivt_ctrl = -100000
    elif ((net_load >= 0) and (SOC < 0.90) and (net_load < 100000)):
        ivt_ctrl = (net_load);
    elif ((SOC < 0.90) and (net_load >= 100000)):
        ivt_ctrl = 100000
    else:
        ivt_ctrl = 0
    return int(ivt_ctrl)
def peak_shaving_triple(dblInp):
    [net_load, SOC, null] = dblInp
    if ((net_load <= -15000) and (SOC > 0.20) and (net_load >= -100000)):
        ivt_ctrl = -1 * abs(net_load + 15000)
    elif ((net_load <= -100000) and (SOC > 0.20)):
        ivt_ctrl = -100000
    elif ((net_load >= 0) and (SOC < 0.90) and (net_load < 100000)):
        ivt_ctrl = (net_load);
    elif ((SOC < 0.90) and (net_load >= 100000)):
        ivt_ctrl = 100000
    else:
        ivt_ctrl = 0
    return int(ivt_ctrl)

def return_zero(dblInp):
    [net_load, SOC, null] = dblInp
    return 0
