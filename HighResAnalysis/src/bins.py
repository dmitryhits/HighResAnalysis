# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/41_src.bins.ipynb.

# %% auto 0
__all__ = ['MaxADC', 'MinPH', 'MaxPH', 'PHBinWidth', 'MinVcal', 'MaxVcal', 'TP', 'get_time', 'get_local', 'get_local_x',
           'get_local_y', 'get_corr', 'get_global', 'get_xy', 'get_global_x', 'get_x', 'get_y', 'get_global_y',
           'get_pixel', 'get_adc', 'get_vcal', 'get_electrons', 'get_ph', 'get_triggerphase']

# %% ../../nbs/41_src.bins.ipynb 2
#!/usr/bin/env python

# %% ../../nbs/41_src.bins.ipynb 3
from ..plotting.binning import *

# %% ../../nbs/41_src.bins.ipynb 4
MaxADC = 2**8 - 1

# %% ../../nbs/41_src.bins.ipynb 5
MinPH = -5000

# %% ../../nbs/41_src.bins.ipynb 6
MaxPH = 65000

# %% ../../nbs/41_src.bins.ipynb 7
PHBinWidth = 200

# %% ../../nbs/41_src.bins.ipynb 8
MinVcal = -100

# %% ../../nbs/41_src.bins.ipynb 9
MaxVcal = 1250

# %% ../../nbs/41_src.bins.ipynb 10
def get_time(t_vec, bin_width, last=False):
    return make(t_vec[0], t_vec[-1], bin_width, last)

# %% ../../nbs/41_src.bins.ipynb 12
def get_local(plane, bin_width=1, aspect_ratio=False):
    return get_local_x(plane, bin_width, aspect_ratio) + get_local_y(plane, bin_width, aspect_ratio)

# %% ../../nbs/41_src.bins.ipynb 13
def get_local_x(plane, bin_width=1, aspect_ratio=False):
    extra_pixel = round((plane.get_max_width() - plane.get_x_width()) / plane.PX / 2) if aspect_ratio else 0  # keep aspect ratio
    return make(-extra_pixel - .5, plane.NCols + extra_pixel - .5, bin_width)

# %% ../../nbs/41_src.bins.ipynb 14
def get_local_y(plane, bin_width=1, aspect_ratio=False):
    extra_pixel = round((plane.get_max_width() - plane.get_y_width()) / plane.PY / 2) if aspect_ratio else 0  # keep aspect ratio
    return make(-extra_pixel - .5, plane.NRows + extra_pixel - .5, bin_width)

# %% ../../nbs/41_src.bins.ipynb 15
def get_corr(mode, pl0, pl1, bw=1):
    return sum([get_local_x(pl, bw) if mode.lower() == 'x' else get_local_y(pl, bw) for pl in [pl0, pl1]], start=[])

# %% ../../nbs/41_src.bins.ipynb 16
def get_global(plane, res=1):
    return get_global_x(plane, res) + get_global_y(plane, res)

# %% ../../nbs/41_src.bins.ipynb 17
def get_xy(local, plane, bin_width=1, aspect_ratio=False):
    return get_local(plane, bin_width, aspect_ratio) if local else get_global(plane, bin_width)

# %% ../../nbs/41_src.bins.ipynb 18
def get_global_x(plane, res=1):
    """ calculates the global telescope bins
    :return: [nbins, bin_array] """
    xmax = plane.get_max_width() * .6  # to keep the aspect ratio
    return make(-xmax, xmax, res * plane.PX)

# %% ../../nbs/41_src.bins.ipynb 19
def get_x(plane, bw=1, res=1, local=True, aspect_ratio=False):
    return get_local_x(plane, bw, aspect_ratio) if local else get_global_x(plane, res)

# %% ../../nbs/41_src.bins.ipynb 20
def get_y(plane, bw=1, res=1, local=True, aspect_ratio=False):
    return get_local_y(plane, bw, aspect_ratio) if local else get_global_y(plane, res)

# %% ../../nbs/41_src.bins.ipynb 21
def get_global_y(plane, res=1):
    ymax = plane.get_max_width() * .6
    return make(-ymax, ymax, res * plane.PY)

# %% ../../nbs/41_src.bins.ipynb 22
def get_pixel(plane, res, outer=.5, cell=False):
    x0 = outer if plane.PX > plane.PY or cell else (2 * outer + 1) * (plane.R - 1) / 2 + outer
    y0 = outer if plane.PY > plane.PX or cell else (2 * outer + 1) * (plane.R - 1) / 2 + outer
    return make(-x0, 1 + x0, res, last=True) + make(-y0, 1 + y0, res, last=True)

# %% ../../nbs/41_src.bins.ipynb 23
def get_adc():
    return make(0, MaxADC)

# %% ../../nbs/41_src.bins.ipynb 24
def get_vcal(bin_width=1):
    return make(MinVcal, MaxVcal, bin_width)

# %% ../../nbs/41_src.bins.ipynb 25
def get_electrons(bin_width=200):
    return make(MinPH, MaxPH, bin_width)

# %% ../../nbs/41_src.bins.ipynb 26
def get_ph(vcal=False, adc=False, bin_width=None):
    return get_vcal() if vcal else get_adc() if adc else get_electrons(bin_width)

# %% ../../nbs/41_src.bins.ipynb 27
def get_triggerphase():
    return make(-.5, 10.5)

# %% ../../nbs/41_src.bins.ipynb 30
TP = get_triggerphase()
