from os import listdir
import numpy as np
import pickle
import pandas as pd
from tabulate import tabulate
import xarray as xr
pd.options.display.float_format = "{:,.2f}".format

H = '../../ocp/users/rh2856/'
G = H+'graphs/'
D = H+'csv/run/'

def edge(a,b,t):
    return (a, b, t)

def get_edge_and_val(edges_dict, i, e):
    return edges_dict.get(e[0]).get(e[1])[i][e[2]]

def get_edge(edges_dict, e):
    return get_edge_and_val(edges_dict,0,e)

def get_val(edges_dict, e):
    return get_edge_and_val(edges_dict,1,e)

def make_edges_dict(G, vals, V):
    return {
        V[i]:{
            V[j]:(G[i][j], vals[i][j]) for j in range(len(V))
        } for i in range(len(V))
    }

def make_dict(V):
    return {
        V[i]:{
            #anc, desc, conf
            V[j]:np.array([0,0,0]) for j in range(len(V))
        } for i in range(len(V))
    }

def get_score(dict, e):
    return dict.get(e[0]).get(e[1])[e[2]]

def get_parameter(s, p):
    v = s.split('_'+p)[1].split('_')[0]
    if p=='knn':
        return float('.'+v)
    else:
        return int(v)

#relies on SN being first in th epickle name. Does not rely on the form on the filename.
def get_filename(s):
    return s.split('_SN')[0] 

edge_points = {
    '-->':np.array([1,0,0,0]),#forward edge
    '<--':np.array([0,1,0,0]),#backward edge
    '<->':np.array([0,0,1,0]),#confounded edge
    'o->':np.array([2/3,0,1/3,0]),#the rest are uncertain combinations
    '<-o':np.array([0,2/3,1/3,0]),
    'o-o':np.array([1/3,1/3,1/3,0]),
    '':np.array([0,0,0,1])    #no edge
}

def open_stuff(D,G,f):
    fl = open(G+f, 'rb')
    g = pickle.load(fl)
    d = pd.read_csv(D+f.split('_SN')[0]+'.csv') #TODO modify original script to save the df with the graph
    d.pop('SB')
    d.pop('IN')
    d.pop('Ph')
    d.pop('L')
    return (g,d)

Files = listdir(G)
GCMs = list(set([get_filename(f) for f in Files]))
Files_GCM = {GCM:[f for f in Files if get_filename(f)==GCM] for GCM in GCMs}
scores = pd.DataFrame(data=None, index=Files, columns=['file','SN', 'knn', 'tm', 'p','robustness','robust_knowledge','recall','strength'])
#do everything completely separately for each GCM because they may have different variables. Can still compile them all into one giant scores table.
for GCM in GCMs:
    Files_gcm = Files_GCM.get(GCM)
    TMs = list(set([get_parameter(f,'tm') for f in Files_gcm])) 
    Files_TM = {tm:[f for f in Files_gcm if get_parameter(f,'tm')==tm] for tm in TMs}
    
    #initialize
    f = Files_TM.get(1)[0]
    (g,d)=open_stuff(D,G,f)
    var_names = d.columns
    seasons = {
        'W':['EN'],
        'Sp': ['GG', 'AMM'],
        'Su': [b for b in var_names if not b in ['EN', 'AMM', 'GG']]
    }
    edge_scores = make_dict(var_names)
    forbidden_right_edges = [
        edge(a,b,0) for b in (seasons.get('Sp')+seasons.get('W')) for a in seasons.get('Su')] + [
        edge(a,b,0) for b in seasons.get('W') for a in seasons.get('Sp')
    ]
    forbidden_left_edges = [
        edge(b,a,0) for b in (seasons.get('Sp')+seasons.get('W')) for a in seasons.get('Su')] + [
        edge(b,a,0) for b in seasons.get('W') for a in seasons.get('Sp')
    ]
    expected_right_edges = [
        edge('EN', 'Pc', 0), edge('Pc', 'EN', 1), #Pacific
        edge('GG', 'SA', 0), edge('SA', 'GG', 1), #South Atlantic
        edge('AMM', 'TA', 0), edge('TA', 'AMM', 1), #Tropical Atlantic
    ] + [edge(s, 'GT', 0) for s in ['Pc', 'SA', 'TA', 'SB', 'IN', 'Ph', 'L'] if s in seasons.get('Su')]
    expected_left_edges = [
        edge('Pc', 'EN', 0), edge('EN','Pc',  1), #Pacific
        edge('SA', 'GG', 0), edge('GG', 'SA', 1), #South Atlantic
        edge('TA', 'AMM', 0), edge('AMM', 'TA', 1), #Tropical Atlantic
    ] + [edge('GT', s, 0) for s in ['Pc', 'SA', 'TA', 'SB', 'IN', 'Ph', 'L'] if s in seasons.get('Su')]
    #above are edges I expect and forbid in the forward direction only. But all edges will include forward and backward edges, so I need to include the opposite too somehow.
    #higher tm should be preferable only if it reduces the amount of confounding in the lower stages.
    for tm in TMs:
        #these depend on tau_max.
        all_edges = [edge(a,b,i) for i in range(tm+1) for b in var_names for a in var_names]
        Adj = {e:np.array([0,0,0,0]) for e in all_edges}
        Adj_knowledge = {e:np.array([0,0,0,0]) for e in all_edges}
        n=0
        n_k = 0
        Files_tm = Files_TM.get(tm)
        #calculate edge scores in Adj
        for f in Files_tm:
            knn = get_parameter(f, 'knn');
            SN = get_parameter(f, 'SN');
            p = get_parameter(f, 'p');
            if tm==1 and ((knn not in [.15, .2, .25, .3, .35]) or (SN < 13) or (SN > 14) or (p < 3)):
                continue #don't include graphs outside the recommended parameters when determining robustness
            if tm==2 and ((knn != .4) or (SN < 11)):
                continue
            (g,d)=open_stuff(D,G,f)
            edges = make_edges_dict(g['graph'], g['val_matrix'], var_names)
            if not any(['x' in get_edge(edges, e) for e in all_edges]):
                Adj.update({e:Adj.get(e)+np.ceil(edge_points.get(get_edge(edges, e))) for e in all_edges}) 
                n = n+1
                if not '-->' in [get_edge(edges,e) for e in forbidden_right_edges]: #only completely directed edges are obviously non-physical. Only have to do this once; dubplicated.
                    #give a full point to every edge type consistent with a graph. 
                    Adj_knowledge.update({e:Adj_knowledge.get(e)+np.ceil(edge_points.get(get_edge(edges, e))) for e in all_edges}) 
                    #count number of physically-permissible graphs.
                    n_k=n_k+1
        Adj.update({e:Adj.get(e)/n for e in all_edges})
        avg_no_edge = sum([Adj.get(e)[-1] for e in all_edges])
        #enforce positive and negative prior knowledge.
        Adj_knowledge.update({e:Adj_knowledge.get(e)/n_k for e in all_edges})
        Adj_knowledge.update({e:np.array([1,0,0,0]) for e in expected_right_edges})
        Adj_knowledge.update({e:np.array([0,1,0,0]) for e in expected_left_edges})
        Adj_knowledge.update({e:Adj_knowledge.get(e)*np.array([0,1,1,1]) for e in forbidden_right_edges})
        Adj_knowledge.update({e:Adj_knowledge.get(e)*np.array([1,0,1,1]) for e in forbidden_left_edges})
        avg_no_edge_k = sum([Adj_knowledge.get(e)[-1] for e in all_edges])
       
        for f in Files_tm:
            scores.loc[f]=[get_filename(f)]+[get_parameter(f, param) for param in scores.columns[1:-4]]+[0,0,0,0];
            (g,d)=open_stuff(D,G,f)
            edges = make_edges_dict(g['graph'], g['val_matrix'], var_names)
            if not any(['x' in get_edge(edges, e) for e in all_edges]):
                scores.loc[f]['robustness'] = (sum([sum(Adj.get(e)*edge_points.get(get_edge(edges,e))) for e in all_edges])-avg_no_edge)/(len(all_edges)-avg_no_edge)
                scores.loc[f]['strength'] = sum([edge_points.get(get_edge(edges,e))[0]*get_val(edges,e) for e in expected_right_edges])/len(expected_right_edges)
                if not '-->' in [get_edge(edges,e) for e in forbidden_right_edges]: #only completely directed edges are obviously non-physical
                    #Only punish for uncertainty once; here we give partial points to uncertain edges.
                    scores.loc[f]['robust_knowledge'] = (sum([sum(Adj_knowledge.get(e)*edge_points.get(get_edge(edges,e))) for e in all_edges])-avg_no_edge_k)/(len(all_edges)-avg_no_edge_k)
                    #this now does this separately for different tau_max
                    scores.loc[f]['recall'] = sum([edge_points.get(get_edge(edges,e))[0] for e in expected_right_edges])/len(expected_right_edges)#don't need duplicates; just look at first value.

scores.set_index(scores.columns[0], inplace=True)
print(tabulate(scores, headers=scores.columns, floatfmt=".2g"))
for col in scores.columns[:-4]:
    scores.set_index(col, append=True, inplace=True)

print("The best robustness score is {:.2f}".format(max(scores['robustness'])))
for GCM in GCMs:
    #for tm in TMs:
    sel = (scores.index.get_level_values('file')==GCM) #&(scores.index.get_level_values('tm')==tm) 
    scores_GCM = scores.loc[sel]
    max_score=max(scores_GCM["recall"])
    print("The best recall of expected edges for {} is {:.2f}, given by the following parameters:".format(GCM, max_score))#and tm = {} tm, 
    print(scores_GCM[scores['recall']==max_score])
    print("The best robustness score is {:.2f}, and the best strength score for expected edges is {:.2f}".format(max(scores_GCM["robustness"]), max(scores_GCM["strength"]))) 

fl = open('scores.pkl', 'wb')
pickle.dump(scores, fl)
#TODO I want to make a scatterplot with SN vs knn (competing parameters for CMIknn) with shape represeting p and color representing score. 1=., 2=*, 3=triangle, 4=square.
