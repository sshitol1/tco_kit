from . import constants
from . import helper


def calculate_crah_cost_per_pod(no_of_crahs_per_pod_redundant):
    installation_cost = 6264.29
    piping_cost = 19807
    return no_of_crahs_per_pod_redundant * (constants.vendor_data[2]["Price ($)"] + installation_cost + piping_cost)

def calculate_cdu_cost_per_pod(no_of_cdus_per_pod_redundant):   
    installation_cost = 3735
    piping_cost = 36000
    return no_of_cdus_per_pod_redundant * (constants.CDU_L2L_DATA["Vertiv"]["XDU1350"]["price"] + installation_cost + piping_cost)

def calculate_total_crah_cost(no_of_crahs_per_pod_redundant,num_pods):
    installation_cost = 6264.29
    piping_cost = 19807
    return no_of_crahs_per_pod_redundant * (constants.vendor_data[2]["Price ($)"] + installation_cost + piping_cost) *num_pods

def calculate_total_cdu_cost(no_of_cdus_per_pod_redundant, num_pods):   
    installation_cost = 3735
    piping_cost = 36000
    return no_of_cdus_per_pod_redundant * (constants.CDU_L2L_DATA["Vertiv"]["XDU1350"]["price"] + installation_cost + piping_cost) * num_pods

def calculate_total_air_ducting_cost(no_of_crahs_per_pod_redundant, num_pods):
    return no_of_crahs_per_pod_redundant * num_pods * 13142.86

def calculate_total_aisle_containment_cost(total_no_of_racks):
    return total_no_of_racks * 1000

def calculate_total_belimo_cost(no_of_belimos):
    return no_of_belimos * constants.BELIMO_PRICE

def calculate_total_dn20_cost(no_of_DN20_valve):
    return no_of_DN20_valve * constants.DN20_VALVE_PRICE

def calculate_above_racks_piping(no_of_racks_gb200):
    return no_of_racks_gb200 * constants.ABOVE_RACKS_PIPING_PRICE

def calculate_piping_cost(length_of_pipe, price_per_meter, piping_cost):
    return (length_of_pipe * price_per_meter) + piping_cost

def calculate_leak_detection(no_of_LD2100_controller):
    return (constants.LD2100_CONTROLLER_PRICE  + constants.LD2100_INSTALLATION_PRICE) * no_of_LD2100_controller

 # Return the lowest key if input is below the lowest key

def calculate_chiller_air_cooling_cost(fws_air_temp, selected_chiller,no_of_chillers_air_cooling_redundant):
    nearest_temp = helper.find_nearest_valid_temp(fws_air_temp)
    print("nearest_temp air cooling", nearest_temp)
    unit_price = constants.VERTIV1_MW_PRICE[nearest_temp]

    # Assuming constants for installation_cost, piping_cost, and startup_cost are defined
    total_cost = (unit_price + 
                  constants.EQUIPMENT_COSTS["Vertiv 1MW"]["installation_cost"] + 
                  constants.EQUIPMENT_COSTS["Vertiv 1MW"]["piping_cost"] + 
                  constants.EQUIPMENT_COSTS["Vertiv 1MW"]["startup_cost"]) * no_of_chillers_air_cooling_redundant
    return total_cost

def calculate_chiller_liquid_cooling_cost(fws_liquid_temp, selected_chiller, no_of_chillers_liquid_cooling_redundant, no_of_dry_cooler_redundant, liquid_cooling_type ):
    nearest_temp = helper.find_nearest_valid_temp(fws_liquid_temp)
    print("nearest_temp liquid cooling", nearest_temp)
    unit_price = constants.VERTIV1_MW_PRICE[nearest_temp]
    if liquid_cooling_type == "Dry Cooler":
        cost = (constants.EQUIPMENT_COSTS["Vertiv DDNT150A272"]["unit_price"] + constants.EQUIPMENT_COSTS["Vertiv DDNT150A272"]["installation_cost"] + constants.EQUIPMENT_COSTS["Vertiv DDNT150A272"]["piping_cost"] + constants.EQUIPMENT_COSTS["Vertiv DDNT150A272"]["startup_cost"]) * no_of_dry_cooler_redundant

    elif liquid_cooling_type == "Chiller":
        cost = (unit_price + constants.EQUIPMENT_COSTS["Vertiv 1MW"]["installation_cost"] + constants.EQUIPMENT_COSTS["Vertiv 1MW"]["piping_cost"] + constants.EQUIPMENT_COSTS["Vertiv 1MW"]["startup_cost"]) * no_of_chillers_liquid_cooling_redundant

    else:
        cost = 0

    return cost

def calculate_cost_wrt_percentage(bms_total_cost, cm_bim_total_cost, fire_fighting_total, percentage):
    return (bms_total_cost + cm_bim_total_cost + fire_fighting_total) * percentage


# Calculate total capex calculation
def calculate_total_common_capex(bms_total_cost, cm_bim_total_cost, fire_fighting_total, design_planning, marginal_expenses, security):
    return (bms_total_cost + cm_bim_total_cost + fire_fighting_total + design_planning + marginal_expenses + security)

def calculate_total_capex(sum_capex):
    design_planning = sum_capex * 0.15
    marginal_expenses = sum_capex * 0.15
    security = sum_capex * 0.1

    total_capex = sum_capex + design_planning + marginal_expenses + security
    return total_capex