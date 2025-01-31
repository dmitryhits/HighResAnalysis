# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/15_cern.calibration.ipynb.

# %% auto 0
__all__ = ['CERNCalibration']

# %% ../../nbs/15_cern.calibration.ipynb 2
from ..src.calibration import Calibration, Run
from ..utility.utils import remove_letters, critical

# %% ../../nbs/15_cern.calibration.ipynb 3
class CERNCalibration(Calibration):

    def __init__(self, run: Run):
        super().__init__(run)

    def load_raw_filename(self):
        files = sorted(list(self.Dir.glob('phCal[0-9]*.dat')), key=lambda x: int(remove_letters(x.name)))
        f = files[next((i - 1 for i, f in enumerate(files) if self.Run.Number < int(remove_letters(f.name.split('-')[0]))), -1)]
        return f if f.exists() else critical(f'could not find adc calibration file {f} ...')

    def get_trim_number(self, n=None):
        f = self.load_raw_filename().stem.split('-')
        return int(f[1]) if len(f) == 2 else None, n
