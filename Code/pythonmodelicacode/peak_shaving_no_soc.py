def peak_shaving(net_load):
    if (net_load <= -15) and (net_load >= -100):
        ivt_ctrl = abs(net_load + 15)
    elif (net_load <= -100):
        ivt_ctrl = 100
    elif (net_load >= 0) and (net_load < 100):
        ivt_ctrl = -1*(net_load);
    elif (net_load < 100):
        ivt_ctrl = -100
    else:
        ivt_ctrl = 0
    return int(ivt_ctrl)
