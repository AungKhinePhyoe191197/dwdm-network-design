from __future__ import print_function, unicode_literals
import regex
import sys
import pandas as pd

import six
import os
clear = lambda: os.system('cls')
from tabulate import tabulate
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict, Separator)

import utils
from utils import log, log_df, generate_questions, update_answers

import dwdm

try:
    from terminalsize import get_terminal_size
    window_width, _ = get_terminal_size()
except ImportError:
    window_width = 100

style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})

constraints = {
    'l1_min': 40,
    'l1_max': 120,
    'l2_min': 40,
    'l2_max': 120,
    'fiber_attenuation_coef_max': 0.2,
    'link_attenuation_coef_max': 0.275,
    'safety_margin_min': 3,
    'safety_margin_max': 5,
    'num_channel_min': 40,
    'num_channel_max': 80,
    'dispersion_min': -510,
    'dispersion_max': 1020,
}
user_inputs = {
    'fiber_class': 'G.625.D'
}
calc_outputs = {}

df_fiber_spec_l1 = pd.DataFrame({
    'Type': ['Single Mode (SM)'],
    'Attenuation (dB/km)': [0.275],
    'Dispersion coefficient (ps/nm-km)': [17]
}).set_index('Type')

df_fiber_spec_l2 = pd.DataFrame({
    'Type': ['Single Mode (SM)'],
    'Attenuation (dB/km)': [0.275],
    'Dispersion coefficient (ps/nm-km)': [17]
}).set_index('Type')

df_insert_loss_spec_addrop_comm = pd.DataFrame({
    'ROADM Degree': ['2', '4', '8'],
    'MDU Loss (dB)': [14, 14, 14],
    'Directionless ROADM (dB)': [4, 7, 7],
    'Degree ROADM (dB)': [4, 7, 7]
}).set_index('ROADM Degree')

df_insert_loss_spec_comm_addrop = pd.DataFrame({
    'ROADM Degree': ['2', '4', '8'],
    'MDU Loss (dB)': [7, 7, 7],
    'Directionless ROADM (dB)': [7, 9, 11],
    'Degree ROADM (dB)': [7, 9, 11]
}).set_index('ROADM Degree')

df_edfa_spec = pd.DataFrame({
    'Amplifier Power Types': [
        'Flat Gain (FG)', 
        'Maximum Gain (G)',
        'Minimum Gain (G)', 
        'Noise Figure (NF)', 
        'Maximum Input Power (Pin Max)',
        'Maximum Output Power (Pout Max)',
        'Minimum Input Power (Pin Min)',
        'Minimum Output Power (Pout Min)'],
    'Power Values': [22, 30, 15, 5.5, 5, 20, -35, -5]
}).set_index('Amplifier Power Types')

df_dcm_spec = pd.DataFrame({
    'DCU Modules': ['30 Km', '40 Km', '60 Km', '80 Km', '120 Km'],
    'Dispersion Compensation (ps/nm)': [-510, -680, -1020, -1360, -2040],
    'Insertion Loss (dB)': [4, 4, 4, 4, 4]
}).set_index('DCU Modules')

df_splic_loss = pd.DataFrame({
    'Type': ['Single Fusion Splice'],
    'Maximum Attenuation Value (dB)': [0.5]
}).set_index('Type')

df_connector_loss = pd.DataFrame({
    'Grade': ['B', 'C', 'D'],
    'Maximum Attenuation Value (dB)': [0.25, 0.5, 1]
}).set_index('Grade')

df_fiber_g625a = pd.DataFrame({
    'Cable No': ['1'],
    'Detail': ['Maximum at 1550 nm'],
    'Attenuation Coefficient (dB/km)': [0.4]
}).set_index('Cable No')

df_fiber_g625b = pd.DataFrame({
    'Cable No': ['1'],
    'Detail': ['Maximum at 1550 nm'],
    'Attenuation Coefficient (dB/km)': [0.35]
}).set_index('Cable No')

df_fiber_g625c = pd.DataFrame({
    'Cable No': ['1'],
    'Detail': ['Maximum at 1550 nm'],
    'Attenuation Coefficient (dB/km)': [0.3]
}).set_index('Cable No')

df_fiber_g625d = pd.DataFrame({
    'Cable No': ['1'],
    'Detail': ['Maximum at 1550 nm'],
    'Attenuation Coefficient (dB/km)': [0.3]
}).set_index('Cable No')

fiber_classes = {
    'G.625.D': df_fiber_g625d,
}

def validate_number(val):
    try:
        int(val)
        return True
    except ValueError:
        return False

def validate_fraction(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

def log_seperator(char):
    log("")
    log(char * window_width, delay=False)
    log("")

def logAndModify(df, title, desc):
    log(f"(TABLE) {title}", color="green")
    log(desc)
    log("")
    log_df(df)
    log("")
    answers = prompt(generate_questions(df), style=style)
    update_answers(df, answers)
    log("")
    log("This table will be used for futher calculation", color='yellow')
    log("")
    log_df(df, flag='pmt')
    log("")

def logIntro(): 
    log("Power Budget", color="blue", figlet=True)
    log("Welcome to power budget", color="green")
    log("This program is for calculating power budget of DWDM transmission Link (Link Distance of 80 km to 220 km).", color="white")
    log("")
    log("In Basic DWDM long distance link, transceiver, MDU, Directionless ROADM and Degree ROADM are both on the Transmitting and Receiving Sites.", color="white")
    log("")
    log("Amplifier used in this calculation are fixed gain EDFA amplifier.")
    log("B is a booster amplifier.")
    log("P is a pre amplifier.")
    log("Line amplifier")
    log("")
    log("There is a Degree ROADM station for changing the data traffic between the link.")
    log("The length of L1 should be in the range between 40 km and 120 km.")
    log("The length of L2 should be in the range between 40 km and 120 km.")
    log("")
    log("Before the calculation start, please choose and input the specification value of the devices.")

def ask_transceiver_power_values():
    log("Please add the transceiver power value in dB.")
    answers = prompt([
        {
            'type': 'input',
            'name': 'transmit_pow_min',
            'message': 'Minimum Transmit Power (dB)',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) or 'Input must be real number'
        },
        {
            'type': 'input',
            'name': 'transmit_pow_max',
            'message': 'Maximum Transmit Power (dB)',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) or 'Input must be real number'
        },
        {
            'type': 'input',
            'name': 'receive_pow_min',
            'message': 'Minimum Receive Sensitivity (dB)',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) or 'Input must be real number'
        },
        {
            'type': 'input',
            'name': 'receive_pow_max',
            'message': 'Maximum Receive Sensitivity (dB)',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) or 'Input must be real number'
        }
    ], style=style)
    log("")
    user_inputs.update(answers)

def ask_connector_loss_value():
    # TODO: additional loss
    log("Please add the maximum connector loss value for the link")
    answers = prompt([
        {
            'type': 'input',
            'name': 'connector_loss_addition',
            'message': 'Additional Connector Loss (dB)',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) or 'Input must be a real number'
        }
    ])
    log("")
    user_inputs.update(answers)

def ask_num_channel():
    log("Number of Channels", color="green")
    log("This program is focus on DWDM link of each channel carrying 10 Gbps of data.")
    log("")
    log("The number of channels in this link should be in the range of %d channels to %d channels." % (constraints["num_channel_min"], constraints["num_channel_max"]))
    log("")
    log("To start the calculation, please input the number of channels (%d channels to %d channels)" % (constraints["num_channel_min"], constraints["num_channel_max"]))
    answers = prompt([
        {
            'type': 'input',
            'name': 'num_channel',
            'message': 'N =',
            'filter': lambda val: int(val),
            'validate': lambda val: validate_number(val) and constraints["num_channel_min"] <= int(val) <= constraints["num_channel_max"] or 'The value must be between %d and %d' % (
                constraints["num_channel_min"], constraints["num_channel_max"]
            )
        }
    ])
    log("")
    user_inputs.update(answers)

def ask_line_lengths():
    log("Please input the length of L1 between the range from 40 km to 80 km.")
    answers = prompt([{
        'type': 'input',
        'name': 'l1_length',
        'message': 'L1 (km) =',
        'filter': lambda val: int(val)
    }])
    log("")
    user_inputs.update(answers)
    log("Please input the length of L2 between the range from 40 km to 120 km.")
    answers = prompt([{
        'type': 'input',
        'name': 'l2_length',
        'message': 'L2 (km) =',
        'filter': lambda val: int(val)
    }])
    log("")
    user_inputs.update(answers)

def ask_option_1(num):
    log("Splicing Loss", color="green")
    log_df(df_splic_loss)
    log("The maximum value of the splicing loss is ≤ 0.5 dB.")
    log("(General splicing loss value is around 0.02 dB)")
    answers = prompt([
        {
            'type': 'input',
            'name': f'splic_loss_l{num}',
            'message': 'Each splicing loss value (dB) =',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) and 0 <= float(val) <= df_splic_loss.loc['Single Fusion Splice', 'Maximum Attenuation Value (dB)'] or 'The value must not be empty and greater than maximum attenuation value.'
        },
        {
            'type': 'input',
            'name': f'num_splic_l{num}',
            'message': 'Number of splices =',
            'filter': lambda val: int(val),
            'validate': lambda val: validate_number(val) or 'The value must be a number'
        }
    ], style=style)
    user_inputs.update(answers)
    log("")
    log("Connector Loss", color="green")
    log_df(df_connector_loss)
    log("(General connector loss value is around 0.5 dB)")
    answers = prompt([
        {
            'type': 'input',
            'name': f'connector_loss_l{num}',
            'message': 'Each connector loss value =',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) and 0 <= float(val) <= max(df_connector_loss['Maximum Attenuation Value (dB)']) or 'The value must be between 0 and %.1f' % (max(df_connector_loss['Maximum Attenuation Value (dB)']))
        },
        {
            'type': 'input',
            'name': f'num_connector_l{num}',
            'message': 'Number of connector =',
            'filter': lambda val: int(val),
            'validate': lambda val: validate_number(val) or 'The value must be a number'
        }
    ], style=style)
    user_inputs.update(answers)
    log("")
    log("G.652 Single Mode Fiber Specification for Cable plant", color="green")
    log("")
    for c in fiber_classes:
        log("ITU-T " + c + " Cable attributes")
        log_df(fiber_classes[c], flag='pmt')
        log("")
    log("Table show the cable attenuation value of G.652.D.")
    log("Fiber attenuation value for the DWDM link should not exceed than %.1f dB/km" % (
        constraints['fiber_attenuation_coef_max']
    ))
    answers = prompt([{
        'type': 'input',
        'name': f'fiber_attenuation_coef_l{num}',
        'message': 'Please input the fiber attenuation coefficient value =',
        'filter': lambda val: float(val),
        'validate': lambda val: validate_fraction(val) and 0 <= float(val) <= constraints['fiber_attenuation_coef_max'] or 'The value must be between 0 and %.1f' % (constraints['fiber_attenuation_coef_max'])
    }], style=style)
    user_inputs.update(answers)
    log("")
    log("The maximum attenuation coefficient value of %s is %.1f dB/km" % (
        user_inputs['fiber_class'],
        fiber_classes[user_inputs['fiber_class']].loc['1', 'Attenuation Coefficient (dB/km)']
    ))
    log("")
    log("Safety Margin", color="green")
    log("Safety margin should be between %.1f dB and %.1f dB." % (
        constraints['safety_margin_min'],
        constraints['safety_margin_max']
    ))
    answers = prompt([{
        'type': 'input',
        'name': f'safety_margin_l{num}',
        'message': 'Please input safety margin value (dB) =',
        'filter': lambda val: float(val),
        'validate': lambda val: validate_fraction(val) and constraints['safety_margin_min'] <= float(val) <= constraints['safety_margin_max'] or 'The value should be between %.1f and %.1f' % (
            constraints['safety_margin_min'],
            constraints['safety_margin_max']
        )
    }])
    user_inputs.update(answers)

def ask_log_option_2(df, num):
    answers = prompt([{
        'type': 'input',
        'name': f'link_attenuation_coef_l{num}',
        'message': f'Please input the attenuation coefficient value of the L{num} (dB/km) =',
        'filter': lambda val: float(val),
        'validate': lambda val: validate_fraction(val) and 0 <= float(val) <= constraints['link_attenuation_coef_max'] or 'The value must be between 0 and %.3f' % (constraints['link_attenuation_coef_max'])
    }])
    user_inputs.update(answers)
    log("")
    df.loc['Single Mode (SM)', 'Attenuation (dB/km)'] = user_inputs[f'link_attenuation_coef_l{num}']
    log_df(df, flag='pmt')
    log("")


def calc_log_option_1(df, num):
    # Calculations
    calc_outputs.update({
        f'total_splic_loss_l{num}': dwdm.total_splic_loss(user_inputs[f'splic_loss_l{num}'], user_inputs[f'num_splic_l{num}']),
        f'total_connector_loss_l{num}': dwdm.total_connector_loss(user_inputs[f'connector_loss_l{num}'], user_inputs[f'num_connector_l{num}']),
        f'fiber_loss_l{num}': dwdm.fiber_loss(user_inputs[f'fiber_attenuation_coef_l{num}'], user_inputs[f'l{num}_length']),
    })
    calc_outputs.update({
        f'link_loss_l{num}': dwdm.link_loss(
            calc_outputs[f'total_splic_loss_l{num}'], 
            calc_outputs[f'total_connector_loss_l{num}'], 
            calc_outputs[f'fiber_loss_l{num}'],
            user_inputs[f'safety_margin_l{num}']
        )
    })
    calc_outputs.update({
        f'link_attenuation_coef_l{num}': dwdm.link_attenuation(calc_outputs[f'link_loss_l{num}'], user_inputs[f'l{num}_length'])
    })

    # log to user
    log(f"Calculation for Link attenuation value of L{num} started.", color='green')
    log("")
    log("Total Splicing Losses")
    log("Total Splice Losses (dB) = splice loss (dB) × number of splices = %.1f dB" % (
        calc_outputs[f'total_splic_loss_l{num}']
    ))
    log("")
    log("Total Connector Losses")
    log("Total Connector Loss (dB) = connector loss (dB) × number of connectors = %.1f dB" % (
        calc_outputs[f'total_connector_loss_l{num}']
    ))
    log("")
    log("Fiber Losses")
    log(f"Fiber losses (dB) = chosen attenuation coefficient value x length of L{num} = %.1f dB" % (
        calc_outputs[f'fiber_loss_l{num}']
    ))
    log("")
    log("Safety margin")
    log("Safety margin value = %.1f dB" % (
        user_inputs[f'safety_margin_l{num}']
    ))
    log("")
    log("Link loss budget for the cable plant")
    log("Link loss budget for the cable plant = Total Splice Losses (dB) + Total connector loss + (dB) Fiber losses + Safety margin = %.1f dB" % (
        calc_outputs[f'link_loss_l{num}']
    ))
    log("")
    log("Link attenuation value")
    log(f"Link attenuation value (dB/km) = link loss budget for the cable plant / length of L{num} = %.3f dB/km" % (
        calc_outputs[f'link_attenuation_coef_l{num}']
    ))
    log("")

    # if not exceed the limit, update to fiber spec dataframe
    if calc_outputs[f'link_attenuation_coef_l{num}'] <= constraints['link_attenuation_coef_max']:
        df.loc['Single Mode (SM)', 'Attenuation (dB/km)'] = calc_outputs[f'link_attenuation_coef_l{num}']
        log("This table show the value of SM fiber Link specification.", color="green")
        log_df(df, flag='pmt')
        log("")
        return True
    else:
        log("Calculated link attenuation is greater than %.3f dB" % (
            constraints['link_attenuation_coef_max']
        ), color="red")
        log("")
        return False

def ask_log_fiber_spec(df, num):
    answers = prompt([{
        'type': 'input',
        'name': f'l{num}_length',
        'message': f'Please Input the Length of L{num} (km) =',
        'filter': lambda val: float(val),
        'validate': lambda val: validate_fraction(val) and constraints[f'l{num}_min'] <= float(val) <= constraints[f'l{num}_max'] or 'Length must be number and between %s and %s' % (constraints[f'l{num}_min'], constraints[f'l{num}_max'])
    }], style=style)
    user_inputs.update(answers)
    log("This table shows the value of SM fiber Link specification.", color="green")
    log_df(df)
    log("")
    log("Maximum link attenuation value for 1530 nm-1565 nm wavelength region is 0.275 dB/km.")
    log("")
    answers = prompt([
        {
            'type': 'confirm',
            'name': f'fiber_spec_change_l{num}',
            'message': f'Do you want to change attenuation value of L{num}?',
        },
        {
            'type': 'list', 
            'name': f'fiber_spec_change_option_l{num}',
            'message': 'Choose option:',
            'choices': [
                {
                    'name': 'Option 1 : Change the attenuation value of the fiber link by inputting the splice losses, connector losses, fiber losses and other losses',
                    'value': '1'
                },
                {
                    'name': 'Option 2 : Change the attenuation value of the fiber link by inputting the value from OTDR',
                    'value': '2'
                }
            ],
            'when': lambda answers: answers.get(f'fiber_spec_change_l{num}', True)
        },
    ], style=style)
    user_inputs.update(answers)
    log("")
    if not user_inputs[f'fiber_spec_change_l{num}']:
        return

    if user_inputs[f'fiber_spec_change_option_l{num}'] == '1':
        ask_option_1(num)
        if not calc_log_option_1(df, num):
            log("Calculated result exceeds the expected result. Please reconsider the losess.", color="yellow")
            log("")
            return ask_log_fiber_spec(df, num)
    elif user_inputs[f'fiber_spec_change_option_l{num}'] == '2':
        ask_log_option_2(df, num)

def ask_log_tables():
    log_seperator("=")
    logAndModify(df_insert_loss_spec_addrop_comm, "Insertion losses from add/drop port to common port",
        "This table shown the general insertion losses from add/drop to common of MDU, Directionless ROADM and Degree ROADM.")
    log("")
    log_seperator("=")
    logAndModify(df_insert_loss_spec_comm_addrop, "Insertion losses from common port to add/drop port",
        "This table shown the general insertion losses common port to add/drop port of MDU, Directionless ROADM and Degree ROADM.")
    log("")
    log_seperator("=")
    ask_transceiver_power_values()
    log("")
    log_seperator("=")
    ask_connector_loss_value()
    log("")
    log_seperator("=")
    logAndModify(df_edfa_spec, "EDFA power specification",
        "This table shown the general value of EDFA power specification.")
    log("")
    log_seperator("=")
    logAndModify(df_dcm_spec, "DCM specificatoin",
        "This table show the general types and values of DCM.")
    log("")

def calc_log_pout_per_channel():
    calc_outputs.update({
        'pout_per_channel': dwdm.pout_per_channel(
            df_edfa_spec.loc['Maximum Output Power (Pout Max)', 'Power Values'],
            user_inputs['num_channel']
        )
    })
    log("Output power of an amplifier per channel", color="green")
    log("The output power of an amplifier per channel in an N channel DWDM network is ")
    log("Pout (dBm) = Pin (dBm) + Gain (dB)")
    log("")
    log("Pout/ch = Maximum output power – 10*log10 (N) = %.2f dBm" % (
        calc_outputs['pout_per_channel']
    ))
    log("")
    log("Per channel output power is")
    log("Pin (dBm) + Gain (dB) = %.2f dBm" % (
        calc_outputs['pout_per_channel']
    ))
    log("")
    log("In %d channel DWDM link, for single channel calculation the maximum output should be %.2f dBm." % (
        user_inputs['num_channel'],
        calc_outputs['pout_per_channel']
    ))
    log("Gain range of the amplifier should be in the range of %.1f to %.1f" % (
        df_edfa_spec.loc['Minimum Gain (G)', 'Power Values'],
        df_edfa_spec.loc['Maximum Gain (G)', 'Power Values']
    ))
    log("")

def calc_log_total_link_length():
    calc_outputs.update({
        'total_link_length': dwdm.total_link_length(
            user_inputs['l1_length'],
            user_inputs['l2_length']
        )
    })
    log("Length of the whole link", color="green")
    log("Length of L1 = %.1f km" % (
        user_inputs['l1_length']
    ))
    log("Length of L2 = %.1f km" % (
        user_inputs['l2_length']
    ))
    log("")
    log("Total length of the link = %.1f km" % (
        calc_outputs['total_link_length']
    ))
    log("")

def calc_log_dispersion():
    # total dispersion
    calc_outputs.update({
        'total_dispersion': dwdm.total_dispersion(
            user_inputs['l1_length'],
            user_inputs['l2_length'],
            df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'],
            df_fiber_spec_l2.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)']
        )
    })

    log("Dispersion of the link", color="green")
    log("Residual dispersion value should be in the range from %d ps/nm to %d ps/nm." % (
        constraints['dispersion_min'],
        constraints['dispersion_max']
    ))
    log("")
    log("Total dispersion value of the link = %.1f ps/nm" % (
        calc_outputs['total_dispersion']
    ))
    log("")

    # residual dispersion
    if calc_outputs['total_dispersion'] > constraints['dispersion_min']:
        log("Dispersion value too high, adding the suitable DCM module for the link.")
        log("")
        for i in df_dcm_spec.index[::-1]:
            dcm = df_dcm_spec.loc[i, 'Dispersion Compensation (ps/nm)']
            residual_dispersion = dwdm.residual_dispersion(calc_outputs['total_dispersion'], dcm)
            if constraints['dispersion_min'] < residual_dispersion < constraints['dispersion_max']:
                calc_outputs['dcm_type'] = i
                calc_outputs['residual_dispersion'] = residual_dispersion

                # logging
                log("Residual Dispersion = %.1f ps/nm + (2 x %.1f) = %.1f ps/nm" % (
                    calc_outputs['total_dispersion'],
                    dcm,
                    calc_outputs['residual_dispersion']
                ))
                log("")
                return

        log("Unable to add dcm module!", color="red")
        log("")
    else:
        calc_outputs['residual_dispersion'] = calc_outputs['total_dispersion']

        # logging
        log("Residual Dispersion = %.1f ps/nm – No DCM = %.1f ps/nm" % (
            calc_outputs['total_dispersion'],
            calc_outputs['residual_dispersion']
        ))
        log("")

def calc_log_span_loss():
    try:
        dcm_loss = df_dcm_spec.loc[calc_outputs['dcm_type'], 'Insertion Loss (dB)']
    except KeyError:
        dcm_loss = 0
    calc_outputs.update({
        'span_1_loss': dwdm.span_loss(
            df_fiber_spec_l1.loc['Single Mode (SM)', 'Attenuation (dB/km)'],
            user_inputs['l1_length'],
            user_inputs['connector_loss_addition'],
            dcm_loss
        ),
        'span_2_loss': dwdm.span_loss(
            df_fiber_spec_l2.loc['Single Mode (SM)', 'Attenuation (dB/km)'],
            user_inputs['l2_length'],
            user_inputs['connector_loss_addition'],
            dcm_loss
        ),
    })

    # Logging
    log("Span Lossess", color="green")
    log("")
    log("Span 1 losses= (attenuation coefficient of L1 x length) + (2 x additional connector losses) + DCM losses = %.1f dB" %(
        calc_outputs['span_1_loss']
    ))
    log("")
    log("Span 2 losses= (attenuation coefficient of L2 x length) + (2 x additional connector losses) + DCM losses = %.1f dB" %(
        calc_outputs['span_2_loss']
    ))
    log("")

def ask_site_degrees():
    log("Minimum transmitter power of the link is %.1f dBm and minimum receiver sensitivity is %.1f dBm" % (
        user_inputs['transmit_pow_min'],
        user_inputs['receive_pow_min']
    ))
    log("")
    answers = prompt([
        {
            'type': 'list',
            'name': 'tx_degree',
            'message': 'Please choose the transmitting site degree: ',
            'choices': df_insert_loss_spec_addrop_comm.index,
        },
        {
            'type': 'list',
            'name': 'pt_degree',
            'message': 'Please choose a degree value of Degree ROADM station which make changing the data traffic between the link: ',
            'choices': df_insert_loss_spec_addrop_comm.index,
        },
        {
            'type': 'list',
            'name': 'rx_degree',
            'message': 'Please choose the receiving site degree: ',
            'choices': df_insert_loss_spec_addrop_comm.index,
        }
    ])
    user_inputs.update(answers)
    log("")

def ask_calc_gain():
    answers = prompt([{
        'type': 'input',
        'name': 'input_power',
        'message': 'Enter input power: ',
        'filter': lambda val: float(val),
        'validate': lambda val: validate_fraction(val) and user_inputs['transmit_pow_min'] <= float(val) <= user_inputs['transmit_pow_max'] or 'Input must be number and between %.1f and %.1f' % (
            user_inputs['transmit_pow_min'],
            user_inputs['transmit_pow_max']
        )
    }])
    user_inputs.update(answers)
    log("")

    power_in_b1, b1_gain = dwdm.power_b1(
        user_inputs['input_power'],
        df_insert_loss_spec_addrop_comm.loc[user_inputs['tx_degree'], 'MDU Loss (dB)'],
        df_insert_loss_spec_addrop_comm.loc[user_inputs['tx_degree'], 'Directionless ROADM (dB)'],
        df_insert_loss_spec_addrop_comm.loc[user_inputs['tx_degree'], 'Degree ROADM (dB)'],
        calc_outputs['pout_per_channel']
    )
    calc_outputs.update({
        'power_in_b1': power_in_b1,
        'b1_gain': b1_gain
    })
    power_in_p1, p1_gain = dwdm.power_p(
        calc_outputs['pout_per_channel'],
        calc_outputs['span_1_loss'],
        calc_outputs['pout_per_channel']
    )
    calc_outputs.update({
        'power_in_p1': power_in_p1,
        'p1_gain': p1_gain
    })
    power_in_b2, b2_gain = dwdm.power_b2(
        calc_outputs['pout_per_channel'],
        df_insert_loss_spec_comm_addrop.loc[user_inputs['pt_degree'], 'Degree ROADM (dB)'],
        df_insert_loss_spec_addrop_comm.loc[user_inputs['pt_degree'], 'Degree ROADM (dB)'],
        calc_outputs['pout_per_channel']
    )
    calc_outputs.update({
        'power_in_b2': power_in_b2,
        'b2_gain': b2_gain
    })
    power_in_p2, p2_gain = dwdm.power_p(
        calc_outputs['pout_per_channel'],
        calc_outputs['span_2_loss'],
        calc_outputs['pout_per_channel']
    )
    calc_outputs.update({
        'power_in_p2': power_in_p2,
        'p2_gain': p2_gain
    })

    # Logging
    log("Gain calculation of B1:", color="green")
    log("B1 I/P power = (Pin1 – MDU Loss – D/L ROADM Loss – Degree ROADM Loss) = %.1f dBm" % (
        power_in_b1
    ))
    # TODO: check gain range
    log("Therefore, B1 Gain = %.1f dB" % (
        b1_gain
    ))
    log("")
    log("Gain calculation of P1:", color="green")
    log("P1 I/P power = B1 O/P power – Span 1 Loss = %.1f dBm" % (
        power_in_p1
    ))

    log("Therefore, P1 Gain = %.1f dB" % (
        p1_gain
    ))
    log("")

    # Check p1 gain range
    if not(df_edfa_spec.loc['Minimum Gain (G)', 'Power Values'] < p1_gain < df_edfa_spec.loc['Maximum Gain (G)', 'Power Values']):
        place_lineamp(df_fiber_spec_l1, '1')

    log("Gain calculation of B2:", color="green")
    log("B2 Input Power = (P1 O/P power – Degree ROADM 1 – DegreeROADM 2) = %.1f dBm" % (
        power_in_b2
    ))
    # TODO: check gain range
    log("Therefore, B1 Gain = %.1f dB" % (
        b2_gain
    ))
    log("")
    log("Gain calculation of P2:", color="green")
    log("P2 I/P power = B2 O/P power – Span 2 Loss = %.1f dBm" % (
        power_in_p2
    ))
    log("Therefore, P2 Gain = %.1f dB" % (
        p2_gain
    ))
    log("")

    # Check p2 gain range
    if not(df_edfa_spec.loc['Minimum Gain (G)', 'Power Values'] < p2_gain < df_edfa_spec.loc['Maximum Gain (G)', 'Power Values']):
        place_lineamp(df_fiber_spec_l2, '2')

def place_lineamp(df, line_number):
    # calculation
    try:
        dcm_loss = df_dcm_spec.loc[calc_outputs['dcm_type'], 'Insertion Loss (dB)']
    except KeyError:
        dcm_loss = 0

    calc_outputs.update({
        'power_in_lineamp': dwdm.power_in_lineamp(
            df_edfa_spec.loc['Minimum Gain (G)', 'Power Values'],
            calc_outputs['pout_per_channel']
        ),
    })
    calc_outputs.update({
        'l'+line_number+'1_fiber_loss': dwdm.ln1_fiber_loss(
            calc_outputs['pout_per_channel'],
            calc_outputs['power_in_lineamp'],
            user_inputs['connector_loss_addition']
        )
    })
    calc_outputs.update({
        'l'+line_number+'1_length': dwdm.link_length(
            calc_outputs['l'+line_number+'1_fiber_loss'],
            df.loc['Single Mode (SM)', 'Attenuation (dB/km)']
        )
    })
    calc_outputs.update({
        'l'+line_number+'2_length': user_inputs['l'+line_number+'_length'] - calc_outputs['l'+line_number+'1_length']
    })
    calc_outputs.update({
        'l'+line_number+'2_fiber_loss': dwdm.ln2_fiber_loss(
            calc_outputs['l'+line_number+'2_length'],
            df.loc['Single Mode (SM)', 'Attenuation (dB/km)']
        )
    })
    calc_outputs.update({
        'l'+line_number+'2_span_loss': dwdm.ln2_span_loss(
            calc_outputs['l'+line_number+'2_fiber_loss'],
            dcm_loss,
            user_inputs['connector_loss_addition']
        )
    })
    calc_outputs.update({
        'l'+line_number+'1_span_loss': dwdm.ln1_span_loss(
            calc_outputs['l'+line_number+'1_fiber_loss'],
            user_inputs['connector_loss_addition']
        )
    })
    # Update P gain
    _, p_gain = dwdm.power_p(
        calc_outputs['pout_per_channel'],
        calc_outputs['l'+line_number+'2_span_loss'],
        calc_outputs['pout_per_channel'],
    )
    calc_outputs.update({
        'p'+line_number+'_gain': p_gain
    })

    # Logging
    log("Line amplifier need to add in the L%s link." % (line_number))
    log("Amplifier is placed at a point where minimum gain can be achieved i.e. %.1f dB" % (
        df_edfa_spec.loc['Minimum Gain (G)', 'Power Values']
    ))
    log("")
    log("Line amp O/P power = Gain(dB) + Line amp input power = %.1f dBm" % (
        calc_outputs['pout_per_channel']
    ))
    log("Line amp input power (dB) = %.1f dB" % (
        calc_outputs['power_in_lineamp']
    ))
    log("")
    log("Due to the Line amplifier placement in the L%s link, the link becomes L%s1 and L%s2." %(
        line_number, line_number, line_number
    ), color="green")
    log("")
    log("L%s1 fiber loss = B%s O/p power – (Line amp input power + (2 x additional connector loss)) = %.1f dB" % (
        line_number,
        line_number,
        calc_outputs['l'+line_number+'1_fiber_loss']
    ))
    log("")
    log("Length of L%s1 = L%s1 Loss (dB) / α (dB/km) = %.1f km" % (
        line_number,
        line_number,
        calc_outputs['l'+line_number+'1_length']
    ))
    log("")
    log("Length of L%s2 = length of L%s – length of L%s1= %.1f km" % (
        line_number,
        line_number,
        line_number,
        calc_outputs['l'+line_number+'2_length']
    ))
    log("")
    log("L%s2 span loss = Fiber L%s2 loss + DCM loss + (2 x additinal connector loss) = %.1f dB" %(
        line_number,
        line_number,
        calc_outputs['l'+line_number+'2_span_loss']
    ))
    log("")

def calc_log_receive_end():
    calc_outputs.update({
        'power_receive': dwdm.power_receive(
            calc_outputs['pout_per_channel'],
            df_insert_loss_spec_comm_addrop.loc[user_inputs['tx_degree'], 'Degree ROADM (dB)'],
            df_insert_loss_spec_comm_addrop.loc[user_inputs['tx_degree'], 'Directionless ROADM (dB)'],
            df_insert_loss_spec_comm_addrop.loc[user_inputs['rx_degree'], 'MDU Loss (dB)'],
        )
    })

    log("After calculating I/P, O/P and gain power values for EDFA the last step remaining is calculating the input power at the receiving end connected to the De-Mux.")
    log("")
    log("Receiving End", color="green")
    log("I/P to receiving end = (P2 O/P power – Degree ROADM Loss – D/L ROADM Loss – MDU Loss) = %.1f dBm" % (
        calc_outputs['power_receive']
    ))
    log("")

    if not (user_inputs['receive_pow_min'] < calc_outputs['power_receive'] < user_inputs['receive_pow_max']):
        log("The input power at the receiving end should be in the range of minimum transceiver sensitivity and maximum receive power of the transceiver.", color="red")
        log("")
        return False
    return True

def create_table():
    try:
        components_dcm = [
            {
                'power': -df_dcm_spec.loc[calc_outputs['dcm_type'], 'Insertion Loss (dB)'],
                'dispersion': df_dcm_spec.loc[calc_outputs['dcm_type'], 'Dispersion Compensation (ps/nm)']
            }
        ]
    except KeyError:
        components_dcm = [
            {
                'power': 0,
                'dispersion': 0
            }
        ]
    components_tx = [
        {
            'power': -df_insert_loss_spec_addrop_comm.loc[user_inputs['tx_degree'], 'MDU Loss (dB)'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_addrop_comm.loc[user_inputs['tx_degree'], 'Directionless ROADM (dB)'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_addrop_comm.loc[user_inputs['tx_degree'], 'Degree ROADM (dB)'],
            'dispersion': 0
        },
        {
            'power': calc_outputs['b1_gain'],
            'dispersion': 0
        },
    ]
    try:
        components_l1 = [
            {
                'power': -calc_outputs['l11_span_loss'],
                'dispersion': dwdm.dispersion(calc_outputs['l11_length'], df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'])
            },
            {
                'power': df_edfa_spec.loc['Minimum Gain (G)', 'Power Values'],
                'dispersion': 0
            },
            {
                'power': -calc_outputs['l12_span_loss'] - components_dcm[0]['power'],
                'dispersion': dwdm.dispersion(calc_outputs['l12_length'], df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'])
            }
        ]
    except KeyError:
        components_l1 = [
            {
                'power': -calc_outputs['span_1_loss'] - components_dcm[0]['power'],
                'dispersion': dwdm.dispersion(user_inputs['l1_length'], df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'])
            }
        ]
    components_pt = [
        {
            'power': calc_outputs['p1_gain'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_comm_addrop.loc[user_inputs['pt_degree'], 'Degree ROADM (dB)'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_addrop_comm.loc[user_inputs['pt_degree'], 'Degree ROADM (dB)'],
            'dispersion': 0
        },
        {
            'power': calc_outputs['b2_gain'],
            'dispersion': 0
        },
    ]
    try:
        components_l2 = [
            {
                'power': -calc_outputs['l21_span_loss'],
                'dispersion': dwdm.dispersion(calc_outputs['l21_length'], df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'])
            },
            {
                'power': df_edfa_spec.loc['Minimum Gain (G)', 'Power Values'],
                'dispersion': 0
            },
            {
                'power': -calc_outputs['l22_span_loss'] - components_dcm[0]['power'],
                'dispersion': dwdm.dispersion(calc_outputs['l22_length'], df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'])
            }
        ]
    except KeyError:
        components_l2 = [
            {
                'power': -calc_outputs['span_2_loss'] - components_dcm[0]['power'],
                'dispersion': dwdm.dispersion(user_inputs['l2_length'], df_fiber_spec_l1.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)'])
            }
        ]
    components_rx = [
        {
            'power': calc_outputs['p2_gain'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_comm_addrop.loc[user_inputs['rx_degree'], 'Degree ROADM (dB)'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_comm_addrop.loc[user_inputs['rx_degree'], 'Directionless ROADM (dB)'],
            'dispersion': 0
        },
        {
            'power': -df_insert_loss_spec_comm_addrop.loc[user_inputs['rx_degree'], 'MDU Loss (dB)'],
            'dispersion': 0
        },
    ]
    components = components_tx + components_l1 + components_dcm + components_pt + components_l2 + components_dcm + components_rx
    p = user_inputs['input_power']
    d = 0
    node_num = [0]
    power = [p]
    dispersion = [d]
    for i, c in enumerate(components):
        p += c['power']
        d += c['dispersion']
        node_num.append(i+1)
        power.append(p)
        dispersion.append(d)
    return pd.DataFrame({
        'Node Numbers': node_num,
        'Power (dBm)': power,
        'Dispersion (ps/nm)': dispersion
    }).set_index('Node Numbers')

def main(argv):
    if len(argv) > 0:
        is_delay = not (argv[0] == 'off')
        utils.init(is_delay)

    clear()
    logIntro()
    ask_log_fiber_spec(df_fiber_spec_l1, 1)
    ask_log_fiber_spec(df_fiber_spec_l2, 2)
    ask_log_tables()
    ask_num_channel()
    calc_log_pout_per_channel()
    calc_log_total_link_length()
    calc_log_dispersion()
    calc_log_span_loss()
    ask_site_degrees()
    ask_calc_gain()
    while(not calc_log_receive_end()):
        log("Please redesign your link.", color="red")
        log("")
        
        answers = prompt([{
            'type': 'confirm',
            'name': 'redesign',
            'message': 'Do you want to redesign?'
        }])
        if not answers['redesign']:
            return 1

        ask_log_tables()
        ask_num_channel()
        calc_log_pout_per_channel()
        calc_log_total_link_length()
        calc_log_dispersion()
        calc_log_span_loss()
        ask_site_degrees()
        ask_calc_gain()
        
    # TODO: table output
    log('Table. Calculation Results For DWDM Link With Single Channel', color="green")
    log("")
    df_table = create_table()
    log_df(df_table, flag='pmt')

if __name__ == "__main__":
    main(sys.argv[1:])