from . import constants


def calculate_liquid_cooling_capacity(rack_type):
    # Calculate liquid cooling capacity as the difference between power per rack and air cooling per rack
    liquid_cooling_capacity = constants.POWER_PER_RACK[rack_type] - constants.AIR_COOLING_CAPACITY_PER_RACK[rack_type]
    return liquid_cooling_capacity

def calculate_total_air_cooling_capacity(pod_type):
    rack_counts = constants.POD_RACK_COUNTS.get(pod_type, {})
    total_air_cooling = sum(constants.AIR_COOLING_CAPACITY_PER_RACK[rack] * count for rack, count in rack_counts.items())
    return total_air_cooling

def calculate_total_liquid_cooling_capacity(pod_type):
    rack_counts = constants.POD_RACK_COUNTS.get(pod_type, {})
    liquid_cooling_capacity = sum(calculate_liquid_cooling_capacity(rack) * count for rack, count in rack_counts.items())
    return liquid_cooling_capacity

def calculate_power_per_pod(pod_type):
    # Retrieve rack breakdown for the selected pod type
    rack_counts = constants.POD_RACK_COUNTS.get(pod_type, {})

    # Calculate the total power for this pod type
    total_power = sum(constants.POWER_PER_RACK[rack] * count for rack, count in rack_counts.items())
    return total_power

def calculate_rack_power_liquid_cooled(tcs_liquid_value):
# """
# Calculate the Rack Power for Liquid Cooling (kW) based on TCS Liquid Temperature.
# Formula: Rack Power _Liquid Cooled (kW) = (44025 / (56.6 - TCS_liquid))^(0.576)
# """
    try:
        rack_power_liquid_cooled = (44025 / (56.6 - tcs_liquid_value)) ** 0.576
        return rack_power_liquid_cooled
    except ZeroDivisionError:
        print("Error: TCS Liquid temperature is too close to 56.6, causing division by zero.")
        return None
    except Exception as e:
        print(f"Error calculating Rack Power _Liquid Cooled: {e}")
        return None