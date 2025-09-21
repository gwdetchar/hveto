#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: nu:ai:ts=4:sw=4

#
#  Copyright (C) 2025 Joseph Areeda <joseph.areeda@ligo.org>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

""""""
import os
import subprocess
import textwrap
import time
from datetime import datetime, timedelta, timezone
import socket

from pytz import reference

start_time = time.time()

import argparse
import logging
from pathlib import Path
import re
import sys
import traceback
from gwpy.time import to_gps, from_gps

try:
    from .._version import __version__
except ImportError:
    __version__ = '0.0.0'

__author__ = 'joseph areeda'
__email__ = 'joseph.areeda@ligo.org'
__process_name__ = re.sub(Path(__file__).suffix, '', Path(__file__).name)

logger = None
TOO_MUCH = 5        # logging level more verbose than DEBUG

hveto_run_sh = textwrap.dedent('''\
    #!/bin/bash
    # script used by %program_name% condor DAG to run one analysis
    # Created by %program_name% version %program_version% on %date%

    # Run specific variables
    configuration="%configuration%"
    nproc=%nproc%
    ifo=%ifo%
    gpsstart="%gpsstart%"
    gpsend="%gpsend%"
    outer_dir="%outer_dir%"
    prefix="%prefix%"
    timeout=%timeout%
    omega_scans=%omega_scans%
    omega_arg=""
    if [ "${omega_scans}" -gt 0 ]
    then
        omega_arg="--omega-scans ${omega_scans}"
    fi

    # run proram in conda environment
    condaRun="/cvmfs/software.igwn.org/conda/condabin/conda run --prefix ${prefix} --no-capture-output  "

    # use a 3 hour timeout to prevent hanging jobs
    timeout_cmd="timeout --kill-after=${timeout}s ${timeout}"

    cmd="python -m hveto ${gpsstart} ${gpsend} --ifo ${ifo} --config-file ${configuration} --nproc ${nproc} \
        --output-directory ${outer_dir} ${omega_arg}"

    ${condaRun} ${timeout_cmd} ${cmd}

    ''')

hveto_job_submit = textwrap.dedent('''\
    #!/usr/bin/env condor_submit
    #
    # Condor submit file for hveto processing in batch mode
    #
    # Created by %program_name% version %program_version% on %date%
    #

    universe = vanilla
    executable = %exec%

    accounting_group = ligo.dev.o4.detchar.dqtriggers.hveto
    accounting_group_user = joseph.areeda

    request_memory = %request_memory%M
    request_disk = 10GB

    output = %condor_dir%/hveto.out
    error = %condor_dir%/hveto.err
    log = %condor_dir%/hveto.log

    batch_name = "%job_name% ID: $(ClusterId)"

    use_oauth_services = scitokens
    environment = BEARER_TOKEN_FILE=$$(CondorScratchDir)/.condor_creds/scitokens.use

    queue
''')

check_dag_txt = textwrap.dedent('''\
    #!/bin/bash
    # check whether the omega DAG file exists
    # Created by %program_name% version %program_version% on %date%

    if [ -f %omega_dag_file% ]
    then
        echo "Omega DAG file %omega_dag_file% exists" >> %log_file%
        exit 0
    else
        echo "Omega DAG file %omega_dag_file% does not exist" >> %log_file%
        exit 12
    fi
    ''')


def to_day(in_str):
    in_gps = to_gps(in_str)
    in_date = from_gps(in_gps)
    ret = in_date.strftime('%Y-%m-%d')
    return ret


def get_default_ifo():
    # if at a site we have a default ifo
    host = socket.getfqdn()
    if 'ligo-la' in host:
        ifo = 'L1'
    elif 'ligo-wa' in host:
        ifo = 'H1'
    else:
        ifo = os.getenv('IFO')
    if ifo is None:
        ifo = 'UK'
    return ifo, host


def parser_add_args(parser):
    """
    Set up command parser
    :param argparse.ArgumentParser parser:
    :return: None but parser object is updated
    """
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help='increase verbose output')
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)
    parser.add_argument('-q', '--quiet', default=False, action='store_true',
                        help='show only fatal errors')

    this_script = Path(__file__)
    user = os.getenv('USER')
    config_possibles = [
        this_script.parent.parent / 'configurations' / 'hveto' / 'h1l1-hveto-daily-o4b.ini',
        Path(f'/home/{user}/etc/ligo-monitors/configurations/hveto/h1l1-hveto-daily-o4b.ini'),
        Path('/home/detchar/etc/ligo-monitors/configurations/hveto/h1l1-hveto-daily-o4b.ini'),
    ]
    default_config_file = None
    for config in config_possibles:
        if config.exists():
            default_config_file = config
            break

    parser.add_argument('-c', '--config-file', default=default_config_file, help='path to hveto configuration file')

    now_utc = datetime.now(timezone.utc)
    default_end_date = now_utc.strftime('%Y-%m-%d')
    default_start_date = (now_utc - timedelta(days=7)).strftime('%Y-%m-%d')

    parser.add_argument('-e', '--end', type=to_day, default=default_end_date,
                        help='Processng looks back duration days up to but not including this date. (default: %(default)s).')
    parser.add_argument('-s', '--start', type=to_day, default=default_end_date,
                        help='We process one day at a time from end daste back to star date each '
                             'run is duration days long (default: %(default)s).')
    parser.add_argument('-d', '--duration', type=int, default=7,
                        help='Number of days analyze for each day (default: %(default)s).')
    parser.add_argument('--today', action='store_true',
                        help='Process today\'s data it will be for 8, 16 or 24 hours dependng on current time. '
                             'Start, end and duration are ignored')

    parser.add_argument('--yesterday', action='store_true',
                        help='Process yesterday\'s data. '
                             'This is equivalent to --start yesterday --end yesterday --duration 1')

    parser.add_argument('--this-week', action='store_true',
                        help='Process this week\'s data. '
                             f'This is equivalent to --start {default_start_date} --end {default_end_date} --duration 7')
    parser.add_argument('--stride', type=int, default=1,
                        help='Number of days between each hveto run. '
                             'For example start=7/1, end=7/29, stride=7, duration=7'
                             'will create 4 hveto reports ending on 7/29, 7/22, 7/15, 7/8, 7/1 each covering 7 days')
    parser.add_argument('--no-submit', action='store_true',
                        help='Create directory, script and submit file but do not submit to Condor')

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('-o', '--output-directory', type=Path,
                              default=f'/home/{os.getenv("USER")}/public_html/hveto',
                              help='Parent directory for what may be multiple hveto runs. '
                                   'A subdirectory based on duration will be used for each run. ')
    output_group.add_argument('-O', '--output-directory-exact', type=Path,
                              help='Parent directory for what may be multiple hveto runs. '
                                   'A subdirectory based on duration will NOT be used for each run. ')

    prefix = os.getenv('CONDA_PREFIX', '/home/detchar/.conda/envs/ligo-summary-3.10')
    parser.add_argument('-p', '--prefix', default=prefix, help='Path to conda environment to run hveto in')

    ifo, host = get_default_ifo()
    parser.add_argument('-i', '--ifo', default=ifo, help='IFO for hveto analysis')
    parser.add_argument('-n', '--nproc', default=4, type=int, help='Number of parallel tigger readers')
    parser.add_argument('--omega-scans', type=int, default=0,
                        help='Number of omega scans per round.'
                             ' Small numbers arerecommended for weekly runs because of the high number of rounds')


def apply_symbols(txt, symbols):
    """
    Search text for {<symbol>} entries use <symbol> as key to dicionary then substite its value
    :param str txt: input string with <symbol> entries
    :param dict symbols: symbol table
    :return str: text with substitutions applied
    """
    ret = ''
    for line in txt.splitlines():
        oline = line
        while re.match('.*%.+%', oline):
            for symbol, value in symbols.items():
                pattern = '%' + rf'{symbol}' + '%'
                oline = re.sub(pattern, str(value), oline)
            if oline != line:
                logger.log(TOO_MUCH, f'  {line} -> {oline}')
            else:
                logger.critical(f'Undefined symbol in {line}')
            break
        ret += oline + '\n'
    return ret


def make_job(job_name, job_args):
    """
    Creates and prepares the directory and condor files for a single hveto job.

    :param str job_name: The name of the job to create
    :param dict job_args: The arguments to use for the job
    :return Path: Path to the submit file
    """
    job_dir = job_args['outer_dir']
    job_dir.mkdir(parents=True, exist_ok=True)
    job_condordir = job_args['condor_dir']
    job_condordir.mkdir(parents=True, exist_ok=True)

    job_submit_file = job_condordir / f'{job_name}.submit'
    job_run_sh = job_condordir / f'{job_name}.sh'
    job_args['job_name'] = job_name
    job_script = apply_symbols(hveto_run_sh, job_args)
    job_run_sh.write_text(job_script)
    job_run_sh.chmod(0o755)
    job_args['exec'] = job_run_sh

    job_submit = apply_symbols(hveto_job_submit, job_args)
    job_submit_file.write_text(job_submit)
    logger.info(f'Job name {job_name} created in {job_condordir}')
    logger.info(f'Created condor submit file {job_submit_file} ')
    logger.info(f' script {job_run_sh}')
    return job_submit_file


def get_today_start():
    """
    create a single job for today that processes 8, 16 or 24 hours of triggers based on current time

    :return str, datetime, int: date string (YYMMDD), as datetime object and duration in hours
    """

    now_dt = datetime.now(timezone.utc)
    run_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    now_hour = now_dt.hour
    if now_hour < 10:
        # process full day yesterday
        run_end = run_start
        run_start -= timedelta(hours=24)
        duration = 24
    elif now_hour < 18:
        run_end = run_start + timedelta(hours=8)
        duration = 8
    else:
        run_end = run_start + timedelta(hours=16)
        duration = 16
    job_day = run_start.strftime('%Y%m%d')
    logger.info(f'Running today {job_day} from {run_start} to {run_end}')

    return job_day, run_start, duration


def process_omega_scans(job_args_in):
    if job_args_in['omega_scans'] > 0:
        duration_label = job_args_in['duration_label']
        job_name = f'omega_{job_args_in["job_day"]}_{duration_label}'
        # Create a script to check whether omega scans DAG ha been made by hveto
        omega_dag_file = job_args_in["omega_dag_file"]
        omega_dag_file.parent.mkdir(parents=True, exist_ok=True)
        dag_log = job_args_in["dag_log"]
        job_args_omega = {'omega_dag_file': omega_dag_file, 'log_file': dag_log, 'job_name': job_name}
        dag_dir = job_args_in['dag_dir']
        check_dag_file = dag_dir / f'check_{job_name}.sh'
        job_args = {**job_args_in, **job_args_omega}
        check_dag_str = apply_symbols(check_dag_txt, job_args)
        check_dag_file.write_text(check_dag_str)

        dag_fh = job_args_in['dag_fh']
        job_day = job_args_in['job_day']
        print(f'SUBDAG EXTERNAL {job_name} "{omega_dag_file}"\n', file=dag_fh)
        print(f'PRE SCRIPT {job_name} "{check_dag_file}" "{omega_dag_file}"', file=dag_fh)
        print(f'PRE_SKIP {job_name} 12', file=dag_fh)
        print(f'PARENT {job_name} CHILD hveto_{job_day}_{duration_label}', file=dag_fh)


def main():
    global logger

    log_file_format = "%(asctime)s - %(levelname)s - %(funcName)s %(lineno)d: %(message)s"
    log_file_date_format = '%m-%d %H:%M:%S'
    logging.basicConfig(format=log_file_format, datefmt=log_file_date_format)
    logger = logging.getLogger(__process_name__)
    logger.setLevel(logging.DEBUG)

    description = textwrap.dedent("""
    Create a bash script and condor_submit for a multi-day run of hveto, then submit to vanilla universe
    By default:
    - We process 7 days of data ending at 00:00 UTC today, expecting it to run around 02:00Z
    - Output goes to ~/public_html/hveto/weekly/<YYYYMM>/<YYYYMMDD>/
    - Uses the configuration file "h1l1-hveto-daily-o4b.ini" found at
      <path to this script>/../configurations/hveto/ or
      ~/etc/ligo-monitors/configurations/hveto/ or
      /home/detchar/etc/ligo-monitors/configurations/hveto/
    """)

    epilog = textwrap.dedent("""
    Running with default (no) arguments  will run hveto over 7 days of data ending at 00:00 UTC this morning.

    To run hveto for every day for the month of July, each run covering 7 days:

        python -m weekly_hveto --start 7/1 --end 7/31 --duration 7 --stride 1

    """)
    parser = argparse.ArgumentParser(description=description, epilog=epilog, prog=__process_name__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser_add_args(parser)
    args = parser.parse_args()
    verbosity = 0 if args.quiet else args.verbose

    if verbosity < 1:
        logger.setLevel(logging.CRITICAL)
    elif verbosity < 2:
        logger.setLevel(logging.WARNING)
    elif verbosity < 3:
        logger.setLevel(logging.INFO)
    elif verbosity < 4:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(TOO_MUCH)

    duration = args.duration
    duration_dt = timedelta(days=duration)

    dur_str = ''
    if args.output_directory_exact:
        output_directory = Path(args.output_directory_exact)
    elif args.output_directory:
        output_directory = Path(args.output_directory)
        if duration == 1 or args.today:
            dur_str = 'day'
        elif duration == 7:
            dur_str = 'week'
        else:
            dur_str = f'{duration}days'

        output_directory = output_directory / dur_str

    now_dt = datetime.now(timezone.utc)
    now_time = now_dt.strftime('%Y%m%dT%H%M0%S')
    now_month = now_dt.strftime('%Y%m')

    if args.today:
        job_day, job_dt, duration = get_today_start()
        dag_dir = output_directory / job_day / 'condor'
    elif args.start == args.end:
        run_dt = datetime.strptime(args.start, '%Y-%m-%d')
        # if we are only doing one run then we use the condor directory for the DAG file
        dag_dir = output_directory / run_dt.strftime('%Y%m%d') / 'condor'
    else:
        dag_dir = output_directory / f'{__process_name__}-DAG' / now_month / f'DAG-{now_time}'

    dag_dir.mkdir(parents=True, exist_ok=True)
    dag_log = dag_dir / 'hveto-run.log'
    dag_file = dag_dir / 'hveto-run.dag'
    logger.info(f'Top level DAG file  will be written to {dag_file}')
    dag_file.parent.mkdir(parents=True, exist_ok=True)

    # add a copy of our logging to a file
    NOW = datetime.now()
    TIMEZONE = reference.LocalTimezone().tzname(NOW)
    DATEFMT = '%Y-%m-%d %H:%M:%S {}'.format(TIMEZONE)
    FMT = '%(name)s %(asctime)s %(levelname)+8s: %(filename)s:%(lineno)d:  %(message)s'
    logf_formatter = logging.Formatter(FMT, datefmt=DATEFMT)
    logf_handler = logging.FileHandler(dag_log, mode='w')
    logf_handler.setFormatter(logf_formatter)
    logger.addHandler(logf_handler)

    # debugging?
    logger.debug(f'{__process_name__} version: {__version__} called with arguments:')
    log_level_names = {logging.CRITICAL: 'CRITICAL', logging.ERROR: 'ERROR', logging.WARNING: 'WARNING',
                       logging.INFO: 'INFO', logging.DEBUG: 'DEBUG', TOO_MUCH: 'TOO_MUCH'}
    logger.debug(f'logger level set to {logger.getEffectiveLevel()} - {log_level_names[logger.getEffectiveLevel()]}')

    for k, v in args.__dict__.items():
        logger.debug('    {} = {}'.format(k, v))

    config = args.config_file
    if config is None:
        logger.critical('Configuration file not specified')
        raise ValueError('Configuration file not specified')

    if args.ifo == 'UK':
        logger.critical('IFO must be specified on command line or in the environment, if not running at LLO or LHO')
        raise ValueError('IFO must be specified')
    elif args.ifo not in ['L1', 'H1']:
        logger.critical(f'IFO {args.ifo} not in ["L1", "H1"]')
        raise ValueError(f'IFO {args.ifo} not in ["L1", "H1"]')

    start_day = args.start
    start_gps = to_gps(start_day)
    start_dt = from_gps(start_gps)

    end_day = args.end
    end_gps = to_gps(end_day)
    end_dt = from_gps(end_gps)
    next_dt = end_dt

    stride = args.stride
    stride_dt = timedelta(days=stride)

    # runtime args are used to create the job's bash script for both
    # the today job and the regular jobs
    job_args_common = {
        "configuration": config,
        "nproc": args.nproc,
        "ifo": args.ifo,
        "prefix": args.prefix,
        "program_name": __process_name__,
        "program_version": __version__,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "request_disk": 100000,
        "timeout": 3 * 3600,
    }

    # create a DAG file for each day in the range
    with dag_file.open('w') as dag_fh:
        job_args_common['dag_dir'] = dag_dir
        job_args_common['dag_log'] = dag_log
        job_args_common['dag_fh'] = dag_fh

        print(f'# process long duration hveto for {start_day} to {end_day}  \n'
              f'# run every (stride)  {stride} day(s) analyzing each over {duration} days', file=dag_fh)
        print(f'# Created by {__process_name__}, version {__version__}\n', file=dag_fh)

        print('CATEGORY ALL_NODES LIMIT', file=dag_fh)
        print('MAXJOBS LIMIT 3', file=dag_fh)
        print('RETRY ALL_NODES 2\n', file=dag_fh)

        if args.today:
            job_day, job_dt, duration = get_today_start()
            job_name = f'hveto_{job_day}_{duration:02d}hr'

            #  create the results directory and add the condor submit file and bash script
            job_dir = output_directory / job_day
            condor_dir = job_dir / 'condor'
            if duration == 24:
                job_end_dt = job_dt + timedelta(hours=duration)
                job_end_str = job_end_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                job_end_str = f'{job_dt.strftime("%Y-%m-%d")} {duration:02d}:00:00'
            job_args_today = {
                "gpsstart": f'{job_dt.strftime("%Y-%m-%d")}',
                "gpsend": job_end_str,
                'duration_label': f'{duration:02d}_hr',
                "outer_dir": job_dir,
                "condor_dir": condor_dir,
                "end_day": 'end_day',
                "out_of": 'out_of_',
                "omega_scans": args.omega_scans,
                "omega_dag_file": job_dir / 'scans' / 'condor' / 'gwdetchar-omega-batch.submit',
                "job_day": job_day,
                "duration": duration,
                "request_memory": 9216,
            }
            job_args = {**job_args_common, **job_args_today}
            job_submit_file = make_job(job_name, job_args)
            print(f'JOB {job_name} {job_submit_file}', file=dag_fh)
            process_omega_scans(job_args)

            njobs = 1
        else:

            njobs = int((end_dt - start_dt).days / stride) + 1
            current_job = 1

            while start_dt <= next_dt:
                begin_dt = to_day(next_dt - duration_dt)
                begin_day = to_day(begin_dt)
                next_day = to_day(next_dt)
                job_name = 'hveto'
                job_name += f'_{current_job:02d}_of_{njobs:02d}' if njobs > 1 else ''
                logger.debug(f'Process hveto {begin_day} to {next_day}')
                job_month = next_dt.strftime('%Y%m')
                job_day = next_dt.strftime('%Y%m%d')

                #  create the results directory and add the condor submit file and bash script
                if duration == 1:
                    job_dir = output_directory / job_day
                else:
                    job_dir = output_directory / job_month / job_day

                job_args_multi_day = {
                    "gpsstart": begin_day,
                    "gpsend": next_day,
                    'job_day': job_day,
                    'duration_label': f'{duration}_day',
                    "outer_dir": job_dir,
                    "condor_dir": job_dir / 'condor',
                    "end_day": next_day,
                    "out_of": f'{current_job:02d}_of_{njobs:02d}' if njobs > 1 else '',
                    "omega_dag_file": job_dir / 'scans' / 'condor' / 'gwdetchar-omega-batch.submit',
                    "omega_scans": args.omega_scans,
                    "request_memory": 10240,
                }
                job_args = {**job_args_common, **job_args_multi_day}
                job_submit_file = make_job(job_name, job_args)

                # add this job to the DAG
                print(f'JOB {job_name} {job_submit_file}', file=dag_fh)
                current_job += 1

                if job_args['omega_scans'] > 0:

                    process_omega_scans(job_args)

                next_dt -= stride_dt

        logger.info(f'DAG file with {njobs} jobs written to {dag_file}')
        if not args.no_submit:
            logger.info(f'Submitting {dag_file} to Condor')
            batch_name = f'hveto {start_dt.strftime("%m/%d")} to {next_dt.strftime("%m/%d")} $(ClusterId)'
            cmd = f'condor_submit_dag -import_env -batch-name "{batch_name}"  {dag_file}'
            logger.debug(f'Running: {cmd}')
            subprocess.run(cmd, shell=True, check=True)
        else:
            logger.info('DAG file written but not submitted to Condor')

    # report our run time
    logger.info(f'Elapsed time: {time.time() - start_time:.1f}s')


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, OSError, NameError, ArithmeticError, RuntimeError) as ex:
        print(ex, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    if logger is None:
        logging.basicConfig()
        logger = logging.getLogger(__process_name__)
        logger.setLevel(logging.DEBUG)
