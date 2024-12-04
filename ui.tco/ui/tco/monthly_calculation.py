import numpy as np
# Helper functions for monthly power calculations
def round_to_nearest(x, base):
    base_array = np.array(base)
    differences = np.abs(base_array - x)
    idx = differences.argmin()
    nearest_value = base_array[idx]
    print(f"Rounding {x} to nearest in {base}: {nearest_value} (differences: {differences}, index: {idx})")
    return nearest_value

def calculate_monthly_air_chiller_power(city_data, chillers_data, fws_air, no_of_equipments_air, air_cooling_capacity_per_pod, num_pods, model):
    equipment_capacity = 1114
    cooling_capacity_total = air_cooling_capacity_per_pod * num_pods
    temp_bins = [25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 46]

    monthly_power_consumption = {
        "Hours in Jan": 0, "Hours in Feb": 0, "Hours in March": 0, "Hours in April": 0,
        "Hours in May": 0, "Hours in June": 0, "Hours in July": 0, "Hours in August": 0,
        "Hours in Sep": 0, "Hours in Oct": 0, "Hours in Nov": 0, "Hours in Dec": 0
    }

    try:
        for _, row in city_data.iterrows():
            dry_bulb = row['Dry Bulb Temperature']

            if model == "Schneider XRAC4812" :
                dry_bulb = round_to_nearest(dry_bulb, temp_bins)
            chiller_data = chillers_data[
                (chillers_data['TWOUT'] == fws_air) &
                (chillers_data['TA'] == dry_bulb) &
                (chillers_data['Model'] == model)
            ]

            if not chiller_data.empty:
                equipment_capacity = chiller_data.iloc[0]['Cooling Capacity']
                partial_load_factor_air = cooling_capacity_total / no_of_equipments_air / equipment_capacity
                power_input = chiller_data.iloc[0]['Power Input (kW)'] * partial_load_factor_air
                for month_col in monthly_power_consumption.keys():
                    month_hours = row[month_col]
                    power_for_temperature = power_input * month_hours * no_of_equipments_air
                    monthly_power_consumption[month_col] += power_for_temperature
            else:
                print(f"No chiller data found for dry bulb {dry_bulb}°C with FWS temp Air{fws_air}")

        return monthly_power_consumption

    except Exception as e:
        print(f"Error calculating monthly air chiller power consumption: {e}")
        return None

def calculate_monthly_liquid_chiller_power(city_data, chillers_data, dryer_data, fws_liquid, no_of_equipments_liquid, no_of_equipments_liquid_dry_cooler, liquid_cooling_capacity_per_pod, num_pods, cooling_capacity_per_unit_dry_cooler, liquid_cooling_type, chiller_model, dryer_model):
    cooling_capacity_total = liquid_cooling_capacity_per_pod * num_pods
    temp_bins_schneider = [25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 46]
    temp_bins_dry = [8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41]
    check_model = True

    if liquid_cooling_type == "Dry Cooler":
        equipment_capacity = 300
        no_of_equipments = no_of_equipments_liquid_dry_cooler
        cooler_data = dryer_data
        model_field = dryer_model
        check_model = False
    elif liquid_cooling_type == "Chiller":
        equipment_capacity = 1114
        no_of_equipments = no_of_equipments_liquid
        cooler_data = chillers_data
        model_field = chiller_model
        check_model = True

    monthly_liquid_cooling_power = {
        "Hours in Jan": 0, "Hours in Feb": 0, "Hours in March": 0, "Hours in April": 0,
        "Hours in May": 0, "Hours in June": 0, "Hours in July": 0, "Hours in August": 0,
        "Hours in Sep": 0, "Hours in Oct": 0, "Hours in Nov": 0, "Hours in Dec": 0
    }

    try:
        for _, row in city_data.iterrows():
            dry_bulb = row['Dry Bulb Temperature']
            if check_model:
                if model_field == "Schneider XRAC4812" :
                    dry_bulb = round_to_nearest(dry_bulb, temp_bins_schneider)
                cooler_row = cooler_data[
                    (cooler_data['TWOUT'] == fws_liquid) &
                    (cooler_data['TA'] == dry_bulb) &
                    (cooler_data['Model'] == model_field)
                ]
            else:
                dry_bulb = round_to_nearest(dry_bulb, temp_bins_dry)
                cooler_row = cooler_data[
                    (cooler_data['TWOUT'] == fws_liquid) &
                    (cooler_data['TA'] == dry_bulb)&
                    (cooler_data['Model'] == model_field)
                ]

            if not cooler_row.empty:
                equipment_capacity = cooler_data.iloc[0]['Cooling Capacity']
                partial_load_factor_air = cooling_capacity_total / no_of_equipments / equipment_capacity
                power_input = cooler_data.iloc[0]['Power Input (kW)'] * partial_load_factor_air
                for month_name in monthly_liquid_cooling_power.keys():
                    hours_in_month = row[month_name]
                    power_for_temperature = power_input * hours_in_month * no_of_equipments
                    monthly_liquid_cooling_power[month_name] += power_for_temperature
            else:
                print(f"No data found for dry bulb {dry_bulb}°C with FWS temp {fws_liquid} for {liquid_cooling_type}")

        return monthly_liquid_cooling_power

    except Exception as e:
        print(f"Error calculating monthly liquid chiller power: {e}")
        return None

def calculate_monthly_common_power(lighting_power, ups_it_loss_power, hvac_power, it_power):
    return lighting_power + ups_it_loss_power + hvac_power + it_power

def calculate_total_monthly_air_cooling_power(pw170_monthly_power, air_chiller_monthly_power):
    air_cooling_air_cooled = (pw170_monthly_power + air_chiller_monthly_power)
    air_cooling_water_cooled = pw170_monthly_power
    return air_cooling_air_cooled, air_cooling_water_cooled

def calculate_total_monthly_liquid_cooling_power(ups_mech_loss_monthly_power, xdu1350_monthly_power, liquid_chiller_monthly_power):
    liquid_cooling_air_cooled = (ups_mech_loss_monthly_power + xdu1350_monthly_power + liquid_chiller_monthly_power)
    liquid_cooling_water_cooled = (ups_mech_loss_monthly_power + xdu1350_monthly_power)
    return liquid_cooling_air_cooled, liquid_cooling_water_cooled

def calculate_monthly_pue(common_power, air_cooling_air_cooled, liquid_cooling_air_cooled, it_power):
    try:
        if it_power == 0:
            print("IT power is zero, cannot calculate PUE.")
            return None
        return (common_power + air_cooling_air_cooled + liquid_cooling_air_cooled) / it_power
    except Exception as e:
        print(f"Error calculating monthly PUE: {e}")
        return None
