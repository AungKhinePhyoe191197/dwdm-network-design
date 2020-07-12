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
    'l2_max': 120
}
user_inputs = {}
calc_outputs = {}

df_fiber_spec = pd.DataFrame({
    'Type': ['Single Mode (SM)'],
    'Attenuation (dB/km)': [0.275],
    'Dispersion coefficient (ps/nm-km)': [17]
}).set_index('Type')

df_insert_loss_spec_addrop_comm = pd.DataFrame({
    'ROADM Degree': [2, 4, 8],
    'MDU Loss (dB)': [14, 14, 14],
    'Directionless ROADM (dB)': [4, 7, 7],
    'Degree ROADM (dB)': [4, 7, 7]
}).set_index('ROADM Degree')

df_insert_loss_spec_comm_addrop = pd.DataFrame({
    'ROADM Degree': [2, 4, 8],
    'MDU Loss (dB)': [7, 7, 7],
    'Directionless ROADM (dB)': [7, 9, 11],
    'Degree ROADM (dB)': [7, 9, 11]
}).set_index('ROADM Degree')

df_edfa_spec = pd.DataFrame({
    'Amplifier Power Types': [
        'Flat Gain (FG)', 
        'Gain Range Upper (G)',
        'Gain Range Lower (G)', 
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
    'G.625.A': df_fiber_g625a,
    'G.625.B': df_fiber_g625b,
    'G.625.C': df_fiber_g625c,
    'G.625.D': df_fiber_g625d,
}

class NumChannelValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))  # Move cursor to end
        if not 40 <= int(document.text) <= 88:
            raise ValidationError(
                message='Number of channel must be between 40 and 88',
                cursor_position=len(document.text))

class NumberRangeValidator(Validator):
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def validate(self, document):
        # TODO: validator of number within range
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))  # Move cursor to end
        if not self.min <= int(document.text) <= self.max:
            raise ValidationError(
                message='Out of range',
                cursor_position=len(document.text))  # Move cursor to end

class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))  # Move cursor to end

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
    log("Amplifier used in this calculation are fixed gain EDFA amplifier.")
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
            'message': 'Minimum Transmit Power (dB)'
        },
        {
            'type': 'input',
            'name': 'transmit_pow_max',
            'message': 'Maximum Transmit Power (dB)'
        },
        {
            'type': 'input',
            'name': 'receive_pow_min',
            'message': 'Minimum Receive Power (dB)'
        },
        {
            'type': 'input',
            'name': 'receive_pow_max',
            'message': 'Maximum Receive Power (dB)'
        }
    ], style=style)
    log("")
    user_inputs.update(answers)

def ask_connector_loss_value():
    log("Please add the maximum connector loss value for the link")
    answers = prompt([
        {
            'type': 'input',
            'name': 'connector_loss_max',
            'message': 'Maximum Connector Loss (dB)'
        }
    ])
    log("")
    user_inputs.update(answers)

def ask_num_channel():
    log("To start the calculation, please input the number of channels (32 channels to 80 channels)")
    answers = prompt([
        {
            'type': 'input',
            'name': 'num_channel',
            'message': 'N =',
            'filter': lambda val: int(val)
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

def ask_option_1():
    log("Splicing Loss", color="green")
    log_df(df_splic_loss)
    answers = prompt([
        {
            'type': 'input',
            'name': 'splic_loss',
            'message': 'Each splicing loss value (dB) =',
            'filter': lambda val: float(val),
            'validate': lambda val: validate_fraction(val) and 0 <= float(val) <= df_splic_loss.loc['Single Fusion Splice', 'Maximum Attenuation Value (dB)'] or 'The value must not be empty and greater than maximum attenuation value.'
        },
        {
            'type': 'input',
            'name': 'num_splic',
            'message': 'Number of splices =',
            'filter': lambda val: int(val),
            'validate': lambda val: validate_number(val) or 'The value must be a number'
        }
    ], style=style)
    user_inputs.update(answers)
    log("")
    log("Connector Loss", color="green")
    log_df(df_connector_loss)
    answers = prompt([
        {
            'type': 'list',
            'name': 'connector_grade',
            'message': 'Please choose the connector grade:',
            'choices': [i for i in df_connector_loss.index],
        },
        {
            'type': 'input',
            'name': 'num_connector',
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
    answers = prompt([{
        'type': 'list',
        'name': 'fiber_class',
        'message': 'Please choose the cable class for calculation',
        'choices': [c for c in fiber_classes]
    }], style=style)
    user_inputs.update(answers)
    log("")
    log("The maximum attenuation coefficient value of %s is %.1f dB/km" % (
        user_inputs['fiber_class'],
        fiber_classes[user_inputs['fiber_class']].loc['1', 'Attenuation Coefficient (dB/km)']
    ))
    log("")
    answers = prompt([{
        'type': 'input',
        'name': 'attenuation_coefficient',
        'message': 'Please input the attenuation coefficient value for the cable (should not exceed than the max value of selected cable) =',
        'filter': lambda val: float(val),
        'validate': lambda val: validate_fraction(val) and 0 <= float(val) <= fiber_classes[user_inputs['fiber_class']].loc['1', 'Attenuation Coefficient (dB/km)'] or 'The value should not exceed than the max value of selected cable'
    }])
    user_inputs.update(answers)

def calc_log_option_1():
    # Calculations
    calc_outputs.update({
        'connector_loss': df_connector_loss.loc[user_inputs['connector_grade'], 'Maximum Attenuation Value (dB)']
    })
    calc_outputs.update({
        'total_splic_loss': dwdm.total_splic_loss(user_inputs['splic_loss'], user_inputs['num_splic']),
        'total_connector_loss': dwdm.total_connector_loss(calc_outputs['connector_loss'], user_inputs['num_connector']),
        'fiber_loss': dwdm.fiber_loss(user_inputs['attenuation_coefficient'], user_inputs['l1_length']),
    })
    calc_outputs.update({
        'link_loss': dwdm.link_loss(calc_outputs['total_splic_loss'], calc_outputs['total_connector_loss'], calc_outputs['fiber_loss'])
    })
    calc_outputs.update({
        'link_attenuation': dwdm.link_attenuation(calc_outputs['link_loss'], user_inputs['l1_length'])
    })
    # update to fiber spec dataframe
    df_fiber_spec.loc['Single Mode (SM)', 'Attenuation (dB/km)'] = calc_outputs['link_attenuation']

    # log to user
    log("Calculation for Link attenuation value of L1 started.", color='green')
    log("")
    log("Total Splicing Losses")
    log("Total Splice Losses (dB) = splice loss (dB) × number of splices = %.1f dB" % (
        calc_outputs['total_splic_loss']
    ))
    log("")
    log("Total Connector Losses")
    log("Total Connector Loss (dB) = connector loss (dB) × number of connectors = %.1f dB" % (
        calc_outputs['total_connector_loss']
    ))
    log("")
    log("Fiber Losses")
    log("Fiber losses (dB) = chosen attenuation coefficient value x length of L1 = %.1f dB" % (
        calc_outputs['fiber_loss']
    ))
    log("")
    log("Link loss budget for the cable plant")
    log("Link loss budget for the cable plant = Total Splice Losses (dB) + Total connector loss + (dB) Fiber losses = %.1f dB" % (
        calc_outputs['link_loss']
    ))
    log("")
    log("Link attenuation value")
    log("Link attenuation value (dB\km) = link loss budget for the cable plant / length of L1 = %.1f dB/km" % (
        calc_outputs['link_attenuation']
    ))
    log("")
    log("This table show the value of SM fiber Link specification.", color="green")
    log_df(df_fiber_spec, flag='pmt')

def ask_log_fiber_spec():
    answers = prompt([{
        'type': 'input',
        'name': 'l1_length',
        'message': 'Please Input the Length of L1 (km) =',
        'filter': lambda val: int(val),
        'validate': lambda val: validate_number(val) and constraints['l1_min'] <= int(val) <= constraints['l1_max'] or 'Length must be number and between %s and %s' % (constraints['l1_min'], constraints['l1_max'])
    }], style=style)
    user_inputs.update(answers)
    log("This table shows the value of SM fiber Link specification.", color="green")
    log_df(df_fiber_spec)
    log("")
    answers = prompt([
        {
            'type': 'confirm',
            'name': 'fiber_spec_change',
            'message': 'Do you want to change attenuation value of L1?',
        },
        {
            'type': 'list', 
            'name': 'fiber_spec_change_option',
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
            ]
        },
    ], style=style)
    user_inputs.update(answers)
    log("")
    if user_inputs['fiber_spec_change_option'] == '1':
        ask_option_1()
        calc_log_option_1()

def calc_and_log_pout_per_channel():
    calc_outputs.update({
        'pout_per_channel': dwdm.pout_per_channel(
            df_edfa_spec.loc['Maximum Output Power (Pout Max)', 'Power Values'],
            user_inputs['num_channel']
        )
    })
    log("The output power of an amplifier per channel in an N channel DWDM network is Pout (dBm) = Pin (dBm) + Gain (dB)")
    log("Pout/ch = Maximum output power – 10*log10 (N) = %.2f dBm" % (
        calc_outputs['pout_per_channel']
    ), color="green")
    log("Per channel output power is")
    log("Pin (dBm) + Gain (dB) = %.2f dBm" % (
        calc_outputs['pout_per_channel']
    ))
    log("In %d channel DWDM link, for single channel calculation the maximum output should be %.2f dBm." % (
        user_inputs['num_channel'],
        calc_outputs['pout_per_channel']
    ))

def main(argv):
    if len(argv) > 0:
        is_delay = not (argv[0] == 'off')
        utils.init(is_delay)

    clear()
    logIntro()
    ask_log_fiber_spec()
    # logAndModify(df_fiber_spec, "Fiber Specification", 
    #     "This table show the general value of SM fiber specification.")
    # log_seperator("=")
    # logAndModify(df_insert_loss_spec_addrop_comm, "Insertion losses from add/drop port to common port",
    #     "This table shown the general insertion losses from add/drop to common of MDU, Directionless ROADM and Degree ROADM.")
    # log_seperator("=")
    # logAndModify(df_insert_loss_spec_comm_addrop, "Insertion losses from common port to add/drop port",
    #     "This table shown the general insertion losses common port to add/drop port of MDU, Directionless ROADM and Degree ROADM.")
    # log_seperator("=")
    # ask_transceiver_power_values()
    # log_seperator("=")
    # ask_connector_loss_value()
    # log_seperator("=")
    # logAndModify(df_edfa_spec, "EDFA power specification",
    #     "This table shown the general value of EDFA power specification.")
    # log_seperator("=")
    # logAndModify(df_dcm_spec, "DCM specificatoin",
    #     "This table show the general types and values of DCM.")
    # log_seperator("=")
    # log("This program is focus on DWDM link of each channel carrying 10 Gbps of data. The number of channels in this link should be in the range of 32 channels to 80 channels.")
    # log("")
    # ask_num_channel()
    # calc_and_log_pout_per_channel()
    # log("Gain range of the amplifier should be in the range of %d to %d" % (
    #     df_edfa_spec.loc['Gain Range Lower (G)', 'Power Values'],
    #     df_edfa_spec.loc['Gain Range Upper (G)', 'Power Values']
    # ))
    # log("")
    # ask_line_lengths()
    # log("Total length of the link = %d km" % (
    #     user_inputs['l1_length'] + user_inputs['l2_length']
    # ))
    # log("")
    # log("Residual dispersion value should be in the range from -510 ps/nm to 1020 ps/nm.")
    # calc_outputs.update({
    #     'total_dispersion': total_disperssion(
    #         user_inputs['l1_length'],
    #         user_inputs['l2_length'],
    #         df_fiber_spec.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)']
    #     )
    # })
    # log("Total dispersion value of the link = %d ps/nm" % (
    #     calc_outputs['total_dispersion']
    # ))
    # log("")
    # if(calc_outputs['total_dispersion'] > 1020):
    #     log("Dispersion value too high, please choose the suitable DCM module for the link.")
    #     log_df(df_dcm_spec)
    #     answers = prompt([{
    #         'type': 'list',
    #         'message': 'Select:',
    #         'name': 'dcm_module',
    #         'choices': [i for i in df_dcm_spec.index]
    #     }])

if __name__ == "__main__":
    main(sys.argv[1:])