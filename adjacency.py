# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 15:46:58 2021

@author: fatjo876
"""


import geopandas as gpd


class Adjacency:
    def __init__(self, buildingPolygon,buildingId, df):
        self.buildingPolygon = buildingPolygon
        self.buildingId= buildingId
        self.df = df    

    
    def adjacent_polygons (buildingPolygon, buildingId, df):
        """
        Finds adjacent buildings.
        
        parameters
        ----------
        buildingPolygon: shapely polygon
        
        buildingId: str
            Building ID
        
        df: gpd.GeoDataFrame
            GIS data of the city
          
        output
        ------
        intersection: gpd.GeoDataFrame  
            Intersecting or adjacent polygons
        """
        
        #Increases the area of the building polygon
        geoB = gpd.GeoDataFrame([buildingPolygon.buffer(0.2, 
                                                        join_style = 2,
                                                        mitre_limit=2,
                                                        cap_style=2 )],
                                columns=['geometry'], 
                                geometry='geometry').set_crs('EPSG:3006')
     
        #Finds any intersection between the building polygon buffer and GIS data.
        intersection = gpd.overlay(geoB, df, how = 'intersection')
        
        #Exclueds the intersection of the building with itself.
        # The building ID is used as a key.
        intersection = intersection[intersection.buildingId != buildingId]
        intersection = intersection.reset_index(drop=True)
        
        return intersection

