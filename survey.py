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
from osmnx.projection import project_gdf
import pandas as pd
import folium
st.set_page_config(layout="wide")
def googlerouting (df_plans):
    otw=df_plans.to_numpy()
    individuals={}
    base="https://www.google.com/maps/dir//"
    basei="https://www.google.com/maps/dir//"
    for o, i in zip(otw, df_plans.index):
        base=base+f"{o[1]},{o[0]}/"
        individuals[i]=basei+f"{o[1]},{o[0]}/"
    return (base.strip(), individuals)
#@st.cache(suppress_st_warning=True,allow_output_mutation=True) 
@st.experimental_singleton(suppress_st_warning=True)
def data_all():
    dataRSB=gpd.read_file("additional_data_Plus_RSBVersion4.json")
    dataS=gpd.read_file("undersampleRW_zerostreet.json")
    dataRW=gpd.read_file("rwtarget.json")
    X=[[xs, ys] for xs, ys in zip(dataRW["x"],dataRW["y"])]
    clustering = SpectralClustering(n_clusters=8, n_neighbors=5, assign_labels='cluster_qr',affinity="nearest_neighbors",random_state=0).fit(X)
    dataRW["cluster"]=clustering.labels_
    allmap=dataRW[["cluster", "unique_no_RW", "geometry"]].explore("cluster", categorical=True, cmap="tab10")
    return(dataRSB, dataS, dataRW, allmap)

dataRSB, dataS, dataRW, allmap=data_all()
def generate_localMap(c):
    rw_geom=dataRW[dataRW["unique_no_RW"].astype(str)==str(c)]
    display=rw_geom[list(dataRW.columns)[1:5]]
    pts_inside=gpd.clip(dataRSB, rw_geom)[["geometry"]]
    line_inside=gpd.clip(dataS, rw_geom)[[c for c in dataS.columns if c !="index_right"]]
    m=rw_geom[["geometry", "unique_no_RW"]].explore(name="rw")
    if len(pts_inside)>0:
        message=f"{len(pts_inside)} recorded points inside RWs in unique_no_RW {c}"
        pts_inside.geometry=project_gdf(pts_inside).buffer(10).to_crs(pts_inside.crs).geometry
        m=pts_inside.explore(m=m, color="red", name="pts")
        omit_line=gpd.sjoin(pts_inside, line_inside)["index_right"]
        if len(omit_line)>0:
            line_inside=line_inside.loc[~line_inside.index.isin(omit_line)]
    else:
        message=f"no recorded points inside RWs in unique_no_RW {c}"

    googledirection=[]
    if len(line_inside)>0:
        line_inside.geometry=project_gdf(line_inside).buffer(0.5).to_crs(line_inside.crs).geometry
        #m=line_inside[["geometry"]].explore( m=m, color="grey", name="street")
        ## a pretty cool algrthm for size-len wise street filtering for field survey !
        line_inside["newlen"]=line_inside.length
        gd=line_inside.sort_values("newlen",ascending=False).geometry
        selection=[]
        num=0
        for g, polygon in enumerate(gd):
            x=polygon.centroid.x
            y=polygon.centroid.y
            base="https://www.google.com/maps/dir//"
            base=base+f"{y},{x}/"
            if len(selection)==0:
                st.write(f"[link to ungated strt: {num}]({base})")
                num=num+1
                selection.append(polygon)
            elif len(selection)>9:
                break
            else:
                pol=project_gdf(gpd.GeoDataFrame(geometry=gpd.GeoSeries([polygon]), crs=line_inside.crs))
                pol=pol.geometry.values[0]
                geoser=project_gdf(gpd.GeoDataFrame(geometry=gpd.GeoSeries(selection), crs=line_inside.crs))
                mind=geoser.distance(pol).min()
                if mind>10: #at least 10 meters away from any selected street 
                    googledirection.append(f"[link to ungated strt: {num}]({base})")
                    num=num+1
                    selection.append(polygon)   
        gd=gpd.GeoSeries(selection).reset_index()
        m=gd.explore(m=m, column="index", cmap="Accent", name="street selected")
    else:
        for polygon in rw_geom.geometry:
            x=polygon.centroid.x
            y=polygon.centroid.y
            base="https://www.google.com/maps/dir//"
            base=base+f"{y},{x}/"
            googledirection.append(f"[link to ungated strt: {c}]({base})")

    folium.LayerControl().add_to(m)

    return(m, googledirection,message, display)


left, space1, s,right=st.columns(4)
genre = right.radio("Mode",('rw', 'all map'))

if  left.button("clear cache"):
    st.experimental_singleton.clear()
    st.experimental_rerun()
if genre == "rw":
    c=st.sidebar.selectbox("rw (targets)",  sorted(list(dataRW["unique_no_RW"].unique())))
    m, googledirection,message, display=generate_localMap(c)
    st.write(display)
    st.write(message)
    
    place=st.empty()
    left, space, right=place.columns([1,5,1])
    place3=st.empty()
    left3, space3, righ3=place3.columns([1,5,1])
    place2=st.empty()
    left2, space2, righ2=place2.columns([1,5,1])
    with space.expander("map", True):
        folium_static(m,width=280, height=400)
    
    with space3.expander("route"):
        st.write(googledirection)
        #for g in googledirection:
        #    st.write(g)

    with space2.expander("input form"):
        form='<iframe src="https://docs.google.com/forms/d/e/1FAIpQLSfGxtpiSVJ2hHzMeqb7HikVtzNYy1kRZLlWg1BW_3aQs1xVew/viewform?embedded=true" width="100%" height="1600" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>'
        st.markdown(form, unsafe_allow_html=True)
    
    st.stop()
if genre =="all map":
    st.title("all map")
    folium_static(allmap,width=400, height=400)
    st.stop()





    
  