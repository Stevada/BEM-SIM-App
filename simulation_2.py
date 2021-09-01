# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 20:41:35 2020

@author: Xu Ziang
"""


import os
import opyplus as op 
import numpy as np
import pandas as pd
import math

class simulation:
    def __init__(self, epm, epw, main_dir):
        self.epm = epm
        self.epw = epw
        self.main_dir = main_dir
        
    def simulate(self):
        s = op.simulate(self.epm, self.epw, self.main_dir)
        if s.get_status() == "finished":
            status = True 
        else:
            status = False 
        # eso = s.get_out_eso()
        if status:
            meters = pd.read_csv(self.main_dir + "/eplusmtr.csv")
            outputs = meters['ELECTRICITY:UNIT_1 [J](Hourly)']
            outputs = [i/3600000 for i in outputs]
            outputs = np.array(outputs)
            # hourly_df = eso.get_data()
            # return outputs
            return status, outputs
        else:
            return status, None
        
    """Edit parameter"""
    # update the parameter with given delta_parameter and step size
    def par_update(self, idx, g, alp):
        """
        idx: index of the parameter that needs to be updated
        g: delta_parameter
        alp: step size
        """
        if idx == 1:
            w = self.epm.WindowMaterial_Shade.one(lambda x: x.name == "coolingshade")
            temp = w.solar_transmittance - alp*g
            if temp > 0.001 and temp < 0.999:
                w.solar_transmittance = temp # no.1
                w.solar_reflectance = 0.999 - w.solar_transmittance # no.2
                
        elif idx == 3:
            w = self.epm.Lights.one(lambda x: x.name == "living hw & plugin lighting_1")
            temp = w.lighting_level - alp*g
            if temp > 300 and temp < 700:
                w.lighting_level = temp
                
        elif idx == 4:
            w = self.epm.ElectricEquipment.one(lambda x: x.name == "ceilingfans_1")
            temp = w.design_level - alp*g 
            if temp > 80 and temp < 180:
                w.design_level = temp
                
        elif idx == 5:
            w = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            temp = w.gross_rated_cooling_cop - alp*g
            if temp > 2 and temp < 5:
                w.gross_rated_cooling_cop = temp 
                
        elif idx == 6:
            w = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            temp = w.gross_rated_total_cooling_capacity - alp*g
            if temp > 12000 and temp < 60000:
                w.gross_rated_total_cooling_capacity = temp 
                
        elif idx == 7:
            w = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            temp = w.nominal_capacity - alp*g 
            if temp > 20000 and temp < 40000:
                w.nominal_capacity = temp 
                
        elif idx == 8:
            w = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            temp = w.burner_efficiency - alp*g 
            if temp > 0.5 and temp < 0.999:
                w.burner_efficiency = temp
        elif idx == 9:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            temp = w.cooling_supply_air_flow_rate - alp*g
            if temp > 0.001 and temp < 0.999:
                w.cooling_supply_air_flow_rate = temp 
        elif idx == 10:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            temp = w.heating_supply_air_flow_rate - alp*g
            if temp > 0.001 and temp < 0.999:
                w.heating_supply_air_flow_rate = temp 
        elif idx == 11:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            temp = w.maximum_supply_air_temperature - alp*g 
            if temp > 30 and temp < 70:
                w.maximum_supply_air_temperature = temp 
        elif idx == 12:
            w = self.epm.WaterHeater_Mixed.one(lambda x:x.name == "water heater_1")
            temp = w.heater_thermal_efficiency - alp*g 
            if temp > 0.001 and temp < 0.999:
                w.heater_thermal_efficiency = temp 
        elif idx == 13:
            w = self.epm.Fan_onOff.one(lambda x:x.name == "supply fan_1")
            temp = w.fan_total_efficiency - alp*g
            if temp > 0.001 and temp < 0.999:
                w.fan_total_efficiency = temp 
        elif idx == 14:
            w = self.epm.ZoneVentilation_DesignFlowRate.one(lambda x:x.name == "natural ventilation_1")
            temp = w.design_flow_rate - alp*g
            if temp > 0.001 and temp < 0.999:
                w.design_flow_rate = temp 
    
    # return current calibration parameters
    def par_print(self):
        v = {}
        w1 = self.epm.WindowMaterial_Shade.one(lambda x: x.name == "coolingshade")
        v[1] = w1.solar_transmittance # no.1
        v[2] = w1.solar_reflectance # no.2
        
        w2 = self.epm.Lights.one(lambda x: x.name == "living hw & plugin lighting_1")
        v[3] = w2.lighting_level # no.3
        
        w3 = self.epm.ElectricEquipment.one(lambda x: x.name == "ceilingfans_1")
        v[4] = w3.design_level # no.4
        
        w4 = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
        v[5] = w4.gross_rated_cooling_cop # no.5
        v[6] = w4.gross_rated_total_cooling_capacity # no.6
        # w4.gross_rated_sensible_heat_ratio = np.random.uniform(0.001, 0.999, 1)
        
        w5 = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
        v[7] = w5.nominal_capacity # no.7
        v[8] = w5.burner_efficiency # no.8
        
        w6 = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
        v[9] = w6.cooling_supply_air_flow_rate # no.9
        v[10] = w6.heating_supply_air_flow_rate # no.10
        v[11] = w6.maximum_supply_air_temperature # no.11
        
        w7 = self.epm.WaterHeater_Mixed.one(lambda x:x.name == "water heater_1")
        v[12] = w7.heater_thermal_efficiency # no.12
        
        w8 = self.epm.Fan_onOff.one(lambda x:x.name == "supply fan_1")
        v[13] = w8.fan_total_efficiency # no.13
        
        w9 = self.epm.ZoneVentilation_DesignFlowRate.one(lambda x:x.name == "natural ventilation_1")
        v[14] = w9.design_flow_rate # no.14
        
        return v
    # assign values to calibration parameters
    def par_assign(self, pars, season=None):
        """
        pars: values of calibration parameters, type: dictionary
        season: in [None, 'global', 'summer', 'winter']
        """
        if season == 'global' or not season:
            w1 = self.epm.WindowMaterial_Shade.one(lambda x: x.name == "coolingshade")
            w1.solar_transmittance = pars[1] # no.1
            w1.solar_reflectance = pars[2] # no.2
            
            w2 = self.epm.Lights.one(lambda x: x.name == "living hw & plugin lighting_1")
            w2.lighting_level = pars[3] # no.3
            
            w3 = self.epm.ElectricEquipment.one(lambda x: x.name == "ceilingfans_1")
            w3.design_level = pars[4]# no.4
            
            w6 = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w6.cooling_supply_air_flow_rate = pars[9]# no.9
            w6.heating_supply_air_flow_rate = pars[10]# no.10
            w6.maximum_supply_air_temperature= pars[11] # no.11
            
            w7 = self.epm.WaterHeater_Mixed.one(lambda x:x.name == "water heater_1")
            w7.heater_thermal_efficiency = pars[12] # no.12
            
            w8 = self.epm.Fan_onOff.one(lambda x:x.name == "supply fan_1")
            w8.fan_total_efficiency = pars[13] # no.13
            
            w9 = self.epm.ZoneVentilation_DesignFlowRate.one(lambda x:x.name == "natural ventilation_1")
            w9.design_flow_rate = pars[14]# no.14
            
        if season == 'summer' or not season:
            w4 = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            w4.gross_rated_cooling_cop = pars[5] # no.5
            w4.gross_rated_total_cooling_capacity = pars[6] # no.6
            # w4.gross_rated_sensible_heat_ratio = np.random.uniform(0.001, 0.999, 1)
        if season == "winter" or not season:
            w5 = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            w5.nominal_capacity = pars[7] # no.7
            w5.burner_efficiency = pars[8]# no.8
    
    # add dt to theta for gradient estimation
    def par_learn(self, idx, dt):
        """
        theta := theta + dt
        """
        if idx == 1:
            w = self.epm.WindowMaterial_Shade.one(lambda x: x.name == "coolingshade")
            w.solar_transmittance +=  dt# no.1
            w.solar_reflectance = 0.999 - w.solar_transmittance # no.2
        elif idx == 3:
            w = self.epm.Lights.one(lambda x: x.name == "living hw & plugin lighting_1")
            w.lighting_level += 400*dt 
        elif idx == 4:
            w = self.epm.ElectricEquipment.one(lambda x: x.name == "ceilingfans_1")
            w.design_level += 100*dt
        elif idx == 5:
            w = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            w.gross_rated_cooling_cop += 3*dt
        elif idx == 6:
            w = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            w.gross_rated_total_cooling_capacity += 48000*dt
        elif idx == 7:
            w = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            w.nominal_capacity += 20000*dt 
        elif idx == 8:
            w = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            w.burner_efficiency += 0.5*dt 
        elif idx == 9:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w.cooling_supply_air_flow_rate += dt 
        elif idx == 10:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w.heating_supply_air_flow_rate += dt 
        elif idx == 11:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w.maximum_supply_air_temperature += 40*dt 
        elif idx == 12:
            w = self.epm.WaterHeater_Mixed.one(lambda x:x.name == "water heater_1")
            w.heater_thermal_efficiency += dt 
        elif idx == 13:
            w = self.epm.Fan_onOff.one(lambda x:x.name == "supply fan_1")
            w.fan_total_efficiency += dt
        elif idx == 14:
            w = self.epm.ZoneVentilation_DesignFlowRate.one(lambda x:x.name == "natural ventilation_1")
            w.design_flow_rate += dt
    
    # recover the theta after some kind of theta update
    def par_rec(self, idx, dt):
        """
        theta := theta - dt
        """
        if idx == 1:
            w = self.epm.WindowMaterial_Shade.one(lambda x: x.name == "coolingshade")
            w.solar_transmittance -=  dt# no.1
            w.solar_reflectance = 0.999 - w.solar_transmittance # no.2
        elif idx == 3:
            w = self.epm.Lights.one(lambda x: x.name == "living hw & plugin lighting_1")
            w.lighting_level -= 400*dt 
        elif idx == 4:
            w = self.epm.ElectricEquipment.one(lambda x: x.name == "ceilingfans_1")
            w.design_level -= 100*dt
        elif idx == 5:
            w = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            w.gross_rated_cooling_cop -= 3*dt
        elif idx == 6:
            w = self.epm.Coil_Cooling_DX_SingleSpeed.one(lambda x:x.name == "dx cooling coil_1")
            w.gross_rated_total_cooling_capacity -= 48000*dt
        elif idx == 7:
            w = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            w.nominal_capacity -= 20000*dt 
        elif idx == 8:
            w = self.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
            w.burner_efficiency -= 0.5*dt 
        elif idx == 9:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w.cooling_supply_air_flow_rate -= dt 
        elif idx == 10:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w.heating_supply_air_flow_rate -= dt 
        elif idx == 11:
            w = self.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
            w.maximum_supply_air_temperature -= 40*dt 
        elif idx == 12:
            w = self.epm.WaterHeater_Mixed.one(lambda x:x.name == "water heater_1")
            w.heater_thermal_efficiency -= dt 
        elif idx == 13:
            w = self.epm.Fan_onOff.one(lambda x:x.name == "supply fan_1")
            w.fan_total_efficiency -= dt
        elif idx == 14:
            w = self.epm.ZoneVentilation_DesignFlowRate.one(lambda x:x.name == "natural ventilation_1")
            w.design_flow_rate -= dt
    
    # change the simulation period
    def par_season(self, season):
        w = self.epm.RunPeriod.one(lambda x:x.name == "austin mueller municipal ap u tx 2340 sqft")
        bath = self.epm.Schedule_File.one(lambda x:x.name == "baths_1")
        cloth = self.epm.Schedule_File.one(lambda x:x.name == "clotheswasher_1")
        dishwater = self.epm.Schedule_File.one(lambda x:x.name == "dishwasher_1")
        shower = self.epm.Schedule_File.one(lambda x:x.name == "showers_1")
        sinks = self.epm.Schedule_File.one(lambda x:x.name == "sinks_1")
        mels = self.epm.Schedule_File.one(lambda x:x.name == "total_mels_1")
        mgls = self.epm.Schedule_File.one(lambda x:x.name == "total_mgls_1")
        if season == 'winter':
            w.begin_month = 11
            w.begin_day_of_month = 1
            w.end_month = 3
            w.end_day_of_month = 31
            
        elif season == 'summer':
            w.begin_month = 3
            w.begin_day_of_month = 1 
            w.end_month = 11
            w.end_day_of_month = 30
            w.day_of_week_for_start_day = 'saturday'
            bath.rows_to_skip_at_top = 8497
            cloth.rows_to_skip_at_top = 8497
            dishwater.rows_to_skip_at_top = 8497
            shower.rows_to_skip_at_top = 8497
            sinks.rows_to_skip_at_top = 8497
            mels.rows_to_skip_at_top = 1417
            mgls.rows_to_skip_at_top = 1417
            
        elif season == 'year':
            w.begin_month = 1
            w.begin_day_of_month = 1
            w.end_month = 12
            w.end_day_of_month = 31
            w.day_of_week_for_start_day = 'wednesday'
            bath.rows_to_skip_at_top = 1
            cloth.rows_to_skip_at_top = 1
            dishwater.rows_to_skip_at_top = 1
            shower.rows_to_skip_at_top = 1
            sinks.rows_to_skip_at_top = 1
            mels.rows_to_skip_at_top = 1
            mgls.rows_to_skip_at_top = 1
            
        elif season == 'BC':
            w.begin_month = 11
            w.begin_day_of_month = 1
            w.end_month = 12
            w.end_day_of_month = 31 
        v = {}
        w = self.epm.ElectricEquipment.one(lambda x:x.name == "refrigerator_1")
        v[1] = w.design_level

        w = self.epm.ElectricEquipment.one(lambda x:x.name == "misc elec load_1")
        v[2] = w.design_level

        w = self.epm.ElectricEquipment.one(lambda x:x.name == "dishwasher_1")
        v[3] = w.design_level
        
        w = self.epm.ElectricEquipment.one(lambda x:x.name == "cooking range_1")
        v[4] = w.design_level

        w = self.epm.ElectricEquipment.one(lambda x:x.name == "clothes washer_1")
        v[5] = w.design_level

        w = self.epm.ElectricEquipment.one(lambda x:x.name == "clothes dryer_1")
        v[6] = w.design_level

        w = self.epm.Material.one(lambda x:x.name == "studandairwall")
        v[7] = w.conductivity

        w = self.epm.Material.one(lambda x:x.name == "studandairwall")
        v[8] = w.thickness

        #u-factors of windows at all four directions are the same 
        w = self.epm.WindowMaterial_SimpleGlazingSystem.one(lambda x:x.name == "back-win")
        v[9] = w.u_factor

        w = self.epm.Exterior_lights.one(lambda x:x.name == "exterior lighting_1")
        v[10] = w.design_level

        w = self.epm.Fan_OnOff.one(lambda x:x.name == "supply fan_1")
        v[11] = w.fan_total_efficiency
        
        return v
            
    def RMSE(self, y, y_hat):
        return np.sqrt(np.square(y - y_hat).mean())

    def MSE(self, y, y_hat):
        return np.square(y - y_hat).mean()
    
    def MAE(self, y, y_hat):
        temp = np.abs(y - np.array(y_hat))
        return temp.mean()
    
    def CVRMSE(self, y, y_hat):
        return np.sqrt(np.square(y - y_hat).mean())/y.mean()
    
    # change the schdule so that summer and winter are not overlapped
    def changeschedule(self):
        for i in range(1, 13):
            if i < 10:
                schname = "coolingseasonschedule" + '0' + str(i)  + 'd'
            else:
                schname = "coolingseasonschedule" + str(i) + 'd'
            sch = self.epm.schedule_day_hourly.one(lambda x:x.name == schname)
            
            if i <= 9 and i >= 5:
                q = 1
            else:
                q = 0 
            sch.hour_1 = q
            sch.hour_2 = q
            sch.hour_3 = q
            sch.hour_4 = q 
            sch.hour_5 = q 
            sch.hour_6 = q 
            sch.hour_7 = q 
            sch.hour_8 = q 
            sch.hour_9 = q 
            sch.hour_10 = q 
            sch.hour_11 = q 
            sch.hour_12 = q 
            sch.hour_13 = q
            sch.hour_14 = q 
            sch.hour_15 = q 
            sch.hour_16 = q 
            sch.hour_17 = q 
            sch.hour_18 = q
            sch.hour_19 = q 
            sch.hour_20 = q 
            sch.hour_21 = q 
            sch.hour_22 = q 
            sch.hour_23 = q 
            sch.hour_24 = q
            
            if i < 10:
                schname = "heatingseasonschedule" + '0' + str(i)  + 'd'
            else:
                schname = "heatingseasonschedule" + str(i) + 'd'
            sch = self.epm.schedule_day_hourly.one(lambda x:x.name == schname)
            
            if i >= 11 or i <= 2:
                q = 1 
            else:
                q = 0
            sch.hour_1 = q
            sch.hour_2 = q
            sch.hour_3 = q
            sch.hour_4 = q
            sch.hour_5 = q
            sch.hour_6 = q 
            sch.hour_7 = q
            sch.hour_8 = q
            sch.hour_9 = q
            sch.hour_10 = q
            sch.hour_11 = q 
            sch.hour_12 = q 
            sch.hour_13 = q
            sch.hour_14 = q 
            sch.hour_15 = q 
            sch.hour_16 = q 
            sch.hour_17 = q 
            sch.hour_18 = q
            sch.hour_19 = q 
            sch.hour_20 = q 
            sch.hour_21 = q 
            sch.hour_22 = q 
            sch.hour_23 = q 
            sch.hour_24 = q

