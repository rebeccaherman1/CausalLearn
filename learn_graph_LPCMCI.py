import argparse
parser = argparse.ArgumentParser()
#-f FILENAME -knn KNN -sn SN -tm TM -p PRELIM_ITERATIONS
parser.add_argument("-f", "--filename", dest="filename", required=True, help="Data Filename")
parser.add_argument("-knn", dest="knn", default=0.2, type=float, help="K Nearest Neighbors fraction for CMIknn")
parser.add_argument("-sn", "--shuffle-neighbors", dest="SN", default=8, type=int, help="Shuffle Neighbors for CMIknn")
parser.add_argument("-tm", "--tau-max", dest="tm", nargs='*',default=[1],  type=int, help="Tau Max: Maximum Time Lag")
parser.add_argument("-p", "--prelim-iterations", dest="p", nargs='*', default=[1], type=int, help="n_preliminary_iterations for LPCMCI")
parser.add_argument("-d", "--home-dir", dest="fldr", default='../../ocp/users/rh2856/', help="Data Storage Directory")
parser.add_argument("-w", "--workers", dest="w", default=-1, type=int, help="number of worksers for parallel CMIknn tests")
args = parser.parse_args()

print( "Filename {}\n CMIknn arguments: knn {}, SN {}\n LPCMCI arguments: tm {}, p {}".format(
        args.filename,
        args.knn,
        args.SN,
        args.tm,
        args.p
        ))

import pandas as pd
import networkx as nx
import numpy as np
from matplotlib import pyplot as plt

import tigramite
from tigramite import data_processing as dp #pp
from tigramite import plotting as tp
from tigramite.lpcmci import LPCMCI
from tigramite.pcmci import PCMCI
from tigramite.independence_tests import CMIknn #, GPDC, ParCorr, CMIsymb
import time
#import dcor
#import sklearn
import pickle

no_GT = False
fname = args.fldr+'csv/run/'+args.filename #AS-RCEC_TaiESM1_r1i1p1f1.csv'
model = args.filename.split('_')[1] #'TaiESM1' 
flnm = args.filename.split('.')[0] #remove .csv
df = pd.read_csv (fname)
df.pop('SB')
df.pop('IN')
df.pop('Ph')
df.pop('L')
if(no_GT):
    df.pop('GT')
df_full_tg = dp.DataFrame(df.values, var_names = df.columns)

IT = CMIknn(knn=args.knn, shuffle_neighbors=args.SN, workers=args.w)#GPDC(significance='analytic')#
M_full = LPCMCI(df_full_tg, IT, verbosity = 1)

#plotting
x_vals = {'NA':4, 'md':5}
x_vals.update(dict.fromkeys(['EN', 'Pc'],1)) #Pacific, Winter and Summer
x_vals.update(dict.fromkeys(['GG', 'SA'],2)) #South Atlantic, Spring and Summer
x_vals.update(dict.fromkeys(['AMM', 'TA'],3)) #Tropical Atlantic, Spring and Summer
x_vals.update(dict.fromkeys(['GT', 'pr'],2.5)) #extras
EXTRA = ['SB', 'IN', 'Ph', 'L'] #usually not included
x_vals.update({EXTRA[i]:(i+6) for i in range(len(EXTRA))})
y_vals = {'EN':5.5, 'GT':2, 'pr':1} #Winter and extras
y_vals.update(dict.fromkeys(['GG', 'AMM'],4.5)) #Spring
su_basins_full = ['Pc', 'SA', 'TA', 'NA', 'md', 'SB', 'IN', 'Ph', 'L']

for tm in args.tm:
    print("Starting tau_max = {}".format(tm))
    for p in args.p:
        print("Starting prelim_iterations = {}".format(p))
        
        fn = flnm+'_SN'+str(args.SN)+'_knn'+str(args.knn).split('.')[1]+'_p'+str(p)+'_tm'+str(tm)
        print("Saving to: {}".format(fn))
        
        t1 = time.time()
        G_full = M_full.run_lpcmci(n_preliminary_iterations=p,tau_max=tm)
        t2 = time.time()
        elapsed = (t2-t1)/3600 #in hours
        print("Elapsed time: {}".format(elapsed))
 
        G_full['var_names'] = df.columns
        G_full['elapsed'] = elapsed
        if(no_GT):
            fn = fn +'_noGT'
        fl = open(args.fldr+'graphs/'+fn, 'wb')
        pickle.dump(G_full, fl)
        fl.close()

        #plotting
        su_basins = [vn for vn in su_basins_full if vn in df_full_tg.var_names]
        r = len(su_basins)
        y_vals.update({b:((r**2-(x_vals.get(b)-(r+1)/2)**2)**.5)-np.min([((3*r**2 + 2*r - 1)**.5)/2,r])+3 for b in su_basins})#
        x = [x_vals.get(vn) for vn in df_full_tg.var_names]
        y = [y_vals.get(vn) for vn in df_full_tg.var_names]
        P=tp.plot_graph(G_full['graph'], val_matrix=G_full['val_matrix'], var_names=G_full['var_names'], node_pos={'x':x, 'y':list(y)})#, arrow_linewidth=7)
        P[0].suptitle(model)
        P[0].set_facecolor('lightgray')
        P[0].savefig(args.fldr+'figures/'+fn+'.png')

