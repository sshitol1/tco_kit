# flow_calculations.py

import math
from . import constants

def calculate_secondary_return_temp(rack_power_liquid_cooled, liquid_flow_rate_per_rack, tcs_liquid_value, rho_c_secondary_flow):
    """Calculate the Secondary Return Temperature (°C) for Liquid Cooling."""
    try:
        if liquid_flow_rate_per_rack == 0:
            raise ValueError("Liquid flow rate per rack cannot be zero for this calculation.")

        temp_increase = (rack_power_liquid_cooled / (liquid_flow_rate_per_rack / 60000)) / rho_c_secondary_flow
        secondary_return_temp = temp_increase + tcs_liquid_value
        return secondary_return_temp
    except Exception as e:
        print(f"Error calculating Secondary Return Temp (°C) LC: {e}")
        return None


def calculate_secondary_flowrate_per_cdu(required_liquid_flow_rate, total_cdus):
    return required_liquid_flow_rate / total_cdus


def calculate_q_per_cdu(liquid_cooling_capacity, total_cdus):
    return liquid_cooling_capacity / total_cdus


def calculate_primary_flow_rate_per_cdu(q_per_cdu):
    """Primary Flow Rate per CDU (LPM)."""
    return ((q_per_cdu / constants.PRIMARY_DELTA_TEMP) / 4170) * 60000


def calculate_q_max_cdu(required_liquid_flow_rate, total_cdus, secondary_return_temp, primary_supply_temp, liquid_cooling_capacity, rho_c_secondary_flow, primary_delta_temp):
    """Calculate the maximum Q (heat transfer rate) for a CDU."""
    q_per_cdu = calculate_q_per_cdu(liquid_cooling_capacity, total_cdus)
    secondary_flow_rate_per_cdu = calculate_secondary_flowrate_per_cdu(required_liquid_flow_rate, total_cdus)
    primary_flow_rate_per_cdu = calculate_primary_flow_rate_per_cdu(q_per_cdu)

    min_flow_rate = min(secondary_flow_rate_per_cdu, primary_flow_rate_per_cdu)
    delta_temp = secondary_return_temp - primary_supply_temp

    return (rho_c_secondary_flow * min_flow_rate / 60000) * delta_temp


def calculate_primary_flow_rate_per_pod(primary_flow_rate_per_cdu, total_cdus):
    return primary_flow_rate_per_cdu * total_cdus


def calculate_air_flow_rate_per_kw(air_supply_temp):
    """Calculate required air flow rate per kW (CFM) based on the air supply temperature."""
    return (
        0.0054667 * (air_supply_temp ** 3) -
        0.34 * (air_supply_temp ** 2) +
        10.263333 * air_supply_temp -
        13
    )


def calculate_air_flow_rate_per_rack(pod_type, air_supply_temp):
    # Retrieve total air cooling capacity per rack for the selected pod type
    air_cooling_capacity_per_rack = constants.AIR_COOLING_CAPACITY_PER_RACK["GB200_NVL72"]

    # Calculate air flow rate per kW
    air_flow_rate_per_kw = calculate_air_flow_rate_per_kw(air_supply_temp)

    # Calculate air flow rate per rack
    air_flow_rate_per_rack = air_flow_rate_per_kw * (air_cooling_capacity_per_rack / 1)  # in kW/rack
    return air_flow_rate_per_rack

def calculate_liquid_flow_rate_per_rack(tcs_liquid_temp):
    """Calculate required liquid flow rate per rack."""
    return (-0.0007656 * (tcs_liquid_temp ** 4) +
            0.11484 * (tcs_liquid_temp ** 3) -
            6.18222 * (tcs_liquid_temp ** 2) +
            145.2726 * tcs_liquid_temp -
            1205.82)
