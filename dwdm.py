from math import log10

def total_link_length(l1, l2):
    return l1+l2

def pout_per_channel(out_pow_max, num_channel):
    return out_pow_max - (10*log10(num_channel))

def total_disperssion(l1, l2, l1_coef, l2_coef):
    return l1*l1_coef + l2*l2_coef

def total_splic_loss(loss, num):
    return loss*num

def total_connector_loss(loss, num):
    return loss*num

def fiber_loss(coef, len):
    return coef*len

def link_loss(splic_loss, connector_loss, fiber_loss, safety_margin):
    return splic_loss+connector_loss+fiber_loss+safety_margin

def link_attenuation(loss, len):
    return loss/len