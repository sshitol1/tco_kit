from . import constants

def calculate_elctrcity_cost_ac_chiller(air_cooling_air_cooled, electricity_price):
    return air_cooling_air_cooled * electricity_price

def calculate_elctrcity_cost_lc(liquid_chiller_power,electricity_price,liquid_cooling_type):
    return liquid_chiller_power * electricity_price

def calculate_nth_energy_cost(annual_cost, years):
    # Calculate the total cost over the given number of years
    if constants.ELECTRICITY_PRICE_ANNUAL_INCREASE != 0:
        total_cost = annual_cost * ((1 - ((1 + constants.ELECTRICITY_PRICE_ANNUAL_INCREASE)**(years))) / (1 - (1 + constants.ELECTRICITY_PRICE_ANNUAL_INCREASE)))
    else:
        total_cost = annual_cost * years  # If there's no increase, it's just cost times number of years
    return total_cost

def calculate_maintenance_for_air_cooling_chiller(total_cost_chiller_air_cooling):
    return constants.CAPEX_COST_PERCENTAGES["Air Cooling - AC Chiller"] * total_cost_chiller_air_cooling

def calculate_maintanence_for_liquid_cooling_chiller(total_cost_chiller_liquid_cooling, liquid_cooling_type):
    if liquid_cooling_type == "Dry Cooler":
        return constants.CAPEX_COST_PERCENTAGES["Liquid Cooling - Dry Cooler"] * total_cost_chiller_liquid_cooling
    elif liquid_cooling_type == "Chiller":
        return constants.CAPEX_COST_PERCENTAGES["Liquid Cooling - AC Chiller"] * total_cost_chiller_liquid_cooling
    
def calculate_nth_maintenance_cost(annual_cost, years):
    # Calculate the total cost over the given number of years
    if constants.MAINTENANCE_ANNUAL_INCREASE != 0:
        total_cost = annual_cost * ((1 - ((1 + constants.MAINTENANCE_ANNUAL_INCREASE)**(years))) / (1 - (1 + constants.MAINTENANCE_ANNUAL_INCREASE)))
    else:
        total_cost = annual_cost * years  # If there's no increase, it's just cost times number of years
    return total_cost

def calculate_flushing_cost(total_volume):
    return total_volume * constants.NUMBER_OF_TEST_PER_YEAR * constants.FLUSHING_COST_PER_GALLON

def calculate_monitoring_cost(num_pods):
    return constants.MONITORING_SAMPLING_COST_PER_TEST * constants.NUMBER_OF_TEST_PER_YEAR * num_pods

def calculate_bms_opex(bms_total_cost):
    return 5000 + (bms_total_cost * 0.05)