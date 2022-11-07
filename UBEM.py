# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 12:20:28 2021

@author: fatjo876
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry.polygon import Polygon, LineString
from eppy.modeleditor import IDF
import numpy as np
import matplotlib.pyplot as plt
import os,  glob
from time import time
from multiprocessing import Pool
import multiprocessing
from shapely import wkt

from simulation import Simulation
from archetype import Archetype
from occupancy import Initials
from hvac import HVAC
from visualization import Visualization


""" Initializing the simulation tool EnergyPlus """

# Call the idd (EnergyPlus exe file)
iddfile = "C:/EnergyPlusV9-2-0/Energy+.idd"

# Initialize the idf file processing.
IDF.setiddname(iddfile)


""" Importing the input parameters """

# EnergyPlus weather file.
epw = "inputs/SWE_Stockholm.Arlanda.024600_IWEC.epw" 

# The Geocoded building data.
df = pd.read_csv('inputs/exampleData.csv')
df = df.drop('Unnamed: 0', axis = 1)
df['geometry'] = df['geometry'].apply(wkt.loads)
df = gpd.GeoDataFrame(df, crs='epsg:3006')


# Input parameters from a user defined text file.
parameters = pd.read_csv('inputs/parameters.txt', sep = ',', header = 'infer', 
                         encoding= 'ANSI')

""" Initializing the input variables """

# Hot and cold water temperatures for domestic hot water use.
hotWaterTemp = parameters.hotWaterTemp[0]
coldWaterTemp = parameters.coldWaterTemp[0]
infiltration = pd.read_csv('archetypes/archetypeClasses.txt').infiltration

#---------------------------------------------------

def leap_year(year):
    """
    Checks if the given year is leap year
    """
    if ((year % 400 == 0) or (year % 100 == 0) and (year % 4 ==0)):
        return 1
    else:
        return 0



firstDayOfYear = pd.read_csv(epw, sep=',',skiprows = 7,
                             low_memory=False).columns[4]

year = int(pd.read_csv(epw, sep=',',skiprows = 8, low_memory=False).columns[0])
leapYear = leap_year(year)

occupancyInputs = pd.read_csv('occupancyInputs.csv', sep=';',low_memory=False)

occupancy = occupancyInputs['Occupancy from mobility data']
personHeat = occupancyInputs['Person heat renormalized to mobility data (W)']
appliances = occupancyInputs['Electricity  demand renormalized to mobility data (W)']
hotWater = occupancyInputs['Hot water  demand renormalized to mobility data (litres)']

_,_,_,_,maxFlowHotWater = Initials.profile_generator (occupancy,
                                                      personHeat, 
                                                      appliances,
                                                      hotWater, 
                                                      firstDayOfYear,
                                                      leapYear)

# MULTIPROCESSING SIMULATION RUN FOR THE DATASET
#-----------------------------------------------


def remove ():
    """
    Removes the output files from EnergyPlus after each simulation run.
    """
    for filename in glob.glob('eplus*'):
        os.remove(filename)
    return None



"RUNS the SIMULATION"
if __name__ == '__main__':
    nThreads = multiprocessing.cpu_count()

    with Pool(nThreads) as p:
        t1 = time()
        print('_________________________')
        print('SIMULATION IS RUNNING ...')
        print('                         ')
        A = []
        DH = []
        ID = []
        

        for i in range (len(df)):
            try:
                print ('Building',i,'/',len(df))
                dff = gpd.GeoDataFrame((df.iloc[i]).to_frame().T).reset_index(drop=True)
                dff = dff.set_crs('EPSG:3006')
                buildingType = dff.buildingType[0]
                mainType = Archetype.building_type(buildingType)
                buildingYear = dff.buildingYear[0]
                arch = Archetype.archetype(mainType, buildingYear)
                A.append(arch)
                buildingId = dff.buildingId[0]
                buildingPolygon= Polygon (dff.geometry[0])            
                basementInfo = 0 
                buildingHeight = dff.buildingHeight[0] 
                buildingArea = dff.area[0]
                propertyCode = dff.propertyCode[0]
                buildingFloor = np.round(buildingHeight/2.8)
                windowArea = np.round(buildingArea * buildingFloor * 0.1)
                perimeter = 0
                x,y = dff.geometry[0].exterior.xy
                for j in range(len(x)-1):
                    line = LineString([(x[j],y[j]),(x[j+1],y[j+1])]).length
                    if line>2:
                        perimeter += line
                        
                windowBBR = windowArea/(perimeter * buildingFloor*2.8)
                wwr = windowBBR
                material_idf = IDF("archetypes/Archetype%d.idf" %arch)
                
                heatRecovery = 0 
                heatRecoveryEffect = 0
                infFlow = infiltration[arch-1]
                idf = Simulation.building_idf (buildingPolygon, buildingArea, 
                                               buildingHeight, buildingId, 
                                               basementInfo, epw, 
                                               wwr, material_idf,
                                               df, hotWaterTemp, coldWaterTemp, 
                                               maxFlowHotWater, mainType,
                                               heatRecovery, heatRecoveryEffect,
                                               infFlow, df)
                
    
    
                DH.append(Simulation.simulation (idf ,basementInfo))

                remove()
            except:
                DH.append([0,0,0,0,0])
            
             
    t2 = time()
    print('SIMULATION IS DONE!')
    print('                   ')
    print("----- Running time:", (t2-t1)//60, ' minutes and', np.round((t2-t1)-(t2-t1)//60,2), ' seconds')
    print("----- Running time per building:", np.round((t2-t1)/len(df),2))

#VALIDATION OF RESULTS
#-----------------------------

df['archetype']=A


dh = pd.DataFrame(DH)

SH = []
DHW = []
El = []
annualDHW = []
annualSH = []
annualElHousehold = []

for i in range(len(dh)):
    El.append(dh[2][i])
    SH.append(dh[3][i])
    DHW.append(dh[4][i])
    annualDHW.append(np.sum(dh[4][i]))
    annualSH.append(np.sum(dh[3][i]))
    annualElHousehold.append(np.sum(dh[2][i]))
