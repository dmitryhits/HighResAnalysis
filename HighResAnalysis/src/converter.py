# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/37_src.converter.ipynb.

# %% auto 0
__all__ = ['Converter', 'batch_converter', 'Raw']

# %% ../../nbs/37_src.converter.ipynb 2
#!/usr/bin/env python

# %% ../../nbs/37_src.converter.ipynb 3
import uproot
from numpy import all, ones, count_nonzero, array  # noqa
from uproot import ReadOnlyDirectory
from uproot.models import TTree
from pathlib import Path
import awkward as aw  
from datetime import timedelta
from time import time
from inspect import signature
from subprocess import check_call
import h5py

from .proteus import Proteus
from .run import Run, Analysis, init_batch, DUT, Batch
from .analysis import BeamTest
from ..utility.utils import *
from ..utility.utils import Dir
# from HighResAnalysis.src.raw import Raw
from .calibration import Calibration
from .dut import Plane
from ..plotting.draw import Draw
from ..plotting.utils import warning, download_file, remove_file, add_to_info, GREEN, prep_kw, choose, info

# %% ../../nbs/37_src.converter.ipynb 4
class Converter:
    """Converts EUDAQ2 raw files in several steps into hdf5 files.
    STEP  0: raw -> root                  (EUDAQ2)
    STEP  1: noisescan                    (proteus)
    STEP  2: alignment                    (proteus)
    STEP  3: track reconstruction         (proteus)
    STEP  4: root -> hdf5                 (python)
    """

    DUTName = None

    def __init__(self, data_dir: Path, run_number, dut_name=None):
        self.T0 = time()
        self.T1 = timedelta(seconds=0)
        self.Run = Run(run_number, 0, data_dir)
        self.DUTName = dut_name  # only used in CERNConverter
        self.DUTs = self.init_duts()

        # DIRECTORIES
        self.DataDir = data_dir
        self.SaveDir = data_dir.joinpath('data')
        self.SoftDir = Path(Analysis.Config.get('SOFTWARE', 'dir')).expanduser()

        self.NTelPlanes = Analysis.Config.getint('TELESCOPE', 'planes')
        self.NDUTPlanes = self.Run.NDUTs

        # PRE-CONVERTER
        self.Raw = self.init_raw()
        self.Proteus = self.init_proteus()

        # FILES
        self.OutFilePath = self.SaveDir.joinpath(f'run{self.Run:04d}.hdf5')
        self.RawFile: ReadOnlyDirectory = None  # noqa
        self.F = None

    def __repr__(self):
        return f'{self.__class__.__name__} of {self.Run!r}'

    def run(self, force=False, steps=None, rm=True):
        if force or not self.OutFilePath.exists():
            self.T0 = info(f'Starting {self!r}\n')
            for i, (s, f) in enumerate(choose(steps, self.steps)):
                if not f.exists() or force:
                    print(f'-----starting step {i}')
                    print_banner(f'Start converter step {i}: {s.__doc__}')
                    try:
                        s(force=force) if 'force' in signature(s).parameters else s()
                    except Exception as err:
                        warning(f'converter crashed: {err}')
                        remove_file(f)
                        return False
                else:
                    info(f'found outfile of step {i}, continue with next step ({f})')
            if rm:
                self.remove_aux_files()
            add_to_info(self.T0, f'\nFinished {self!r} in ', color=GREEN)
            self.T1 = timedelta(seconds=time() - self.T0)
            return True
        return False

    @property
    def finished(self):
        return self.T1.total_seconds() > 0

    def raw2root(self, force=True):
        self.run(force=force, steps=self.first_steps, rm=False)

    def realign(self, rm=True):
        self.raw2root()
        self.Proteus.align(force=True)
        if rm:
            self.remove_aux_files()

    @property
    def first_steps(self):
        return self.Raw.Steps

    @property
    def steps(self):
        return self.first_steps + self.Proteus.Steps + [(self.root2hdf5, self.OutFilePath)]

    @property
    def aux_files(self):
        return [self.Proteus.RawFilePath, self.Proteus.OutFilePath, self.Proteus.HistFilePath]

    @property
    def raw_files(self):
        return [self.Raw.RawFilePath]

    def remove_files(self, all_=False):
        for s, f in self.steps:
            if f.suffix == '.root' or f.suffix == '.hdf5' or all_:
                remove_file(f)

    def remove_raw_files(self, warn=True):
        remove_file(*self.raw_files, warn=warn)

    def remove_aux_files(self):
        remove_file(*self.aux_files)

    def clean(self):
        self.remove_aux_files()

    @staticmethod
    def download_raw_file(f: Path, out=True, force=False):
        if not f.exists() or force:
            server, loc = [Analysis.Config.get('data', n) for n in ['server', 'server dir']]
            info(f'downloading DUT raw file from {server}:{loc}', prnt=out)
            f.parent.mkdir(exist_ok=True)
            return download_file(server, Path(loc).expanduser().joinpath(*f.parts[-4:]), f, out)

    def copy_raw_files(self, out=True, force=False):
        return [self.download_raw_file(f, out, force) for f in self.raw_files]

    # ----------------------------------------
    # region INIT
    @classmethod
    def from_run(cls, run: Run, dut_name=None):
        conv = cls(run.TCDir, run.Number, dut_name)
        conv.Run = run
        return conv

    @classmethod
    def from_ana(cls, run_number, dut=0, ana: Analysis = None):
        ana = choose(ana, Analysis)
        return cls.from_run(Run.from_ana(run_number, dut, ana))

    def init_proteus(self):
        soft_dir = self.SoftDir.joinpath(Analysis.Config.get('SOFTWARE', 'proteus'))
        data_dir = self.DataDir.joinpath('proteus')
        conf_dir = Dir.joinpath('proteus', self.DataDir.stem)
        me, se = [Analysis.Config.getint('align', opt) for opt in ['max events', 'skip events']]
        print('*************** Initing PROTEUS ******************')
        return Proteus(soft_dir, data_dir, conf_dir, raw_file=self.proteus_raw_file_path(), max_events=me, skip_events=se, dut_pos=self.dut_pos, duts=self.dut_names, align_run=self.Run.Number)

    def init_raw(self):
        return Raw(self)

    def init_event_alignment(self):
        return None

    @property
    def calibration(self):
        return Calibration

    def init_duts(self):
        return [DUT(i, self.Run.Info) for i in range(self.Run.NDUTs)]

    @property
    def dut_names(self):
        return [dut.Name for dut in self.DUTs]

    @property
    def dut_pos(self):
        return [dut.Position for dut in self.DUTs]

    def load_calibration(self, dut_nr=None):
        return self.calibration(self.Run if dut_nr is None else Run(self.Run.Number, dut_nr, self.Run.TCDir))

    def proteus_raw_file_path(self):
        return self.Raw.OutFilePath

    def load_file(self, opt='w'):
        return h5py.File(self.OutFilePath, opt)
    # endregion INIT
    # ----------------------------------------

    # ----------------------------------------
    # region HDF5
    def root2hdf5(self):
        """ convert tracked root file to hdf5 file. """
        remove_file(self.OutFilePath)  # remove hdf5 file if it exists
        start_time = info('starting root -> hdf5 conversion ...')

        self.F = self.load_file()
        self.RawFile = uproot.open(self.Proteus.OutFilePath)

        self.add_tracks()
        self.add_planes()

        add_to_info(start_time, '\nFinished hdf5 conversion in')
        self.F.close()
        self.F = None

    def add_tracks(self):
        t0 = info('adding track information ...', endl=False)
        g = self.F.create_group('Tracks')
        b = array([['evt_frame', 'Events', 'u4'], ['evt_ntracks', 'N', 'u1'],
                   ['trk_size',  'Size',   'f2'],
                   ['trk_chi2',  'Chi2',   'f2'], ['trk_dof', 'Dof', 'u1'],
                   ['trk_du',    'SlopeX', 'f2'], ['trk_dv', 'SlopeY', 'f2']]).T
        tree = self.RawFile['C0/tracks_clusters_matched']  # same for all planes
        self.add_time_stamp()
        self.add_data(tree, g, b)
        add_to_info(t0, color=GREEN)

    @property
    def time_stamp_file(self):
        return self.Raw.OutFilePath

    def get_time_stamp(self):
        t = array(uproot.open(self.time_stamp_file)['Event']['TimeStamp'])
        return ((t - t[0]) / 1e9).astype('f4')  # time stamp is just a number counting up

    def add_time_stamp(self):
        self.F.create_group('Event').create_dataset('Time', data=self.get_time_stamp())

    def add_planes(self):
        n = len(self.RawFile.keys(recursive=False))  # noqa (raises stupid warning)
        info(f'adding {n} planes ... ')
        PBAR.start(n * 2)
        for pl in range(n):
            try:
                self.add_plane(pl)
            except Exception as err:
                PBAR.finish()
                raise ValueError(f'root2hdf crashed adding plane {pl} having {err}')

    def add_plane(self, i):
        g = self.F.create_group(f'Plane{i}')
        key = list(self.RawFile.keys(recursive=False))[i]

        # mask
        m_tree = self.RawFile[f'{key}/masked_pixels']
        g.create_dataset('Mask', data=array(list(m_tree.arrays(library='np').values()), 'u2'))

        # cluster & track interpolations
        tree = self.RawFile[f'{key}/tracks_clusters_matched']
        self.add_plane_tracks(g, tree)
        self.add_clusters(g, tree)
        if i >= self.NTelPlanes + self.Proteus.NRefPlanes:
            self.add_trigger_info(g)

    @update_pbar
    def add_plane_tracks(self, group, tree: TTree):
        g = group.create_group('Tracks')
        b = array([['trk_u', 'U', 'f2'], ['trk_v', 'V', 'f2'], ['trk_col', 'X', 'f4'], ['trk_row', 'Y', 'f4'], ['trk_std_u', 'eU', 'f2'], ['trk_std_v', 'eV', 'f2']]).T
        self.add_data(tree, g, b)

    @update_pbar
    def add_clusters(self, group, tree: TTree):
        g = group.create_group('Clusters')
        cs = self.add_data(tree, g, array([['clu_size', 'Size', 'u2'], ['evt_nclusters', 'N', 'u2']]).T)['clu_size']
        b = array([['clu_u', 'U', 'f2'], ['clu_v', 'V', 'f2'], ['clu_col', 'X', 'f2'], ['clu_row', 'Y', 'f2'], ['clu_value', 'Charge', 'i']]).T
        self.add_data(tree, g, b, cut=cs > 0)  # filter out the nan events

    def trigger_info_file(self):
        return self.Raw.OutFilePath

    def add_trigger_info(self, group):
        tree = uproot.open(self.trigger_info_file())[f'{group.name}/Hits']
        g = group.create_group('Trigger')
        b = array([[key, key.replace('Trigger', ''), 'u1'] for key in tree.keys(filter_name='Trigger*')]).T
        self.add_data(tree, g, b)

    @staticmethod
    def add_data(tree: TTree, g, b, cut=...):
        data = tree.arrays(b[0], library='np')
        for i, (old_name, new_name, dtype) in enumerate(b.T):
            g.create_dataset(new_name, data=data[old_name][cut].astype(dtype))
        return data
    # endregion HDF5
    # ----------------------------------------

    # ----------------------------------------
    # region ALIGN
    def align_tree(self):
        import uproot
        hf = h5py.File(self.OutFilePath)
        with uproot.recreate('bla.root') as f:
            n = [array(hf[f'Plane{pl}']['Clusters']['Size']) > 0 for pl in range(self.NTelPlanes)]
            cut = all(n, axis=0) & (array(hf['Tracks']['Size']) == self.NTelPlanes)
            for pl in range(self.NTelPlanes):
                d = f.mkdir(f'Plane{pl}')
                ci = cut[n[pl]]
                i = count_nonzero(ci)
                d['Clusters'] = {'NClusters': ones(i, 'i'),
                                 'Col': array(hf[f'Plane{pl}']['Clusters']['X'])[ci].astype('d').reshape((-1, 1)),
                                 'Row': array(hf[f'Plane{pl}']['Clusters']['Y'])[ci].astype('d').reshape((-1, 1)),
                                 'VarCol': ones((i, 1)),
                                 'VarRow': ones((i, 1)),
                                 'Value': ones((i, 1)),
                                 'CovColRow': zeros((i, 1)),
                                 'Timing': zeros((i, 1)),
                                 'Track': ones((i, 1), 'i')}
            f['Plane0']['Clusters'].show()
    # endregion ALIGN
    # ----------------------------------------

    # ----------------------------------------
    # region MISC
    @staticmethod
    def check_root_version():
        v = gROOT.GetVersion()
        return True if v.startswith('6') else critical(f'ROOT 6 required for the conversion! Current version: {v}')
    # endregion MISC
    # ----------------------------------------

# %% ../../nbs/37_src.converter.ipynb 5
def batch_converter(cls: Converter):
    class BatchConverter(cls):

        def __init__(self, beam_test: BeamTest, batch_name):

            self.Batch = batch_name if isinstance(batch_name, Batch) else init_batch(batch_name, 0, beam_test)
            super().__init__(beam_test.Path, self.Batch.Runs[0].Number, self.Batch.DUTName)
            self.OutFilePath = self.Batch.FileName

        def __repr__(self):
            return f'{self.__class__.__name__} of {self.Batch!r}'

        def proteus_raw_file_path(self):
            return self.Batch.FileName.with_suffix('.root')

        @classmethod
        def from_batch(cls, b: Batch):
            return cls(b.BeamTest, b)

        def trigger_info_file(self):
            return super().trigger_info_file().with_name(f'dut-{self.Batch.FileName.stem}.root')

        @property
        def time_stamp_file(self):
            return self.trigger_info_file()

    return BatchConverter

# %% ../../nbs/37_src.converter.ipynb 6
class Raw:

    def __init__(self, c: Converter, load_file=False, step=-1):

        self.Parent = c
        self.Run = c.Run
        self.NT = c.NTelPlanes
        self.ND = c.NDUTPlanes
        self.P = range(self.NT)
        self.Planes = [Plane(i, typ='TELESCOPE' if i < self.NT else 'DUT') for i in range(self.NT + self.ND)]

        self.SoftDir = self.load_soft_dir()
        self.DataDir = c.DataDir
        self.SaveDir = c.SaveDir

        self.RawFilePath = self.load_raw_file_path()
        self.OutFilePath = self.load_out_file_path()

        if load_file:
            self.F = c.F if c.F is not None else h5py.File(c.OutFilePath, 'r')

        self.Steps = [(self.convert, self.OutFilePath)]
        self.AtStep = step
        self.Draw = Draw(Analysis.Config.FilePath)

    def __repr__(self):
        return f'{self.__class__.__name__} file analysis run {self.Run} ({self.RawFilePath.name})'

    # ----------------------------------------
    # region CONVERT
    def load_raw_file_path(self):
        return self.DataDir.joinpath('raw', f'run{self.Run:06d}.raw')

    def load_out_file_path(self):
        return self.SaveDir.joinpath(f'run{self.Run:06d}.root')

    def load_soft_dir(self):
        return self.Parent.SoftDir.joinpath(Analysis.Config.get('SOFTWARE', 'eudaq2'))

    def generate_fit_files(self):
        c = None
        for dut in range(self.Parent.NDUTPlanes):
            c = self.Parent.load_calibration(dut)
            if not c.FitFileName.exists():
                c.save_fit_pars()
        return c.CalPath

    @property
    def soft(self):
        return self.SoftDir.joinpath('bin', 'euCliConverter')

    def options(self, max_events=None):
        return f'-c {self.generate_fit_files()}{f" -m {max_events}" if max_events is not None else ""}'

    def convert(self, max_events=None):
        """ convert binary raw file to root file with eudaq"""
        Converter.download_raw_file(self.RawFilePath)
        self.OutFilePath.parent.mkdir(exist_ok=True)
        cmd = f'{self.soft} -i {self.RawFilePath} -o {self.OutFilePath} {self.options(max_events)}'
        info(f'Convert {self.RawFilePath.name} to {self.OutFilePath.name} using {self.soft.name}\n')
        info(f'{cmd}\n')
        check_call(cmd, shell=True)
        for f in Path().glob('AutoDict_vector*'):
            remove_file(f)
    # endregion CONVERT
    # ----------------------------------------

    # ----------------------------------------
    # region ANALYSIS
    def get(self, p, g, k):
        return array(self.F[f'Plane{p}'][g][k])

    def z(self):
        return self.Parent.Proteus.z_positions(raw=True)[:self.NT]

    def l2g(self, x, y, p, step=None):
        p = self.Planes[p]
        a = self.Parent.Proteus.alignment(choose(step, self.AtStep))['sensors'][p.Number]
        ox, oy = array(a['offset'][:2])
        rx, ry = array(a['unit_u']), a['unit_v']
        return transform(x, y, sx=p.PX, sy=p.PY, ox=ox, oy=oy, rx=rx, ry=ry, order='trs')

    def xy(self, p, cut=...):
        return [self.get(p, 'Clusters', k)[cut] for k in ['X', 'Y']]

    def txy(self, p, cut=...):
        return [self.get(p, 'Tracks', k)[cut] for k in ['X', 'Y']]

    def uv(self, p, cut=..., step=None):
        return self.l2g(*self.xy(p, cut), p, step)

    def uvs(self, step=None):
        return array([self.uv(p, c, step) for p, c in zip(self.P, self.cuts())])

    def tuv(self, p, cut=..., step=None):
        return self.l2g(*self.txy(p, cut), p, step)

    def tuvs(self, step=None):
        return array([self.tuv(p, self.cut(), step) for p in self.P])

    def du(self, p, step=None):
        c = self.all_planes()
        return self.uv(p, self.cuts(c)[p], step)[0] - self.tuv(p, self.cut(c), step)[0]

    def all_planes(self):
        return array(self.F['Tracks']['Size']) == self.NT

    def cuts(self, cut=True):
        n = [self.get(p, 'Clusters', 'Size') > 0 for p in self.P]
        c = all(n, axis=0) & cut
        return [c[i] for i in n]

    def res(self):
        return array([Gauss(self.draw_du(p, show=False)).fit(draw=False).get_pars(err=False)[1:] for p in self.P])

    def cut(self, cut=True):
        return all([self.get(p, 'Clusters', 'Size') > 0 for p in self.P], axis=0) & cut

    def draw_clu_u(self, i=0, step=None):
        self.Draw.graph(self.z(), self.uvs(step)[:, 0, :].T[i], x_tit='Z [mm]', y_tit='Cluster U [mm]')

    def draw_track_u(self, i=0, step=None):
        self.Draw.graph(self.z(), self.tuvs(step)[:, 0, :].T[i], x_tit='Z [mm]', y_tit='Track U [mm]')

    def draw_du(self, p=0, step=None, **dkw):
        return self.Draw.distribution(self.du(p, step) * 1e3, **prep_kw(dkw, x_tit='dU [#mum]'))

    def draw_clu_y(self, i=0, step=None):
        self.Draw.graph(self.z(),  self.uvs(step)[:, 1, :].T[i], x_tit='Z [mm]', y_tit='V [mm]')
    # ----------------------------------------
    # endregion ANALYSIS
