# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/10_cern.raw.ipynb.

# %% auto 0
__all__ = ['CERNRaw']

# %% ../../nbs/10_cern.raw.ipynb 2
#!/usr/bin/env python

# %% ../../nbs/10_cern.raw.ipynb 3
from ..src.raw import Raw
from ..src.converter import Converter, Analysis

# %% ../../nbs/10_cern.raw.ipynb 4
class CERNRaw(Raw):

    def __init__(self, c: Converter, load_file=False, step=-1):
        self.Offset = 0
        super().__init__(c, load_file, step)

    def load_raw_file_path(self):
        return self.DataDir.joinpath('tel', f'acq{self.Run.Info["telescope run"]:03d}.bin')

    def load_out_file_path(self):
        return self.RawFilePath.with_name(f'tel-run{self.Run:04d}.root')

    def load_soft_dir(self):
        return self.Parent.SoftDir.joinpath(Analysis.Config.get('SOFTWARE', 'judith'))

    @property
    def soft(self):
        return self.SoftDir.joinpath('Judith')

    def options(self, max_events=None):
        emax = f' -n {max_events}' if max_events is not None else ''
        return f'-c convert -m {self.SoftDir.joinpath("configs", "readout", "CERN.cfg")}{f" -s {self.Offset}" if self.Offset else ""}{emax}'

    def convert(self, max_events=None):  # update doc str
        """convert binary raw file (from KARTEL telescope) to root file with judith."""
        super().convert()
