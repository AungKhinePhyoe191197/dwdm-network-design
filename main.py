from __future__ import print_function, unicode_literals
import regex

import six
from pyfiglet import figlet_format
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict)

try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

try:
    from termcolor import colored
except ImportError:
    colored = None

style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})

def log(string, color, font="slant", figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

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

questions = [
    {
        'type': 'input',
        'name': 'num_channel',
        'message': 'Number of channel',
        'validate': NumChannelValidator,
        'filter': lambda val: int(val)
    },
    {
        'type': 'input',
        'name': 'amplifier_max_output_power',
        'message': 'Maximum output power of amplifier in dBm',
        'validate': NumberValidator,
        'filter': lambda val: int(val),
        'default': '20'
    },
    {
        'type': 'input',
        'name': 'amplifier_gain_min',
        'message': 'Minimum gain of amplifier',
        'validate': NumberValidator,
        'filter': lambda val: int(val)
    },
    {
        'type': 'input',
        'name': 'amplifier_gain_max',
        'message': 'Maximum gain of amplifier',
        'validate': NumberValidator,
        'filter': lambda val: int(val)
    },
    {
        'type': 'input',
        'name': 'length_line_1',
        'message': 'Length of line 1',
        'validate': NumberValidator,
        'filter': lambda val: int(val)
    },
    {
        'type': 'input',
        'name': 'length_line_2',
        'message': 'Length of line 2',
        'validate': NumberValidator,
        'filter': lambda val: int(val)
    }
]

def askQuestions(questions):
    return prompt(questions, style=style)

def main():
    log(chr(27) + "[2J", color="white")
    log("Power Budget", color="blue", figlet=True)
    log("Welcome to power budget", color="green")
    log("This program is for calculating power budget of DWDM transmission Link (Distance of 80 km to 220 km", color="white")

if __name__ == "__main__":
    main()