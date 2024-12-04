import omni.ui as ui
import pandas as pd
from omni.ui import color as cl


RPM1_PERCENT = 1  # Base RPM percentage for calculations
CFM1 = 29081      # PW170 CFM value
HP1_PER_CRAH = 1  # PW170 total power in kW
HOURS_IN_YEAR = 8766  # Total hours in a year
HOURS_IN_MONTH = 730
UNITS_PER_POD_PW170 = 4  # PW170 units per pod
UNITS_PER_POD_XDU1350 = 3  # XDU1350 units per pod
# POWER_PER_POD_PW170 = 1
# POWER_PER_POD_XDU1350 = 4.3

# capex unit price of components
BELIMO_PRICE = 2680
DN20_VALVE_PRICE = 1392
ABOVE_RACKS_PIPING_PRICE = 1835
INSULATION_PRICE = 40
LD2100_CONTROLLER_PRICE = 1730
LD2100_INSTALLATION_PRICE = 173
PG25_PRICE = 21

BMS_UNIT_PRICE = 180000
CM_BIM_UNIT_PRICE = 150000 
FIRE_FIGHTING_PRICE = 4280

#OPEX
ELECTRICITY_PRICE_ANNUAL_INCREASE = 0.03
RENT_ANNUAL_INCREASE = 0.03
MAINTENANCE_ANNUAL_INCREASE = 0.05

NUMBER_OF_TEST_PER_YEAR = 4
FLUSHING_COST_PER_GALLON = 0.15
MONITORING_SAMPLING_COST_PER_TEST = 1000
RENT_KW_MONTH = 170

CAPEX_COST_PERCENTAGES = {
    "Air Cooling - AC Chiller": 0.06,
    "Air Cooling - LC Chiller": 0.07,
    "Air Cooling - Cooling Tower": 0.06,
    "Air Cooling - Pumps": 0.04,
    "Liquid Cooling - AC Chiller": 0.06,
    "Liquid Cooling - LC Chiller": 0.07,
    "Liquid Cooling - Cooling Tower": 0.06,
    "Liquid Cooling - Dry Cooler": 0.05,
    "Liquid Cooling - Pumps": 0.04,
}

# Cooling equipment configuration
VERTIV1_MW_PRICE = {
    10: 545436.00,
    15: 457941.70,
    20: 428930.26,
    25: 356354.79,
    35: 334224.52
}

EQUIPMENT_COSTS = {
    "Vertiv 1MW": {
        "unit_price": 485000.00,
        "installation_cost": 150000.00,
        "piping_cost": 159000.00,
        "startup_cost": 4000.00
    },
    "Vertiv DDNT150A272": {
        "unit_price": 100000.00,
        "installation_cost": 30000.00,
        "piping_cost": 159000.00,
        "startup_cost": 4000.00
    }
}
#Fluid-piping constants

LIQUID_COOLING_PIPING_PER_POD = {
    "Header" : {
        "Rack to Rack Dist" : 1.2,
        "Loop End Length" : 6,
        "Quantity_Supply_return" : 2,
        "No of racks" : 8,
        "Margin" : 6
    },
    "Rack Outlet/Inlet" : {
        "Diameter" : 2,
        "Rack to Rack Dist" : 1,
        "Loop End Length" : None,
        "Quantity_Supply_return" : 2,
        "No of racks" : 8,
        "Margin" : None,
    },
    "Air Cooling Loop" : {
        "Pod to Pod Dist" : 10,
        "Loop End Length" : 25,
        "Quantity_Supply_return" : 2,
        "No of racks" : 8,
        "Margin" : 60
    },
    "Liquid Cooling Loop" : {
        "Pod to Pod Dist" : 10,
        "Loop End Length" : 25,
        "Quantity_Supply_return" : 2,
        "No of racks" : 8,
        "Margin" : 60
    },
}

# constants.py

PIPE_PRICE_PER_METER = {
    1: 25,
    1.5: 30,
    2: 35,
    2.5: 40,
    3: 50,
    4: 60,
    5: 70,
    6: 80,
    8: 100,
    10: 120,
    12: 150,
    14: 200,
    16: 220,
    18: 230,
    20: 250,
    24: 300
}

# capex unit price of Piping

#capex PG25
LIQUID_CAPACITY_XDU1350 = 29


PERCENTAGE={
    "Lighting" : 0.02,
    "UPS IT Loss" : 0.05 ,
    "UPS Mechanical Loss" : 0.05 ,
    "HVAC" : 0.01
}

POWER_PER_POD = {
    "PW170" : 1,
    "XDU1350" : 4.3
}

vendor_data = [
{
    "Vendor": "Vertiv",
    "CDU Model": "AHU FA069HC",
    "Net Total Capacity (kW)": 252.4,
    "Inlet Water Temperature (°C)": 18,
    "Outlet Water Temperature (°C)": 25,
    "Primary Max Flow Rate (LPM)": 548.4,
    "Air CFM": 40600,
    "Total Power (kW)": 15,
    "Price ($)": None  # Add price here if needed
},
{
    "Vendor": "Vertiv",
    "CDU Model": "AHU FA096HC",
    "Net Total Capacity (kW)": 351.7,
    "Inlet Water Temperature (°C)": 18,
    "Outlet Water Temperature (°C)": 25,
    "Primary Max Flow Rate (LPM)": 761.4,
    "Air CFM": 56800,
    "Total Power (kW)": 19.5,
    "Price ($)": None  # Add price here if needed
},
{
    "Vendor": "Vertiv",
    "CDU Model": "PW170",
    "Net Total Capacity (kW)": 233,
    "Inlet Water Temperature (°C)": 18,
    "Outlet Water Temperature (°C)": 38,
    "Primary Max Flow Rate (LPM)": 175,
    "Air CFM": 29081,
    "Total Power (kW)": 1,
    "Price ($)": 74000
}
]
water_rho_cp = 4193
# Quadratic System Curve coefficients based on pod type and CDUs
QSC_COEFFICIENTS = {
    "576 GPU DGX GB200 Super Pod": {
        1: {"a": 0.00007100, "b": 0.02422900, "c": -0.39533800},
        2: {"a": 0.0028300, "b": 0.04845800, "c": -0.39533800}
    },
    "1152 GPU DGX GB200 Super Pod": {
        3: {"a": 0.00018600, "b": 0.04140900, "c": -0.55493400},
        4: {"a": 0.00033000, "b": 0.05521200, "c": -0.55493400}
    }
}
HP1 = 13.7  # Constant power (kW) for HP1
rpm1 = 1  # Treat rpm1 as a constant
    # XDU 1350 PQ curve constants
XDU_PQC = {
    "a": -0.000234,
    "b": 0.092063,
    "c": 476.456770
}

PRIMARY_DELTA_TEMP = 10  # in °C
MAX_SECONDARY_FLOW_RATE_CDU = 1200  # in LPM
NOMINAL_COOLING_CAPACITIES = {
    "XDU1350": 1367,
    "MCDU60": 1200,
    "MCDU50": 1725,
    "XDU600": 600,
    "XDU070": 55,
    "MHDU5900": 1368,
    "MHDU5910": 1200
}

CDU_L2L_DATA = {
    "Vertiv": {
        "XDU1350": {
            "nominal_cooling_capacity_4adt": 1367,
            "nominal_cooling_capacity_8adt": 2912,
            "max_power_consumption": 13.7,
            "primary_max_flow_rate": None,  # Data missing
            "secondary_max_flow_rate": 1200,
            "price": 150000
        },
        "XDU600": {
            "nominal_cooling_capacity_4adt": 600,
            "nominal_cooling_capacity_8adt": None,  # Data missing
            "max_power_consumption": None,  # Data missing
            "primary_max_flow_rate": None,  # Data missing
            "secondary_max_flow_rate": None,  # Data missing
            "price": None  # Data missing
        }
    },
    "Motivair": {
        "MCDU60": {
            "nominal_cooling_capacity_4adt": 1200,
            "nominal_cooling_capacity_8adt": None,  # Data missing
            "max_power_consumption": None,  # Data missing
            "primary_max_flow_rate": 2587,
            "secondary_max_flow_rate": 2007,
            "price": 184000
        },
        "MCDU50": {
            "nominal_cooling_capacity_4adt": 1725,
            "nominal_cooling_capacity_8adt": None,  # Data missing
            "max_power_consumption": None,  # Data missing
            "primary_max_flow_rate": 1590,
            "secondary_max_flow_rate": 1287,
            "price": 130000
        },
        "MCDU30": {
            "nominal_cooling_capacity_4adt": None,  # Data missing
            "nominal_cooling_capacity_8adt": None,  # Data missing
            "max_power_consumption": None,  # Data missing
            "primary_max_flow_rate": None,  # Data missing
            "secondary_max_flow_rate": None,  # Data missing
            "price": 80000
        }
    }
}

# Constant for Rho * C Secondary Flow in kJ/(C * m^3)
RHO_C_SECONDARY_FLOW = 4120  # in kJ/(C * m^3)

# Constants for fixed air flow rates (in CFM) for Management and Network racks
AIR_FLOW_RATE_MANAGEMENT_RACK = 3900
AIR_FLOW_RATE_NETWORK_RACK = 3900

POWER_PER_RACK = {
    "GB200_NVL72": 132,
    "Management": 30,
    "Networking": 30
}

# Air cooling capacity per rack in kW
AIR_COOLING_CAPACITY_PER_RACK = {
    "GB200_NVL72": 17.16,
    "Management": 30,
    "Networking": 30
}

# Rack configuration per pod type
POD_RACK_COUNTS = {
    "288 GPU DGX GB200 Super Pod": {"GB200_NVL72": 4, "Management": 2, "Networking": 3},
    "576 GPU DGX GB200 Super Pod": {"GB200_NVL72": 8, "Management": 4, "Networking": 6},
    "1152 GPU DGX GB200 Super Pod": {"GB200_NVL72": 16, "Management": 8, "Networking": 12}
}


temperature_ranges = {
            "A1": list(range(15, 33)),
            "A2": list(range(10, 36)),
            "A3": list(range(5, 41)),
            "A4": list(range(5, 46)),
            "B": list(range(5, 37)),
            "C": list(range(5, 42)),
            "H1": list(range(15, 27)),
            "Default": list(range(15, 34))
        }

liquid_cooling_temp_ranges = {
            "W17": list(range(2, 18)),
            "W27": list(range(2, 28)),
            "W32": list(range(2, 33)),
            "W40": list(range(2, 41)),
            "W45": list(range(2, 46)),
            "W+": list(range(2, 50)),
            "Default": list(range(15, 34))
        }

liquid_cooling_options = ["Select Data Center Liquid Cooling option","W17", "W27", "W32", "W40", "W45", "W+"]

# Define configuration options
it_product_options = ["GB200_NVL72", "GB200_NVL36"]
pod_options = ["288 GPU DGX GB200 Super Pod", "576 GPU DGX GB200 Super Pod", "1152 GPU DGX GB200 Super Pod"]
data_center_class_options = ["Select Data Center Air Cooling option","A1", "A2", "A3", "A4", "B", "C", "H1"]
cdu_options = ["Liquid to Liquid", "Liquid to Air"]
chiller_options = ["Vertiv 1MW", "Schneider XRAC4812", "DAIKIN AIR COOLED  SCREW C20"]
dryer_options = ["Vertiv DDNT150A272", "Schneider DSAF1200"]


STYLES = {
            "main_container": {
                "padding": 10,
                "spacing": 5,
                "background_color": cl("#2E2E2E"),  # Dark gray background
            },
            "section_frame": {
                "border_radius": 5,
                "border_width": 2,
                "border_color": cl("#444444"),  # Slightly lighter gray for subtle separation
                "margin": 5,
                "padding": 5,
                "background_color": cl("#333333"),  # Darker gray for contrast within sections
            },
            "title": {
                "font_size": 32,
                "font_weight": "bold",
                "color": cl("#FFFFFF"),  # White for primary headers
                "alignment": ui.Alignment.CENTER,
            },
            "section_title": {
                "font_size": 20,
                "font_weight": "bold",
                "color": cl("#FFFFFF"),  # White for readability
                "margin": 15,
            },
            "label": {
                "font_size": 18,
                "color": cl("#FFFFFF"),  # Light gray for better readability on dark background
            },
            "value_label": {
                "font_size": 18,
                "color": cl("#76B900"),  # NVIDIA green for highlighted values
                "font_weight": "bold",
            },
            "dynamic_value": {
                "font_size": 18,
                "color": cl("#1ABC9C"),  # Teal for updated values
                "font_weight": "bold",
            },
            "highlight_label": {
                "font_size": 18,
                "color": cl("#FFFFFF"),  # White for important labels
                "font_weight": "bold",
                "alignment": ui.Alignment.LEFT,
                "margin_top": 15,
            },
            "highlight_value_label": {
                "font_size": 20,
                "color": cl("#FFFFFF"),  # White for important labels
                "font_weight": "bold",
                "alignment": ui.Alignment.LEFT,
                "margin_top": 15,
            },
            "combo_box": {
                "font_size": 16,
                "color": cl("#FFFFFF"),  # Light gray for dropdown text
                "background_color": cl("#2E2E2E"),  # Dark gray dropdown background
            },
            "input_container": {
                "margin": 10,
                "spacing": 10,
                "background_color": cl("#3B3B3B"),  # Darker shade for input backgrounds
            },
            "separator": {
                "margin_top": 5,
                "margin_bottom": 5,
                "color": cl("#555555"),  # Subtle gray for separator
            },
            "footer": {
                "font_size": 12,
                "color": cl("#888888"),  # Consistent gray for footer text
                "alignment": ui.Alignment.CENTER,
                "margin_top": 20,
            },
            "axis_label": {
                "font_size": 12,
                "color": cl("#CCCCCC"),  # Light gray for readability
                "alignment": ui.Alignment.RIGHT,
                "padding": 2,
            },
            "checkbox": {
                "background_color": "#444",
                "border_color": "#fff",
                "checked_color": "#0f0",  # Green tick mark
            },

        }



city_name_map = {
        "DALLAS LOVE FIELD": "Dallas",
        "CHICAGO O'HARE": "Chicago",
        "LONDON STANSTED": "London",
        "FRANKFURT AM MAIN": "Frankfurt",
        "WASHINGTON DULLES": "Washington",
        "LESSBURG": "Lessburg",
        "COLUMBUS RICKENBACKER": "Columbus",
        "TORONTO BUTTONVILLE": "Toronto",
        "SYDNEY RICHMOND": "Sydney",
        "ATLANTA HARTSFIELD-JACKSON": "Atlanta",
        "MANASSAS": "Manassas",
        "PARIS MONTSOURIS": "Paris",
        "AMSTERDAM AP SCHIPHOL": "Amsterdam",
        "PHOENIX SKY HARBOR": "Phoenix",
        "TOKYO": "Tokyo",
        "JAKARTA OBSERVATORY": "Jakarta",
        "DUBLIN AP": "Dublin",
        "HONG KONG INTL": "Hong Kong",
        "LOS ANGELES USC": "Los Angeles",
        "SAN JOSE INTL": "San Jose",
        "NEW YORK LA GUARDIA": "New York",
        "SINGAPORE PAYA LEBAR": "Singapore",
        "SEATTLE RENTON": "Seattle",
        "SAO PAULO CONGONHAS": "Sao Paulo",
        "MONTREAL MCTAVISH": "Montreal",
        "MELBOURNE AP": "Melbourne",
        "DENVER INTL": "Denver",
        "SANTIAGO DEL ESTERO": "Santiago",
        "MILANO LINATE": "Milan",
        "MIAMI EXECUTIVE": "Miami",
        "HOUSTON DUNN": "Houston",
        "MUMBAI SHIVAJI INTL": "Mumbai",
        "MINNEAPOLIS-ST PAUL": "Minneapolis",
        "ISTANBUL ATATURK": "Istanbul",
        "MOSKOVA DOMODEDOVO": "Moscow",
        "MADRID TORREJON AB": "Madrid",
        "SEOUL OBSERVATORY": "Seoul"
    }