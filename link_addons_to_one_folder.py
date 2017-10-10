#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
#    XPANSA Utils for Odoo
#    Copyright (C) 2017 Xpansa Group (<http://xpansa.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from __future__ import print_function

from os import listdir as os_listdir
from os.path import join as os_path_join
from os.path import isdir as os_path_isdir
from os.path import basename as os_path_basename
import os
import errno
import click

MANIFEST_FILES = [
    '__manifest__.py',
    '__odoo__.py',
    '__openerp__.py',
    '__terp__.py',
]


def is_module(path):
    '''return False if the path doesn't contain an odoo module, and the full
    path to the module manifest otherwise'''

    if not os_path_isdir(path):
        return False
    files = os_listdir(path)
    filtered = [x for x in files if x in (MANIFEST_FILES + ['__init__.py'])]
    if len(filtered) == 2 and '__init__.py' in filtered:
        return os_path_join(
            path, next(x for x in filtered if x != '__init__.py')
        )
    else:
        return False


def get_addons_paths(root_path):
    addons_paths = []
    try:
        filenames = os_listdir(root_path)
    except OSError as os_err:
        if os_err.errno == errno.ENOENT:
            filenames = []
    for filename in filenames:
        path = os_path_join(root_path, filename)
        if os_path_isdir(path):
            if is_module(path):
                addons_paths.append(path)
            else:
                addons_paths += get_addons_paths(path)
        else:
            pass
    return addons_paths


def parse_with_depends(paths):
    result = {}
    for path in paths:
        name = os_path_basename(path)
        result[name] = {'path': path, 'depends': []}
        manifest_filename = is_module(path)
        manifest = eval(open(manifest_filename).read())
        result[name].update({'manifest': manifest})
        depends = manifest.get('depends', [])
        result[name]['depends'] = depends
    return result


CLICK_DIR = click.Path(exists=True, dir_okay=True, resolve_path=True)


@click.command()
@click.option(
    'main_path',
    '--main-path',
    envvar='MAIN_ADDONS_PATH',
    multiple=False,
    type=CLICK_DIR,
    required=True,
    help='Main paths with addons'
)
@click.option(
    'ext_path',
    '--ext-path',
    envvar='EXT_ADDONS_PATH',
    multiple=False,
    type=CLICK_DIR,
    required=True,
    help='ext-addons paths with addons'
)
@click.option(
    'result_path',
    '--result-path',
    envvar='RESULT_EXT_ADDONS_PATH',
    multiple=False,
    type=CLICK_DIR,
    required=True,
    help='Result paths with addons'
)
def main(main_path, ext_path, result_path):
    def unique(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    print('MAIN_ADDONS_PATH:', main_path)
    print('EXT_ADDONS_PATH:', ext_path)
    print('RESULT_EXT_ADDONS_PATH:', result_path)
    if not os_path_isdir(result_path):
        os.makedirs(result_path)
    main_addons = parse_with_depends(get_addons_paths(main_path))
    main_deps = [data['depends'] for name, data in main_addons.iteritems()]
    main_deps = unique([item for sublist in main_deps for item in sublist])
    main_deps.sort()
    ext_addons = parse_with_depends(get_addons_paths(ext_path))

    need_link = ext_addons
    for addon_name, row in need_link.iteritems():
        src = row['path']
        dst = os_path_join(result_path, addon_name)
        if not os.path.islink(dst):
            os.symlink(src, dst)
        print('{} -> {}'.format(src, dst))


if __name__ == '__main__':
    try:
        exit(main(standalone_mode=False))
    except click.ClickException as e:
        e.show()
        exit(e.exit_code)
