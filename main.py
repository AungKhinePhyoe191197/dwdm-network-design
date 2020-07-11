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

from dwdm import pout_per_channel, total_disperssion

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

user_inputs = {}
calc_outputs = {}

df_fiber_spec = pd.DataFrame({
    'Fiber Type': ['Single Mode (SM)', 'Multi Mode (MM)'],
    'Attenuation (dB/km)': [0.275, 0.5],
    'Dispersion coefficient (ps/nm-km)': [17, 20]
}).set_index('Fiber Type')

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
    log("B is a booster amplifier.")
    log("P is a pre amplifier.")
    log("")
    log("There is an add/drop station between the transmission link. The length of the L2 should be equal or longer than the L1.")
    log("")
    log("Before the calculation starts, please choose and input the specification value of the devices.")
    log("")

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

def calc_and_log_pout_per_channel():
    calc_outputs.update({
        'pout_per_channel': pout_per_channel(
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
    ask_line_lengths()
    log("Total length of the link = %d km" % (
        user_inputs['l1_length'] + user_inputs['l2_length']
    ))
    log("")
    log("Residual dispersion value should be in the range from -510 ps/nm to 1020 ps/nm.")
    calc_outputs.update({
        'total_dispersion': total_disperssion(
            user_inputs['l1_length'],
            user_inputs['l2_length'],
            df_fiber_spec.loc['Single Mode (SM)', 'Dispersion coefficient (ps/nm-km)']
        )
    })
    log("Total dispersion value of the link = %d ps/nm" % (
        calc_outputs['total_dispersion']
    ))
    log("")
    if(calc_outputs['total_dispersion'] > 1020):
        log("Dispersion value too high, please choose the suitable DCM module for the link.")
        log_df(df_dcm_spec)
        answers = prompt([{
            'type': 'list',
            'message': 'Select:',
            'name': 'dcm_module',
            'choices': [i for i in df_dcm_spec.index]
        }])

if __name__ == "__main__":
    main(sys.argv[1:])