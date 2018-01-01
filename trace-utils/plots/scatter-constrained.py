#=========================================================================
# scatter-constrained.py
#=========================================================================
# Quick and super dirty script to summarize results
#
# Author : Shreesha Srinath
# Date   : December 31st, 2017

import brg_plot

import re
import math
import sys

import pandas as pd

from collections import OrderedDict

#-------------------------------------------------------------------------
# Global variables
#-------------------------------------------------------------------------

app_short_name_dict = OrderedDict([
  ('pbbs-bfs-deterministicBFS'    , 'bfs-d'),
  ('pbbs-bfs-ndBFS'               , 'bfs-nd'),
  ('pbbs-dict-deterministicHash'  , 'dict'),
  #('pbbs-knn-octTree2Neighbors'   , 'knn'),
  ('pbbs-mis-ndMIS'               , 'mis'),
  #('pbbs-nbody-parallelBarnesHut' , 'nbody'),
  ('pbbs-rdups-deterministicHash' , 'rdups'),
  ('pbbs-sa-parallelRange'        , 'sarray'),
  ('pbbs-st-ndST'                 , 'sptree'),
  #('pbbs-isort-blockRadixSort'    , 'radix-1'),
  #('pbbs-isort-blockRadixSort-1'  , 'radix-2'),
  ('pbbs-csort-quickSort'         , 'qsort'),
  ('pbbs-csort-quickSort-1'       , 'qsort-1'),
  ('pbbs-csort-quickSort-2'       , 'qsort-2'),
  ('pbbs-csort-sampleSort'        , 'sampsort'),
  ('pbbs-csort-sampleSort-1'      , 'sampsort-1'),
  ('pbbs-csort-sampleSort-2'      , 'sampsort-2'),
  ('pbbs-hull-quickHull'          , 'hull'),
  #('cilk-cholesky'                , 'clsky'),
  ('cilk-cilksort'                , 'cilksort'),
  ('cilk-heat'                    , 'heat'),
  ('cilk-knapsack'                , 'ksack'),
  ('cilk-matmul'                  , 'matmul'),
])

app_normalize_map = {
  'sampsort'   : 'pbbs-csort-serialSort',
  'sampsort-1' : 'pbbs-csort-serialSort-1',
  'sampsort-2' : 'pbbs-csort-serialSort-2',
  'qsort'      : 'pbbs-csort-serialSort',
  'qsort-1'    : 'pbbs-csort-serialSort-1',
  'qsort-2'    : 'pbbs-csort-serialSort-2',
  'radix-1'    : 'pbbs-isort-serialRadixSort',
  'radix-2'    : 'pbbs-isort-serialRadixSort-1',
  'nbody'      : 'pbbs-nbody-serialBarnesHut',
  'bfs-d'      : 'pbbs-bfs-serialBFS',
  'bfs-nd'     : 'pbbs-bfs-serialBFS',
  'dict'       : 'pbbs-dict-serialHash',
  'knn'        : 'pbbs-knn-serialNeighbors',
  'sarray'     : 'pbbs-sa-serialKS',
  'sptree'     : 'pbbs-st-serialST',
  'rdups'      : 'pbbs-rdups-serialHash',
  'mis'        : 'pbbs-mis-serialMIS',
  'hull'       : 'pbbs-hull-serialHull',
  'matmul'     : 'cilk-matmul',
  'heat'       : 'cilk-heat',
  'ksack'      : 'cilk-knapsack',
  'cilksort'   : 'cilk-cilksort',
  'clsky'      : 'cilk-cholesky',
}

app_list = app_short_name_dict.values()

file_list = [
  'results-spmd.csv',
  'results-wsrt.csv',
  'results-serial.csv',
]

g_config_str = "%s-%dc-%dl0-%dip-%ddp-%dlp-%dl-%dr"

g_ncores = 4

#-------------------------------------------------------------------------
# parse
#-------------------------------------------------------------------------

def parse_stat( stat, app, df, configs, base_df=None ):
  data = []
  if stat == 'steps':
    ts, = base_df[(base_df.app == app_normalize_map[app]) & (base_df.config == 'serial') & (base_df.stat == stat)]['value']
  temp = []
  for config in configs:
    try:
      val, = df[(df.config == config) & (df.app == app) & (df.stat == stat)]['value']
      if stat == 'steps':
        temp.append(ts/float(val))
      else:
        temp.append(val)
    except:
      temp.append(0)
  data.append( temp )
  return data

#-------------------------------------------------------------------------
# plot_data()
#-------------------------------------------------------------------------

def plot_data( df, base_df, opts ):
  l0_buffer_sz = 1
  configs = []
  data = []
  for index,app in enumerate( app_list ):
    for x in range( 1, g_ncores+1 ):
      for analysis in range( 2,3 ):
        for lockstep in range( 1,2 ):
          #config = g_config_str % ( 'spmd', g_ncores, l0_buffer_sz, x,x,x, lockstep, analysis )
          #configs.append( config )
          config = g_config_str % ( 'wsrt', g_ncores, l0_buffer_sz, x,x,x, lockstep, analysis )
          configs.append( config )

    steps = parse_stat( 'steps', app, df, configs, base_df )
    savings = parse_stat( 'savings', app, df, configs )
    for x,y in zip(steps,savings):
      temp = []
      for c,d in zip(x,y):
        temp.append([c, d])
      data.append(temp)

  data = map(list,zip(*data))
  opts.data           = data
  opts.labels         = [[],configs]
  opts.legend_ncol    = len(configs)
  opts.rotate_labels  = True
  opts.colors         = brg_plot.colors['unique20']

  opts.scatter_bar_arrow = True
  opts.legend_enabled    = True
  opts.legend_ncol       = 6
  opts.file_name         = 'wsrt-scatter.pdf'

  # plot data
  brg_plot.add_plot( opts )

#-------------------------------------------------------------------------
# plot
#-------------------------------------------------------------------------

def plot( df ):

  #-----------------------------------------------------------------------
  # scatter plot
  #-----------------------------------------------------------------------

  base_df = df[df.config == "serial"].copy()
  opts = brg_plot.PlotOptions()
  attribute_dict = \
  {
    'show'            : False,
    'plot_type'       : 'scatter',
    'figsize'         : (8.0, 8.0),
    'rotate_labels'   : False,
    'markersize'      : 50,
    'labels_fontsize' : 1,
    'legend_enabled'  : False,
  }
  for name, value in attribute_dict.iteritems():
    setattr( opts, name, value )

  plot_data( df, base_df, opts )

#-------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------

if __name__ == "__main__":
  df_list = []
  for res_file in file_list:
    df_list.append( pd.read_csv( res_file ) )
  df = pd.concat(df_list)
  df.to_csv('combined.csv',index=False)
  plot( df )