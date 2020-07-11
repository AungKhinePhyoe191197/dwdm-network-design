from math import log10

def pout_per_channel(out_pow_max, num_channel):
    return out_pow_max - (10*log10(num_channel))

def total_disperssion(l1, l2, disp_coeff):
    return l1*disp_coeff + l2*disp_coeff