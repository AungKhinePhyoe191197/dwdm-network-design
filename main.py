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

style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})

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
})

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

def logAndModify(df, title, desc):
    log('=' * 50)
    log(title, color="green")
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
    

def main():
    clear()
    logIntro()
    logAndModify(df_fiber_spec, "Fiber Specification",
        "This table show the general value of SM fiber specification.")
    logAndModify(df_insert_loss_spec_addrop_comm, "Insertion losses from add/drop port to common port",
        "This table shown the general insertion losses from add/drop to common of MDU, \
Directionless ROADM and Degree ROADM.")
    logAndModify(df_insert_loss_spec_comm_addrop, "Insertion losses from common port to add/drop port",
        "This table shown the general insertion losses common port to add/drop port of MDU, \
Directionless ROADM and Degree ROADM.")

if __name__ == "__main__":
    main()