#!python

import os, sys, string, time, BaseHTTPServer, getopt, re, subprocess, webbrowser
from operator import itemgetter

from utils import *
from annotate import Annotate
from scaffold import Scaffold
from findscforfs import FindScaffoldORFS

sys.path.append(INITIAL_UTILS)
from ruffus import *

_readlibs = []
_skipsteps = []
_cls = None
_settings = Settings()

def init(reads, skipsteps, cls):
   global _readlibs
   global _skipsteps
   global _cls

   _readlibs = reads
   _skipsteps = skipsteps
   _cls = cls


if "Propagate" in _skipsteps or _cls == None:
   run_process(_settings, "touch %s/Annotate/out/%s.annots"%(_settings.rundir, _settings.PREFIX), "Propagate")


@follows(Scaffold)
@posttask(touch_file("%s/Logs/propagate.ok"%(_settings.rundir)))
@files("%s/Annotate/out/%s.annots"%(_settings.rundir, _settings.PREFIX),"%s/Propagate/out/%s.clusters"%(_settings.rundir,_settings.PREFIX))
def Propagate(input,output):
   #run propogate java script
   # create s12.annots from Metaphyler output
   if "Propagate" in _skipsteps or _cls == None:
       run_process(_settings, "touch %s/Logs/propagate.skip"%(_settings.rundir), "Propagate")
       return 0
   if _cls == "metaphyler":
       run_process(_settings, "python %s/python/create_mapping.py %s/DB/class_key.tab %s/Abundance/out/%s.classify.txt %s/Propagate/in/%s.annots"%(_settings.METAMOS_UTILS,_settings.METAMOS_UTILS,_settings.rundir,_settings.PREFIX,_settings.rundir,_settings.PREFIX),"Propagate")
   if _cls == "phylosift" or _cls == "PhyloSift" or _cls == "Phylosift" or _cls == "FCP" or _cls == "fcp":
       run_process(_settings, "ln %s/Annotate/out/%s.annots %s/Propagate/in/%s.annots"%(_settings.rundir,_settings.PREFIX,_settings.rundir,_settings.PREFIX),"Propagate")

   # strip headers from file and contig name prefix
   
   # some output from the classifiers (for example PhyloSift) outputs multiple contigs with the same classification on one line
   # the line looks like ctg1","ctg2 class so we don't know which is right and we skip it in the classification below
   run_process(_settings, "cat %s/Propagate/in/%s.annots | grep -v \"\\\"\" | grep -v contigID |sed s/utg//g |sed s/ctg//g > %s/Propagate/in/%s.clusters"%(_settings.rundir,_settings.PREFIX,_settings.rundir,_settings.PREFIX),"Propagate")

   if "Propagate" in _skipsteps or "propagate" in _skipsteps:
      run_process(_settings, "ln %s/Propagate/in/%s.clusters %s/Propagate/out/%s.clusters"%(_settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX), "Propagate")
   else:
      run_process(_settings, "%s/FilterEdgesByCluster -b %s/Scaffold/in/%s.bnk -clusters %s/Propagate/in/%s.clusters -noRemoveEdges > %s/Propagate/out/%s.clusters"%(_settings.AMOS,_settings.rundir,_settings.PREFIX,_settings.rundir,_settings.PREFIX,_settings.rundir,_settings.PREFIX),"Propagate")

   # now add the headers to the propagated file
   run_process(_settings, "head -n 1 %s/Propagate/in/%s.annots | cat - %s/Propagate/out/%s.clusters > %s/Propagate/out/%s.tmp && mv %s/Propagate/out/%s.tmp %s/Propagate/out/%s.clusters"%(_settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX, _settings.rundir, _settings.PREFIX), "Propagate")

   # here we also propagate to the reads within contigs
   readctg_dict = {}
   for lib in _readlibs:
     ctgfile = open("%s/Assemble/out/%s.lib%dcontig.reads"%(_settings.rundir, _settings.PREFIX, lib.id), 'r')
     for line in ctgfile.xreadlines():
        line = line.replace("\n","")
        read, ctg = line.split()
        if ctg in readctg_dict:
           readctg_dict[ctg].append(read)
        else:
           readctg_dict[ctg] = [read,]
     ctgfile.close()

   annotsfile = open("%s/Propagate/out/%s.clusters"%(_settings.rundir, _settings.PREFIX), 'r')
   annotreads = open("%s/Propagate/out/%s.reads.clusters"%(_settings.rundir, _settings.PREFIX), 'w')
   for line in annotsfile.xreadlines():
     line = line.replace("\n", "")
     ctg, annot = line.split()
     if ctg in readctg_dict:
        for x in readctg_dict[ctg]:
           annotreads.write("%s\t%s\n"%(x, annot))
     else:
        annotreads.write("%s\t%s\n"%(ctg, annot))
   annotsfile.close()
   annotreads.close()
   readctg_dict.clear()
