from __future__ import print_function, unicode_literals
import regex
import pandas as pd

import six
import os
clear = lambda: os.system('cls')
from tabulate import tabulate
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict, Separator)

from utils import log, log_df, generate_questions, update_answers

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

def main():
    clear()
    logIntro()
    logAndModify(df_fiber_spec, "Fiber Specification", 
        "This table show the general value of SM fiber specification.")
    log_seperator("=")
    logAndModify(df_insert_loss_spec_addrop_comm, "Insertion losses from add/drop port to common port",
        "This table shown the general insertion losses from add/drop to common of MDU, Directionless ROADM and Degree ROADM.")
    log_seperator("=")
    logAndModify(df_insert_loss_spec_comm_addrop, "Insertion losses from common port to add/drop port",
        "This table shown the general insertion losses common port to add/drop port of MDU, Directionless ROADM and Degree ROADM.")
    log_seperator("=")
    ask_transceiver_power_values()
    log_seperator("=")
    ask_connector_loss_value()
    log_seperator("=")
    logAndModify(df_edfa_spec, "EDFA power specification",
        "This table shown the general value of EDFA power specification.")
    log_seperator("=")
    logAndModify(df_dcm_spec, "DCM specificatoin",
        "This table show the general types and values of DCM.")

if __name__ == "__main__":
    main()