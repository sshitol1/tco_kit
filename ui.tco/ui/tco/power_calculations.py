from . import constants
import numpy as np

def round_to_nearest(x, base):
    base_array = np.array(base)
    differences = np.abs(base_array - x)
    idx = differences.argmin()
    nearest_value = base_array[idx]
    print(f"Rounding {x} to nearest in {base}: {nearest_value} (differences: {differences}, index: {idx})")
    return nearest_value

def calculate_annual_power_consumption(num_pods,total_power_per_pod, hp2_per_cdu, hp2_per_crah, no_of_cdus_per_pod, no_of_crahs_per_pod):
    """Calculate annual power consumption for IT, PW170, and XDU1350 components."""
    try:
        # Calculate total IT power consumption per year  # assuming this returns power in kW
        it_power_consumption_yearly = total_power_per_pod * num_pods * constants.HOURS_IN_YEAR

        # Calculate PW170 power consumption per year
        pw170_power = hp2_per_crah
        pw170_annual_consumption = pw170_power * num_pods * no_of_crahs_per_pod * constants.HOURS_IN_YEAR

        # Calculate XDU1350 power consumption per year
        xdu1350_power = hp2_per_cdu # in kW
        xdu1350_annual_consumption = xdu1350_power * num_pods * no_of_cdus_per_pod * constants.HOURS_IN_YEAR

        return {
            "it_power": it_power_consumption_yearly,
            "pw170_power": pw170_annual_consumption,
            "xdu1350_power": xdu1350_annual_consumption
        }
    except Exception as e:
        print(f"Error calculating annual power consumption: {e}")
        return None


def calculate_general_power_consumption(total_power_per_pod, num_pods, hp2_per_cdu, no_of_cdus_per_pod):
    hours_in_year = constants.HOURS_IN_YEAR
    lighting_power = constants.PERCENTAGE["Lighting"] * total_power_per_pod * hours_in_year * num_pods
    ups_it_loss_power = constants.PERCENTAGE["UPS IT Loss"] * total_power_per_pod * hours_in_year * num_pods
    ups_mech_loss_power = constants.PERCENTAGE["UPS Mechanical Loss"] * hp2_per_cdu * no_of_cdus_per_pod * hours_in_year * num_pods
    hvac_power = constants.PERCENTAGE["HVAC"] * total_power_per_pod * hours_in_year * num_pods

    return {
        "lighting_power": lighting_power,
        "ups_it_loss_power": ups_it_loss_power,
        "ups_mech_loss_power": ups_mech_loss_power,
        "hvac_power": hvac_power
    }

def calculate_common_power_consumption(lighting_power, ups_it_loss_power, hvac_power, it_power_yearly):
    return lighting_power + ups_it_loss_power + hvac_power + it_power_yearly


def calculate_total_air_cooling_power(pw170_annual_power, air_chiller_power):
    air_cooling_air_cooled = pw170_annual_power + air_chiller_power
    air_cooling_water_cooled = pw170_annual_power
    return air_cooling_air_cooled, air_cooling_water_cooled


def calculate_total_liquid_cooling_power(ups_mech_loss_power, xdu1350_annual_power, liquid_chiller_power):
    liquid_cooling_air_cooled = ups_mech_loss_power + xdu1350_annual_power + liquid_chiller_power
    liquid_cooling_water_cooled = ups_mech_loss_power + xdu1350_annual_power
    return liquid_cooling_air_cooled, liquid_cooling_water_cooled


def calculate_total_pue(it_power_yearly, common_power, air_cooling_air_cooled, liquid_cooling_air_cooled):
    return (common_power + air_cooling_air_cooled + liquid_cooling_air_cooled) / it_power_yearly


def calculate_liquid_cooling_power(dry_bulb,city_data, chillers_data, dryer_data, fws_liquid, no_of_equipments_liquid, no_of_equipments_liquid_dry_cooler, liquid_cooling_capacity_per_pod, num_pods, cooling_capacity_per_unit_dry_cooler, chiller_model, dryer_model, liquid_cooling_type):
    try:
        cooling_capacity_total = liquid_cooling_capacity_per_pod * num_pods
        total_power_consumption = 0
        temp_bins = [8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41]  # Temperature bins

        # Load relevant data and set the partial load factor based on the type of liquid cooling
        if liquid_cooling_type == "Dry Cooler":
            cooler_data = dryer_data
            equipment_field = 'Cooling Capacity' 
            model_field = dryer_model
            equipments = no_of_equipments_liquid_dry_cooler
        elif liquid_cooling_type == "Chiller":
            cooler_data = chillers_data
            equipment_field = 'Cooling Capacity'
            model_field = chiller_model
            equipments = no_of_equipments_liquid

        # Iterate over each dry bulb temperature in the city data
        for _, row in city_data.iterrows():
            dry_bulb = row['Dry Bulb Temperature']
            hours = row['Hours in Year']

            if liquid_cooling_type == "Dry Cooler":
                dry_bulb = round_to_nearest(dry_bulb, temp_bins)

            # Filter cooler data based on conditions; model check only if needed
            cooler_row = cooler_data[
                (cooler_data['TWOUT'] == fws_liquid) &
                (cooler_data['TA'] == dry_bulb) &
                (cooler_data['Model'] == model_field)
            ]
            print("cooler_row", cooler_row)
            if not cooler_row.empty:
                for idx, cr in cooler_row.iterrows():
                    equipment_capacity = cr[equipment_field]
                    partial_load_factor_liquid = cooling_capacity_total / equipments / equipment_capacity
                    power_input = (cr['Power Input (kW)'] * (partial_load_factor_liquid ** 3))

                    # Calculate power consumption for the current dry bulb temperature
                    power_for_temperature = power_input * hours * equipments
                    total_power_consumption += power_for_temperature
                    print(f"Power input for {dry_bulb}°C {liquid_cooling_type}: {power_input} kW, hours: {hours}, no. of equipments: {equipments}")

            else:
                print(f"No data found for dry bulb {dry_bulb}°C with FWS temp {fws_liquid} for {liquid_cooling_type}")

        print(f"Total Power Consumption for liquid: {total_power_consumption} kWh")
        return total_power_consumption
    except Exception as e:
        print("Error during computation: ", e)
        return None

def calculate_air_cooling_power(dry_bulb, city_data, chillers_data, fws_air, no_of_equipments_air, air_cooling_capacity_per_pod, num_pods, model):
    try:
        cooling_capacity_total = air_cooling_capacity_per_pod * num_pods
        total_power_consumption = 0
        temp_bins = [25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 46]  # Temperature bins

        # Iterate over each dry bulb temperature in the Dallas data
        for _, row in city_data.iterrows():
            dry_bulb = row['Dry Bulb Temperature']
            hours = row['Hours in Year']

            if model == "Schneider XRAC4812" :
                dry_bulb = round_to_nearest(dry_bulb, temp_bins)

            # Find matching chiller data for current dry bulb and fws_temp
            chiller_data = chillers_data[
                (chillers_data['TWOUT'] == fws_air) &
                (chillers_data['TA'] == dry_bulb) &
                (chillers_data['Model'] == model)
            ]

            if not chiller_data.empty:
                # Now extracting the equipment capacity dynamically from the chiller data
                equipment_capacity = chiller_data.iloc[0]['Cooling Capacity']
                partial_load_factor_air = cooling_capacity_total / no_of_equipments_air / equipment_capacity
                
                power_input = (chiller_data.iloc[0]['Power Input (kW)'] * partial_load_factor_air)
                print(f"Power input for {dry_bulb}°C and FWS {fws_air}°C and model {model}: {power_input} kW")

                # Calculate power consumption for the current dry bulb temperature
                power_for_temperature = power_input * hours * no_of_equipments_air
                total_power_consumption += power_for_temperature

            else:
                print(f"No chiller data found for dry bulb {dry_bulb}°C with FWS temp {fws_air}")

        print(f"Total Power Consumption Air: {total_power_consumption} kWh")
        return total_power_consumption

    except Exception as e:
        print(f"Error calculating total power consumption: {str(e)}")


