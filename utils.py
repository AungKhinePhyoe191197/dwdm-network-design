import six
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

def trim(s):
    return s.replace(' ', '')

def log(string, color="white", font="slant", figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

def generate_questions(df, col_indices):
    cols = df.columns[col_indices]
    questions = [
        {
            'type': 'checkbox',
            'name': 'checkbox',
            'message': 'Select:',
            'choices': [{'name': col} for col in cols]
        }
    ]
    for col in cols:
        for val in df[col]:
            questions.append({
                'type': 'input',
                'name': col,
                'message': col,
                'default': f'{val}',
                'when': lambda answers, col=col: col in answers.get('checkbox')
            })
    return questions