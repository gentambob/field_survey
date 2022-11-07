#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 11:25:41 2022

@author: genta
"""

import geopadas as gpd
import streamlit as st
from streamlit_folium import folium_static
import shapely
from sklearn.cluster import SpectralClustering
def googlerouting (df_plans):
    otw=df_plans.head(len(df_plans)-1).to_numpy()
    final=df_plans.tail(1).to_numpy()[0]
    
    base="https://www.google.com/maps/dir//"
    for o in otw:
        base=base+f"{o[1]},{o[0]}/"
    base=base+f"@{final[1]},{final[0]}"
    return base.strip()
@st.cache(suppress_st_warning=True,allow_output_mutation=True) 
def data_all():
    data=gpd.read_file("target_fieldstream.json")
    x=data.geometry.x
    y=data.geometry.y
    data["x"]=x
    data["y"]=y
    X=[[xs, ys] for xs, ys in zip(x, y)]
    clustering = SpectralClustering(n_clusters=30,
            assign_labels='discretize',
            affinity="nearest_neighbors",
            random_state=0).fit(X)
    data["cluster"]=clustering.labels_
    groups=data.groupby("cluster")
    datp=data.copy()
    boxs=gpd.GeoSeries(
        groups.apply(lambda x:shapely.geometry.box(* x.total_bounds)),
        crs=data.crs
                       ).rename("geometry")
    for i, d in enumerate(boxs):
        index=len(datp)+1
        datp.at[index, "geometry"]=d.exterior
        datp.at[index, "cluster"]="box"+str(i)


    fol=datp.explore("cluster", categorical=True, cmap="prism")
    return data, fol, groups
data, fol, groups=data()
st.title("zore grid and unsure survey points")
c=st.sidebar.selectbox("cluster (targets)",  list(data["cluster"]))
cd=groups.get_group(c)
folc=cd.explore()
folium_static(folc)
folium_static(fol)
routes=googlerouting (
    cd.to_crs("EPSG:900913")
    [["x", "y"]].sort_values(["x","y"]
     ))
st.write(routes)
"""
def plans_implement(geom):
    try:
        plans=tsp(geom, plot=False)
    except:
        plans=None
    if plans is not None:
        plans=split_dataframe(plans)
        plans=[p for p in plans if len(p)>0]
        routes=[]
        for i, plan in enumerate(plans):
            routes.append(googlerouting(plan))
        return routes
    else:
        return []
    
def tsp_2d(coords_list):
    fitness = mlrose.TravellingSales(coords = coords_list)
    #fitness = mlrose.TravellingSales(distances = dist_list)
    problem_fit = mlrose.TSPOpt(length = len(coords_list), fitness_fn = fitness, maximize=False)
    best_state, best_fitness = mlrose.genetic_alg(problem_fit, mutation_prob = 0.2,
                                                  max_attempts =100, random_state = 2)
    return best_state


def percentsample(data, perce):
    n=(perce/100)*len(data)
    return data.sample(round(n))

def tsp(geom, plot=False):
    G=osmnx.graph.graph_from_polygon(geom, retain_all=False,truncate_by_edge =True)
    tsp = nx.approximation.traveling_salesman_problem
    nodes, edges = osmnx.graph_to_gdfs(G)
    nodes=nodes[nodes["street_count"]>1]
    nodes=percentsample(nodes, 10) # 10% (random) of all nodes within the boundaries with street count >1 as initial state/filtering
    noid=list(nodes.index) 
    print(f"{len (noid)} nodes to be visited")
    if len (noid)==0:
        noid==None
    if len(nodes)>1:
        best_state=tsp(G.to_undirected(), nodes=noid,
                       weight="length")
        best_state=list(set(best_state))
    
        nodes, edges = osmnx.graph_to_gdfs(G)
        
        num=0
        for b in best_state:
            nodes.at[b, "state"]=num
            num=num+1
        nodes=nodes[nodes["state"].notna()==True]
    else:
        nodes["state"]=0
    if plot==True:
        n, edges = osmnx.graph_to_gdfs(G)
        ax=n.plot(color="black", alpha=0.4)
        edges.plot(ax=ax)
        nodes.plot(color="red", ax=ax)
        for idx, row in nodes.iterrows():
            ax.annotate(text=int(row['state']), xy=[row["x"],row["y"]],
                         horizontalalignment='center')
    nodes=nodes.to_crs("EPSG:3857")
    plan=nodes.sort_values("state")[["x","y"]]
    return plan
    

def split_dataframe(df, chunk_size = 5): 
    chunks = list()
    num_chunks = len(df) // chunk_size + 1
    for i in range(num_chunks):
        chunks.append(df[i*chunk_size:(i+1)*chunk_size])
    return chunks
"""
