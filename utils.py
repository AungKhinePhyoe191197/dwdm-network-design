import six
from tabulate import tabulate
from pyfiglet import figlet_format

try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

try:
    from termcolor import colored
except ImportError:
    colored = None

def log(string, color="white", font="slant", figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

def log_df(df):
    log(tabulate(df, headers='keys', tablefmt='orgtbl'), color="blue")

def generate_questions(df):
    questions = [
        {
            'type': 'checkbox',
            'name': 'checkbox',
            'message': 'Select:',
            'choices': [{'name': col} for col in df.columns]
        }
    ]
    for col in df.columns:
        for val in df[col]:
            questions.append({
                'type': 'input',
                'name': col,
                'message': col,
                'default': f'{val}',
                'when': lambda answers, col=col: col in answers.get('checkbox')
            })
    return questions

def update_answers(df, answers):
    updated = False
    for ans in answers:
        if ans in df:
            df[ans] = answers[ans]
            updated = True
    return updated