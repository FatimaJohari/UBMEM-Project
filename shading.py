# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 13:00:38 2022

@author: fatjo876
"""
from shapely.geometry import Point, LineString,MultiLineString
from shapely import affinity
from shapely.affinity import translate
from shapely.ops import cascaded_union
import io
from eppy.modeleditor import IDF
import numpy as np

class Shading:
    def __init__(self, propertyCode, df, gdf, idx):
        self.propertyCode = propertyCode
        self.df = df
        self.gdf = gdf
        self.idx = idx


    def densification(df, propertyCode):

        building = df[df['propertyCode'] == propertyCode].reset_index(drop=True)
        
        propertyArea = building['propertyArea']
        
        if propertyArea[0]>0:
            buildingArea = building.area
            buildingHeight = building['modifiedHeight']
            bcr = np.sum(buildingArea)/np.sum(propertyArea)
            far = np.sum( buildingArea* np.round(buildingHeight/2.8))/np.sum(propertyArea)
            
            if far>1 and bcr>0.3:
                return 1
            else:
                return 0
        else:
            return 0
                
                
        
    def shading(df, gdf, idx):
        shadingDistance = gdf['modifiedHeight'][0]/np.tan(np.radians(10))
        
        line = LineString([(gdf.centroid.x[0],gdf.centroid.y[0]),
                           (gdf.centroid.x[0]+shadingDistance,gdf.centroid.y[0])])
        
        # Rotate i degrees CCW from origin at point (step 10°)
        radii= [affinity.rotate(line, i, (gdf.centroid.x[0],
                                          gdf.centroid.y[0])) for i in range(0,360,5)]
        mergedradii = cascaded_union(radii)      
        
        d = 0
        indxs = df.index.drop(idx)
        for i in indxs:
            
            if mergedradii.intersects(df.geometry[i]):
                if (gdf.geometry[0].distance(df.geometry[i]))>0.5:

                    shadingGeo = df.geometry[i]
                    shadingHeight = df.modifiedHeight[i]
                    gdf['shadingPolygon%d'%d] = shadingGeo
                    gdf['shadingHeight%d'%d] = shadingHeight
                    d += 1
        return gdf, d





    def shading_idf(gdf, d):
        shade = "" 
        for i in range(d):
            x,y = gdf['shadingPolygon%d'%i][0].exterior.xy
            z0 = 0
            z1 = gdf['shadingHeight%d'%i][0]
            
            
            shade += ('SHADING:BUILDING:DETAILED,'+'\n'+
                      str('shadingBuilding%d'%i)+',\n'+
                      ', \n'+ 
                      'autocalculate,'+'\n')
            
            for j in range(len(x)-2):

                                      
                shade+= (str(x[j])+',\n' + str(y[j]) + ',\n' + str(z0) + ',\n' +
                         str(x[j+1])+',\n' + str(y[j+1]) + ',\n' + str(z1) + ',\n' +
                         str(x[j+1])+',\n' + str(y[j+1]) + ',\n' + str(z1) + ',\n' +
                         str(x[j])+',\n' + str(y[j]) + ',\n' + str(z0) + ',\n' )
                
            shade+= (str(x[-2])+',\n' + str(y[-2]) + ',\n' + str(z0) + ',\n' +
                    str(x[-1])+',\n' + str(y[-1]) + ',\n' + str(z1) + ',\n' +
                    str(x[-1])+',\n' + str(y[-1]) + ',\n' + str(z1) + ',\n' +
                    str(x[-2])+',\n' + str(y[-2]) + ',\n' + str(z0) + ';\n' )               
                
            fhandle = io.StringIO(shade) 
            idfShading = IDF(fhandle) 
       
        return idfShading

