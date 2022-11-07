#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 11:25:41 2022

@author: genta
"""

import geopandas as gpd
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
        datp.at[index, "cluster"]="box"#+str(i)


    fol=datp.explore("cluster", categorical=True, cmap="Set1", legend=True)
    return data, fol, groups
data, fol, groups=data_all()
@st.cache(suppress_st_warning=True,allow_output_mutation=True)
def cluster_map(c, groups):
    cd=groups.get_group(c)
    cdplot=cd.copy()
    cdplot.geometry=cdplot.geometry.buffer(0.0031)
    folc=cdplot.explore("kind", categorical=True, cmap="prism_r", legend=True)
    return folc, cd

if st.button("clear cache"):
   st.experimental_singleton.clear()
c=st.sidebar.selectbox("cluster (targets)",  data["cluster"].unique())
folc, cd=cluster_map(c, groups)
st.title(f"Zore grid and unsure survey points for cluster {c}")
folium_static(folc)

routes=googlerouting (
    cd.to_crs("epsg:900913")
    [["x", "y"]].sort_values(["x","y"]
     ))
st.write(routes)
st.markdown("""-----""")
st.title("all map")
folium_static(fol)
