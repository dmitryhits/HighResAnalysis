#!/usr/bin/env python
# --------------------------------------------------------
#       alignment and tracking of telescope data with proteus
# created on April 14th 2022 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------
from pathlib import Path
from os import chdir
import toml
from numpy import array
from plotting.utils import info, warning, choose
from utility.utils import print_banner, GREEN, print_elapsed_time
from subprocess import check_call, CalledProcessError


class Proteus:
    """ Alignment and tracking of telescope data.
        STEP 1: noisescan
        STEP 2: alignment
        STEP 3: tracking
        STEP 4: track-matching  """

    def __init__(self, soft_dir, data_dir, cfg_dir, raw_file, max_events=None, skip_events=None):

        # DIRECTORIES
        self.SoftDir = Path(soft_dir)
        self.DataDir = Path(data_dir)
        self.ConfigDir = Path(cfg_dir)

        self.RawFilePath = Path(raw_file)
        self.RunNumber = int(''.join(filter(lambda x: x.isdigit(), self.RawFilePath.stem)))

        self.N = max_events
        self.S = skip_events

        self.Steps = self.get_align_steps()

    def __repr__(self):
        return f'Proteus interface for run {self.RunNumber} ({self.RawFilePath.name})'

    def get_align_steps(self):
        # toml.load(PurePath('bla'))
        return list(toml.load(str(self.ConfigDir.joinpath('align.toml')))['align'])

    def get_align_files(self):
        return [self.ConfigDir.joinpath(name) for name in [self.toml_name('all', 'mask', 'mask'), self.toml_name()]]

    def get_alignment(self, step=-1):
        return toml.load(str(self.ConfigDir.joinpath(self.toml_name(self.Steps[step]))))

    def get_z_positions(self, raw=False):
        d = toml.load(str(self.ConfigDir.joinpath('geometry.toml' if raw else self.toml_name())))
        return array([s['offset'][-1] for s in d['sensors']])

    # ----------------------------------------
    # region MISC
    def toml_name(self, name=None, d='alignment', typ='geo'):
        return self.ConfigDir.joinpath(d, f'{self.Steps[-1] if name is None else name}-{typ}.toml')

    def make_empty_masks(self, cfg):
        for section in cfg:
            m = self.toml_name(section, d='mask', typ='mask')
            if not m.exists():
                m.write_text('[[sensors]]\nid = 0\nmasked_pixels = []\n')
    # endregion MISC
    # ----------------------------------------

    # ----------------------------------------
    # region RUN
    def run(self, prog, out, cfg=None, geo=None, section=None, f=None, n=None, s=None):
        old_dir = Path.cwd()
        chdir(self.ConfigDir)  # proteus needs to be in the directory where all the toml files are (for the default args)...
        cfg = '' if cfg is None else f' -c {str(cfg).replace(".toml", "")}.toml'
        section = '' if section is None else f' -u {section}'
        geo = '' if geo is None else f' -g {geo}'
        n = f' -n {choose(n, self.N)}' if choose(n, self.N) is not None else ''
        s = f' -s {choose(s, self.S)}' if choose(s, self.S) is not None else ''
        cmd = f'{self.SoftDir.joinpath("bin", prog)} {choose(f, self.RawFilePath)} {out}{cfg}{geo}{section}{n}{s}'
        info(cmd)
        try:
            check_call(cmd, shell=True)
        except CalledProcessError:
            warning(f'{prog} failed!')
        chdir(old_dir)

    def noise_scan(self):
        """ step 1: find noisy pixels. """
        d = Path('mask')
        cfg = toml.load(str(self.ConfigDir.joinpath('noisescan.toml')))['noisescan']
        self.make_empty_masks(cfg)
        for section in cfg:
            print_banner(f'Starting noise scan for {section}', color=GREEN)
            self.run('pt-noisescan', out=d.joinpath(section), cfg='noisescan', section=section)

    def align(self, step=None, force=False):
        """ step 2: align the telescope in several steps. """
        t = info('Starting alignment ...')
        d = Path('alignment')
        for i in range(len(self.Steps)) if step is None else [step]:
            step = self.Steps[i]
            if not self.toml_name(step).exists() or force:
                self.run('pt-align', out=d.joinpath(step), geo=self.toml_name(self.Steps[i - 1]) if i else None, section=step, cfg='align')
            else:
                warning('geo file already exists!')
        print_elapsed_time(t)

    def track(self):
        """ step 3: based on the alignment generate the tracks with proteus. """
        d = Path('root')
        self.run('pt-track', out=d.joinpath(f'track-{self.RunNumber:04d}'), cfg=self.toml_name())

    def match(self):
        """ step 4: match the tracks to the hits in the DUT with proteus. """
        d = Path('root')
        self.run('pt-match', out=d.joinpath(f'match-{self.RunNumber:04d}'), cfg=self.toml_name(), f=f'track-{self.RunNumber:04d}-data.root')
    # endregion RUN
    # ----------------------------------------


if __name__ == '__main__':
    from src.analysis import Analysis, Dir

    a = Analysis()
    sdir = Path(a.Config.get('SOFTWARE', 'dir')).expanduser().joinpath(a.Config.get('SOFTWARE', 'proteus'))
    f_ = a.BeamTest.Path.joinpath('data', f'run{17:06d}.root')
    z = Proteus(sdir, a.BeamTest.Path.joinpath('proteus'), Dir.joinpath('proteus'), f_, a.Config.getint('align', 'max events'), a.Config.getint('align', 'skip events'))
