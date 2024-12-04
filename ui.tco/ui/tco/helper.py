from . import data_loader
from . import constants
import math

chillers_data = data_loader.load_chillers_data()

def find_nearest_valid_temp(input_temp):
    """ Returns the nearest lower valid Fws_temp based on input_temp. """
    sorted_keys = sorted(constants.VERTIV1_MW_PRICE.keys())
    for key in reversed(sorted_keys):
        if input_temp >= key:
            return key
    return sorted_keys[0] 

def calculate_chilled_water_temperature_rise(fws_design_temperature_air, dry_bulb):
    """Calculate chilled water temperature rise based on conditions."""
    try:
        model_filter = "Vertiv 1MW"
        ta = math.ceil(dry_bulb)
        # Filter for rows where TWOUT matches fws_design_temperature and TA matches the ceiling of dry_bulb
        target_row = chillers_data[
            (chillers_data['Model'] == model_filter) &
            (chillers_data['TWOUT'] == fws_design_temperature_air) &
            (chillers_data['TA'] == ta)
        ]

        if not target_row.empty:
            # Retrieve the 'evaporator' value for chilled water temperature rise
            chilled_water_temp_rise = target_row.iloc[0]['Evaporator']
            return chilled_water_temp_rise
        else:
            print("No matching row found in chillers.csv for the specified conditions.")
            return None

    except Exception as e:
        print(f"Error calculating chilled water temperature rise: {e}")
        return None

def calculate_q_per_crah(cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, no_of_crahs_per_pod):
    """Calculate Q per CRAH based on CDU type."""

    if cdu_type == "Liquid to Liquid":
        return air_cooling_capacity_per_pod / no_of_crahs_per_pod
    elif cdu_type == "Liquid to Air":
        return total_power_per_pod / no_of_crahs_per_pod
    return 0  # Return a default value if CDU type is unrecognized

def calculate_chilled_water_flow_rate_per_crah(q_per_crah, chilled_water_temperature_rise):
    """Calculate the chilled water flow rate per CRAH."""
    return (q_per_crah / (chilled_water_temperature_rise * constants.water_rho_cp)) * 60000

def calculate_chilled_water_flow_rate_per_pod(chilled_water_flow_rate_crah, no_of_crahs_per_pod):
    """Calculate the chilled water flow rate per POD."""
    return chilled_water_flow_rate_crah * no_of_crahs_per_pod

def calculate_q_ac_per_pod(cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, no_of_pods):

    """Calculate Q AC per POD based on CDU type."""
    if cdu_type == "Liquid to Liquid":
        return air_cooling_capacity_per_pod
    elif cdu_type == "Liquid to Air":
        return total_power_per_pod
    return 0  # Return a default value if CDU type is unrecognized



def calculate_roots(a, b, c):
    """Calculate and return the roots of the quadratic equation."""
    try:
        # Calculate the discriminant
        discriminant = b**2 - 4 * a * c

        # Check if discriminant is non-negative for real roots
        if discriminant < 0:
            print("No real roots exist.")
            return None, None

        # Calculate the two roots using the quadratic formula
        sqrt_discriminant = math.sqrt(discriminant)
        root1 = (-b + sqrt_discriminant) / (2 * a)
        root2 = (-b - sqrt_discriminant) / (2 * a)

        return root1, root2
    except Exception as e:
        print(f"Error calculating roots: {e}")
        return None, None

def calculate_dp(qsc_coefficients, flowrate):
    """Calculate the differential pressure (dp) based on flowrate."""
    a = qsc_coefficients["a"]
    b = qsc_coefficients["b"]
    c = qsc_coefficients["c"]
    dp = a * (flowrate ** 2) + b * flowrate + c
    return dp

def calculate_no_of_crahs_per_pod(air_cooling_capacity_per_pod):
    """Calculate number of CRAHs based on air cooling capacity and CRAH model data."""
    crah_model_capacity = constants.vendor_data[2]["Net Total Capacity (kW)"]  # Replace with logic to select specific model if needed
    return math.ceil(air_cooling_capacity_per_pod / crah_model_capacity)

def calculate_total_no_of_crahs(air_cooling_capacity_per_pod, num_pods):
    """Calculate number of CRAHs based on air cooling capacity and CRAH model data."""
    crah_model_capacity = constants.vendor_data[2]["Net Total Capacity (kW)"]  # Replace with logic to select specific model if needed
    no_of_crahs_per_pod = math.ceil(air_cooling_capacity_per_pod / crah_model_capacity)
    return no_of_crahs_per_pod * num_pods

def calculate_total_no_of_crahs_redundant(air_cooling_capacity_per_pod, num_pods):
    """Calculate number of CRAHs based on air cooling capacity and CRAH model data."""
    crah_model_capacity = constants.vendor_data[2]["Net Total Capacity (kW)"]  # Replace with logic to select specific model if needed
    no_of_crahs_per_pod_redundant = math.ceil(air_cooling_capacity_per_pod / crah_model_capacity) + 1
    return no_of_crahs_per_pod_redundant * num_pods


def calculate_air_return_temperature(air_supply_temperature, air_temperature_rise_in_rack):
    """Calculate the air return temperature."""
    return air_supply_temperature + air_temperature_rise_in_rack

def calculate_air_temperature_rise_in_rack(air_cooling_capacity_per_pod, required_air_flow_rate_capacity_per_pod):
    """Calculate the air temperature rise in rack."""
    return air_cooling_capacity_per_pod / 1.08 / (required_air_flow_rate_capacity_per_pod * 0.00047194745)

def calculate_belimo_count(rack_counts, num_pods):
    return rack_counts.get("GB200_NVL72", 0) * num_pods
    
def calculate_length_of_pipe(no_of_racks_gb200,num_pods):
    length = ((no_of_racks_gb200 * 1.2) + constants.LIQUID_COOLING_PIPING_PER_POD["Header"]["Loop End Length"] + constants.LIQUID_COOLING_PIPING_PER_POD["Header"]["Margin"] ) * constants.LIQUID_COOLING_PIPING_PER_POD["Header"]["Quantity_Supply_return"]
    return length * num_pods

def calculate_diameter_of_pipe(tcs_liquid_flow_rate_gpm, fluid_piping_data):
    flow_rate_gpm = math.ceil(tcs_liquid_flow_rate_gpm/100) * 100
        # Filter the DataFrame for rows where Flow Rate (GPM) matches
    matching_row = fluid_piping_data[fluid_piping_data['Flow Rate (GPM)'] == flow_rate_gpm]
    
    if not matching_row.empty:
        # Retrieve the Header Size (inch) from the matching row
        pipe_size = matching_row['Pipe size (inch)'].values[0]
    else:
        print("No matching flow rate found.")

    diameter = max(6, pipe_size)
    return diameter

def calculate_length_of_air_cooling_loop(num_pods):
    return ((constants.LIQUID_COOLING_PIPING_PER_POD["Air Cooling Loop"]["Pod to Pod Dist"] * num_pods) + constants.LIQUID_COOLING_PIPING_PER_POD["Air Cooling Loop"]["Loop End Length"] + constants.LIQUID_COOLING_PIPING_PER_POD["Air Cooling Loop"]["Margin"]) * constants.LIQUID_COOLING_PIPING_PER_POD["Air Cooling Loop"]["Quantity_Supply_return"]

def calculate_length_of_liquid_cooling_loop(num_pods):
    return ((constants.LIQUID_COOLING_PIPING_PER_POD["Liquid Cooling Loop"]["Pod to Pod Dist"] * num_pods) + constants.LIQUID_COOLING_PIPING_PER_POD["Liquid Cooling Loop"]["Loop End Length"] + constants.LIQUID_COOLING_PIPING_PER_POD["Liquid Cooling Loop"]["Margin"]) * constants.LIQUID_COOLING_PIPING_PER_POD["Liquid Cooling Loop"]["Quantity_Supply_return"]

def get_price_per_meter_pipe(diamter_of_pipe):
    return constants.PIPE_PRICE_PER_METER.get(diamter_of_pipe, None)

def calculate_cooling_loop_cost(cooling_loop_price_per_meter, length_of_cooling_loop):
    installation = cooling_loop_price_per_meter / 2
    piping = 0.2 * cooling_loop_price_per_meter
    fittings = 0.4
    cost = (cooling_loop_price_per_meter + installation + piping) * (1 + fittings) * length_of_cooling_loop
    return cost


def calculate_piping_cost(length_of_pipe, header_price_per_meter):
    return length_of_pipe * header_price_per_meter * 0.2

def calculate_length_of_pipe_rack_outlet_inlet(no_of_racks):
    quantity_supply_return = constants.LIQUID_COOLING_PIPING_PER_POD["Rack Outlet/Inlet"]["Quantity_Supply_return"]
    rack_to_rack_dist = constants.LIQUID_COOLING_PIPING_PER_POD["Rack Outlet/Inlet"]["Rack to Rack Dist"]
    length = ( rack_to_rack_dist* no_of_racks * quantity_supply_return)
    print("Length" , length)
    return (length)

def calculate_total_pg25(total_volume_pg25_rack_manifold, total_volume_pg25_header, total_volume_pg25_cdu, total_volume_pg_tank):
    total_capacity = total_volume_pg25_rack_manifold + total_volume_pg25_header + total_volume_pg25_cdu + total_volume_pg_tank
    flushing_comissioning = 2.5 * total_capacity
    total_pg25_required = total_capacity + flushing_comissioning
    return total_pg25_required

def get_equipment_capacity_chiller(chillers_data, dry_bulb, fws_air_temp, model):
        # Filter the DataFrame based on the conditions
    nearest_temp = find_nearest_valid_temp(fws_air_temp)
    filtered_data = chillers_data[
        (chillers_data['Model'] == model) &
        (chillers_data['TA'] == dry_bulb) &
        (chillers_data['TWOUT'] == nearest_temp)
    ]
    
    # Check if a matching row is found and retrieve the 'Cooling Capacity' value
    if not filtered_data.empty:
        return filtered_data.iloc[0]['Cooling Capacity']  # Get the first match if there are multiple
    else:
        print("No matching row found.")
        return None
    

def get_electricity_price(climate_data, selected_city):
    selected_city = selected_city.strip()
    city_data = climate_data[climate_data['Station Name'] == selected_city]
    if not city_data.empty:
        electricity_price = float(city_data['Electricity price'].iloc[0])

    return electricity_price

def format_large_number(value):
    """Format the number to display in millions (M) or thousands (K)."""
    if value >= 1e9:
        return f"{value / 1e9:.2f}B"
    elif value >= 1e6:
        return f"{value / 1e6:.2f}M"  # Format in millions
    elif value >= 1e3:
        return f"{value / 1e3:.2f}K"  # Format in thousands
    else:
        return f"{value:.0f}"  # Show the full value for smaller numbers


def calculate_bar_height_capex(value):
    """Calculate bar height based on 5M layers with adjusted increments."""
    base_height = 10
    increment = 10  # 10 pixels per million
    height = base_height + (value / 1e6) * increment
    return height