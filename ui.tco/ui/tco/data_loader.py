# data_loader.py
import pandas as pd
from collections import OrderedDict

# File paths defined directly within this file
CHILLERS_FILE = r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Chillers.csv"
DRYER_FILE = r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Dryer.csv"
TCO_FILE = r"C:\Users\sshitol1\ui.tco\ui.tco\docs\TCO_new.csv"
FLUID_PIPING = r"C:\Users\sshitol1\ui.tco\ui.tco\docs\fluid_piping.csv"

def load_chillers_data():
    """Load the chillers data CSV and return a DataFrame."""
    try:
        chillers_data = pd.read_csv(CHILLERS_FILE)
        required_columns = [
            'Model', 'TWOUT', 'TA', 'Cooling Capacity',
            'Power Input (kW)', 'Fluid Flow rate (l/s)',
            'Fluid Pressure Drop (kPa)', 'Evaporator'
        ]
        return chillers_data[required_columns]
    except Exception as e:
        print(f"Error loading chillers data: {e}")
        return None

def load_dryer_data():
    """Load the dryer data CSV and return a DataFrame."""
    try:
        dryer_data = pd.read_csv(DRYER_FILE)
        required_columns = [
            'Model', 'TWOUT', 'TA', 'Cooling Capacity',
            'Power Input (kW)', 'Fluid Flow rate (l/s)',
            'Fluid Pressure Drop (kPa)', 'dT'
        ]
        return dryer_data[required_columns]
    except Exception as e:
        print(f"Error loading dryer data: {e}")
        return None

def load_city_data():
    """Load climate data for different cities and store in a dictionary."""
    city_data =OrderedDict(sorted({
            "DALLAS LOVE FIELD": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Dallas_dry_bulb.csv"),
            "CHICAGO O'HARE": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Chicago_dry_bulb.csv"),
            "LONDON STANSTED": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\London_dry_bulb.csv"),
            "FRANKFURT AM MAIN": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Frankfurt_dry_bulb.csv"),
            "WASHINGTON DULLES": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Washington_dry_bulb.csv"),
            "LESSBURG": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Lessburg_dry_bulb.csv"),
            "COLUMBUS RICKENBACKER": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Columbus_dry_bulb.csv"),
            "TORONTO BUTTONVILLE": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Toronto_dry_bulb.csv"),
            "SYDNEY RICHMOND": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Sydney_dry_bulb.csv"),
            "ATLANTA HARTSFIELD-JACKSON": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Atlanta_dry_bulb.csv"),
            "MANASSAS": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Manassas_dry_bulb.csv"),
            "PARIS MONTSOURIS": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Paris_dry_bulb.csv"),
            "AMSTERDAM AP SCHIPHOL": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Amsterdam_dry_bulb.csv"),
            "PHOENIX SKY HARBOR": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Phoenix_dry_bulb.csv"),
            "TOKYO": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Tokyo_dry_bulb.csv"),
            "JAKARTA OBSERVATORY": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Jakarta_dry_bulb.csv"),
            "DUBLIN AP": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Dublin_dry_bulb.csv"),
            "HONG KONG INTL": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\HongKong_dry_bulb.csv"),
            "LOS ANGELES USC": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\LosAngeles_dry_bulb.csv"),
            "SAN JOSE INTL": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\SanJose_dry_bulb.csv"),
            "NEW YORK LA GUARDIA": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\NewYork_dry_bulb.csv"),
            "SINGAPORE PAYA LEBAR": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Singapore_dry_bulb.csv"),
            "SEATTLE RENTON": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Seattle_dry_bulb.csv"),
            "SAO PAULO CONGONHAS": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\SaoPaulo_dry_bulb.csv"),
            "MONTREAL MCTAVISH": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Montreal_dry_bulb.csv"),
            "MELBOURNE AP": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Melbourne_dry_bulb.csv"),
            "DENVER INTL": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Denver_dry_bulb.csv"),
            "SANTIAGO DEL ESTERO": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Santiago_dry_bulb.csv"),
            "MILANO LINATE": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Milano_dry_bulb.csv"),
            "MIAMI EXECUTIVE": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Miami_dry_bulb.csv"),
            "HOUSTON DUNN": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Houston_dry_bulb.csv"),
            "MUMBAI SHIVAJI INTL": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Mumbai_dry_bulb.csv"),
            "MINNEAPOLIS-ST PAUL": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Minneapolis_dry_bulb.csv"),
            "ISTANBUL ATATURK": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Istanbul_dry_bulb.csv"),
            "MOSKOVA DOMODEDOVO": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Moskova_dry_bulb.csv"),
            "MADRID TORREJON AB": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Madrid_dry_bulb.csv"),
            # "ZURICH AP": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Zurich_dry_bulb.csv"),
            "SEOUL OBSERVATORY": pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\Seoul_dry_bulb.csv")
    }.items(), key=lambda x: x[0]))
    climate_data = pd.read_csv(r"C:\Users\sshitol1\ui.tco\ui.tco\docs\TCO_new.csv")
    # Set unique cities for ComboBox
    unique_cities = list(city_data.keys())

    return city_data, climate_data, unique_cities

def load_fluid_piping_data():
    fluid_piping_data = pd.read_csv(FLUID_PIPING)
    return fluid_piping_data