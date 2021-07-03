# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import sys

from collections import defaultdict
from datetime import datetime


WF_DATA_DIR = os.environ['alfred_workflow_data']
HIST_PATH = os.path.join(WF_DATA_DIR, 'query-history.txt')


class Trie(object):
  def __init__(self, root_data=None):
    self.root_data = root_data
    self.children = defaultdict(Trie)

  def insert(self, key, data, key_idx=0):
    if key_idx == len(key) - 1:
      self.root_data = data
    else:
      self.children[key[key_idx]].insert(key, data, key_idx + 1)

  def _collect_leaves(self, accumulator=[]):
    if len(self.children) == 0 and self.root_data is not None:
      accumulator.append(self.root_data)
    else:
      for _, child in self.children.items():
        child._collect_leaves(accumulator)

  def leaves(self):
    l = []
    self._collect_leaves(l)
    return l


def lines(filepath):
  with open(filepath) as f:
    return f.readlines()


def get_timestamps_and_queries():
  trie = Trie()
  regex = r'(\d+) (.*)'
  for linum, line in enumerate(lines(HIST_PATH)):
    try:
      timestamp, query = re.findall(regex, line)[0]
      trie.insert(query, (int(timestamp), query))
    except Exception as e:
      logging.error("%d: %s (len: %d)\n" % (linum, line, len(line)))
      logging.exception(e)
  return sorted(trie.leaves(), reverse=True)
  

def write_consolidated_query_log(timestamps_and_queries):
  hist = ''.join([
    '%d %s\n' % ts_n_q
    for ts_n_q in timestamps_and_queries
  ])
  with open(HIST_PATH, 'w') as histfile:
    histfile.write(hist)


def make_alfred_json(timestamps_and_queries):
  alfred_json = {'items': []}
  for timestamp, query in timestamps_and_queries:
    alfred_json['items'].append({
      'arg': query,
      'title': query,
      'autocomplete': query,
      'subtitle': datetime.fromtimestamp(timestamp).strftime("%d %b %Y %H:%M:%S")
    })
  return alfred_json
  

if __name__ == '__main__':
  ts_n_qs = get_timestamps_and_queries()
  write_consolidated_query_log(ts_n_qs)
  json.dump(make_alfred_json(ts_n_qs), sys.stdout, indent=2)
  sys.stdout.flush()
