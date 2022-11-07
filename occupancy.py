# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 10:06:33 2021

@author: fatjo876
"""

import numpy as np  
import pandas as pd  

class Initials:
    def __init__(self, idf, area, height, firstDayOfYear, leapYear, occupancy,
                 personHeat, appliances, hotWater):
        self.idf = idf
        self.area = area
        self.height = height
        self.firstDayOfYear = firstDayOfYear
        self.leapYear = leapYear
        self.occupancy = occupancy
        self.personHeat = personHeat 
        self.appliances = appliances
        self.hotWater = hotWater 
        self.lighting = lighting
        
    def occupants(area, height):
        """
        Estimates the number of building occupants.
        
        parameters
        ----------
        area: int
            Area of the building footprint. 
        height: int
            Height of the building.
        
        output
        ------
        occupants: int 
            Number of occupants in buildings.
        """
        # Calculates the number of floors.
        # Floor height (floor to floor) is assumed to be 2.8.
        numberOfFloors = round(height // 2.8)
        floorArea = area * numberOfFloors
        
        # Calulates the building occupants for the floor area.
        # In Sweden, on average, floor area per person is 42 m2.
        occupants = round(floorArea // 42)
        
        return occupants


    def days (firstDayOfYear, leapYear ):
        """
        Generates an array of days of a given calendar year with a specific start day.
 
        
        parameters
        ----------
        firstDayOfYear: str
            First day of the calendar year, i.e., Monday, Tuesday, or etc.
        leapYear: int
            1 if calender year is a leap year, 0 if it is not.
        
        output
        ------
        list
            A list of 365 days of calendar year, staring from the specific start day.
        """
        
        # A list of days of a week starting from Monday.
        daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']       
        
        # Duplicate the days of a week for a year with 53 weeks starting from Monday.
        arrayOfDays =  list(np.tile(daysOfWeek, 53))
        
        # Get the index of the specific start day in the list of days of a year.
        index = arrayOfDays.index(firstDayOfYear)
        
        # Rearrange the list of days of a year based on the specific start day 
        # and with considering the leap year. 
        daysOfYear = list( arrayOfDays[index:] + arrayOfDays )[:(365 + leapYear)]
        
        return daysOfYear 


      
    def profile_generator (occupancy, personHeat, appliances,hotWater, 
                           firstDayOfYear, leapYear):
        """
        Generates hourly user profile for occupancy, metabolic heat, 
        domestic hot water, use of electrical appliances and lighting. 
 
        
        parameters
        ------
        occupancy: dataframe
            Annual average daily occupancy profile.
        personHeat: dataframe
            Annual average daily metabolic heat gain profile.
        appliances: dataframe
            Annual average daily electricity use for electrical appliances.
        hotWater: dataframe
            Annual average daily domestic hot water use.
        firstDayOfYear: str
            First day of the calendar year, i.e., Monday, Tuesday, or etc.
        leapYear: int
            1 if calendar year is a leap year, 0 if it is not.

        output
        ------
        occupancyProfile***.txt
        personHeatProfile***.txt
        appliancesProfile***.txt
        hotWaterProfile***.txt
        
            Stand-alone text files including hourly user profiles for both apartments and houses.
        """

        # Get the list of days of the year.
        daysOfYear = Initials.days (firstDayOfYear, leapYear)
        
        # Define an array of the months based on the day numbers.
        months = np.array([31, 59+leapYear, 90+leapYear, 120+leapYear,
                           151+leapYear, 181+leapYear, 212+leapYear,
                           243+leapYear, 273+leapYear, 304+leapYear,
                           334+leapYear, 365+leapYear+1])
 
        # Write an hourly array for annual user profiles based on days (weekday or weekend), 
        # as well as leap year.
        
        occupancyProfile = []
        personHeatProfile = []
        appliancesProfile = []
        hotWaterProfile = []

        for day in daysOfYear:
            # For profiles with no seasonal dependencies.
            occupancyProfile.append(occupancy.values if day == 'Saturday' or day == 'Sunday' else occupancy.values)
            personHeatProfile.append(personHeat.values if day == 'Saturday' or day == 'Sunday' else personHeat.values)
            appliancesProfile.append(appliances.values if day == 'Saturday' or day == 'Sunday' else appliances.values)            
            hotWaterProfile.append(hotWater.values if day == 'Saturday' or day == 'Sunday' else hotWater.values)
            
            
        # Convert lists to numy arrays and reshape them. 
        occupancyProfile = np.array(occupancyProfile).flatten()
        personHeatProfile = np.array(personHeatProfile).flatten() # Watts/person
        appliancesProfile = np.array(appliancesProfile).flatten() # Watts/person
        hotWaterProfile = np.array(hotWaterProfile).flatten()/3600000 #liter/h.person to m3/s.person

        # Get hot water peak flow rate from the profile.
        maxFlowHotWater =  np.max(hotWaterProfile)
        
            
        return (pd.DataFrame(occupancyProfile).to_csv('occupancyProfiles.txt',
                                                      index=False, header=False),
                pd.DataFrame(personHeatProfile).to_csv('personHeatProfiles.txt',
                                                       index=False, header=False), 
                pd.DataFrame(appliancesProfile).to_csv('appliancesProfiles.txt',
                                                       index=False, header=False),
                # The flow rate should be a fraction of peak flow rate.
                pd.DataFrame(hotWaterProfile/maxFlowHotWater).to_csv('hotWaterProfiles.txt',
                                                                     index=False, header=False),
                maxFlowHotWater)


           
class Occupancy(Initials):
    
    
    def __init__(self, idf, area, height, hotWaterTemp, coldWaterTemp, maxFlowHotWater):
        self.idf = idf
        self.area = area
        self.height = height
        self.hotWaterTemp = hotWaterTemp
        self.coldWaterTemp = coldWaterTemp
        self.maxFlowHotWater = maxFlowHotWater          
    
    
    def people (idf, area, height):
        """
        Sets occupants' related heat gain.
            
        input
        ----------
        idf: idf
        
        area: int
            Area of building footprint
        
        height: int
            Height of building
      
        output
        ------
        idf 
        """
        
        # Sets the number of occupants
        occ = Initials.occupants(area, height)
        
        # Sets internal heat gain for occupants in the zone.
        idf.newidfobject('PEOPLE',
                         Name = 'People',
                         Number_of_People = str(occ), 
                         Zone_or_ZoneList_Name = 'Zone',
                         Number_of_People_Schedule_Name = 'OccupancyProfile',
                         Activity_Level_Schedule_Name = 'PersonHeatProfile'
                         )
        
        # Activity_Level_Schedule.
        idf.newidfobject ('SCHEDULE:FILE',
                          Name = 'PersonHeatProfile',
                          Schedule_Type_Limits_Name = 'Any Number',
                          File_Name = 'personHeatProfiles.txt', 
                          Column_Number = '1',
                          Rows_to_Skip_at_Top = '0'
                          )        
        
        # Number_of_People_Schedule.
        idf.newidfobject ('SCHEDULE:FILE',
                          Name = 'OccupancyProfile',
                          Schedule_Type_Limits_Name = 'Any Number',
                          File_Name = 'occupancyProfiles.txt', 
                          Column_Number = '1',
                          Rows_to_Skip_at_Top = '0'
                          )
        
        return idf
 
        
    def equipment (idf, area, height):
        """
        Sets the heat gain from using equipment and lighting.
            
        parameters
        ----------
        idf: idf
        
        area: int
            Area of building footprint.        
        height: int
            Height of building.
        building: str
            Main type of buildings, i.e., Apartment or House.
            
        output
        ------
        idf
        """
        # Sets the number of occupants
        occ = Initials.occupants(area, height)
        
        # Sets internal gains for electric equipment in the zone.
        idf.newidfobject ('ELECTRICEQUIPMENT',
                          Name = 'ElectricEquipment',
                          Zone_or_ZoneList_Name = 'Zone',
                          Schedule_Name = 'AppliancesProfile',
                          Design_Level_Calculation_Method = 'EquipmentLevel',
                          Design_Level = str(occ* 1) #power/person
                          )
        
        # Use profile schedule
        idf.newidfobject ('SCHEDULE:FILE',
                          Name = 'AppliancesProfile',
                          Schedule_Type_Limits_Name = 'Any Number',
                          File_Name = 'appliancesProfiles.txt',
                          Column_Number = '1',
                          Rows_to_Skip_at_Top = '0'
                          )        
            
        return idf
    

    def dhw (idf, area, height, hotWaterTemp, coldWaterTemp, maxFlowHotWater):
        """
        Calculates the hot water use in the zone.
            
        parameters
        ------
        idf: idf
        
        area: int
            Area of building footprint       
        height: int
            Height of building
        hotWaterTemp: int
            Temperature of hot water
        coldWaterTemp: int
            Temperature of cold water.
        maxFlowHotWater: float
            Peak flow rate for hot water use.
        building: str
            Main type of buildings, i.e., Apartment or House.
            
        output
        ------
        idf
        """
        # Sets the number of occupants
        occ = Initials.occupants(area, height)
        
        # Heat demand for hot water use, based on the given use profile and hot and cold water temperatures. 
        idf.newidfobject ('WATERUSE:EQUIPMENT',
                          Name = 'HotWaterUse',
                          Peak_Flow_Rate = str(float(maxFlowHotWater)*occ),
                          Flow_Rate_Fraction_Schedule_Name= 'HotWaterUse',
                          Hot_Water_Supply_Temperature_Schedule_Name = 'HotWaterTemp',
                          Cold_Water_Supply_Temperature_Schedule_Name = 'ColdWaterTemp',
                          Zone_Name = 'Zone'
                          )

        # Schedule for hot water temperature.
        idf.newidfobject ('SCHEDULE:COMPACT',
                          Name = 'HotWaterTemp',
                          Schedule_Type_Limits_Name = 'Any Number',
                          Field_1 = 'Through: 12/31',
                          Field_2 = 'For: AllDays', 
                          Field_3 = 'Until: 24:00',
                          Field_4 = str(hotWaterTemp)
                          )
        
        # Schedule for cold water temperature.
        idf.newidfobject ('SCHEDULE:COMPACT',
                          Name = 'ColdWaterTemp',
                          Schedule_Type_Limits_Name = 'Any Number',
                          Field_1 = 'Through: 12/31',
                          Field_2 = 'For: AllDays', 
                          Field_3 = 'Until: 24:00',
                          Field_4 = str(coldWaterTemp)
                          )
        
        # Schedule for hot water use
        idf.newidfobject ('SCHEDULE:FILE',
                          Name = 'HotWaterUse',
                          Schedule_Type_Limits_Name = 'Any Number',
                          File_Name = 'hotWaterProfiles.txt',
                          Column_Number = '1',
                          Rows_to_Skip_at_Top = '0'
                          )

        return idf
