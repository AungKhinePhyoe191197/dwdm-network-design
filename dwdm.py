from math import log10

def pout_per_channel(out_pow_max, num_channel):
    return out_pow_max - (10*log10(num_channel))

def total_disperssion(l1, l2, disp_coeff):
    return l1*disp_coeff + l2*disp_coeff

def total_splic_loss(loss, num):
    return loss*num

def total_connector_loss(loss, num):
    return loss*num

def fiber_loss(coef, len):
    return coef*len

def link_loss(splic_loss, connector_loss, fiber_loss):
    return splic_loss+connector_loss+fiber_loss

def link_attenuation(loss, len):
    return loss/len