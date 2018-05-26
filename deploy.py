#! /usr/bin/env python

from __future__ import print_function
from tempfile import NamedTemporaryFile
import argparse
import datetime
import os
import subprocess
import sys
import textwrap

FILE_PATH = os.path.dirname(__file__)


def run(cmd, fail=True, capture_stdout=False, capture_stderr=False, verbose=False):
    """
    Provides syntactic sugar around running a bash command as a subprocess
    :param cmd:  The command to run
    :param fail: Halt execution if bash command returns an error
    :param capture_stdout:  Capture standard out
    :param capture_stderr:  Capture standard error
    :param verbose:  Print the command before running
    :return:  A completed process object, p, on which you can execute p.stdout.read().decode(), etc,
    """
    stdout, stderr = None, None
    if capture_stderr:
        stderr = subprocess.PIPE
    if capture_stdout:
        stdout = subprocess.PIPE

    if verbose:
        print(cmd)

    p = subprocess.run(['bash', '-c', cmd], stderr=stderr, stdout=stdout)
    if p.returncode and fail:
        sys.exit(1)

    return p


def run_script(text, fail=True, capture_stdout=False, capture_stderr=False, verbose=False):
    with NamedTemporaryFile('w') as buff:
        buff.write(text)
        buff.flush()
        cmd = 'bash {}'.format(buff.name)
        return run(cmd, fail, capture_stdout, capture_stderr, verbose)


class Deploy(object):
    # (source, target)
    FILES_TO_LINK = [
        # Dot files
        ('~/dot_files/.bash_profile', '~/.bash_profile'),
        ('~/dot_files/.bashrc', '~/.bashrc'),
        ('~/dot_files/.inputrc', '~/.inputrc'),
        ('~/dot_files/.vim', '~/.vim'),
        ('~/dot_files/.vimrc', '~/.vimrc'),
        ('~/dot_files/.ideavimrc', '~/.ideavimrc'),
        ('~/dot_files/.ackrc', '~/.ackrc'),
        ('~/dot_files/.ctags', '~/.ctags'),
        ('~/dot_files/rcconda.sh', '~/rcconda.sh'),
        ('~/dot_files/gitignore_global', '~/.gitignore_global'),
        ('~/dot_files/flake8', '~/.config/flake8'),

        # Executables
        ('~/dot_files/git_diff_wrapper', '~/bin/git_diff_wrapper'),
        ('~/dot_files/git_branch_diff', '~/bin/git_branch_diff'),
        ('~/dot_files/circle_checker', '~/bin/circle_checker'),
        ('~/dot_files/serve_dir.py', '~/bin/serve_dir.py'),
        ('~/dot_files/imgcat', '~/bin/imgcat'),
        ('~/dot_files/make_tags', '~/bin/make_tags'),
        ('~/dot_files/clean_vim_backup.py', '~/bin/clean_vim_backup.py'),
        ('~/dot_files/diffconflicts', '~/bin/diffconflicts'),
        ('~/dot_files/myip', '~/bin/myip'),

    ]

    PATHS_TO_CREATE = [
        '~/bin',
        '~/.undodir',
        '~/.config',
    ]

    def __init__(self, kind, dry_run=False):
        """
        kind: either 'generic' or 'personal'
        dry_run: boolean designating whether or not this is a dry run
        """
        self.kind = kind
        self.dry_run = dry_run

    def clean(self):
        targets = [t[1] for t in self.FILES_TO_LINK]
        targets.extend([
            '~/.gitconfig',
        ])
        command_list = []
        for target in targets:
            target = os.path.expanduser(target)
            if not os.path.exists(target):
                continue
            if os.path.islink(target):
                cmd = 'rm {}'.format(target)
            else:
                cmd = 'rm -rf {}'.format(target)

            command_list.append(cmd)

        self._run_commands(command_list)



    def run(self):
        """
        The main run script for deploying (doesn't include python stuff)
        """
        self.archive_bashrc()
        self.create_paths()
        self.copy_files()
        self.make_git_config()
        self.ensure_bash_history()

    def _run_commands(self, command_list):
        """
        A utility function for running a list of commands
        """
        for cmd in command_list:
            print(cmd)
            if not self.dry_run:
                run(cmd)

    def archive_bashrc(self):
        bashrc = os.path.expanduser('~/.bashrc')
        if os.path.isfile(bashrc):
            now = datetime.datetime.now()
            date_str = now.strftime('%Y-%m-%dT%H.%M.%S.%f')
            archive_base_name = '._bashrc_{}'.format(date_str)
            archive_name = os.path.expanduser('~/{}'.format(archive_base_name))
            cmd = 'cp {} {}'.format(bashrc, archive_name)
            print(cmd)
            if not self.dry_run:
                run(cmd)


    def build_base_env(self):
        """
        Builds a python3 virtualenv at ~/envs/base and installs requirements.
        """
        command_list = []
        act = '. "$HOME/envs/base/bin/activate"'
        req = '"$HOME/dot_files/requirements.txt"'

        cmd = 'mkdir -p "$HOME/envs"'
        command_list.append(cmd)

        cmd = 'python3 -m venv "$HOME/envs/base"'
        command_list.append(cmd)

        cmd = '{}  && pip install -U pip'.format(act)
        command_list.append(cmd)

        cmd = '{}  && pip install numpy'.format(act)
        command_list.append(cmd)

        cmd = '{} && pip install -r {}'.format(act, req)
        command_list.append(cmd)

        self._run_commands(command_list)

        self._install_jupyter_lab_extension()

    def install_miniconda(self):
        """
        Install miniconda into ~/miniconda
        """
        command_list = []
        tmp_dir = '/tmp'
        if os.environ['OS_TYPE'] == 'mac':
            script_name = 'Miniconda3-latest-MacOSX-x86_64.sh'
        elif os.environ['OS_TYPE'] == 'linux':
            script_name = 'Miniconda3-latest-Linux-x86_64.sh'
        else:
            raise ValueError('Unrecognized OS')

        url = os.path.join(
            'http://repo.continuum.io/miniconda',
            script_name,
        )
        downloaded_file = os.path.join(tmp_dir, 'miniconda.sh')

        cmd = 'wget {} -O {}'.format(url, downloaded_file)
        command_list.append(cmd)

        cmd = 'bash {} -b -p "$HOME/miniconda"'.format(downloaded_file)
        command_list.append(cmd)

        cmd = 'rm {}'.format(downloaded_file)
        command_list.append(cmd)

        self._run_commands(command_list)

    def create_paths(self):
        """
        Creates all paths for deployment
        """
        for path in self.PATHS_TO_CREATE:
            path = os.path.expanduser(path)
            if not os.path.isdir(path):
                if self.dry_run:
                    print('mkdir -p {}'.format(path))
                else:
                    os.makedirs(path)

    def copy_files(self):
        """
        Makes all symlinks for a deployment
        """
        for (source_name, target_name) in self.FILES_TO_LINK:
            src = os.path.expanduser(source_name)
            tgt = os.path.expanduser(target_name)
            if os.path.isfile(tgt):
                run('rm {}'.format(tgt))
            cmd = 'cp -r {src} {tgt}'.format(src=src, tgt=tgt)

            print(cmd)
            if not self.dry_run:
                run(cmd)

    def ensure_bash_history(self):
        """
        Makes sure a .bash_history file exists
        """
        history_file = os.path.expanduser('~/.bash_history')
        if not os.path.isfile(history_file):
            cmd = 'cp ~/dot_files/fake_bash_history {}'.format(history_file)
            print(cmd)
            if not self.dry_run:
                run(cmd)

    def make_git_config(self):
        """
        Creates an appropriate gitconfig
        """
        if self.kind == 'personal':
            context = dict(
                name='Rob deCarvalho',
                email='robdmc@gmail.com',
                github_user_spec=textwrap.dedent(
                    """
                    [github]
                        user = robdmc
                    """
                )
            )
        elif self.kind == 'generic':
            context = dict(
                name='Generic User',
                email='generic@user.net',
                github_user_spec='',
            )

        else:
            raise ValueError('"kind" must be in ["personal", "generic"]')

        with open(os.path.join(FILE_PATH, 'gitconfig_template')) as f:
            template = f.read()
            contents = template.format(**context)

        if self.dry_run:
            print('=' * 40 + ' .git_config ' + '=' * 40)
            print(contents)
            print('=' * 40 + ' end .git_config ' + '=' * 40)
        else:
            with open(os.path.expanduser('~/.gitconfig'), 'w') as out:
                out.write(contents)


if __name__ == '__main__':

    msg = textwrap.dedent("""Deploy dotfiles""")
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=msg)

    parser.add_argument(
        '-d', '--dry-run', dest='dry_run', action='store_true', default=False,
        help='Use with any other flag to not do anythin, just print commands')

    parser.add_argument(
        '-g', '--generic', dest='generic', action='store_true', default=False,
        help='Use generic gitconfig when deploying dotfiles')

    parser.add_argument(
        '-v', '--venv', dest='venv', action='store_true', default=False,
        help='Don\'t deploy.  Just install default virtualenv at ~/envs/base')

    parser.add_argument(
        '--miniconda', dest='miniconda', action='store_true', default=False,
        help='Download and install miniconda')

    parser.add_argument(
        '--clean', dest='clean', action='store_true', default=False,
        help='Remove all dot files')

    args = parser.parse_args()

    # Determine what type of deployment was requested
    if args.generic:
        deploy = Deploy('generic', args.dry_run)
    else:
        deploy = Deploy('personal', args.dry_run)

    # Only build the conda env
    if args.conda:
        deploy.build_conda_env()

    # Only install Miniconda
    elif args.miniconda:
        deploy.install_miniconda()

    # Only build the base env
    elif args.venv:
        deploy.build_base_env()

    elif args.clean:
        deploy.clean()

    # Do a general deployment
    else:
        deploy.run()
