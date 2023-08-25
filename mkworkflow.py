#!/usr/bin/env python3

import os
import plistlib
import shutil
import subprocess
import sys

from contextlib import contextmanager
from uuid import uuid4


START_LETTERS = (
  'abcdefghijklmnopqrstuvwxyz'
  '0123456789'
  "._'`,"
)

SCRIPT_DIR = sys.path[0]
BUILD_DIR = 'wfbuild'
WF_FILES = [
  'icon.png',
  'info.plist',
  'README.md',
  'search_history.py',
]


def copy(filenames, dest_folder):
  if os.path.exists(dest_folder):
    shutil.rmtree(dest_folder)
  os.makedirs(dest_folder)

  for filename in filenames:
    if os.path.isdir(filename):
      shutil.copytree(filename, f'{dest_folder}/{filename}')
    else:
      shutil.copy(filename, f'{dest_folder}/{filename}')


def plistRead(path):
  with open(path, 'rb') as f:
    return plistlib.load(f)


def plistWrite(obj, path):
  with open(path, 'wb') as f:
    return plistlib.dump(obj, f)


def fileContents(filepath):
  with open(filepath) as f:
    return f.read()


@contextmanager
def cwd(dir):
  old_wd = os.path.abspath(os.curdir)
  os.chdir(dir)
  yield
  os.chdir(old_wd)

  
def make_query_logger_object(starting_letter):
  return {
    "uid": f'{uuid4()}'.upper(),
    "config": {
      "keyword": starting_letter,
      "script": f'''
query="{starting_letter}$1"

mkdir -p "$alfred_workflow_data"
echo "$(date +%s) $query" >> "$alfred_workflow_data/query-history.txt"
      ''',
      "alfredfiltersresults": False,
      "alfredfiltersresultsmatchmode": 0,
      "argumenttreatemptyqueryasnil": True,
      "argumenttrimmode": 0,
      "argumenttype": 0,
      "escaping": 102,
      "queuedelaycustom": 3,
      "queuedelayimmediatelyinitially": True,
      "queuedelaymode": 0,
      "queuemode": 1,
      "runningsubtext": "",
      "scriptargtype": 1,
      "scriptfile": "",
      "subtext": "",
      "title": "",
      "type": 0,
      "withspace": False
    },
    "type": "alfred.workflow.input.scriptfilter",
    "version": 3,
  }


def make_export_ready(plist_path):
  wf = plistRead(plist_path)

  # remove noexport vars
  wf['variablesdontexport'] = []

  # remove noexport objects
  noexport_uids = [
    uid
    for uid, data
    in wf['uidata'].items()
    if 'noexport' in data
  ]

  num_columns = 6
  for i, start_letter in enumerate(START_LETTERS):
    x = (i % num_columns) * 150
    y = 150 + (i // num_columns) * 120
    new_filter_obj = make_query_logger_object(start_letter)
    wf['objects'].append(new_filter_obj)
    wf['uidata'][new_filter_obj['uid']] = {'xpos': x, 'ypos': y}

  # add readme
  with open('README.md') as f:
    wf['readme'] = f.read()

  plistWrite(wf, plist_path)
  return wf['name']


if __name__ == '__main__':
  copy(WF_FILES, BUILD_DIR)
  wf_name = make_export_ready(f'{BUILD_DIR}/info.plist')
  with cwd(BUILD_DIR):
    subprocess.call(['zip', '-r', f'../{wf_name}.alfredworkflow'] + WF_FILES)
