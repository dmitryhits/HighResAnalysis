# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_analyse.ipynb.

# %% auto 0
__all__ = ['t_start', 'main']

# %% ../nbs/00_analyse.ipynb 2
#!/usr/bin/env python

# %% ../nbs/00_analyse.ipynb 3
# from argparse import ArgumentParser
from numpy import *
from functools import partial
from time import time

import HighResAnalysis.convert as converter
from .plotting.draw import *  # noqa
import HighResAnalysis.src.bins as bins  # noqa
from .src.dut_analysis import DUTAnalysis, Analysis
from .src.batch_analysis import BatchAnalysis
from .src.run import load_nrs
from .src.scan import Ensemble, Scan, VScan, TScan
from .utility.utils import *  # noqa
from .src.spreadsheet import make
from .plotting.utils import load_json
from nbdev.showdoc import *

from fastcore.script import *

# %% ../nbs/00_analyse.ipynb 4
t_start = time()

# %% ../nbs/00_analyse.ipynb 7
@call_parse
def main(test:Param('test run, nothing is converted, just initialize the classes', action='store_false'),
         verbose:Param('verbosity level', action='store_false'),
         remove_meta:Param('removes meta files', action='store_false'),
         convert:Param('removes current analysis files and reconverts from the raw files', action='store_false'),
         test_campaign:Param('test campaign in the YYYYMM format, for example 201912', default=Analysis.find_testcampaign()),
         run:str=Analysis.Config.get_value('data', 'default run'), # run number or batch id or scan id
         dut:int=Analysis.Config.get_value('data', 'default dut', default=0), # DUT number in the telescope
         batch:str=None, #batch name
         run_plan:str=None, # create new runplan.json for beam test <YYYYMM>
        ):
    # ToDo: Check why sometimes it is 'False' could be name conflict test and test_campaign
    if test_campaign == 'False':
        test_campaign = Analysis.find_testcampaign() 
        print('test campaign was == "False":', test_campaign)
    
    if run_plan is not None:
        make(run_plan)
        exit(2)
    
    ensembles = load_json(Ensemble.FilePath)

    if run in ensembles:
        s = VScan if 'v-' in run else TScan if 't-' in run else Scan
        z = s(run, verbose, test)

    else:

        ana = Analysis(test_campaign)
        runs = load_nrs(ana.BeamTest.Path)
        is_batch = not (run in runs and batch is None)
        dut_ana = partial(BatchAnalysis, choose(batch, run)) if is_batch else partial(DUTAnalysis, run)
        dut_ana = partial(dut_ana, dut, test_campaign)

        if is_batch:
            print('Doing batch')
            bc = converter.BatchConvert(dut_ana.args[0], dut_ana.args[-1], verbose=False, force=False)
            if convert:
                remove_file(bc.Batch.FileName)
                bc.remove_aux_files()
            if not bc.Batch.FileName.exists() and not test:
                bc.run()

        if remove_meta:
            print('Removing Meta')
            z = dut_ana(verbose=False, test=True)
            z.remove_metadata()

        if convert and not is_batch:
            print('Convert but not batch')
            z = dut_ana(verbose=True, test=True)
            z.remove_file()
            z.Converter.remove_aux_files()

        z = dut_ana(verbose=verbose, test=test)

        # if not test and z.REF is not None and not z.has_alignment():
        #     z.Residuals.align(_save=True)
        #     z.REF.Residuals.align(_save=True)
        #     z.remove_metadata()
        #     z = DUTAnalysis(run, dut, test_campaign=test_campaign, single_mode=single_mode, verbose=verbose, test=test)

        z.add_info(t_start, 'Init time:', prnt=True)
        cut = z.Cut

    # aliases
    try:
        d = z.Draw
        dut = z.DUT
        pl = dut.Plane
        b = z.BeamTest
        r = z.Run
        c = z.Converter
        raw = c.Raw
        p = z.Proteus
        if 'CERN' in str(c):
            al = c.EventAlignment
            adc = c.Adc2Vcal
        cal = z.Calibration
        cut = z.Cut
        res = z.Residuals
        tel = z.Tel
        ref = z.REF
        t = z.Tracks
        e = z.Efficiency
        re = ref.Efficiency
        rsl = z.Resolution
        cur = z.Currents 
        print("Everything is available and ready for analysis!")
    except:
        print('Not everything is available :-(')
