#!/usr/bin/env python3

import pkg_resources
import pytest
import os
import sys

from git import Repo
from cvehound import check_cve

devnull = open(os.devnull, 'w')
curdir = os.path.dirname(os.path.realpath(__file__))
linux = os.path.join(curdir, 'linux')

repo = None
if os.path.isdir(os.path.join(linux, '.git')):
    repo = Repo(linux)
else:
    repo = Repo.clone_from('git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git', linux)


def test_kernel_setup():
    assert not repo.bare, 'bare repo'
    assert not repo.is_dirty(), 'dirty repo'
    assert not repo.untracked_files, 'there are untracked files'

def test_fix(cve):
    cocci = pkg_resources.resource_filename('cvehound', 'cve/' + cve + '.cocci')
    grep = pkg_resources.resource_filename('cvehound', 'cve/' + cve + '.grep')
    rule = cocci
    if os.path.isfile(grep):
        rule = grep
    fix = None
    with open(rule, 'r') as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            if 'Fix:' in line:
                fix = line.partition('Fix:')[2].strip()
                break
    assert fix
    repo.git.checkout(fix)
    assert check_cve(linux, cve) == False, cve + ' fails on fix commit'
    repo.git.checkout(fix + '~')
    assert check_cve(linux, cve) == True, cve + ' fails to detect fix~ commit'
