from math import log10

def total_link_length(l1, l2):
    return l1+l2

def pout_per_channel(out_pow_max, num_channel):
    return out_pow_max - (10*log10(num_channel))

def total_dispersion(l1, l2, l1_coef, l2_coef):
    return l1*l1_coef + l2*l2_coef

def residual_dispersion(total, dcm):
    return total + 2*dcm

def span_loss(coef, length, addi_connector_loss, dcm_loss):
    return coef*length + 2*addi_connector_loss + dcm_loss

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

def power_b1(in_power, mdu_loss, dl_loss, deg_loss, out_power):
    power_in_b1 = in_power - mdu_loss - dl_loss - deg_loss
    return power_in_b1, out_power - power_in_b1

def power_b2(in_power, dl_loss, deg_loss, out_power):
    power_in_b2 = in_power - dl_loss - deg_loss
    return power_in_b2, out_power - power_in_b2

def power_p1(in_power, span_loss, out_power):
    power_in_p1 = in_power - span_loss
    return power_in_p1, out_power - power_in_p1

def power_p2(in_power, span_loss, out_power):
    power_in_p2 = in_power - span_loss
    return power_in_p2, out_power - power_in_p2

def power_in_lineamp(amp_gain, out_power):
    return out_power - amp_gain

def ln1_fiber_loss(bn_out_power, lineamp_in_power, additional_connector_loss):
    return bn_out_power - 2*additional_connector_loss - lineamp_in_power

def ln2_fiber_loss(length, coef):
    return length*coef

def ln2_span_loss(fiber_loss, dcm_loss, connector_loss):
    return fiber_loss + dcm_loss + 2*connector_loss

def link_length(loss, coeff):
    return loss/coeff

def power_receive(in_power, deg_loss, dl_loss, mdu_loss):
    return in_power - deg_loss - dl_loss - mdu_loss
