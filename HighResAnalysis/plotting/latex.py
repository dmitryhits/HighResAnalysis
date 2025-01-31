# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/08_plotting.latex.ipynb.

# %% auto 0
__all__ = ['f', 'multirow', 'makecell', 'bold', 'math', 'unit', 'si', 'qty', 'si_2err', 'num', 'num_2err', 'si_range',
           'qty_range', 'num_range', 'hline', 'table_row', 'table']

# %% ../../nbs/08_plotting.latex.ipynb 2
from numpy import array, column_stack

# %% ../../nbs/08_plotting.latex.ipynb 3
def f(name, *args):
    return f'\\{name}' + ''.join(f'{{{i}}}' for i in args)

# %% ../../nbs/08_plotting.latex.ipynb 4
def multirow(txt, n, pos='*'):
    return f('multirow', n, pos, txt)

# %% ../../nbs/08_plotting.latex.ipynb 5
def makecell(*txt):
    return f('makecell', '\\\\'.join(txt))

# %% ../../nbs/08_plotting.latex.ipynb 6
def bold(*txt):
    return [f('textbf', i) for i in txt]

# %% ../../nbs/08_plotting.latex.ipynb 7
def math(txt):
    return f'${txt}$'

# %% ../../nbs/08_plotting.latex.ipynb 8
def unit(*txt, custom=False):
    return f('unit', ''.join(f' {t}' if custom else f(t) for t in txt))

# %% ../../nbs/08_plotting.latex.ipynb 9
def si(*v, fmt='.1f', unt=None):
    return qty(*v, fmt=fmt, unt=unt)

# %% ../../nbs/08_plotting.latex.ipynb 10
def qty(*v, fmt='.1f', unt=None):
    return num(*v, fmt=fmt) if unt is None else [f('qty', f'{i:{fmt}}', f'\\{unt}').replace('/', '') for i in v]

# %% ../../nbs/08_plotting.latex.ipynb 11
def si_2err(*v, fmt='.1f', unt=None):
    return f('SIserr', *[f'{i:{fmt}}' for i in v], f(unt))

# %% ../../nbs/08_plotting.latex.ipynb 12
def num(*v, fmt='.1f', rm='@'):
    return [num_2err(i) if hasattr(i, '__len__') else f('num', f'{i:{fmt}}').replace('/', '').replace(rm, '') for i in v]

# %% ../../nbs/08_plotting.latex.ipynb 13
def num_2err(v, fmt='.1f'):
    return f('numerr', *[f'{i:{fmt}}' for i in v])

# %% ../../nbs/08_plotting.latex.ipynb 14
def si_range(v0, v1, fmt='.0f', unt=None):
    return qty_range(v0, v1, fmt, unt)

# %% ../../nbs/08_plotting.latex.ipynb 15
def qty_range(v0, v1, fmt='.0f', unt=None):
    return num_range(v0, v1, fmt) if unt is None else f('qtyrange', f'{v0:{fmt}}', f'{float(v1):{fmt}}', f'\\{unt}')

# %% ../../nbs/08_plotting.latex.ipynb 16
def num_range(v0, v1, fmt='.0f'):
    return f('numrange', f'{v0:{fmt}}', f'{v1:{fmt}}')

# %% ../../nbs/08_plotting.latex.ipynb 17
def hline(word):
    return word + ' \\\\' + f('hline') if 'hline' not in word else word

# %% ../../nbs/08_plotting.latex.ipynb 18
def table_row(*words, endl=False):
    row = f'  { " & ".join(words)}'
    return hline(row) if endl or 'hline' in row else f'{row} \\\\'

# %% ../../nbs/08_plotting.latex.ipynb 19
def table(header, rows, endl=False, align_header=False):
    cols = array(rows, str).T
    max_width = [len(max(col, key=len).replace(' \\\\\\hline', '')) for col in (column_stack([cols, header]) if align_header else cols)]  # noqa
    rows = array([[f'{word:<{w}}' for word in col] for col, w in zip(cols, max_width)]).T
    rows = '\n'.join(table_row(*row, endl=endl) for row in rows)
    return f'{table_row(*header, endl=True)}\n{rows}' if header else rows
