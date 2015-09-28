#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#
import os
from GangaGaudi.Lib.RTHandlers.RunTimeHandlerUtils import master_sandbox_prepare, sandbox_prepare, script_generator
from GangaDirac.Lib.RTHandlers.DiracRTHUtils import dirac_inputdata, dirac_ouputdata, mangle_job_name, diracAPI_script_template, diracAPI_script_settings
from GangaGaudi.Lib.RTHandlers.GaudiRunTimeHandler import GaudiRunTimeHandler
from Ganga.GPIDev.Adapters.StandardJobConfig import StandardJobConfig
from Ganga.GPIDev.Lib.File.OutputFileManager import getOutputSandboxPatterns, getWNCodeForOutputPostprocessing
from Ganga.Utility.Config import getConfig
from Ganga.Utility.util import unique
from GangaDirac.Lib.Files.DiracFile import DiracFile
#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#


class GaudiDiracRunTimeHandler(GaudiRunTimeHandler):

    """The runtime handler to run Gaudi jobs on the Dirac backend"""

    def prepare(self, app, appsubconfig, appmasterconfig, jobmasterconfig):
        inputsandbox, outputsandbox = sandbox_prepare(
            app, appsubconfig, appmasterconfig, jobmasterconfig)
        input_data,   parametricinput_data = dirac_inputdata(app)

        job = app.getJobObject()
        outputfiles = [this_file.namePattern for this_file in job.outputfiles if isinstance(this_file, DiracFile)]

        gaudi_script_path = os.path.join(
            job.getInputWorkspace().getPath(), "gaudi-script.py")
        script_generator(gaudi_script_template(),
                         #remove_unreplaced = False,
                         outputfile_path=gaudi_script_path,
                         PLATFORM=app.platform,
                         COMMAND='gaudirun.py'  # ,
                         #OUTPUTFILESINJECTEDCODE = getWNCodeForOutputPostprocessing(job, '    ')
                         )

        dirac_script = script_generator(diracAPI_script_template(),
                                        DIRAC_IMPORT='from DIRAC.Interfaces.API.Dirac import Dirac',
                                        DIRAC_JOB_IMPORT='from DIRAC.Interfaces.API.Job import Job',
                                        DIRAC_OBJECT='Dirac()',
                                        JOB_OBJECT='Job()',
                                        NAME=mangle_job_name(app),
                                        EXE=gaudi_script_path,
                                        EXE_ARG_STR=' '.join(
                                            [str(arg) for arg in app.args]),
                                        EXE_LOG_FILE='Ganga_%s_%s.log' % (
                                            app.appname, app.version),
                                        INPUTDATA=input_data,
                                        PARAMETRIC_INPUTDATA=parametricinput_data,
                                        OUTPUT_SANDBOX=outputsandbox,
                                        OUTPUTDATA=list(outputfiles),
                                        OUTPUT_PATH="",  # job.fqid,
                                        OUTPUT_SE=getConfig(
                                            'DIRAC')['DiracOutputDataSE'],
                                        SETTINGS=diracAPI_script_settings(app),
                                        DIRAC_OPTS=job.backend.diracOpts,
                                        PLATFORM=app.platform,
                                        # leave the sandbox for altering later as needs
                                        # to be done in backend.submit to combine master.
                                        # Note only using 2 #s as auto-remove 3
                                        INPUT_SANDBOX='##INPUT_SANDBOX##'
                                        )

        return StandardJobConfig(dirac_script,
                                 inputbox=unique(inputsandbox),
                                 outputbox=unique(outputsandbox))


#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#
def gaudi_script_template(self):
    '''Creates the script that will be executed by DIRAC job. '''

    script_template = """#!/usr/bin/env python
'''Script to run Gaudi application'''

from os import curdir, system, environ, pathsep, sep, getcwd
from os.path import join
import sys

def prependEnv(key, value):
    if key in environ: value += (pathsep + environ[key])
    environ[key] = value

# Main
if __name__ == '__main__':

    prependEnv('LD_LIBRARY_PATH', getcwd() + '/lib')
    prependEnv('PYTHONPATH', getcwd() + '/InstallArea/python')
    prependEnv('PYTHONPATH', getcwd() + '/InstallArea/###PLATFORM###/python')

    rc = system('''###COMMAND### ''' + ' '.join(sys.argv))/256

    ###OUTPUTFILESINJECTEDCODE###
    sys.exit(rc)
"""
    return script_template


#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#