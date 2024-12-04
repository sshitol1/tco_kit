import omni.ext
import omni.ui as ui
import pandas as pd
from omni.ui import color as cl
import math
import matplotlib.pyplot as plt
from omni.kit.window.file_exporter import get_file_exporter
from reportlab.lib.colors import Color, HexColor, CMYKColor
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.lib.colors import skyblue, black, palegreen, lavender, lightgoldenrodyellow, beige, paleturquoise
from reportlab.lib import colors
import os
import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from typing import List
from PIL import Image as PILImage
from omni.ui import Image
from omni.ui import ImageWithProvider, ByteImageProvider
import matplotlib.figure
from matplotlib.ticker import ScalarFormatter
import tempfile
from io import BytesIO
from omni.gpu_foundation_factory import TextureFormat
from omni.ui import DockPosition, DockPolicy
from . import flow_calculations
from . import power_calculations
from . import monthly_calculation
from . import constants
from . import data_loader
from . import cooling_capacities
from . import helper
from . import capex_calculations
from . import opex_calculations


class MyExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        data_loader.load_city_data()
        self.city_data, self.climate_data, self.unique_cities = data_loader.load_city_data()
        self.chillers_data = data_loader.load_chillers_data()
        self.dryer_data = data_loader.load_dryer_data()
        self.fluid_piping = data_loader.load_fluid_piping_data()
        print("My Extension has started")
        self._window = ui.Window("Data Center Configuration", width=800, height=800)
        print(dir(ui.DockPosition))
        print(dir(ui.DockPolicy))

        self.fws_design_temperature_air = None
        available_colors = [name for name in dir(colors) if not name.startswith("_")]
        print("Available Colors:")
        for color in available_colors:
            print(color)


        self.temperature_ranges = constants.temperature_ranges

        # Temperature ranges for liquid cooling options
        self.liquid_cooling_temp_ranges = constants.liquid_cooling_temp_ranges

        self.liquid_cooling_options = constants.liquid_cooling_options
        self.dry_bulb = 0

        # Define configuration options
        self.it_product_options = constants.it_product_options
        self.pod_options = constants.pod_options
        self.data_center_class_options = constants.data_center_class_options
        self.cdu_options = constants.cdu_options
        self.chiller_options = constants.chiller_options
        self.dryer_options = constants.dryer_options

        # Define options for ComboBoxes

        self.air_supply_options = [str(x) for x in range(15, 33)]
        self.tcs_liquid_options = [str(x) for x in range(17, 46)]
        self.fws_air_options = [str(x) for x in range(5,46)]
        self.fws_liquid_options = [str(x) for x in range(5,46)]
        self.current_cdu_type = self.cdu_options[0]
        self.liquid_cooling_type = None
        self.liquid_cooling_type_secondary = None

        # Flags to control PUE chart display
        self.fws_design_temperature_air = None
        self.fws_design_temperature_liquid = None
        self.should_display_pue_chart = False
        self.should_display_capex_chart = False

        self._pue_chart_window = ui.Window("PUE Chart", width=600, height=400, visible=False)
        self.pue_chart_container = self._pue_chart_window.frame

        self._capex_chart_window = ui.Window("CAPEX Chart", width=750, height=800, visible = False)
        self.capex_chart_container = self._capex_chart_window.frame

        self._capex_opex_chart_window = ui.Window("CAPEX OPEX Chart", width=600, height=1000, visible = False)
        self.capexopex_chart_container = self._capex_opex_chart_window.frame

        self._opex_chart_window = ui.Window("OPEX Chart", width=750, height=700, visible = False)
        self.opex_chart_container = self._opex_chart_window.frame

        self.STYLES = constants.STYLES

        self.setup_primary_ui()

    def setup_primary_ui(self):

        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(style=self.STYLES["main_container"]):
                    try:

                        # Header Section
                        ui.Label("Data Center Configuration", style=self.STYLES["title"])
                        ui.Spacer(height=20)

                        # Location Section
                        with ui.CollapsableFrame("Location Information", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):
                                with ui.HStack(height=30):
                                    ui.Label("Select City:", width=100, style=self.STYLES["label"])
                                    self.city_menu = ui.ComboBox(0, *self.unique_cities, style = self.STYLES["combo_box"])
                                self.country_label = ui.Label("Country: ", style=self.STYLES["label"])
                                self.state_label = ui.Label("State: ", style=self.STYLES["label"])

                        # Climate Information Section
                        with ui.CollapsableFrame("Climate Information", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):
                                self.dry_bulb_label = ui.Label("Dry Bulb: ", style=self.STYLES["label"])
                                self.wet_bulb_label = ui.Label("Wet Bulb: ", style=self.STYLES["label"])
                                self.dew_point_label = ui.Label("Dew Point: ", style=self.STYLES["label"])
                                self.humidity_ratio_label = ui.Label("Humidity Ratio: ", style=self.STYLES["label"])

                        # IT Product Configuration Section
                        with ui.CollapsableFrame("IT Product Configuration", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):
                                with ui.HStack(height=30):
                                    ui.Label("IT Product:", width=150, style=self.STYLES["label"])
                                    self.it_product_menu = ui.ComboBox(0, *self.it_product_options, style = self.STYLES["combo_box"])

                                with ui.HStack(height=30):
                                    ui.Label("POD:", width=150, style=self.STYLES["label"])
                                    self.pod_menu = ui.ComboBox(0, *self.pod_options, style = self.STYLES["combo_box"])

                                with ui.HStack(height=30):
                                    ui.Label("Number of Pods:", width=150, style=self.STYLES["label"])
                                    self.num_pods_field = ui.StringField(style = self.STYLES["combo_box"])

                        # Data Center Class Section
                        with ui.CollapsableFrame("Data Center Specifications", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):
                                with ui.HStack(height=30):
                                    ui.Label("Data Center Class:", width=260, style=self.STYLES["label"])
                                    self.class_menu = ui.ComboBox(0, *self.data_center_class_options, style = self.STYLES["combo_box"])

                                    # New Liquid Cooling Options
                                with ui.HStack(height=30):
                                    ui.Label("Data Center Class Liquid Cooling:", width=150, style=self.STYLES["label"])
                                    self.liquid_cooling_menu = ui.ComboBox(0, *self.liquid_cooling_options, style = self.STYLES["combo_box"])


                        # Cooling Specification Section
                        with ui.CollapsableFrame("Cooling Specification", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):

                                # TCS container
                                # ComboBox for Air Supply Temperature
                                with ui.HStack(height=30) as self.air_supply_container:
                                    ui.Label("Air Supply Temperature:", width=150, style=self.STYLES["label"])
                                    self.air_supply_menu = ui.ComboBox(0, *self.air_supply_options, style = self.STYLES["combo_box"])  # Use options list

                                # ComboBox for TCS Liquid
                                with ui.HStack(height=30):
                                    ui.Label("TCS Liquid:", width=195, style=self.STYLES["label"])
                                    self.tcs_liquid_menu = ui.ComboBox(0, *self.tcs_liquid_options, style = self.STYLES["combo_box"])  # Use options list


                        # Facility Specification Section
                        with ui.CollapsableFrame(" Facility Specification", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):

                                # Container for fws_air_menu ComboBox
                                with ui.HStack(height=30) as self.fws_air_container:
                                    ui.Label("FWS Design Temp (Air):", width=210, style=self.STYLES["label"])
                                    self.fws_air_menu = ui.ComboBox(0, *self.fws_air_options, style = self.STYLES["combo_box"])  # Initial values
                                    ui.Label("°C", width=30)
                                    self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(self.on_fws_air_temp_changed)

                                # Container for fws_liquid_menu ComboBox
                                with ui.HStack(height=30) as self.fws_liquid_container:
                                    ui.Label("FWS Design Temp (Liquid):", width=150, style=self.STYLES["label"])
                                    self.fws_liquid_menu = ui.ComboBox(0, *self.fws_liquid_options, style = self.STYLES["combo_box"])  # Initial values
                                    ui.Label("°C", width=30)
                                    self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(self.on_fws_liquid_temp_changed)

                                with ui.HStack(height=30):
                                    ui.Label("CDU Type:", width=210, style=self.STYLES["label"])
                                    self.cdu_menu = ui.ComboBox(0, *self.cdu_options,style = self.STYLES["combo_box"])
                                    self.cdu_menu.model.get_item_value_model().add_value_changed_fn(self.on_cdu_type_selected)

                                with ui.HStack(height=30):
                                    ui.Label("Select Chiller:", width=200, style=self.STYLES["label"])
                                    self.chiller_menu = ui.ComboBox(0,*self.chiller_options ,style=self.STYLES["combo_box"])

                                with ui.HStack(height=30):
                                    ui.Label("Select Dry Cooler:", width=200, style=self.STYLES["label"])
                                    self.dryer_menu = ui.ComboBox(0,*self.dryer_options ,style=self.STYLES["combo_box"])

                        with ui.CollapsableFrame("Number of years", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):

                                with ui.HStack(height=30):
                                    ui.Label("Number of Years:", width=150, style=self.STYLES["label"])
                                    self.num_years_field = ui.StringField(style = self.STYLES["combo_box"])
                                # ui.Button("Download Report", clicked_fn=self.save_report)

                         # Chart Toggle Buttons
                        # Chart Toggle Switches with Dynamic Color
                        # Facility Specification Section
                        with ui.CollapsableFrame(" Facility Specification 1", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):

                                # Container for fws_air_menu ComboBox
                                with ui.HStack(height=30) as self.fws_air_container:
                                    ui.Label("FWS Design Temp (Air):", width=210, style=self.STYLES["label"])
                                    self.fws_air_menu_1 = ui.ComboBox(0, *self.fws_air_options, style = self.STYLES["combo_box"])  # Initial values
                                    ui.Label("°C", width=30)

                                # Container for fws_liquid_menu ComboBox
                                with ui.HStack(height=30) as self.fws_liquid_container:
                                    ui.Label("FWS Design Temp (Liquid):", width=150, style=self.STYLES["label"])
                                    self.fws_liquid_menu_1 = ui.ComboBox(0, *self.fws_liquid_options, style = self.STYLES["combo_box"])  # Initial values
                                    ui.Label("°C", width=30)

                                with ui.HStack(height=30):
                                    ui.Label("Select Chiller:", width=200, style=self.STYLES["label"])
                                    self.chiller_menu_1 = ui.ComboBox(0,*self.chiller_options ,style=self.STYLES["combo_box"])

                                with ui.HStack(height=30):
                                    ui.Label("Select Dry Cooler:", width=200, style=self.STYLES["label"])
                                    self.dryer_menu_1 = ui.ComboBox(0,*self.dryer_options ,style=self.STYLES["combo_box"])

                        # Facility Specification Section
                        with ui.CollapsableFrame(" Facility Specification 2", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):

                                # Container for fws_air_menu ComboBox
                                with ui.HStack(height=30) as self.fws_air_container:
                                    ui.Label("FWS Design Temp (Air):", width=210, style=self.STYLES["label"])
                                    self.fws_air_menu_2 = ui.ComboBox(0, *self.fws_air_options, style = self.STYLES["combo_box"])  # Initial values
                                    ui.Label("°C", width=30)

                                # Container for fws_liquid_menu ComboBox
                                with ui.HStack(height=30) as self.fws_liquid_container:
                                    ui.Label("FWS Design Temp (Liquid):", width=150, style=self.STYLES["label"])
                                    self.fws_liquid_menu_2 = ui.ComboBox(0, *self.fws_liquid_options, style = self.STYLES["combo_box"])  # Initial values
                                    ui.Label("°C", width=30)

                                with ui.HStack(height=30):
                                    ui.Label("Select Chiller:", width=200, style=self.STYLES["label"])
                                    self.chiller_menu_2 = ui.ComboBox(0,*self.chiller_options ,style=self.STYLES["combo_box"])

                                with ui.HStack(height=30):
                                    ui.Label("Select Dry Cooler:", width=200, style=self.STYLES["label"])
                                    self.dryer_menu_2 = ui.ComboBox(0,*self.dryer_options ,style=self.STYLES["combo_box"])

                                with ui.HStack(height=30):
                                    ui.Button("Show CAPEX Comparison", clicked_fn=self.show_capex_comparison)

                        with ui.CollapsableFrame("Chart Controls", style=self.STYLES["section_frame"]):
                            with ui.VStack(spacing=5):
                                ui.Label("Toggle Chart Visibility:", style=self.STYLES["label"])

                                # Switch for PUE Chart
                                with ui.HStack():
                                    ui.Label("PUE Chart", width=100, style=constants.STYLES["label"])
                                    self.pue_chart_switch = ui.CheckBox(value=False) # Default color
                                    self.pue_chart_switch.model.add_value_changed_fn(
                                        lambda model: self.toggle_chart(self._pue_chart_window, self.pue_chart_switch, model)
                                    )

                                # Switch for CAPEX Chart
                                with ui.HStack():
                                    ui.Label("CAPEX Chart", width=100, style=constants.STYLES["label"])
                                    self.capex_chart_switch = ui.CheckBox(value=False) # Default color
                                    self.capex_chart_switch.model.add_value_changed_fn(
                                        lambda model: self.toggle_chart(self._capex_chart_window, self.capex_chart_switch, model)
                                    )

                                # Switch for OPEX Chart
                                with ui.HStack():
                                    ui.Label("OPEX Chart", width=100, style=constants.STYLES["label"])
                                    self.opex_chart_switch = ui.CheckBox(value=False,  height=30, width=30)# Default color
                                        # Define a style dictionary with a hex color
                                    # Apply the style to the checkbox
                                    self.opex_chart_switch.model.add_value_changed_fn(
                                        lambda model: self.toggle_chart(self._opex_chart_window, self.opex_chart_switch, model)
                                    )

                        with ui.CollapsableFrame("OPEX calculations", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):
                                self.total_common_opex_label = ui.Label("Total Common OpEx: N/A", style=self.STYLES["highlight_label"])
                                self.total_ac_chiller_opex_label = ui.Label("Total AC Chiller OpEx: N/A", style=self.STYLES["highlight_label"])
                                self.total_ac_water_chiller_opex_label = ui.Label("Total AC Water Chiller OpEx: N/A", style=self.STYLES["highlight_label"])
                                self.total_lc_opex_label = ui.Label("Total LC OpEx: N/A", style=self.STYLES["highlight_label"])
                                self.total_lc_water_opex_label = ui.Label("Total LC Water OpEx: N/A", style=self.STYLES["highlight_label"])

                         # Facility Equipment Options Section
                        with ui.CollapsableFrame("Power Consumption", style=self.STYLES["section_frame"]):
                            with ui.VStack(style=self.STYLES["input_container"]):
                                self.common_power_label = ui.Label("Common Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.air_cooling_air_cooled_label = ui.Label("Air Cooling - Air Cooled Chiller (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.liquid_cooling_air_cooled_label = ui.Label("Liquid Cooling - Air Cooled Chiller (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.total_pue_label = ui.Label("Annual PUE: N/A", style=self.STYLES["highlight_label"])

                        with ui.CollapsableFrame("Additional details", style=self.STYLES["section_frame"]):
                            # Add a dropdown for CDU selection (1-4)
                            with ui.VStack():
                                self.total_power_label = ui.Label("Total Power: N/A", style=self.STYLES["highlight_label"])
                                self.total_air_cooling_label = ui.Label("Total Air Cooling Capacity: N/A", style=self.STYLES["highlight_label"])
                                self.total_cdus_label = ui.Label("Total CDUs: N/A", style=self.STYLES["highlight_label"])
                                self.total_liquid_cooling_label = ui.Label("Total Liquid Cooling Capacity: N/A", style=self.STYLES["highlight_label"])
                                self.required_airflow_rate_label = ui.Label("Required Air Flow Rate per Pod (CFM): N/A", style=self.STYLES["highlight_label"])
                                self.required_liquid_flow_rate_label = ui.Label("Required Liquid Flow Rate per Pod (LPM): N/A", style=self.STYLES["highlight_label"])
                                self.pod_flowrate_cdu_label = ui.Label("POD Flow Rate per CDU: N/A LPM", style=self.STYLES["highlight_label"])
                                self.cdu_hp2_label = ui.Label("HP2 (kW): N/A", style=self.STYLES["highlight_label"])
                                self.cdu_hp_per_pod_label = ui.Label("HP per Pod: N/A", style=self.STYLES["highlight_label"])
                                self.air_temperature_rise_label = ui.Label("Air Temperature Rise in Rack: Calculating...", style=self.STYLES["highlight_label"])
                                self.air_return_temperature_label = ui.Label("Air Return Temperature: Calculating...", style=self.STYLES["highlight_label"])
                                self.q_per_crah_label = ui.Label("Q per CRAH: Calculating...", style=self.STYLES["highlight_label"])
                                self.chilled_water_flow_rate_crah_label = ui.Label("Chilled Water Flow Rate per CRAH (LPM): Calculating...", style=self.STYLES["highlight_label"])
                                self.chilled_water_flow_rate_pod_label = ui.Label("Chilled Water Flow Rate per POD (LPM): Calculating...", style=self.STYLES["highlight_label"])
                                self.q_ac_per_pod_label = ui.Label("Q AC per POD (kW): Calculating...", style=self.STYLES["highlight_label"])
                                self.liquid_cooling_label1 = ui.Label("Liquid Cooling Option 1: Not Set", style=self.STYLES["label"])
                                self.liquid_cooling_label2 = ui.Label("Liquid Cooling Option 2: Not Set", style=self.STYLES["label"])
                                self.crah_hp1_label = ui.Label("HP1 PER CRAH: N/A", style=self.STYLES["highlight_label"])
                                self.crah_hp2_label = ui.Label("HP2 per CRAH: N/A", style=self.STYLES["highlight_label"])
                                self.air_chiller_power_consumption_label = ui.Label("Power consumption for Chiller(Air cooling) : N/A", style=self.STYLES["highlight_label"])
                                self.liquid_chiller_power_consumption_label = ui.Label("Power Consumption for Chiller(Liquid Cooling): N/A", style = self.STYLES["highlight_label"])
                                self.total_it_power_label = ui.Label("Total IT Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.pw170_power_label = ui.Label("PW170 Annual Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.xdu1350_power_label = ui.Label("XDU1350 Annual Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.lighting_power_label = ui.Label("Lighting Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.ups_it_loss_label = ui.Label("UPS IT Loss Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.ups_mech_loss_label = ui.Label("UPS Mechanical Loss Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.hvac_power_label = ui.Label("HVAC Power Consumption (kWh): N/A", style=self.STYLES["highlight_label"])
                                self.total_common_capex_label = ui.Label("Total Common CAPEX: $0", style=self.STYLES["highlight_label"])
                                self.total_ac_air_cooled_chiller_capex_label = ui.Label("Total AC Air Cooled Chiller CAPEX: $0", style=self.STYLES["highlight_label"])
                                self.total_ac_water_cooled_chiller_capex_label = ui.Label("Total AC Water Cooled Chiller CAPEX: $0", style=self.STYLES["highlight_label"])
                                self.total_lc_air_cooled_chiller_capex_label = ui.Label("Total LC Air Cooled Chiller CAPEX: $0", style=self.STYLES["highlight_label"])
                                self.total_lc_water_cooled_chiller_capex_label = ui.Label("Total LC Water Cooled Chiller CAPEX: $0", style=self.STYLES["highlight_label"])

                            # Initialize calculations based on default settings
                                    # Initial calculation and UI update
                                self.update_calculations()
                                self.update_flow_rates()

                                    # CRAH Labels
                                self.crah_labels = []
                                self.crah_label_vertiv_pw170 = ui.Label("Number of CRAHs for Vertiv PW170: Calculating...", style=self.STYLES["highlight_label"])


                        # Footer
                        ui.Label(
                            "💡 Select different options to see updated climate information",
                            style=constants.STYLES["footer"]
                        )

                        # Event handlers
                        self.class_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_air_supply_temperature_range()
                        )
                        self.city_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_climate_info(self.unique_cities[model.as_int])
                        )
                        self.city_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_calculations())

                        self.city_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.calculate_monthly_power_consumption())

                        self.liquid_cooling_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_air_supply_temperature_range()
                        )

                        # Event listener to update FWS Design Temp (Liquid) based on TCS Liquid selection
                        self.tcs_liquid_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_fws_design_temperature_liquid(int(self.tcs_liquid_options[model.as_int]))
                        )

                        self.air_supply_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_fws_design_temperature_air(int(self.tcs_liquid_options[model.as_int])))
                        self.pod_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.calculate_total_power())
                        self.num_pods_field.model.add_value_changed_fn(lambda model: self.calculate_total_power())
                        self.num_pods_field.model.add_value_changed_fn(lambda model: self.update_calculations())
                        self.num_pods_field.model.add_value_changed_fn(lambda model: self.calculate_monthly_power_consumption())

                        self.num_years_field.model.add_value_changed_fn(lambda model: self.update_calculations())
                        self.pod_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_cooling_capacities())
                        self.pod_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_calculations())
                        self.pod_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.calculate_monthly_power_consumption())

                        # Attach to event listeners
                        self.tcs_liquid_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_flow_rates())
                        self.tcs_liquid_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_calculations())

                                # Attach event listeners

                        self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_flow_rates())
                        self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_calculations())
                        self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.calculate_monthly_power_consumption())
                        self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_climate_info())

                        self.tcs_liquid_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_flow_rates())

                        self.air_supply_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_calculations())
                        self.num_pods_field.model.add_value_changed_fn(lambda model: self.update_calculations())

                        self.cdu_menu.model.get_item_value_model().add_value_changed_fn(self.on_cdu_type_selected)
                        self.chiller_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_calculations())
                        self.chiller_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.calculate_monthly_power_consumption())
                        
                        self.dryer_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.update_calculations())
                        self.dryer_menu.model.get_item_value_model().add_value_changed_fn(
                            lambda model: self.calculate_monthly_power_consumption())
                        # Initial update
                        if self.unique_cities:
                            self.update_climate_info(self.unique_cities[0])

                    except Exception as e:
                        ui.Label(f"Error loading data: {str(e)}", style=self.STYLES["label"])

    def update_air_supply_temperature_range(self):
        try:
            # Get selected data center class and liquid cooling option
            selected_class = self.data_center_class_options[self.class_menu.model.get_item_value_model().as_int]
            selected_cooling = self.liquid_cooling_options[self.liquid_cooling_menu.model.get_item_value_model().as_int]

            # Determine ranges based on selections
            class_range = self.temperature_ranges.get(selected_class, [])
            cooling_range = self.liquid_cooling_temp_ranges.get(selected_cooling, [])

            # Handle cases based on selection states
            if selected_class == "Select Data Center Air Cooling option" and selected_cooling == "Select Data Center Liquid Cooling option":
                self.air_supply_container.clear()
                with self.air_supply_container:
                    ui.Label("Air Supply Temperature:", width=150, style=self.STYLES["label"])
                    self.air_supply_menu = ui.ComboBox(0, "Select")
                return

            elif selected_class != "Select Data Center Air Cooling option" and selected_cooling == "Select Data Center Liquid Cooling option":
                final_range = class_range

            elif selected_class == "Select Data Center Air Cooling option" and selected_cooling != "Select Data Center Liquid Cooling option":
                final_range = cooling_range

            else:
                min_temp = max(class_range[0], cooling_range[0])
                max_temp = min(class_range[-1], cooling_range[-1])
                final_range = list(range(min_temp, max_temp + 1))

            # Convert to °C format
            final_range_formatted = [f"{temp}" for temp in final_range]

            # Update `self.air_supply_options` with the new range
            self.air_supply_options = final_range_formatted

            # Update ComboBox with the new range
            self.air_supply_container.clear()
            with self.air_supply_container:
                ui.Label("Air Supply Temperature", width=150, style=self.STYLES["label"])
                self.air_supply_menu = ui.ComboBox(0,"Select", *self.air_supply_options, style = self.STYLES["combo_box"])

            # Attach recalculation handler
            self.air_supply_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_calculations())

            print(f"Updated Air Supply Temperature range to: {final_range_formatted}")

        except Exception as e:
            print(f"Error updating Air Supply Temperature range: {str(e)}")

    def on_cdu_type_selected(self, model):
        """Event handler for updating cdu_type based on user selection."""
        try:
            selected_index = model.as_int
            self.current_cdu_type = self.cdu_options[selected_index]  # Update cdu_type with selected value
            self.update_calculations()  # Trigger recalculations if necessary
        except Exception as e:
            print(f"Error selecting CDU Type: {str(e)}")

    def update_climate_info(self, selected_city):
        print(selected_city)
        try:
            selected_city = selected_city.strip()

            city_data = self.climate_data[self.climate_data['Station Name'] == selected_city]
            fws_liquid_temp = self.get_selected_fws_design_liquid_temperature()
            fws_air_temp = self.get_selected_fws_design_air_temperature()
            # no_of_equipments_air = self.get_number_of_equipments_air_cooling()

            if not city_data.empty:
                city_data = city_data.iloc[0]
                self.country_label.text = f"Country: {city_data['Country']}"
                self.state_label.text = f"State: {city_data['Prov State'] if pd.notna(city_data['Prov State']) else 'N/A'}"
                self.dry_bulb_label.text = f"Dry Bulb: {city_data['Dry Bulb Temperature']} °C"
                self.wet_bulb_label.text = f"Wet Bulb: {city_data['Wet Bulb Temperature']} °C"
                self.dew_point_label.text = f"Dew Point: {city_data['Dew point']} °C"
                self.humidity_ratio_label.text = f"Humidity Ratio: {city_data['Humidity point %']}"

                # Update dry_bulb for calculations
                self.dry_bulb = city_data['Dry Bulb Temperature']
                self.city_name = city_data['Station Name']

            else:
                self._clear_labels()
                print("City data not found in CSV.")

        except Exception as e:
            print(f"Error updating climate info: {str(e)}")
            self._clear_labels()

    def update_liquid_cooling_options(self, fws_liquid_temp):
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
            city_data = self.climate_data[self.climate_data['Station Name'] == selected_city]

            if not city_data.empty:
                dry_bulb = float(city_data['Dry Bulb Temperature'].iloc[0])
                wet_bulb = float(city_data['Wet Bulb Temperature'].iloc[0])

                # Determine Option 1 (Dry Cooler or Chiller)
                if fws_liquid_temp - 5 - dry_bulb >= 0:
                    self.liquid_cooling_label1.text = "Liquid Cooling Option 1: Dry Cooler"
                    self.liquid_cooling_type = "Dry Cooler"
                else:
                    self.liquid_cooling_label1.text = "Liquid Cooling Option 1: Chiller"
                    self.liquid_cooling_type = "Chiller"

                # Determine Option 2 (Closed Loop Cooling Tower or Chiller)
                if fws_liquid_temp - 3 - wet_bulb >= 0:
                    self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Closed Loop Cooling Tower"
                    self.liquid_cooling_type_secondary = "Closed Loop Cooling Tower"
                else:
                    self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Chiller"
                    self.liquid_cooling_type_secondary = "Chiller"

            else:
                self.liquid_cooling_label1.text = "Liquid Cooling Option 1: Not Set"
                self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Not Set"

        except Exception as e:
            print(f"Error updating liquid cooling options: {str(e)}")
            self.liquid_cooling_label1.text = "Liquid Cooling Option 1: Not Set"
            self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Not Set"

    def update_liquid_cooling_options_1(self, fws_liquid_temp_1):
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
            city_data = self.climate_data[self.climate_data['Station Name'] == selected_city]

            if not city_data.empty:
                dry_bulb = float(city_data['Dry Bulb Temperature'].iloc[0])
                wet_bulb = float(city_data['Wet Bulb Temperature'].iloc[0])

                # Determine Option 1 (Dry Cooler or Chiller)
                if fws_liquid_temp_1 - 5 - dry_bulb >= 0:
                    # self.liquid_cooling_labels2_1.text = "Liquid Cooling Option 1: Dry Cooler"
                    self.liquid_cooling_type_1 = "Dry Cooler"
                else:
                    # self.liquid_cooling_labels2_1.text = "Liquid Cooling Option 1: Chiller"
                    self.liquid_cooling_type_1 = "Chiller"

                # Determine Option 2 (Closed Loop Cooling Tower or Chiller)
                if fws_liquid_temp_1 - 3 - wet_bulb >= 0:
                    # self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Closed Loop Cooling Tower"
                    self.liquid_cooling_type_secondary_1 = "Closed Loop Cooling Tower"
                else:
                    # self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Chiller"
                    self.liquid_cooling_type_secondary_1 = "Chiller"

        except Exception as e:
            print(f"Error updating liquid cooling options: {str(e)}")

    def update_liquid_cooling_options_2(self, fws_liquid_temp_2):
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
            city_data = self.climate_data[self.climate_data['Station Name'] == selected_city]

            if not city_data.empty:
                dry_bulb = float(city_data['Dry Bulb Temperature'].iloc[0])
                wet_bulb = float(city_data['Wet Bulb Temperature'].iloc[0])

                # Determine Option 1 (Dry Cooler or Chiller)
                if fws_liquid_temp_2 - 5 - dry_bulb >= 0:
                    # self.liquid_cooling_labels2_1.text = "Liquid Cooling Option 1: Dry Cooler"
                    self.liquid_cooling_type_2 = "Dry Cooler"
                else:
                    # self.liquid_cooling_labels2_1.text = "Liquid Cooling Option 1: Chiller"
                    self.liquid_cooling_type_2 = "Chiller"

                # Determine Option 2 (Closed Loop Cooling Tower or Chiller)
                if fws_liquid_temp_2 - 3 - wet_bulb >= 0:
                    # self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Closed Loop Cooling Tower"
                    self.liquid_cooling_type_secondary_2 = "Closed Loop Cooling Tower"
                else:
                    # self.liquid_cooling_label2.text = "Liquid Cooling Option 2: Chiller"
                    self.liquid_cooling_type_secondary_2 = "Chiller"

        except Exception as e:
            print(f"Error updating liquid cooling options: {str(e)}")

    def update_cooling_capacities(self):
        selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
        total_air_cooling = cooling_capacities.calculate_total_air_cooling_capacity(selected_pod_type)
        liquid_cooling_capacity = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)

        # Display the cooling capacities in the UI
        self.total_air_cooling_label.text = f"Total Air Cooling Capacity: {total_air_cooling} kW"
        self.total_liquid_cooling_label.text = f"Total Liquid Cooling Capacity: {liquid_cooling_capacity} kW"


    def update_fws_design_temperature_liquid(self, tcs_liquid_value):
        selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]

        # Calculate the maximum temperature based on TCS Liquid
        max_temp = max(5, tcs_liquid_value - 4)
        liquid_temp_range = list(range(5, max_temp + 1))
          # Debugging statement

        # Update ComboBox with new items
        self.fws_liquid_container.clear()
        with self.fws_liquid_container:
            ui.Label("FWS Design Temp (Liquid):", width=150, style=self.STYLES["label"])
            self.fws_liquid_menu = ui.ComboBox(0, *[str(temp) for temp in liquid_temp_range], style = self.STYLES["combo_box"])  # Populate with calculated range
            ui.Label("°C", width=30)

        self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(
                lambda model: self.update_liquid_cooling_options(int(self.fws_liquid_options[model.as_int]))
                        )
        self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(
                lambda model: self.calculate_monthly_power_consumption()
                        )
        self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(
                lambda model: self.update_calculations()
                        )
        self.fws_liquid_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_climate_info(selected_city))
    def calculate_cdus(self, selected_pod_type, liquid_cooling_capacity, required_liquid_flow_rate_per_pod):
        # """
        # Calculate the number of CDUs based on total liquid cooling capacity and required liquid flow rate per pod.
        # Formula:
        # No. of CDUs = MAX(CEILING(liquid_cooling_capacity / XDU1350(nominal cooling capacity), 1),
        #                 CEILING(required_liquid_flow_rate_per_pod / Max Secondary Flow Rate CDU, 1)) + 1
        # """
        try:
            # Nominal cooling capacity for XDU1350
            xdu1350_capacity = constants.NOMINAL_COOLING_CAPACITIES["XDU1350"]

            # Calculate number of CDUs based on cooling capacity and flow rate
            cdus_by_cooling_capacity = math.ceil(liquid_cooling_capacity / xdu1350_capacity)
            cdus_by_flow_rate = math.ceil(required_liquid_flow_rate_per_pod / constants.MAX_SECONDARY_FLOW_RATE_CDU)

            # Final CDU count
            total_cdus = max(cdus_by_cooling_capacity, cdus_by_flow_rate)
            if selected_pod_type == "1152 GPU DGX GB200 Super Pod":
                total_cdus += 1  # Increment CDU count by 1 for this specific pod type

            return total_cdus
        except Exception as e:
            print(f"Error calculating CDUs: {e}")
            return None


    def update_fws_design_temperature_air(self,air_supply_temp):
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]

            # Calculate the FWS Design Temperature Air range
            max_temp = max(5, air_supply_temp - 12)
            air_temp_range = list(range(5, max_temp + 1))

            # Clear the existing ComboBox and recreate it with the new range
            self.fws_air_container.clear()
            with self.fws_air_container:
                ui.Label("FWS Design Temp (Air):", width=150, style=self.STYLES["label"])
                # Populate ComboBox with the new air temperature range as strings
                self.fws_air_menu = ui.ComboBox(0, *[str(temp) for temp in air_temp_range],style = self.STYLES["combo_box"])
                ui.Label("°C", width=30)

            # Attach an event listener to update `fws_design_temperature_air` when selection changes
            self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(
                lambda model: helper.calculate_chilled_water_temperature_rise(int(self.fws_air_options[model.as_int]), self.dry_bulb)
                        )
            self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(
                lambda model: self.update_climate_info(selected_city)
                        )
            self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(self.update_fws_design_temperature_air_value)
            self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.update_calculations())
            self.fws_air_menu.model.get_item_value_model().add_value_changed_fn(lambda model: self.calculate_monthly_power_consumption())

            # Initialize `fws_design_temperature_air` with the current ComboBox selection
            self.update_fws_design_temperature_air_value(self.fws_air_menu.model.get_item_value_model())
            # Ensuring update_calculations triggers when fws_air_menu changes
        except ValueError as e:
            print(f"ValueError in update_fws_design_temperature_air: {e}")
        except Exception as e:
            print(f"Unexpected error in update_fws_design_temperature_air: {e}")

    def update_fws_design_temperature_air_value(self, model):
        """Update `fws_design_temperature_air` based on ComboBox selection."""
        try:
            # Get the selected index and retrieve the actual value from the ComboBox options
            # Assuming fws_air_menu is defined as ui.ComboBox with a model
            children = self.fws_air_menu.model.get_item_children()
            selected_index = self.fws_air_menu.model.get_item_value_model(None).as_int

            # Get the selected item model and value as a string
            if 0 <= selected_index < len(children):
                selected_item_model = self.fws_air_menu.model.get_item_value_model(children[selected_index])
                self.fws_design_temperature_air = int(selected_item_model.get_value_as_string())

            else:
                print("Selected index is out of range")


        except Exception as e:
            print(f"Error updating FWS Design Temperature Air: {e}")


    def get_number_of_equipments_air_cooling(self,fws_air, air_cooling_capacity_per_pod, num_pods, selected_chiller):
        required_cooling_capacity = air_cooling_capacity_per_pod * num_pods
        dry_bulb = int(self.dry_bulb)

        # Consolidate filter for 'TWOUT', 'Model', and 'TA' adjustments in one line
        matching_cooler_data = self.chillers_data[
            (self.chillers_data['TWOUT'] == fws_air) &
            (self.chillers_data['Model'] == selected_chiller)
        ]
        matching_cooler_data.loc[:, 'TA'] = matching_cooler_data['TA'].astype(int)

        # Filter to find nearest 'TA' value above or equal to the dry bulb temperature
        possible_ta_values = matching_cooler_data['TA'][matching_cooler_data['TA'] >= dry_bulb]

        if not possible_ta_values.empty:
            nearest_ta_above = possible_ta_values.min()
            # Retrieve cooling capacity for the nearest TA above, ensuring model and temperature match
            cooling_capacity_per_unit = matching_cooler_data[
                (matching_cooler_data['TA'] == nearest_ta_above)
            ]['Cooling Capacity'].iloc[0]
        else:
            print(f"No suitable TA value found above or equal to the dry bulb {dry_bulb}. Using default capacity.")
            cooling_capacity_per_unit = 1114  # Default capacity; adjust as necessary based on your system's needs

        # Calculate the number of units required to meet the total cooling demand
        no_of_equipments_liquid = math.ceil(required_cooling_capacity / cooling_capacity_per_unit)
        print(f"Number of Chiller Units required: {no_of_equipments_liquid}")

        return no_of_equipments_liquid, cooling_capacity_per_unit

    def get_number_of_equipments_liquid_cooling(self, fws_liquid, liquid_cooling_capacity_per_pod, num_pods, selected_chiller):
        required_cooling_capacity = liquid_cooling_capacity_per_pod * num_pods
        dry_bulb = int(self.dry_bulb)

        # Consolidate filter for 'TWOUT', 'Model', and 'TA' adjustments in one line
        matching_cooler_data = self.chillers_data[
            (self.chillers_data['TWOUT'] == fws_liquid) &
            (self.chillers_data['Model'] == selected_chiller)
        ]
        matching_cooler_data.loc[:, 'TA'] = matching_cooler_data['TA'].astype(int)

        # Filter to find nearest 'TA' value above or equal to the dry bulb temperature
        possible_ta_values = matching_cooler_data['TA'][matching_cooler_data['TA'] >= dry_bulb]

        if not possible_ta_values.empty:
            nearest_ta_above = possible_ta_values.min()
            # Retrieve cooling capacity for the nearest TA above, ensuring model and temperature match
            cooling_capacity_per_unit = matching_cooler_data[
                (matching_cooler_data['TA'] == nearest_ta_above)
            ]['Cooling Capacity'].iloc[0]
        else:
            print(f"No suitable TA value found above or equal to the dry bulb {dry_bulb}. Using default capacity.")
            cooling_capacity_per_unit = 1114  # Default capacity; adjust as necessary based on your system's needs

        # Calculate the number of units required to meet the total cooling demand
        no_of_equipments_liquid = math.ceil(required_cooling_capacity / cooling_capacity_per_unit)
        print(f"Number of Chiller Units required: {no_of_equipments_liquid}")

        return no_of_equipments_liquid, cooling_capacity_per_unit

    def get_number_of_equipments_liquid_cooling_dry_cooler(self, fws_liquid, liquid_cooling_capacity_per_pod, num_pods, selected_dryer):
        required_cooling_capacity = liquid_cooling_capacity_per_pod * num_pods
        dry_bulb = int(self.dry_bulb)
        cooling_capacity_per_unit = 300  # Default capacity if no match is found

        # Filter dryer data based on `fws_liquid`, `Model` and ensuring `TA` is above or equal to `dry_bulb`
        matching_cooler_data = self.dryer_data[
            (self.dryer_data['TWOUT'] == fws_liquid) &
            (self.dryer_data['Model'] == selected_dryer)
        ]
        matching_cooler_data.loc[:, 'TA'] = matching_cooler_data['TA'].astype(int)

        # Select the minimum TA that is greater than or equal to the dry_bulb
        possible_ta_values = matching_cooler_data['TA'][matching_cooler_data['TA'] >= dry_bulb]

        if not possible_ta_values.empty:
            nearest_ta_above = possible_ta_values.min()
            # Retrieve cooling capacity for the nearest TA above and specific dryer model
            cooling_capacity_per_unit = matching_cooler_data[
                (matching_cooler_data['TA'] == nearest_ta_above)
            ]['Cooling Capacity'].iloc[0]
        else:
            print(f"No suitable TA value found above or equal to the dry bulb {dry_bulb}. Using default capacity.")

        # Calculate the number of units required to meet the total cooling demand
        no_of_equipments_liquid = math.ceil(required_cooling_capacity / cooling_capacity_per_unit)
        print(f"Number of Dry Cooler Units required: {no_of_equipments_liquid}")

        return no_of_equipments_liquid, cooling_capacity_per_unit

    def calculate_total_power(self):
        try:
            # Get the selected pod type and the number of pods
            selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
            num_pods = int(self.num_pods_field.model.get_value_as_string())

            # Calculate the power per pod
            power_per_pod = cooling_capacities.calculate_power_per_pod(selected_pod_type)

            # Calculate total power based on the number of pods
            total_power = power_per_pod * num_pods

            # Display the total power in the UI
            self.total_power_label.text = f"Total Power: {total_power} kW"
            return total_power

        except ValueError:
            # Handle cases where the input is not a valid integer
            self.total_power_label.text = "Enter a valid number of pods."

        # Function to calculate required air flow rate per kW (CFM)


    def update_flow_rates(self):
        """Main method to update flow rates in the UI."""
        try:

                    # Get the selected pod type
            selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
            
            # Calculate the required liquid cooling capacity per pod based on the selected pod type
            liquid_cooling_capacity = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)

            # Calculate liquid flow rate per pod and update the UI label
            required_liquid_flow_rate_per_pod = self.calculate_liquid_flow_rate_per_pod()
            self.required_liquid_flow_rate_label.text = f"Required Liquid Flow Rate per Pod (LPM): {required_liquid_flow_rate_per_pod:.2f}"

            # Calculate total CDUs and update the UI label
            total_cdus = self.calculate_cdus(selected_pod_type, liquid_cooling_capacity, required_liquid_flow_rate_per_pod)
            total_cdus_1152 = total_cdus + 1
            self.total_cdus_label.text = f"Number of CDUs: {total_cdus}" if total_cdus else "Calculation error"

            # Calculate primary and secondary flow rates per CDU and per pod
            self.calculate_primary_and_secondary_flowrates(total_cdus, required_liquid_flow_rate_per_pod)
            self.update_pod_flowrate_and_curve(selected_pod_type, total_cdus, required_liquid_flow_rate_per_pod)


        except Exception as e:
            print(f"Unexpected error in update_flow_rates: {e}")

    ### Sub-Methods for Calculations

    def update_calculations(self):
        """Main method to perform all calculations and update UI."""
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
            city_data = self.city_data.get(selected_city)
            chillers_data = self.chillers_data
            dryer_data = self.dryer_data
            climate_data = self.climate_data
            print("Climate", climate_data)
            fluid_piping_data = self.fluid_piping
            selected_pod_type, rack_counts = self.get_selected_pod_info()
            dry_bulb = int(self.dry_bulb)

            current_cdu_type = self.cdu_options[self.cdu_menu.model.get_item_value_model().as_int]
            num_pods = int(self.num_pods_field.model.get_value_as_string())
            num_years = int(self.num_years_field.model.get_value_as_string())
            air_supply_temperature = self.get_selected_air_supply_temperature() # Fetch the selected air supply temperature

            selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
            selected_chiller = self.chiller_options[self.chiller_menu.model.get_item_value_model().as_int]
            selected_dryer = self.dryer_options[self.dryer_menu.model.get_item_value_model().as_int]
            air_cooling_capacity_per_pod = cooling_capacities.calculate_total_air_cooling_capacity(selected_pod_type)
            required_air_flow_rate_capacity_per_pod = self.calculate_airflow_rate_per_pod(air_supply_temperature)
            electricity_price = helper.get_electricity_price(climate_data, selected_city)
            print("Electricity price", electricity_price)
            fws_air_temp = self.get_selected_fws_design_air_temperature()
            fws_liquid_temp = self.get_selected_fws_design_liquid_temperature()
            liquid_cooling_capacity_per_pod = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
            equipment_capacity_chillers = helper.get_equipment_capacity_chiller(chillers_data, dry_bulb, fws_air_temp, model = selected_chiller)
            no_of_equipments_air, cooling_capacity_per_unit_air_chiller = self.get_number_of_equipments_air_cooling(fws_air_temp, air_cooling_capacity_per_pod,num_pods,selected_chiller)
            no_of_equipments_liquid, cooling_capacity_per_unit_liquid_chiller = self.get_number_of_equipments_liquid_cooling(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_chiller)
            no_of_equipments_liquid_dry_cooler , cooling_capacity_per_unit_dry_cooler = self.get_number_of_equipments_liquid_cooling_dry_cooler(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_dryer)
            liquid_cooling_capacity = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
            # Calculate liquid flow rate per pod and update the UI label
            required_liquid_flow_rate_per_pod = self.calculate_liquid_flow_rate_per_pod()
            no_of_racks_gb200_per_pod = rack_counts.get("GB200_NVL72", 0)
            no_of_racks_gb200 = rack_counts.get("GB200_NVL72", 0) * num_pods
            total_no_of_racks = (rack_counts.get("GB200_NVL72") + rack_counts.get("Management") + rack_counts.get("Networking")) * num_pods
            no_of_belimos = no_of_racks_gb200
            no_of_DN20_valve = no_of_belimos * 2
            no_of_chillers_air_cooling = no_of_equipments_air
            no_of_chillers_air_cooling_redundant = no_of_chillers_air_cooling + 1
            no_of_chillers_liquid_cooling = no_of_equipments_liquid
            no_of_chillers_liquid_cooling_redundant = no_of_chillers_liquid_cooling + 1
            no_of_dry_cooler_redundant = no_of_equipments_liquid_dry_cooler + 1
           
           
            # Calculate air temperature rise in rack
            air_temperature_rise_in_rack = helper.calculate_air_temperature_rise_in_rack(air_cooling_capacity_per_pod, required_air_flow_rate_capacity_per_pod)
            self.air_temperature_rise_label.text = f"Air Temperature Rise in Rack: {air_temperature_rise_in_rack:.2f} °C"

            # Calculate air return temperature
            air_return_temperature = helper.calculate_air_return_temperature(air_supply_temperature, air_temperature_rise_in_rack)
            self.air_return_temperature_label.text = f"Air Return Temperature: {air_return_temperature:.2f} °C"

            self.required_airflow_rate_label.text = f"Required Air Flow Rate per Pod (CFM): {required_air_flow_rate_capacity_per_pod:.2f}" if required_air_flow_rate_capacity_per_pod else "Calculation error"

            no_of_cdus_per_pod = self.calculate_cdus(selected_pod_type,liquid_cooling_capacity, required_liquid_flow_rate_per_pod)
            no_of_cdus_per_pod_redundant = no_of_cdus_per_pod + 1
            hp2_per_cdu = self.update_pod_flowrate_and_curve(selected_pod_type, no_of_cdus_per_pod, required_liquid_flow_rate_per_pod)

            cdu_capex_per_pod = capex_calculations.calculate_cdu_cost_per_pod(no_of_cdus_per_pod_redundant)
            cdu_total_capex = capex_calculations.calculate_total_cdu_cost(no_of_cdus_per_pod_redundant, num_pods)

            # Calculate number of CRAHs
            no_of_crahs_per_pod = helper.calculate_no_of_crahs_per_pod(air_cooling_capacity_per_pod)
            no_of_crahs_per_pod_redundant = no_of_crahs_per_pod + 1

            crah_capex_per_pod = capex_calculations.calculate_crah_cost_per_pod(no_of_crahs_per_pod_redundant)
            crah_total_capex = capex_calculations.calculate_total_crah_cost(no_of_crahs_per_pod_redundant, num_pods)

            air_ducting_total_capex = capex_calculations.calculate_total_air_ducting_cost(no_of_crahs_per_pod_redundant, num_pods)
            aisle_containment_total_capex = capex_calculations.calculate_total_aisle_containment_cost(total_no_of_racks)

                    # Update CRAH count label for Vertiv PW170
            self.crah_label_vertiv_pw170.text = f"Number of CRAHs for Vertiv PW170: {no_of_crahs_per_pod}"

            belimo_total_capex = capex_calculations.calculate_total_belimo_cost(no_of_belimos)
            DN20_valve_total_capex = capex_calculations.calculate_total_dn20_cost(no_of_DN20_valve)

            # Calculate Q per CRAH based on CDU type
            total_power_per_pod = cooling_capacities.calculate_power_per_pod(selected_pod_type)  
            total_power = self.calculate_total_power()
            q_per_crah = helper.calculate_q_per_crah(current_cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, no_of_crahs_per_pod)
            self.q_per_crah_label.text = f"Q per CRAH: {q_per_crah:.2f} kW"

            chilled_water_temperature_rise = helper.calculate_chilled_water_temperature_rise(fws_air_temp, self.dry_bulb)

            # Calculate chilled water flow rate per CRAH
            chilled_water_flow_rate_crah = helper.calculate_chilled_water_flow_rate_per_crah(q_per_crah, chilled_water_temperature_rise)
            self.chilled_water_flow_rate_crah_label.text = f"Chilled Water Flow Rate per CRAH (LPM): {chilled_water_flow_rate_crah:.2f}"

            # Calculate chilled water flow rate per POD
            chilled_water_flow_rate_pod = helper.calculate_chilled_water_flow_rate_per_pod(chilled_water_flow_rate_crah, no_of_crahs_per_pod)
            self.chilled_water_flow_rate_pod_label.text = f"Chilled Water Flow Rate per POD (LPM): {chilled_water_flow_rate_pod:.2f}"

            q_ac_per_pod = helper.calculate_q_ac_per_pod(current_cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, num_pods)
            self.q_ac_per_pod_label.text = f"Q AC per POD (kW): {q_ac_per_pod:.2f}"

            hp2_per_crah = self.calculate_crah_rpm_and_power(required_air_flow_rate_capacity_per_pod,no_of_crahs_per_pod)

            # Piping cost
            print("num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod", num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod)

            power_consumption = power_calculations.calculate_annual_power_consumption(num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod)

            if power_consumption:
                self.total_it_power_label.text = f"Total IT Power Consumption (kWh): {power_consumption['it_power']:.2f}"
                self.pw170_power_label.text = f"PW170 Annual Power Consumption (kWh): {power_consumption['pw170_power']:.2f}"
                pw170_annual_power = power_consumption["pw170_power"]
                self.xdu1350_power_label.text = f"XDU1350 Annual Power Consumption (kWh): {power_consumption['xdu1350_power']:.2f}"
                xdu1350_annual_power = power_consumption["xdu1350_power"]
            else:
                self.total_power_label.text = "Error in power calculation."

            general_power = power_calculations.calculate_general_power_consumption(total_power_per_pod, num_pods, hp2_per_cdu, no_of_cdus_per_pod)
            if general_power:
                self.lighting_power_label.text = f"Lighting Power Consumption (kWh): {general_power['lighting_power']:.2f}"
                lighting_power = general_power['lighting_power']
                self.ups_it_loss_label.text = f"UPS IT Loss Power Consumption (kWh): {general_power['ups_it_loss_power']:.2f}"
                ups_it_loss_power = general_power['ups_it_loss_power']
                self.ups_mech_loss_label.text = f"UPS Mechanical Loss Power Consumption (kWh): {general_power['ups_mech_loss_power']:.2f}"
                ups_mech_loss_power = general_power['ups_mech_loss_power']
                self.hvac_power_label.text = f"HVAC Power Consumption (kWh): {general_power['hvac_power']:.2f}"
                hvac_power = general_power['hvac_power']
            else:
                print("Error calculating additional power consumption.")
            # self.calculate_monthly_power_consumption(fws_air_temp,fws_liquid_temp)
             # Calculate IT power consumption
            it_power_yearly = power_calculations.calculate_annual_power_consumption(num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah, no_of_cdus_per_pod, no_of_crahs_per_pod)["it_power"]
            air_chiller_power = power_calculations.calculate_air_cooling_power(dry_bulb,city_data , chillers_data ,fws_air_temp, no_of_equipments_air, air_cooling_capacity_per_pod, num_pods , model = selected_chiller)
            liquid_chiller_power = power_calculations.calculate_liquid_cooling_power(dry_bulb,city_data, chillers_data, dryer_data, fws_liquid_temp,no_of_equipments_liquid,no_of_equipments_liquid_dry_cooler,liquid_cooling_capacity_per_pod,num_pods,cooling_capacity_per_unit_dry_cooler, selected_chiller, selected_dryer, liquid_cooling_type = self.liquid_cooling_type)
            self.air_chiller_power_consumption_label.text = f"Power consumption for Chiller(Air cooling) : {air_chiller_power:.2f}"
            self.liquid_chiller_power_consumption_label.text = f"Power consumption for {self.liquid_cooling_type} (Liquid cooling): {liquid_chiller_power:.2f}"

            # Calculate power values for each category
            common_power = power_calculations.calculate_common_power_consumption(lighting_power, ups_it_loss_power, hvac_power, it_power_yearly)
            air_cooling_air_cooled, air_cooling_water_cooled = power_calculations.calculate_total_air_cooling_power(
                pw170_annual_power, air_chiller_power
            )
            liquid_cooling_air_cooled, liquid_cooling_water_cooled = power_calculations.calculate_total_liquid_cooling_power(
                ups_mech_loss_power, xdu1350_annual_power, liquid_chiller_power
            )

            # Calculate Total PUE
            total_pue = power_calculations.calculate_total_pue(it_power_yearly, common_power, air_cooling_air_cooled, liquid_cooling_air_cooled)

                    # Display results in UI
            self.common_power_label.text = f"Common Power Consumption (kWh): {common_power:.2f}"
            self.air_cooling_air_cooled_label.text = f"Air Cooling - Air Cooled Chiller (kWh): {air_cooling_air_cooled:.2f}"
            # self.air_cooling_water_cooled_label.text = f"Air Cooling - Water Cooled Chiller (kWh): {air_cooling_water_cooled:.2f}"
            self.liquid_cooling_air_cooled_label.text = f"Liquid Cooling - Air Cooled Chiller (kWh): {liquid_cooling_air_cooled:.2f}"
            # self.liquid_cooling_water_cooled_label.text = f"Liquid Cooling - Water Cooled Chiller (kWh): {liquid_cooling_water_cooled:.2f}"
            self.total_pue_label.text = f"Total PUE: {total_pue:.2f}"

            print("No of racks check",no_of_racks_gb200_per_pod)
            length_of_header_pipe = helper.calculate_length_of_pipe(no_of_racks_gb200_per_pod, num_pods)
            total_length_of_rack_outlet_inlet = helper.calculate_length_of_pipe_rack_outlet_inlet(no_of_racks_gb200)
            secondary_flowrate_per_cdu = flow_calculations.calculate_secondary_flowrate_per_cdu(required_liquid_flow_rate_per_pod, no_of_cdus_per_pod)
            tcs_liquid_flow_rate_gpm = round(secondary_flowrate_per_cdu / 3.7854)
            diameter_of_header_pipe = helper.calculate_diameter_of_pipe(tcs_liquid_flow_rate_gpm, fluid_piping_data)


            header_price_per_meter = helper.get_price_per_meter_pipe(diameter_of_header_pipe)
            insultaion_price_per_meter = 40
            piping_cost_header = helper.calculate_piping_cost(length_of_header_pipe, header_price_per_meter)
            piping_cost_insulation = helper.calculate_piping_cost(length_of_header_pipe, insultaion_price_per_meter)

            total_price_above_racks_piping = capex_calculations.calculate_above_racks_piping(no_of_racks_gb200)
            total_price_header_piping = capex_calculations.calculate_piping_cost(length_of_header_pipe, header_price_per_meter, piping_cost_header)
            total_price_insulation_piping = capex_calculations.calculate_piping_cost(length_of_header_pipe, insultaion_price_per_meter, piping_cost_insulation)
            total_cost_fittings = total_price_header_piping * 0.3

            # Leak detection
            no_of_spot_detectors = no_of_racks_gb200 * 3
            length_of_sensing_cable = no_of_racks_gb200 * 20
            no_of_LD2100_controller = num_pods
            total_cost_leak_detection = capex_calculations.calculate_leak_detection(no_of_LD2100_controller)

            # Coolant
            total_pg25_per_unit_rack_manifold = (3.14*(((constants.LIQUID_COOLING_PIPING_PER_POD["Rack Outlet/Inlet"]["Diameter"]/2) * 0.0254) ** 2)) * 264.17
            total_volume_pg25_rack_manifold = total_pg25_per_unit_rack_manifold * total_length_of_rack_outlet_inlet

            total_pg25_per_unit_header = (3.14 * (((diameter_of_header_pipe / 2) * 0.0254) ** 2)) * 264.17
            total_volume_pg25_header = total_pg25_per_unit_header * length_of_header_pipe
            total_volume_pg25_cdu = constants.LIQUID_CAPACITY_XDU1350 * no_of_cdus_per_pod_redundant * num_pods
            total_volume_pg_tank = (total_volume_pg25_cdu + total_volume_pg25_rack_manifold + total_volume_pg25_header) * 0.15

            total_pg25 = helper.calculate_total_pg25(total_volume_pg25_rack_manifold, total_volume_pg25_header, total_volume_pg25_cdu, total_volume_pg_tank)
            total_cost_pg25 = total_pg25 * constants.PG25_PRICE
            total_cost_comissioning = 5588.24 * no_of_racks_gb200
           
            # capex Air cooling
            total_cost_chiller_air_cooling = capex_calculations.calculate_chiller_air_cooling_cost(fws_liquid_temp,selected_chiller, no_of_chillers_air_cooling_redundant)
            total_cost_chiller_liquid_cooling = capex_calculations.calculate_chiller_liquid_cooling_cost(fws_liquid_temp,selected_chiller, no_of_chillers_liquid_cooling_redundant, no_of_dry_cooler_redundant, liquid_cooling_type = self.liquid_cooling_type )

            # piping cooling loop
            total_chilled_water_flow_rate = chilled_water_flow_rate_pod * num_pods
            diameter_air_cooling_loop = helper.calculate_diameter_of_pipe(total_chilled_water_flow_rate,fluid_piping_data)
            length_of_air_cooling_loop = helper.calculate_length_of_air_cooling_loop(num_pods)
            air_cooling_loop_price_per_meter = helper.get_price_per_meter_pipe(diameter_air_cooling_loop)
            air_cooling_loop_plumbing_total_cost = helper.calculate_cooling_loop_cost(air_cooling_loop_price_per_meter, length_of_air_cooling_loop)
           
            total_secondary_flowrate = secondary_flowrate_per_cdu * num_pods
            diameter_liquid_cooling_loop = helper.calculate_diameter_of_pipe(total_secondary_flowrate, fluid_piping_data)
            length_of_liquid_cooling_loop = helper.calculate_length_of_liquid_cooling_loop(num_pods)
            liquid_cooling_loop_price_per_meter = helper.get_price_per_meter_pipe(diameter_liquid_cooling_loop)
            liquid_cooling_loop_plumbing_total_cost = helper.calculate_cooling_loop_cost(liquid_cooling_loop_price_per_meter, length_of_liquid_cooling_loop)
           
            # COMMON CAPEX
            bms_total_cost = constants.BMS_UNIT_PRICE * num_pods
            cm_bim_total_cost = constants.CM_BIM_UNIT_PRICE * num_pods
            fire_fighting_total = constants.FIRE_FIGHTING_PRICE * total_no_of_racks
            sum_common_capex = bms_total_cost + cm_bim_total_cost + fire_fighting_total
           

            sum_ac_air_cooled_chiller_capex = crah_total_capex + air_ducting_total_capex + aisle_containment_total_capex + total_cost_chiller_air_cooling + air_cooling_loop_plumbing_total_cost
            sum_ac_water_cooled_chiller_capex = crah_total_capex + air_ducting_total_capex + aisle_containment_total_capex + air_cooling_loop_plumbing_total_cost

            sum_lc_air_cooled_chiller_capex = cdu_total_capex + belimo_total_capex + DN20_valve_total_capex + total_price_above_racks_piping + total_price_header_piping + total_cost_fittings + total_price_insulation_piping + total_cost_leak_detection + total_cost_pg25 + total_cost_comissioning + total_cost_chiller_liquid_cooling + liquid_cooling_loop_plumbing_total_cost
            # Printing each component's value
            sum_lc_water_cooled_chiller_capex = cdu_total_capex + belimo_total_capex + DN20_valve_total_capex + total_price_above_racks_piping + total_price_header_piping + total_cost_fittings + total_price_insulation_piping + total_cost_leak_detection + total_cost_pg25 + total_cost_comissioning + liquid_cooling_loop_plumbing_total_cost


            # total capex calculations
            total_common_capex = capex_calculations.calculate_total_capex(sum_common_capex)
            total_ac_air_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_ac_air_cooled_chiller_capex)
            total_ac_water_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_ac_water_cooled_chiller_capex)
            total_lc_air_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_lc_air_cooled_chiller_capex)
            total_lc_water_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_lc_water_cooled_chiller_capex)

            self.plot_capex(total_common_capex,total_ac_air_cooled_chiller_capex,total_ac_water_cooled_chiller_capex,total_lc_air_cooled_chiller_capex,total_lc_water_cooled_chiller_capex, total_pue, selected_pod_type)

            # Opex_calculation ----------------
            print("Liquid chiller power, total_power", liquid_chiller_power, total_power)
            space_rent_opex_annual = total_power * constants.RENT_KW_MONTH * 12
            print(space_rent_opex_annual)
            space_rent_opex_nth_year = opex_calculations.calculate_nth_energy_cost(space_rent_opex_annual, num_years)
           
            annual_electricity_cost_ac_chiller = opex_calculations.calculate_elctrcity_cost_ac_chiller(air_chiller_power, electricity_price)
            annual_electricity_cost_lc = opex_calculations.calculate_elctrcity_cost_lc(liquid_chiller_power,electricity_price,liquid_cooling_type = self.liquid_cooling_type)
            ac_chiller_nth_year_cost = opex_calculations.calculate_nth_energy_cost(annual_electricity_cost_ac_chiller,num_years)
            lc_nth_year_cost = opex_calculations.calculate_nth_energy_cost(annual_electricity_cost_lc, num_years)

            ac_chiller_maintenance = opex_calculations.calculate_maintenance_for_air_cooling_chiller(total_cost_chiller_air_cooling)
            lc_maintenance = opex_calculations.calculate_maintanence_for_liquid_cooling_chiller(total_cost_chiller_liquid_cooling,liquid_cooling_type = self.liquid_cooling_type)
            ac_chiller_maintenance_nth_year = opex_calculations.calculate_nth_maintenance_cost(ac_chiller_maintenance, num_years)
            lc_maintenance_nth_year = opex_calculations.calculate_nth_maintenance_cost(lc_maintenance, num_years)
           
            # Calculating total volume for flushing
            total_flushing_volume = total_volume_pg25_cdu + total_pg25_per_unit_header + total_volume_pg25_rack_manifold
            # Calculating CDU flushing cost
            cdu_flushing_cost = opex_calculations.calculate_flushing_cost(total_volume=total_flushing_volume)
            # Calculating nth year cost for CDU flushing
            cdu_flushing_cost_nth_year = opex_calculations.calculate_nth_energy_cost(cdu_flushing_cost, num_years)
            # Calculating monitoring and sampling cost
            monitoring_sampling_cost = opex_calculations.calculate_monitoring_cost(num_pods)
            # Calculating nth year cost for monitoring and sampling
            monitoring_sampling_cost_nth_year = opex_calculations.calculate_nth_energy_cost(monitoring_sampling_cost, num_years)

            bms_opex_annual = opex_calculations.calculate_bms_opex(bms_total_cost)
            bms_opex_nth_year = opex_calculations.calculate_nth_energy_cost(bms_opex_annual, num_years)
            security_opex_annual = 0.1 * sum_common_capex
            security_opex_nth_year = opex_calculations.calculate_nth_energy_cost(security_opex_annual,num_years)
            fire_protection_opex_annual = 0.05 * fire_fighting_total
            fire_protection_opex_nth_year = opex_calculations.calculate_nth_energy_cost(fire_protection_opex_annual,num_years)
           
            it_opex_annual = it_power_yearly * electricity_price
            it_opex_nth_year = opex_calculations.calculate_nth_energy_cost(it_opex_annual,num_years)
            ups_it_loss_opex_annual = ups_it_loss_power * electricity_price
            ups_it_loss_opex_nth_year = opex_calculations.calculate_nth_energy_cost(ups_it_loss_opex_annual,num_years)
            lighting_opex_annual = lighting_power * electricity_price
            lighting_opex_nth_year = opex_calculations.calculate_nth_energy_cost(lighting_opex_annual,num_years)
            hvac_opex_annual = hvac_power * electricity_price
            hvac_opex_nth_year = opex_calculations.calculate_nth_energy_cost(hvac_opex_annual,num_years)
            cdu_opex_annual = xdu1350_annual_power * electricity_price
            print("xdu1350_annual_power, hp2", xdu1350_annual_power, hp2_per_cdu)
            cdu_opex_nth_year = opex_calculations.calculate_nth_energy_cost(cdu_opex_annual, num_years)
            ups_mech_loss_opex_annual = ups_mech_loss_power * electricity_price
            print("ups_mech_loss_power", ups_mech_loss_power)
            ups_mech_loss_opex_nth_year = opex_calculations.calculate_nth_energy_cost(ups_mech_loss_opex_annual, num_years)
            crah_opex_annual = pw170_annual_power * electricity_price
            print("pw170_annual_power", pw170_annual_power,hp2_per_crah)
            crah_opex_nth_year = opex_calculations.calculate_nth_energy_cost(crah_opex_annual, num_years)
            print(f"IT OpEx Annual: {it_opex_annual}, IT OpEx Nth Year: {it_opex_nth_year}, UPS IT Loss OpEx Annual: {ups_it_loss_opex_annual}, UPS IT Loss OpEx Nth Year: {ups_it_loss_opex_nth_year}, Lighting OpEx Annual: {lighting_opex_annual}, Lighting OpEx Nth Year: {lighting_opex_nth_year}, HVAC OpEx Annual: {hvac_opex_annual}, HVAC OpEx Nth Year: {hvac_opex_nth_year}, CDU OpEx Annual: {cdu_opex_annual}, CDU OpEx Nth Year: {cdu_opex_nth_year}, UPS Mech Loss OpEx Annual: {ups_mech_loss_opex_annual}, UPS Mech Loss OpEx Nth Year: {ups_mech_loss_opex_nth_year}, CRAH OpEx Annual: {crah_opex_annual}, CRAH OpEx Nth Year: {crah_opex_nth_year}")
            # final sum calculations
            total_common_opex_nth_year = space_rent_opex_nth_year + bms_opex_nth_year + security_opex_nth_year + fire_protection_opex_nth_year + it_opex_nth_year + ups_it_loss_opex_nth_year  + lighting_opex_nth_year + hvac_opex_nth_year
            total_ac_chiller_opex_nth_year = ac_chiller_nth_year_cost + ac_chiller_maintenance_nth_year + crah_opex_nth_year
            total_ac_water_chiller_opex_nth_year = crah_opex_nth_year
            total_lc_opex_nth_year = lc_nth_year_cost + lc_maintenance_nth_year +cdu_flushing_cost_nth_year + monitoring_sampling_cost_nth_year + cdu_opex_nth_year + ups_mech_loss_opex_nth_year
            total_lc_water_opex_nth_year = cdu_flushing_cost_nth_year + monitoring_sampling_cost_nth_year + cdu_opex_nth_year + ups_mech_loss_opex_nth_year
            print(f"Total Common OpEx: {total_common_opex_nth_year}"); print(f"Total AC Chiller OpEx: {total_ac_chiller_opex_nth_year}"); print(f"Total AC Water Chiller OpEx: {total_ac_water_chiller_opex_nth_year}"); print(f"Total LC OpEx: {total_lc_opex_nth_year}"); print(f"Total LC Water OpEx: {total_lc_water_opex_nth_year}"); print(f"Components: Space Rent: {space_rent_opex_nth_year}, BMS: {bms_opex_nth_year}, Security: {security_opex_nth_year}, Fire Protection: {fire_protection_opex_nth_year}, IT: {it_opex_nth_year}, UPS IT Loss: {ups_it_loss_opex_nth_year}, Lighting: {lighting_opex_nth_year}, HVAC: {hvac_opex_nth_year}, AC Chiller Cost: {ac_chiller_nth_year_cost}, AC Chiller Maintenance: {ac_chiller_maintenance_nth_year}, CRAH: {crah_opex_nth_year}, LC Cost: {lc_nth_year_cost}, LC Maintenance: {lc_maintenance_nth_year}, CDU Flushing: {cdu_flushing_cost_nth_year}, Monitoring Sampling: {monitoring_sampling_cost_nth_year}, CDU OpEx: {cdu_opex_nth_year}, UPS Mech Loss: {ups_mech_loss_opex_nth_year}")
            self.total_common_opex_label.text = f"Total Common OpEx after {num_years} years: {total_common_opex_nth_year:.0f} $"
            self.total_ac_chiller_opex_label.text = f"Total AC Chiller OpEx after {num_years} years: {total_ac_chiller_opex_nth_year:.0f} $"
            self.total_ac_water_chiller_opex_label.text = f"Total AC Water Chiller OpEx after {num_years} years: {total_ac_water_chiller_opex_nth_year:.0f} $"
            self.total_lc_opex_label.text = f"Total LC {self.liquid_cooling_type} OpEx after {num_years} years: {total_lc_opex_nth_year:.0f} $"
            self.total_lc_water_opex_label.text = f"Total LC Water OpEx after {num_years} years: {total_lc_water_opex_nth_year:.0f} $"

            # CAPEX Dictionary
            capex_values = {
                "Common": total_common_capex,
                "AC Air Cooled": total_ac_air_cooled_chiller_capex,
                # "AC Water Cooled": total_ac_water_cooled_chiller_capex,
                "LC Air Cooled": total_lc_air_cooled_chiller_capex,
                # "LC Water Cooled": total_lc_water_cooled_chiller_capex,
            }

            # OPEX Dictionary
            opex_values = {
                "Common": total_common_opex_nth_year,
                "AC Chiller": total_ac_chiller_opex_nth_year,
                # "AC Water Chiller": total_ac_water_chiller_opex_nth_year,
                "LC": total_lc_opex_nth_year,
                # "LC Water": total_lc_water_opex_nth_year,
            }
            self.capex_data = capex_values
            self.opex_data = opex_values

            # Example Function Call
            self.plot_opex(total_common_opex_nth_year, total_ac_chiller_opex_nth_year, total_ac_water_chiller_opex_nth_year, total_lc_opex_nth_year, total_lc_water_opex_nth_year, num_years, total_pue, selected_pod_type)


        except ValueError:
            self.total_power_label.text = "Enter a valid number of pods."


        except Exception as e:
            print(f"Error in update_calculations: {e}")

    def update_calculations_1(self):
        """Main method to perform all calculations and update UI."""
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
            city_data = self.city_data.get(selected_city)
            chillers_data = self.chillers_data
            dryer_data = self.dryer_data
            climate_data = self.climate_data
            print("Climate", climate_data)
            fluid_piping_data = self.fluid_piping
            selected_pod_type, rack_counts = self.get_selected_pod_info()
            dry_bulb = int(self.dry_bulb)

            current_cdu_type = self.cdu_options[self.cdu_menu.model.get_item_value_model().as_int]
            num_pods = int(self.num_pods_field.model.get_value_as_string())
            num_years = int(self.num_years_field.model.get_value_as_string())
            air_supply_temperature = self.get_selected_air_supply_temperature() # Fetch the selected air supply temperature

            selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
            selected_chiller = self.chiller_options[self.chiller_menu_1.model.get_item_value_model().as_int]
            selected_dryer = self.dryer_options[self.dryer_menu_1.model.get_item_value_model().as_int]
            air_cooling_capacity_per_pod = cooling_capacities.calculate_total_air_cooling_capacity(selected_pod_type)
            required_air_flow_rate_capacity_per_pod = self.calculate_airflow_rate_per_pod(air_supply_temperature)
            electricity_price = helper.get_electricity_price(climate_data, selected_city)
            print("Electricity price", electricity_price)
            fws_air_temp = int(self.fws_air_options[self.fws_air_menu_1.model.get_item_value_model().as_int])
            fws_liquid_temp = int(self.fws_liquid_options[self.fws_liquid_menu_1.model.get_item_value_model().as_int])
            liquid_cooling_capacity_per_pod = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
            equipment_capacity_chillers = helper.get_equipment_capacity_chiller(chillers_data, dry_bulb, fws_air_temp, model = selected_chiller)
            no_of_equipments_air, cooling_capacity_per_unit_air_chiller = self.get_number_of_equipments_air_cooling(fws_air_temp, air_cooling_capacity_per_pod,num_pods,selected_chiller)
            no_of_equipments_liquid, cooling_capacity_per_unit_liquid_chiller = self.get_number_of_equipments_liquid_cooling(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_chiller)
            no_of_equipments_liquid_dry_cooler , cooling_capacity_per_unit_dry_cooler = self.get_number_of_equipments_liquid_cooling_dry_cooler(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_dryer)
            liquid_cooling_capacity = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
            # Calculate liquid flow rate per pod and update the UI label
            required_liquid_flow_rate_per_pod = self.calculate_liquid_flow_rate_per_pod()
            no_of_racks_gb200_per_pod = rack_counts.get("GB200_NVL72", 0)
            no_of_racks_gb200 = rack_counts.get("GB200_NVL72", 0) * num_pods
            total_no_of_racks = (rack_counts.get("GB200_NVL72") + rack_counts.get("Management") + rack_counts.get("Networking")) * num_pods
            no_of_belimos = no_of_racks_gb200
            no_of_DN20_valve = no_of_belimos * 2
            no_of_chillers_air_cooling = no_of_equipments_air
            no_of_chillers_air_cooling_redundant = no_of_chillers_air_cooling + 1
            no_of_chillers_liquid_cooling = no_of_equipments_liquid
            no_of_chillers_liquid_cooling_redundant = no_of_chillers_liquid_cooling + 1
            no_of_dry_cooler_redundant = no_of_equipments_liquid_dry_cooler + 1
           
            # Calculate air temperature rise in rack
            air_temperature_rise_in_rack = helper.calculate_air_temperature_rise_in_rack(air_cooling_capacity_per_pod, required_air_flow_rate_capacity_per_pod)

            # Calculate air return temperature
            air_return_temperature = helper.calculate_air_return_temperature(air_supply_temperature, air_temperature_rise_in_rack)
            no_of_cdus_per_pod = self.calculate_cdus(selected_pod_type,liquid_cooling_capacity, required_liquid_flow_rate_per_pod)
            no_of_cdus_per_pod_redundant = no_of_cdus_per_pod + 1
            hp2_per_cdu = self.update_pod_flowrate_and_curve(selected_pod_type, no_of_cdus_per_pod, required_liquid_flow_rate_per_pod)

            cdu_capex_per_pod = capex_calculations.calculate_cdu_cost_per_pod(no_of_cdus_per_pod_redundant)
            cdu_total_capex = capex_calculations.calculate_total_cdu_cost(no_of_cdus_per_pod_redundant, num_pods)

            # Calculate number of CRAHs
            no_of_crahs_per_pod = helper.calculate_no_of_crahs_per_pod(air_cooling_capacity_per_pod)
            no_of_crahs_per_pod_redundant = no_of_crahs_per_pod + 1

            crah_capex_per_pod = capex_calculations.calculate_crah_cost_per_pod(no_of_crahs_per_pod_redundant)
            crah_total_capex = capex_calculations.calculate_total_crah_cost(no_of_crahs_per_pod_redundant, num_pods)

            air_ducting_total_capex = capex_calculations.calculate_total_air_ducting_cost(no_of_crahs_per_pod_redundant, num_pods)
            aisle_containment_total_capex = capex_calculations.calculate_total_aisle_containment_cost(total_no_of_racks)

            belimo_total_capex = capex_calculations.calculate_total_belimo_cost(no_of_belimos)
            DN20_valve_total_capex = capex_calculations.calculate_total_dn20_cost(no_of_DN20_valve)

            # Calculate Q per CRAH based on CDU type
            total_power_per_pod = cooling_capacities.calculate_power_per_pod(selected_pod_type)  
            total_power = self.calculate_total_power()
            q_per_crah = helper.calculate_q_per_crah(current_cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, no_of_crahs_per_pod)
            self.q_per_crah_label.text = f"Q per CRAH: {q_per_crah:.2f} kW"

            chilled_water_temperature_rise = helper.calculate_chilled_water_temperature_rise(fws_air_temp, self.dry_bulb)

            # Calculate chilled water flow rate per CRAH
            chilled_water_flow_rate_crah = helper.calculate_chilled_water_flow_rate_per_crah(q_per_crah, chilled_water_temperature_rise)

            # Calculate chilled water flow rate per POD
            chilled_water_flow_rate_pod = helper.calculate_chilled_water_flow_rate_per_pod(chilled_water_flow_rate_crah, no_of_crahs_per_pod)

            q_ac_per_pod = helper.calculate_q_ac_per_pod(current_cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, num_pods)

            hp2_per_crah = self.calculate_crah_rpm_and_power(required_air_flow_rate_capacity_per_pod,no_of_crahs_per_pod)

            # Piping cost
            print("num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod", num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod)

            power_consumption = power_calculations.calculate_annual_power_consumption(num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod)

            if power_consumption:
                pw170_annual_power = power_consumption["pw170_power"]
                xdu1350_annual_power = power_consumption["xdu1350_power"]

            general_power = power_calculations.calculate_general_power_consumption(total_power_per_pod, num_pods, hp2_per_cdu, no_of_cdus_per_pod)
            if general_power:
                lighting_power = general_power['lighting_power']
                ups_it_loss_power = general_power['ups_it_loss_power']
                ups_mech_loss_power = general_power['ups_mech_loss_power']
                hvac_power = general_power['hvac_power']

             # Calculate IT power consumption
            it_power_yearly = power_calculations.calculate_annual_power_consumption(num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah, no_of_cdus_per_pod, no_of_crahs_per_pod)["it_power"]
            air_chiller_power = power_calculations.calculate_air_cooling_power(dry_bulb,city_data , chillers_data ,fws_air_temp, no_of_equipments_air, air_cooling_capacity_per_pod, num_pods , model = selected_chiller)
            liquid_chiller_power = power_calculations.calculate_liquid_cooling_power(dry_bulb,city_data, chillers_data, dryer_data, fws_liquid_temp,no_of_equipments_liquid,no_of_equipments_liquid_dry_cooler,liquid_cooling_capacity_per_pod,num_pods,cooling_capacity_per_unit_dry_cooler, selected_chiller, selected_dryer, liquid_cooling_type = self.liquid_cooling_type_1)

            # Calculate power values for each category
            common_power = power_calculations.calculate_common_power_consumption(lighting_power, ups_it_loss_power, hvac_power, it_power_yearly)
            air_cooling_air_cooled, air_cooling_water_cooled = power_calculations.calculate_total_air_cooling_power(
                pw170_annual_power, air_chiller_power
            )
            liquid_cooling_air_cooled, liquid_cooling_water_cooled = power_calculations.calculate_total_liquid_cooling_power(
                ups_mech_loss_power, xdu1350_annual_power, liquid_chiller_power
            )

            # Calculate Total PUE
            total_pue = power_calculations.calculate_total_pue(it_power_yearly, common_power, air_cooling_air_cooled, liquid_cooling_air_cooled)

                    # Display results in Ui

            print("No of racks check",no_of_racks_gb200_per_pod)
            length_of_header_pipe = helper.calculate_length_of_pipe(no_of_racks_gb200_per_pod, num_pods)
            total_length_of_rack_outlet_inlet = helper.calculate_length_of_pipe_rack_outlet_inlet(no_of_racks_gb200)
            secondary_flowrate_per_cdu = flow_calculations.calculate_secondary_flowrate_per_cdu(required_liquid_flow_rate_per_pod, no_of_cdus_per_pod)
            tcs_liquid_flow_rate_gpm = round(secondary_flowrate_per_cdu / 3.7854)
            diameter_of_header_pipe = helper.calculate_diameter_of_pipe(tcs_liquid_flow_rate_gpm, fluid_piping_data)

            header_price_per_meter = helper.get_price_per_meter_pipe(diameter_of_header_pipe)
            insultaion_price_per_meter = 40
            piping_cost_header = helper.calculate_piping_cost(length_of_header_pipe, header_price_per_meter)
            piping_cost_insulation = helper.calculate_piping_cost(length_of_header_pipe, insultaion_price_per_meter)

            total_price_above_racks_piping = capex_calculations.calculate_above_racks_piping(no_of_racks_gb200)
            total_price_header_piping = capex_calculations.calculate_piping_cost(length_of_header_pipe, header_price_per_meter, piping_cost_header)
            total_price_insulation_piping = capex_calculations.calculate_piping_cost(length_of_header_pipe, insultaion_price_per_meter, piping_cost_insulation)
            total_cost_fittings = total_price_header_piping * 0.3

            # Leak detection
            no_of_spot_detectors = no_of_racks_gb200 * 3
            length_of_sensing_cable = no_of_racks_gb200 * 20
            no_of_LD2100_controller = num_pods
            total_cost_leak_detection = capex_calculations.calculate_leak_detection(no_of_LD2100_controller)

            # Coolant
            total_pg25_per_unit_rack_manifold = (3.14*(((constants.LIQUID_COOLING_PIPING_PER_POD["Rack Outlet/Inlet"]["Diameter"]/2) * 0.0254) ** 2)) * 264.17
            total_volume_pg25_rack_manifold = total_pg25_per_unit_rack_manifold * total_length_of_rack_outlet_inlet

            total_pg25_per_unit_header = (3.14 * (((diameter_of_header_pipe / 2) * 0.0254) ** 2)) * 264.17
            total_volume_pg25_header = total_pg25_per_unit_header * length_of_header_pipe
            total_volume_pg25_cdu = constants.LIQUID_CAPACITY_XDU1350 * no_of_cdus_per_pod_redundant * num_pods
            total_volume_pg_tank = (total_volume_pg25_cdu + total_volume_pg25_rack_manifold + total_volume_pg25_header) * 0.15

            total_pg25 = helper.calculate_total_pg25(total_volume_pg25_rack_manifold, total_volume_pg25_header, total_volume_pg25_cdu, total_volume_pg_tank)
            total_cost_pg25 = total_pg25 * constants.PG25_PRICE
            total_cost_comissioning = 5588.24 * no_of_racks_gb200
           
            # capex Air cooling
            total_cost_chiller_air_cooling = capex_calculations.calculate_chiller_air_cooling_cost(fws_liquid_temp,selected_chiller, no_of_chillers_air_cooling_redundant)
            total_cost_chiller_liquid_cooling = capex_calculations.calculate_chiller_liquid_cooling_cost(fws_liquid_temp,selected_chiller, no_of_chillers_liquid_cooling_redundant, no_of_dry_cooler_redundant, liquid_cooling_type = self.liquid_cooling_type_1 )

            # piping cooling loop
            total_chilled_water_flow_rate = chilled_water_flow_rate_pod * num_pods
            diameter_air_cooling_loop = helper.calculate_diameter_of_pipe(total_chilled_water_flow_rate,fluid_piping_data)
            length_of_air_cooling_loop = helper.calculate_length_of_air_cooling_loop(num_pods)
            air_cooling_loop_price_per_meter = helper.get_price_per_meter_pipe(diameter_air_cooling_loop)
            air_cooling_loop_plumbing_total_cost = helper.calculate_cooling_loop_cost(air_cooling_loop_price_per_meter, length_of_air_cooling_loop)
           
            total_secondary_flowrate = secondary_flowrate_per_cdu * num_pods
            diameter_liquid_cooling_loop = helper.calculate_diameter_of_pipe(total_secondary_flowrate, fluid_piping_data)
            length_of_liquid_cooling_loop = helper.calculate_length_of_liquid_cooling_loop(num_pods)
            liquid_cooling_loop_price_per_meter = helper.get_price_per_meter_pipe(diameter_liquid_cooling_loop)
            liquid_cooling_loop_plumbing_total_cost = helper.calculate_cooling_loop_cost(liquid_cooling_loop_price_per_meter, length_of_liquid_cooling_loop)
           
            # COMMON CAPEX
            bms_total_cost = constants.BMS_UNIT_PRICE * num_pods
            cm_bim_total_cost = constants.CM_BIM_UNIT_PRICE * num_pods
            fire_fighting_total = constants.FIRE_FIGHTING_PRICE * total_no_of_racks
            sum_common_capex = bms_total_cost + cm_bim_total_cost + fire_fighting_total
           
            sum_ac_air_cooled_chiller_capex = crah_total_capex + air_ducting_total_capex + aisle_containment_total_capex + total_cost_chiller_air_cooling + air_cooling_loop_plumbing_total_cost
            sum_ac_water_cooled_chiller_capex = crah_total_capex + air_ducting_total_capex + aisle_containment_total_capex + air_cooling_loop_plumbing_total_cost

            sum_lc_air_cooled_chiller_capex = cdu_total_capex + belimo_total_capex + DN20_valve_total_capex + total_price_above_racks_piping + total_price_header_piping + total_cost_fittings + total_price_insulation_piping + total_cost_leak_detection + total_cost_pg25 + total_cost_comissioning + total_cost_chiller_liquid_cooling + liquid_cooling_loop_plumbing_total_cost
            # Printing each component's value
            sum_lc_water_cooled_chiller_capex = cdu_total_capex + belimo_total_capex + DN20_valve_total_capex + total_price_above_racks_piping + total_price_header_piping + total_cost_fittings + total_price_insulation_piping + total_cost_leak_detection + total_cost_pg25 + total_cost_comissioning + liquid_cooling_loop_plumbing_total_cost

            # total capex calculations
            total_common_capex = capex_calculations.calculate_total_capex(sum_common_capex)
            total_ac_air_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_ac_air_cooled_chiller_capex)
            total_ac_water_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_ac_water_cooled_chiller_capex)
            total_lc_air_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_lc_air_cooled_chiller_capex)
            total_lc_water_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_lc_water_cooled_chiller_capex)

            self.plot_capex(total_common_capex,total_ac_air_cooled_chiller_capex,total_ac_water_cooled_chiller_capex,total_lc_air_cooled_chiller_capex,total_lc_water_cooled_chiller_capex, total_pue, selected_pod_type)

            # Opex_calculation ----------------
            print("Liquid chiller power, total_power", liquid_chiller_power, total_power)
            space_rent_opex_annual = total_power * constants.RENT_KW_MONTH * 12
            print(space_rent_opex_annual)
            space_rent_opex_nth_year = opex_calculations.calculate_nth_energy_cost(space_rent_opex_annual, num_years)
           
            annual_electricity_cost_ac_chiller = opex_calculations.calculate_elctrcity_cost_ac_chiller(air_chiller_power, electricity_price)
            annual_electricity_cost_lc = opex_calculations.calculate_elctrcity_cost_lc(liquid_chiller_power,electricity_price,liquid_cooling_type = self.liquid_cooling_type_1)
            ac_chiller_nth_year_cost = opex_calculations.calculate_nth_energy_cost(annual_electricity_cost_ac_chiller,num_years)
            lc_nth_year_cost = opex_calculations.calculate_nth_energy_cost(annual_electricity_cost_lc, num_years)

            ac_chiller_maintenance = opex_calculations.calculate_maintenance_for_air_cooling_chiller(total_cost_chiller_air_cooling)
            lc_maintenance = opex_calculations.calculate_maintanence_for_liquid_cooling_chiller(total_cost_chiller_liquid_cooling,liquid_cooling_type = self.liquid_cooling_type_1)
            ac_chiller_maintenance_nth_year = opex_calculations.calculate_nth_maintenance_cost(ac_chiller_maintenance, num_years)
            lc_maintenance_nth_year = opex_calculations.calculate_nth_maintenance_cost(lc_maintenance, num_years)
           
            # Calculating total volume for flushing
            total_flushing_volume = total_volume_pg25_cdu + total_pg25_per_unit_header + total_volume_pg25_rack_manifold
            # Calculating CDU flushing cost
            cdu_flushing_cost = opex_calculations.calculate_flushing_cost(total_volume=total_flushing_volume)
            # Calculating nth year cost for CDU flushing
            cdu_flushing_cost_nth_year = opex_calculations.calculate_nth_energy_cost(cdu_flushing_cost, num_years)
            # Calculating monitoring and sampling cost
            monitoring_sampling_cost = opex_calculations.calculate_monitoring_cost(num_pods)
            # Calculating nth year cost for monitoring and sampling
            monitoring_sampling_cost_nth_year = opex_calculations.calculate_nth_energy_cost(monitoring_sampling_cost, num_years)

            bms_opex_annual = opex_calculations.calculate_bms_opex(bms_total_cost)
            bms_opex_nth_year = opex_calculations.calculate_nth_energy_cost(bms_opex_annual, num_years)
            security_opex_annual = 0.1 * sum_common_capex
            security_opex_nth_year = opex_calculations.calculate_nth_energy_cost(security_opex_annual,num_years)
            fire_protection_opex_annual = 0.05 * fire_fighting_total
            fire_protection_opex_nth_year = opex_calculations.calculate_nth_energy_cost(fire_protection_opex_annual,num_years)
           
            it_opex_annual = it_power_yearly * electricity_price
            it_opex_nth_year = opex_calculations.calculate_nth_energy_cost(it_opex_annual,num_years)
            ups_it_loss_opex_annual = ups_it_loss_power * electricity_price
            ups_it_loss_opex_nth_year = opex_calculations.calculate_nth_energy_cost(ups_it_loss_opex_annual,num_years)
            lighting_opex_annual = lighting_power * electricity_price
            lighting_opex_nth_year = opex_calculations.calculate_nth_energy_cost(lighting_opex_annual,num_years)
            hvac_opex_annual = hvac_power * electricity_price
            hvac_opex_nth_year = opex_calculations.calculate_nth_energy_cost(hvac_opex_annual,num_years)
            cdu_opex_annual = xdu1350_annual_power * electricity_price
            print("xdu1350_annual_power, hp2", xdu1350_annual_power, hp2_per_cdu)
            cdu_opex_nth_year = opex_calculations.calculate_nth_energy_cost(cdu_opex_annual, num_years)
            ups_mech_loss_opex_annual = ups_mech_loss_power * electricity_price
            print("ups_mech_loss_power", ups_mech_loss_power)
            ups_mech_loss_opex_nth_year = opex_calculations.calculate_nth_energy_cost(ups_mech_loss_opex_annual, num_years)
            crah_opex_annual = pw170_annual_power * electricity_price
            print("pw170_annual_power", pw170_annual_power,hp2_per_crah)
            crah_opex_nth_year = opex_calculations.calculate_nth_energy_cost(crah_opex_annual, num_years)
            print(f"IT OpEx Annual: {it_opex_annual}, IT OpEx Nth Year: {it_opex_nth_year}, UPS IT Loss OpEx Annual: {ups_it_loss_opex_annual}, UPS IT Loss OpEx Nth Year: {ups_it_loss_opex_nth_year}, Lighting OpEx Annual: {lighting_opex_annual}, Lighting OpEx Nth Year: {lighting_opex_nth_year}, HVAC OpEx Annual: {hvac_opex_annual}, HVAC OpEx Nth Year: {hvac_opex_nth_year}, CDU OpEx Annual: {cdu_opex_annual}, CDU OpEx Nth Year: {cdu_opex_nth_year}, UPS Mech Loss OpEx Annual: {ups_mech_loss_opex_annual}, UPS Mech Loss OpEx Nth Year: {ups_mech_loss_opex_nth_year}, CRAH OpEx Annual: {crah_opex_annual}, CRAH OpEx Nth Year: {crah_opex_nth_year}")
            # final sum calculations
            total_common_opex_nth_year = space_rent_opex_nth_year + bms_opex_nth_year + security_opex_nth_year + fire_protection_opex_nth_year + it_opex_nth_year + ups_it_loss_opex_nth_year  + lighting_opex_nth_year + hvac_opex_nth_year
            total_ac_chiller_opex_nth_year = ac_chiller_nth_year_cost + ac_chiller_maintenance_nth_year + crah_opex_nth_year
            total_ac_water_chiller_opex_nth_year = crah_opex_nth_year
            total_lc_opex_nth_year = lc_nth_year_cost + lc_maintenance_nth_year +cdu_flushing_cost_nth_year + monitoring_sampling_cost_nth_year + cdu_opex_nth_year + ups_mech_loss_opex_nth_year
            total_lc_water_opex_nth_year = cdu_flushing_cost_nth_year + monitoring_sampling_cost_nth_year + cdu_opex_nth_year + ups_mech_loss_opex_nth_year
            print(f"Total Common OpEx: {total_common_opex_nth_year}"); print(f"Total AC Chiller OpEx: {total_ac_chiller_opex_nth_year}"); print(f"Total AC Water Chiller OpEx: {total_ac_water_chiller_opex_nth_year}"); print(f"Total LC OpEx: {total_lc_opex_nth_year}"); print(f"Total LC Water OpEx: {total_lc_water_opex_nth_year}"); print(f"Components: Space Rent: {space_rent_opex_nth_year}, BMS: {bms_opex_nth_year}, Security: {security_opex_nth_year}, Fire Protection: {fire_protection_opex_nth_year}, IT: {it_opex_nth_year}, UPS IT Loss: {ups_it_loss_opex_nth_year}, Lighting: {lighting_opex_nth_year}, HVAC: {hvac_opex_nth_year}, AC Chiller Cost: {ac_chiller_nth_year_cost}, AC Chiller Maintenance: {ac_chiller_maintenance_nth_year}, CRAH: {crah_opex_nth_year}, LC Cost: {lc_nth_year_cost}, LC Maintenance: {lc_maintenance_nth_year}, CDU Flushing: {cdu_flushing_cost_nth_year}, Monitoring Sampling: {monitoring_sampling_cost_nth_year}, CDU OpEx: {cdu_opex_nth_year}, UPS Mech Loss: {ups_mech_loss_opex_nth_year}")
            # self.total_common_opex_label.text = f"Total Common OpEx after {num_years} years: {total_common_opex_nth_year:.0f} $"
            # self.total_ac_chiller_opex_label.text = f"Total AC Chiller OpEx after {num_years} years: {total_ac_chiller_opex_nth_year:.0f} $"
            # self.total_ac_water_chiller_opex_label.text = f"Total AC Water Chiller OpEx after {num_years} years: {total_ac_water_chiller_opex_nth_year:.0f} $"
            # self.total_lc_opex_label.text = f"Total LC {self.liquid_cooling_type_1} OpEx after {num_years} years: {total_lc_opex_nth_year:.0f} $"
            # self.total_lc_water_opex_label.text = f"Total LC Water OpEx after {num_years} years: {total_lc_water_opex_nth_year:.0f} $"

            # CAPEX Dictionary
            capex_values = {
                "Common": total_common_capex,
                "AC Air Cooled": total_ac_air_cooled_chiller_capex,
                # "AC Water Cooled": total_ac_water_cooled_chiller_capex,
                "LC Air Cooled": total_lc_air_cooled_chiller_capex,
                # "LC Water Cooled": total_lc_water_cooled_chiller_capex,
            }

            # OPEX Dictionary
            opex_values = {
                "Common": total_common_opex_nth_year,
                "AC Chiller": total_ac_chiller_opex_nth_year,
                # "AC Water Chiller": total_ac_water_chiller_opex_nth_year,
                "LC": total_lc_opex_nth_year,
                # "LC Water": total_lc_water_opex_nth_year,
            }
            self.capex_data_1 = capex_values
            self.opex_data_1 = opex_values

            # Example Function Call
            # self.plot_opex(total_common_opex_nth_year, total_ac_chiller_opex_nth_year, total_ac_water_chiller_opex_nth_year, total_lc_opex_nth_year, total_lc_water_opex_nth_year, num_years, total_pue, selected_pod_type)

        except ValueError:
            self.total_power_label.text = "Enter a valid number of pods."

        except Exception as e:
            print(f"Error in update_calculations: {e}")

    def update_calculations_2(self):
        """Main method to perform all calculations and update UI."""
        try:
            selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
            city_data = self.city_data.get(selected_city)
            chillers_data = self.chillers_data
            dryer_data = self.dryer_data
            climate_data = self.climate_data
            fluid_piping_data = self.fluid_piping
            selected_pod_type, rack_counts = self.get_selected_pod_info()
            dry_bulb = int(self.dry_bulb)

            current_cdu_type = self.cdu_options[self.cdu_menu.model.get_item_value_model().as_int]
            num_pods = int(self.num_pods_field.model.get_value_as_string())
            num_years = int(self.num_years_field.model.get_value_as_string())
            air_supply_temperature = self.get_selected_air_supply_temperature() # Fetch the selected air supply temperature

            selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
            selected_chiller = self.chiller_options[self.chiller_menu_2.model.get_item_value_model().as_int]
            selected_dryer = self.dryer_options[self.dryer_menu_2.model.get_item_value_model().as_int]
            air_cooling_capacity_per_pod = cooling_capacities.calculate_total_air_cooling_capacity(selected_pod_type)
            required_air_flow_rate_capacity_per_pod = self.calculate_airflow_rate_per_pod(air_supply_temperature)
            electricity_price = helper.get_electricity_price(climate_data, selected_city)
            print("Electricity price", electricity_price)
            fws_air_temp = int(self.fws_air_options[self.fws_air_menu_2.model.get_item_value_model().as_int])
            fws_liquid_temp = int(self.fws_liquid_options[self.fws_liquid_menu_2.model.get_item_value_model().as_int])
            liquid_cooling_capacity_per_pod = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
            equipment_capacity_chillers = helper.get_equipment_capacity_chiller(chillers_data, dry_bulb, fws_air_temp, model = selected_chiller)
            no_of_equipments_air, cooling_capacity_per_unit_air_chiller = self.get_number_of_equipments_air_cooling(fws_air_temp, air_cooling_capacity_per_pod,num_pods,selected_chiller)
            no_of_equipments_liquid, cooling_capacity_per_unit_liquid_chiller = self.get_number_of_equipments_liquid_cooling(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_chiller)
            no_of_equipments_liquid_dry_cooler , cooling_capacity_per_unit_dry_cooler = self.get_number_of_equipments_liquid_cooling_dry_cooler(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_dryer)
            liquid_cooling_capacity = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
            # Calculate liquid flow rate per pod and update the UI label
            required_liquid_flow_rate_per_pod = self.calculate_liquid_flow_rate_per_pod()
            no_of_racks_gb200_per_pod = rack_counts.get("GB200_NVL72", 0)
            no_of_racks_gb200 = rack_counts.get("GB200_NVL72", 0) * num_pods
            total_no_of_racks = (rack_counts.get("GB200_NVL72") + rack_counts.get("Management") + rack_counts.get("Networking")) * num_pods
            no_of_belimos = no_of_racks_gb200
            no_of_DN20_valve = no_of_belimos * 2
            no_of_chillers_air_cooling = no_of_equipments_air
            no_of_chillers_air_cooling_redundant = no_of_chillers_air_cooling + 1
            no_of_chillers_liquid_cooling = no_of_equipments_liquid
            no_of_chillers_liquid_cooling_redundant = no_of_chillers_liquid_cooling + 1
            no_of_dry_cooler_redundant = no_of_equipments_liquid_dry_cooler + 1
           
            # Calculate air temperature rise in rack
            air_temperature_rise_in_rack = helper.calculate_air_temperature_rise_in_rack(air_cooling_capacity_per_pod, required_air_flow_rate_capacity_per_pod)

            # Calculate air return temperature
            air_return_temperature = helper.calculate_air_return_temperature(air_supply_temperature, air_temperature_rise_in_rack)
            no_of_cdus_per_pod = self.calculate_cdus(selected_pod_type,liquid_cooling_capacity, required_liquid_flow_rate_per_pod)
            no_of_cdus_per_pod_redundant = no_of_cdus_per_pod + 1
            hp2_per_cdu = self.update_pod_flowrate_and_curve(selected_pod_type, no_of_cdus_per_pod, required_liquid_flow_rate_per_pod)

            cdu_capex_per_pod = capex_calculations.calculate_cdu_cost_per_pod(no_of_cdus_per_pod_redundant)
            cdu_total_capex = capex_calculations.calculate_total_cdu_cost(no_of_cdus_per_pod_redundant, num_pods)

            # Calculate number of CRAHs
            no_of_crahs_per_pod = helper.calculate_no_of_crahs_per_pod(air_cooling_capacity_per_pod)
            no_of_crahs_per_pod_redundant = no_of_crahs_per_pod + 1

            crah_capex_per_pod = capex_calculations.calculate_crah_cost_per_pod(no_of_crahs_per_pod_redundant)
            crah_total_capex = capex_calculations.calculate_total_crah_cost(no_of_crahs_per_pod_redundant, num_pods)

            air_ducting_total_capex = capex_calculations.calculate_total_air_ducting_cost(no_of_crahs_per_pod_redundant, num_pods)
            aisle_containment_total_capex = capex_calculations.calculate_total_aisle_containment_cost(total_no_of_racks)

            belimo_total_capex = capex_calculations.calculate_total_belimo_cost(no_of_belimos)
            DN20_valve_total_capex = capex_calculations.calculate_total_dn20_cost(no_of_DN20_valve)

            # Calculate Q per CRAH based on CDU type
            total_power_per_pod = cooling_capacities.calculate_power_per_pod(selected_pod_type)  
            total_power = self.calculate_total_power()
            q_per_crah = helper.calculate_q_per_crah(current_cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, no_of_crahs_per_pod)
            self.q_per_crah_label.text = f"Q per CRAH: {q_per_crah:.2f} kW"

            chilled_water_temperature_rise = helper.calculate_chilled_water_temperature_rise(fws_air_temp, self.dry_bulb)

            # Calculate chilled water flow rate per CRAH
            chilled_water_flow_rate_crah = helper.calculate_chilled_water_flow_rate_per_crah(q_per_crah, chilled_water_temperature_rise)

            # Calculate chilled water flow rate per POD
            chilled_water_flow_rate_pod = helper.calculate_chilled_water_flow_rate_per_pod(chilled_water_flow_rate_crah, no_of_crahs_per_pod)

            q_ac_per_pod = helper.calculate_q_ac_per_pod(current_cdu_type, air_cooling_capacity_per_pod, total_power_per_pod, num_pods)

            hp2_per_crah = self.calculate_crah_rpm_and_power(required_air_flow_rate_capacity_per_pod,no_of_crahs_per_pod)

            # Piping cost
            print("num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod", num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod)

            power_consumption = power_calculations.calculate_annual_power_consumption(num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah,no_of_cdus_per_pod, no_of_crahs_per_pod)

            if power_consumption:
                pw170_annual_power = power_consumption["pw170_power"]
                xdu1350_annual_power = power_consumption["xdu1350_power"]

            general_power = power_calculations.calculate_general_power_consumption(total_power_per_pod, num_pods, hp2_per_cdu, no_of_cdus_per_pod)
            if general_power:
                lighting_power = general_power['lighting_power']
                ups_it_loss_power = general_power['ups_it_loss_power']
                ups_mech_loss_power = general_power['ups_mech_loss_power']
                hvac_power = general_power['hvac_power']

             # Calculate IT power consumption
            it_power_yearly = power_calculations.calculate_annual_power_consumption(num_pods, total_power_per_pod, hp2_per_cdu, hp2_per_crah, no_of_cdus_per_pod, no_of_crahs_per_pod)["it_power"]
            air_chiller_power = power_calculations.calculate_air_cooling_power(dry_bulb,city_data , chillers_data ,fws_air_temp, no_of_equipments_air, air_cooling_capacity_per_pod, num_pods , model = selected_chiller)
            liquid_chiller_power = power_calculations.calculate_liquid_cooling_power(dry_bulb,city_data, chillers_data, dryer_data, fws_liquid_temp,no_of_equipments_liquid,no_of_equipments_liquid_dry_cooler,liquid_cooling_capacity_per_pod,num_pods,cooling_capacity_per_unit_dry_cooler, selected_chiller, selected_dryer, liquid_cooling_type = self.liquid_cooling_type_2)

            # Calculate power values for each category
            common_power = power_calculations.calculate_common_power_consumption(lighting_power, ups_it_loss_power, hvac_power, it_power_yearly)
            air_cooling_air_cooled, air_cooling_water_cooled = power_calculations.calculate_total_air_cooling_power(
                pw170_annual_power, air_chiller_power
            )
            liquid_cooling_air_cooled, liquid_cooling_water_cooled = power_calculations.calculate_total_liquid_cooling_power(
                ups_mech_loss_power, xdu1350_annual_power, liquid_chiller_power
            )

            # Calculate Total PUE
            total_pue = power_calculations.calculate_total_pue(it_power_yearly, common_power, air_cooling_air_cooled, liquid_cooling_air_cooled)

                    # Display results in Ui

            print("No of racks check",no_of_racks_gb200_per_pod)
            length_of_header_pipe = helper.calculate_length_of_pipe(no_of_racks_gb200_per_pod, num_pods)
            total_length_of_rack_outlet_inlet = helper.calculate_length_of_pipe_rack_outlet_inlet(no_of_racks_gb200)
            secondary_flowrate_per_cdu = flow_calculations.calculate_secondary_flowrate_per_cdu(required_liquid_flow_rate_per_pod, no_of_cdus_per_pod)
            tcs_liquid_flow_rate_gpm = round(secondary_flowrate_per_cdu / 3.7854)
            diameter_of_header_pipe = helper.calculate_diameter_of_pipe(tcs_liquid_flow_rate_gpm, fluid_piping_data)

            header_price_per_meter = helper.get_price_per_meter_pipe(diameter_of_header_pipe)
            insultaion_price_per_meter = 40
            piping_cost_header = helper.calculate_piping_cost(length_of_header_pipe, header_price_per_meter)
            piping_cost_insulation = helper.calculate_piping_cost(length_of_header_pipe, insultaion_price_per_meter)

            total_price_above_racks_piping = capex_calculations.calculate_above_racks_piping(no_of_racks_gb200)
            total_price_header_piping = capex_calculations.calculate_piping_cost(length_of_header_pipe, header_price_per_meter, piping_cost_header)
            total_price_insulation_piping = capex_calculations.calculate_piping_cost(length_of_header_pipe, insultaion_price_per_meter, piping_cost_insulation)
            total_cost_fittings = total_price_header_piping * 0.3

            # Leak detection
            no_of_spot_detectors = no_of_racks_gb200 * 3
            length_of_sensing_cable = no_of_racks_gb200 * 20
            no_of_LD2100_controller = num_pods
            total_cost_leak_detection = capex_calculations.calculate_leak_detection(no_of_LD2100_controller)

            # Coolant
            total_pg25_per_unit_rack_manifold = (3.14*(((constants.LIQUID_COOLING_PIPING_PER_POD["Rack Outlet/Inlet"]["Diameter"]/2) * 0.0254) ** 2)) * 264.17
            total_volume_pg25_rack_manifold = total_pg25_per_unit_rack_manifold * total_length_of_rack_outlet_inlet

            total_pg25_per_unit_header = (3.14 * (((diameter_of_header_pipe / 2) * 0.0254) ** 2)) * 264.17
            total_volume_pg25_header = total_pg25_per_unit_header * length_of_header_pipe
            total_volume_pg25_cdu = constants.LIQUID_CAPACITY_XDU1350 * no_of_cdus_per_pod_redundant * num_pods
            total_volume_pg_tank = (total_volume_pg25_cdu + total_volume_pg25_rack_manifold + total_volume_pg25_header) * 0.15

            total_pg25 = helper.calculate_total_pg25(total_volume_pg25_rack_manifold, total_volume_pg25_header, total_volume_pg25_cdu, total_volume_pg_tank)
            total_cost_pg25 = total_pg25 * constants.PG25_PRICE
            total_cost_comissioning = 5588.24 * no_of_racks_gb200
           
            # capex Air cooling
            total_cost_chiller_air_cooling = capex_calculations.calculate_chiller_air_cooling_cost(fws_liquid_temp,selected_chiller, no_of_chillers_air_cooling_redundant)
            total_cost_chiller_liquid_cooling = capex_calculations.calculate_chiller_liquid_cooling_cost(fws_liquid_temp,selected_chiller, no_of_chillers_liquid_cooling_redundant, no_of_dry_cooler_redundant, liquid_cooling_type = self.liquid_cooling_type_2 )

            # piping cooling loop
            total_chilled_water_flow_rate = chilled_water_flow_rate_pod * num_pods
            diameter_air_cooling_loop = helper.calculate_diameter_of_pipe(total_chilled_water_flow_rate,fluid_piping_data)
            length_of_air_cooling_loop = helper.calculate_length_of_air_cooling_loop(num_pods)
            air_cooling_loop_price_per_meter = helper.get_price_per_meter_pipe(diameter_air_cooling_loop)
            air_cooling_loop_plumbing_total_cost = helper.calculate_cooling_loop_cost(air_cooling_loop_price_per_meter, length_of_air_cooling_loop)
           
            total_secondary_flowrate = secondary_flowrate_per_cdu * num_pods
            diameter_liquid_cooling_loop = helper.calculate_diameter_of_pipe(total_secondary_flowrate, fluid_piping_data)
            length_of_liquid_cooling_loop = helper.calculate_length_of_liquid_cooling_loop(num_pods)
            liquid_cooling_loop_price_per_meter = helper.get_price_per_meter_pipe(diameter_liquid_cooling_loop)
            liquid_cooling_loop_plumbing_total_cost = helper.calculate_cooling_loop_cost(liquid_cooling_loop_price_per_meter, length_of_liquid_cooling_loop)
           
            # COMMON CAPEX
            bms_total_cost = constants.BMS_UNIT_PRICE * num_pods
            cm_bim_total_cost = constants.CM_BIM_UNIT_PRICE * num_pods
            fire_fighting_total = constants.FIRE_FIGHTING_PRICE * total_no_of_racks
            sum_common_capex = bms_total_cost + cm_bim_total_cost + fire_fighting_total
           
            sum_ac_air_cooled_chiller_capex = crah_total_capex + air_ducting_total_capex + aisle_containment_total_capex + total_cost_chiller_air_cooling + air_cooling_loop_plumbing_total_cost
            sum_ac_water_cooled_chiller_capex = crah_total_capex + air_ducting_total_capex + aisle_containment_total_capex + air_cooling_loop_plumbing_total_cost

            sum_lc_air_cooled_chiller_capex = cdu_total_capex + belimo_total_capex + DN20_valve_total_capex + total_price_above_racks_piping + total_price_header_piping + total_cost_fittings + total_price_insulation_piping + total_cost_leak_detection + total_cost_pg25 + total_cost_comissioning + total_cost_chiller_liquid_cooling + liquid_cooling_loop_plumbing_total_cost
            # Printing each component's value
            sum_lc_water_cooled_chiller_capex = cdu_total_capex + belimo_total_capex + DN20_valve_total_capex + total_price_above_racks_piping + total_price_header_piping + total_cost_fittings + total_price_insulation_piping + total_cost_leak_detection + total_cost_pg25 + total_cost_comissioning + liquid_cooling_loop_plumbing_total_cost

            # total capex calculations
            total_common_capex = capex_calculations.calculate_total_capex(sum_common_capex)
            total_ac_air_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_ac_air_cooled_chiller_capex)
            total_ac_water_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_ac_water_cooled_chiller_capex)
            total_lc_air_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_lc_air_cooled_chiller_capex)
            total_lc_water_cooled_chiller_capex = capex_calculations.calculate_total_capex(sum_lc_water_cooled_chiller_capex)

            self.plot_capex(total_common_capex,total_ac_air_cooled_chiller_capex,total_ac_water_cooled_chiller_capex,total_lc_air_cooled_chiller_capex,total_lc_water_cooled_chiller_capex, total_pue, selected_pod_type)

            # Opex_calculation ----------------
            print("Liquid chiller power, total_power", liquid_chiller_power, total_power)
            space_rent_opex_annual = total_power * constants.RENT_KW_MONTH * 12
            print(space_rent_opex_annual)
            space_rent_opex_nth_year = opex_calculations.calculate_nth_energy_cost(space_rent_opex_annual, num_years)
           
            annual_electricity_cost_ac_chiller = opex_calculations.calculate_elctrcity_cost_ac_chiller(air_chiller_power, electricity_price)
            annual_electricity_cost_lc = opex_calculations.calculate_elctrcity_cost_lc(liquid_chiller_power,electricity_price,liquid_cooling_type = self.liquid_cooling_type_2)
            ac_chiller_nth_year_cost = opex_calculations.calculate_nth_energy_cost(annual_electricity_cost_ac_chiller,num_years)
            lc_nth_year_cost = opex_calculations.calculate_nth_energy_cost(annual_electricity_cost_lc, num_years)

            ac_chiller_maintenance = opex_calculations.calculate_maintenance_for_air_cooling_chiller(total_cost_chiller_air_cooling)
            lc_maintenance = opex_calculations.calculate_maintanence_for_liquid_cooling_chiller(total_cost_chiller_liquid_cooling,liquid_cooling_type = self.liquid_cooling_type_2)
            ac_chiller_maintenance_nth_year = opex_calculations.calculate_nth_maintenance_cost(ac_chiller_maintenance, num_years)
            lc_maintenance_nth_year = opex_calculations.calculate_nth_maintenance_cost(lc_maintenance, num_years)
           
            # Calculating total volume for flushing
            total_flushing_volume = total_volume_pg25_cdu + total_pg25_per_unit_header + total_volume_pg25_rack_manifold
            # Calculating CDU flushing cost
            cdu_flushing_cost = opex_calculations.calculate_flushing_cost(total_volume=total_flushing_volume)
            # Calculating nth year cost for CDU flushing
            cdu_flushing_cost_nth_year = opex_calculations.calculate_nth_energy_cost(cdu_flushing_cost, num_years)
            # Calculating monitoring and sampling cost
            monitoring_sampling_cost = opex_calculations.calculate_monitoring_cost(num_pods)
            # Calculating nth year cost for monitoring and sampling
            monitoring_sampling_cost_nth_year = opex_calculations.calculate_nth_energy_cost(monitoring_sampling_cost, num_years)

            bms_opex_annual = opex_calculations.calculate_bms_opex(bms_total_cost)
            bms_opex_nth_year = opex_calculations.calculate_nth_energy_cost(bms_opex_annual, num_years)
            security_opex_annual = 0.1 * sum_common_capex
            security_opex_nth_year = opex_calculations.calculate_nth_energy_cost(security_opex_annual,num_years)
            fire_protection_opex_annual = 0.05 * fire_fighting_total
            fire_protection_opex_nth_year = opex_calculations.calculate_nth_energy_cost(fire_protection_opex_annual,num_years)
           
            it_opex_annual = it_power_yearly * electricity_price
            it_opex_nth_year = opex_calculations.calculate_nth_energy_cost(it_opex_annual,num_years)
            ups_it_loss_opex_annual = ups_it_loss_power * electricity_price
            ups_it_loss_opex_nth_year = opex_calculations.calculate_nth_energy_cost(ups_it_loss_opex_annual,num_years)
            lighting_opex_annual = lighting_power * electricity_price
            lighting_opex_nth_year = opex_calculations.calculate_nth_energy_cost(lighting_opex_annual,num_years)
            hvac_opex_annual = hvac_power * electricity_price
            hvac_opex_nth_year = opex_calculations.calculate_nth_energy_cost(hvac_opex_annual,num_years)
            cdu_opex_annual = xdu1350_annual_power * electricity_price
            print("xdu1350_annual_power, hp2", xdu1350_annual_power, hp2_per_cdu)
            cdu_opex_nth_year = opex_calculations.calculate_nth_energy_cost(cdu_opex_annual, num_years)
            ups_mech_loss_opex_annual = ups_mech_loss_power * electricity_price
            print("ups_mech_loss_power", ups_mech_loss_power)
            ups_mech_loss_opex_nth_year = opex_calculations.calculate_nth_energy_cost(ups_mech_loss_opex_annual, num_years)
            crah_opex_annual = pw170_annual_power * electricity_price
            print("pw170_annual_power", pw170_annual_power,hp2_per_crah)
            crah_opex_nth_year = opex_calculations.calculate_nth_energy_cost(crah_opex_annual, num_years)
            print(f"IT OpEx Annual: {it_opex_annual}, IT OpEx Nth Year: {it_opex_nth_year}, UPS IT Loss OpEx Annual: {ups_it_loss_opex_annual}, UPS IT Loss OpEx Nth Year: {ups_it_loss_opex_nth_year}, Lighting OpEx Annual: {lighting_opex_annual}, Lighting OpEx Nth Year: {lighting_opex_nth_year}, HVAC OpEx Annual: {hvac_opex_annual}, HVAC OpEx Nth Year: {hvac_opex_nth_year}, CDU OpEx Annual: {cdu_opex_annual}, CDU OpEx Nth Year: {cdu_opex_nth_year}, UPS Mech Loss OpEx Annual: {ups_mech_loss_opex_annual}, UPS Mech Loss OpEx Nth Year: {ups_mech_loss_opex_nth_year}, CRAH OpEx Annual: {crah_opex_annual}, CRAH OpEx Nth Year: {crah_opex_nth_year}")
            # final sum calculations
            total_common_opex_nth_year = space_rent_opex_nth_year + bms_opex_nth_year + security_opex_nth_year + fire_protection_opex_nth_year + it_opex_nth_year + ups_it_loss_opex_nth_year  + lighting_opex_nth_year + hvac_opex_nth_year
            total_ac_chiller_opex_nth_year = ac_chiller_nth_year_cost + ac_chiller_maintenance_nth_year + crah_opex_nth_year
            total_ac_water_chiller_opex_nth_year = crah_opex_nth_year
            total_lc_opex_nth_year = lc_nth_year_cost + lc_maintenance_nth_year +cdu_flushing_cost_nth_year + monitoring_sampling_cost_nth_year + cdu_opex_nth_year + ups_mech_loss_opex_nth_year
            total_lc_water_opex_nth_year = cdu_flushing_cost_nth_year + monitoring_sampling_cost_nth_year + cdu_opex_nth_year + ups_mech_loss_opex_nth_year
            print(f"Total Common OpEx: {total_common_opex_nth_year}"); print(f"Total AC Chiller OpEx: {total_ac_chiller_opex_nth_year}"); print(f"Total AC Water Chiller OpEx: {total_ac_water_chiller_opex_nth_year}"); print(f"Total LC OpEx: {total_lc_opex_nth_year}"); print(f"Total LC Water OpEx: {total_lc_water_opex_nth_year}"); print(f"Components: Space Rent: {space_rent_opex_nth_year}, BMS: {bms_opex_nth_year}, Security: {security_opex_nth_year}, Fire Protection: {fire_protection_opex_nth_year}, IT: {it_opex_nth_year}, UPS IT Loss: {ups_it_loss_opex_nth_year}, Lighting: {lighting_opex_nth_year}, HVAC: {hvac_opex_nth_year}, AC Chiller Cost: {ac_chiller_nth_year_cost}, AC Chiller Maintenance: {ac_chiller_maintenance_nth_year}, CRAH: {crah_opex_nth_year}, LC Cost: {lc_nth_year_cost}, LC Maintenance: {lc_maintenance_nth_year}, CDU Flushing: {cdu_flushing_cost_nth_year}, Monitoring Sampling: {monitoring_sampling_cost_nth_year}, CDU OpEx: {cdu_opex_nth_year}, UPS Mech Loss: {ups_mech_loss_opex_nth_year}")
            # self.total_common_opex_label.text = f"Total Common OpEx after {num_years} years: {total_common_opex_nth_year:.0f} $"
            # self.total_ac_chiller_opex_label.text = f"Total AC Chiller OpEx after {num_years} years: {total_ac_chiller_opex_nth_year:.0f} $"
            # self.total_ac_water_chiller_opex_label.text = f"Total AC Water Chiller OpEx after {num_years} years: {total_ac_water_chiller_opex_nth_year:.0f} $"
            # self.total_lc_opex_label.text = f"Total LC {self.liquid_cooling_type_1} OpEx after {num_years} years: {total_lc_opex_nth_year:.0f} $"
            # self.total_lc_water_opex_label.text = f"Total LC Water OpEx after {num_years} years: {total_lc_water_opex_nth_year:.0f} $"

            # CAPEX Dictionary
            capex_values = {
                "Common": total_common_capex,
                "AC Air Cooled": total_ac_air_cooled_chiller_capex,
                # "AC Water Cooled": total_ac_water_cooled_chiller_capex,
                "LC Air Cooled": total_lc_air_cooled_chiller_capex,
                # "LC Water Cooled": total_lc_water_cooled_chiller_capex,
            }

            # OPEX Dictionary
            opex_values = {
                "Common": total_common_opex_nth_year,
                "AC Chiller": total_ac_chiller_opex_nth_year,
                # "AC Water Chiller": total_ac_water_chiller_opex_nth_year,
                "LC": total_lc_opex_nth_year,
                # "LC Water": total_lc_water_opex_nth_year,
            }
            self.capex_data_2 = capex_values
            self.opex_data_2 = opex_values

            # Example Function Call
            # self.plot_opex(total_common_opex_nth_year, total_ac_chiller_opex_nth_year, total_ac_water_chiller_opex_nth_year, total_lc_opex_nth_year, total_lc_water_opex_nth_year, num_years, total_pue, selected_pod_type)

        except ValueError:
            self.total_power_label.text = "Enter a valid number of pods."

        except Exception as e:
            print(f"Error in update_calculations: {e}")

    def calculate_airflow_rate_per_pod(self, air_supply_temp):
        """Calculate and return required airflow rate per pod (CFM) based on the selected air supply temperature."""
        try:
            # Calculate air flow rate for the primary rack (GB200_NVL72) based on air supply temperature
            air_flow_rate_per_rack_gb200 = flow_calculations.calculate_air_flow_rate_per_rack("GB200_NVL72", air_supply_temp)

            # Retrieve rack counts for the selected pod type
            selected_pod_type, rack_counts = self.get_selected_pod_info()
            print("Air_flow_rate_per_rack",air_flow_rate_per_rack_gb200)
            print("No of racks", rack_counts.get("GB200_NVL72", 0))
            no_of_racks_gb200 = rack_counts.get("GB200_NVL72", 0)
            no_of_racks_management = rack_counts.get("Management",0)
            no_of_racks_networking = rack_counts.get("Networking", 0)
            GB200_flow_rate = air_flow_rate_per_rack_gb200 * no_of_racks_gb200
            Management_rack_flow_rate = constants.AIR_FLOW_RATE_MANAGEMENT_RACK * no_of_racks_management
            Networking_rack_flow_rate = constants.AIR_FLOW_RATE_NETWORK_RACK * no_of_racks_networking

            # Calculate the total required airflow rate per pod
            required_airflow_rate_per_pod = (
                GB200_flow_rate +
                Management_rack_flow_rate +
                Networking_rack_flow_rate
            )

            return (required_airflow_rate_per_pod * 1.05)
        except Exception as e:
            print(f"Error calculating airflow rate per pod: {str(e)}")
            return None


    def calculate_liquid_flow_rate_per_pod(self):
        """Calculate and return required liquid flow rate per pod (LPM)."""
        tcs_liquid_temp = self.get_selected_tcs_liquid_temperature()
        liquid_flow_rate_per_rack_gb200 = flow_calculations.calculate_liquid_flow_rate_per_rack(tcs_liquid_temp)
        selected_pod_type, rack_counts = self.get_selected_pod_info()

        required_liquid_flow_rate_per_pod = liquid_flow_rate_per_rack_gb200 * rack_counts.get("GB200_NVL72", 0)
        return required_liquid_flow_rate_per_pod


    def calculate_primary_and_secondary_flowrates(self, total_cdus, required_liquid_flow_rate_per_pod):
        """Calculate and update primary and secondary flow rates per CDU and per Pod in the UI."""
        if total_cdus is None:
            print("Error: Total CDUs not calculated.")
            return

        # Secondary flow rate per CDU
        secondary_flowrate_per_cdu = flow_calculations.calculate_secondary_flowrate_per_cdu(required_liquid_flow_rate_per_pod, total_cdus)
        # self.secondary_flow_rate_per_cdu_label.text = f"Secondary Flowrate per CDU (LPM): {secondary_flowrate_per_cdu:.2f}"

        # Primary flow rate per CDU and per Pod
        q_per_cdu = flow_calculations.calculate_q_per_cdu(cooling_capacities.calculate_total_liquid_cooling_capacity(self.get_selected_pod_info()[0]), total_cdus)

        primary_flow_rate_per_cdu = flow_calculations.calculate_primary_flow_rate_per_cdu(q_per_cdu)

        # self.primary_flow_rate_per_cdu_label.text = f"Primary Flow Rate per CDU (LPM): {primary_flow_rate_per_cdu:.2f}"

        primary_flow_rate_per_pod = flow_calculations.calculate_primary_flow_rate_per_pod(primary_flow_rate_per_cdu, total_cdus)
        # self.primary_flow_rate_per_pod_label.text = f"Primary Flow Rate per POD (LPM): {primary_flow_rate_per_pod:.2f}"

    ### Helper Methods

    def get_selected_air_supply_temperature(self):
        """Retrieve selected air supply temperature."""
        air_supply_index = self.air_supply_menu.model.get_item_value_model().as_int
        return int(self.air_supply_options[air_supply_index])

    def get_selected_tcs_liquid_temperature(self):
        """Retrieve selected TCS liquid temperature."""
        tcs_liquid_index = self.tcs_liquid_menu.model.get_item_value_model().as_int
        return int(self.tcs_liquid_options[tcs_liquid_index])

    def get_selected_fws_design_air_temperature(self):
        fws_air_index = self.fws_air_menu.model.get_item_value_model().as_int
        return int(self.fws_air_options[fws_air_index])

    def get_selected_fws_design_liquid_temperature(self):
        fws_liquid_index = self.fws_liquid_menu.model.get_item_value_model().as_int
        return int(self.fws_air_options[fws_liquid_index])
    def get_selected_pod_info(self):
        """Retrieve selected pod type and rack counts for the selected pod configuration."""
        selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
        rack_counts = constants.POD_RACK_COUNTS.get(selected_pod_type, {})
        return selected_pod_type, rack_counts

    def update_pod_flowrate_and_curve(self, selected_pod_type, total_cdus, required_liquid_flow_rate_per_pod):
        """Calculate POD flowrate per CDU using existing total CDUs and log QSC coefficients."""
        try:
            # Calculate POD flow rate per CDU
            POD_flowrate_CDU = required_liquid_flow_rate_per_pod / total_cdus
            print("In function : selected_pod_type, total_cdus, required_liquid_flow_rate_per_pod", selected_pod_type, total_cdus, required_liquid_flow_rate_per_pod)
            # Update the UI label with calculated POD Flow Rate per CDU
            self.pod_flowrate_cdu_label.text = f"POD Flow Rate per CDU: {POD_flowrate_CDU:.2f} LPM"

            # Optionally: Log QSC data for internal debugging
            if selected_pod_type in constants.QSC_COEFFICIENTS and total_cdus in constants.QSC_COEFFICIENTS[selected_pod_type]:
                qsc_coefficients = constants.QSC_COEFFICIENTS[selected_pod_type][total_cdus]
                qsc_a, qsc_b, qsc_c = qsc_coefficients["a"], qsc_coefficients["b"], qsc_coefficients["c"]

                                # Calculate QES coefficients
                qes_a = constants.XDU_PQC["a"] - qsc_a
                qes_b = constants.XDU_PQC["b"] - qsc_b
                qes_c = constants.XDU_PQC["c"] - qsc_c

                                # Calculate roots of the quadratic equation
                root1, root2 = helper.calculate_roots(qes_a, qes_b, qes_c)
                                # Calculate flowrate1 as the maximum of root1 and root2
                flowrate1 = max(root1, root2)

                                # Calculate dp1 and dp2
                dp1 = helper.calculate_dp(qsc_coefficients, flowrate1)
                dp2 = helper.calculate_dp(qsc_coefficients, POD_flowrate_CDU)

                                # Calculate rpm2 and HP2
                rpm2 = math.sqrt(dp2 / dp1) * (constants.rpm1 ** 2)
                hp2 = ((rpm2 / constants.rpm1) ** 3) * constants.HP1
                hp_per_pod = hp2 * total_cdus

                                # Display HP2 and HP per pod in the UI
               
                self.cdu_hp2_label.text = f"HP2 (kW): {hp2:.2f}"
                self.cdu_hp_per_pod_label.text = f"HP per Pod: {hp_per_pod:.2f}"
                return hp2

        except Exception as e:
            print(f"Error in update_pod_flowrate_and_curve: {e}")


    def calculate_crah_rpm_and_power(self,required_airflow_rate_capacity_per_pod, no_of_crahs_per_pod):
        try:
            # Calculate CFM2
            CFM2 = required_airflow_rate_capacity_per_pod / no_of_crahs_per_pod
            print(f"Calculated CFM2: {CFM2} CFM")

            # Calculate RPM2% using the defined RPM1_PERCENT constant
            RPM2_percent = (CFM2 / constants.CFM1) * constants.RPM1_PERCENT
            print(f"Calculated RPM2%: {RPM2_percent}")
            HP1_per_CRAH = constants.HP1_PER_CRAH

            # Calculate HP2_per_crah using the constants
            HP2_per_crah = ((RPM2_percent / constants.RPM1_PERCENT) ** 3) * constants.HP1_PER_CRAH

            # Display the results in the UI if labels are set up for them
            self.crah_hp2_label.text = f"HP2 per CRAH: {HP2_per_crah:.2f}"
            self.crah_hp1_label.text = f"HP1 per CRAH: {HP1_per_CRAH:.2f}"
            return HP2_per_crah
        except Exception as e:

            print(f"Error calculating CRAH RPM and power: {e}")

    def on_fws_air_temp_changed(self, model):
        # Set fws_design_temperature_air based on ComboBox selection and check to display PUE
        self.fws_design_temperature_air = int(model.as_int)
        self.display_pue_chart_if_ready()

    def on_fws_liquid_temp_changed(self, model):
        # Set fws_design_temperature_liquid based on ComboBox selection and check to display PUE
        self.fws_design_temperature_liquid = int(model.as_int)
        self.display_pue_chart_if_ready()

    def display_pue_chart_if_ready(self):
        # Display PUE chart if both temps are set and visible in a separate window
        if self.fws_design_temperature_air is not None and self.fws_design_temperature_liquid is not None:
            self.should_display_pue_chart = True
            self._pue_chart_window.visible = True  # Show the PUE chart window
            self._capex_chart_window.visible = True
            self._opex_chart_window.visible = True
            self.calculate_monthly_power_consumption()
        else:
            self.should_display_pue_chart = False
            self._pue_chart_window.visible = False
            self.should_display_capex_chart = False
            self._capex_chart_window.visible = False
            self._opex_chart_window.visible = True

    def calculate_monthly_power_consumption(self):
        num_pods = int(self.num_pods_field.model.get_value_as_string())
        fws_air_temp = self.get_selected_fws_design_air_temperature()
        fws_liquid_temp = self.get_selected_fws_design_liquid_temperature()
        dry_bulb = int(self.dry_bulb)
        monthly_power_data = {}  # Dictionary to store power data per month
        total_hours_in_month = constants.HOURS_IN_MONTH  # 730, as defined in the extension
         # Calculate IT power for each month for the selected pod configuration
        selected_pod_type = self.pod_options[self.pod_menu.model.get_item_value_model().as_int]
        air_cooling_capacity_per_pod = cooling_capacities.calculate_total_air_cooling_capacity(selected_pod_type)
        liquid_cooling_capacity_per_pod = cooling_capacities.calculate_total_liquid_cooling_capacity(selected_pod_type)
        num_pods = int(self.num_pods_field.model.get_value_as_string())
        it_power_per_pod = cooling_capacities.calculate_power_per_pod(selected_pod_type)
        chillers_data = self.chillers_data
        selected_chiller = self.chiller_options[self.chiller_menu.model.get_item_value_model().as_int]
        selected_dryer = self.dryer_options[self.dryer_menu.model.get_item_value_model().as_int]
        equipment_capacity_chillers = helper.get_equipment_capacity_chiller(chillers_data, dry_bulb, fws_air_temp, model = "Vertiv 1MW")
        no_of_equipments_air, cooling_capacity_per_unit_air_chiller = self.get_number_of_equipments_air_cooling(fws_air_temp, air_cooling_capacity_per_pod,num_pods,selected_chiller)
        no_of_equipments_liquid, cooling_capacity_per_unit_liquid_chiller = self.get_number_of_equipments_liquid_cooling(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_chiller)
        no_of_equipments_liquid_dry_cooler , cooling_capacity_per_unit_dry_cooler = self.get_number_of_equipments_liquid_cooling_dry_cooler(fws_liquid_temp, liquid_cooling_capacity_per_pod, num_pods, selected_dryer)
        selected_city = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
        city_data = self.city_data.get(selected_city)
       
        dryer_data = self.dryer_data
        it_power = it_power_per_pod * num_pods * total_hours_in_month
        xdu1350_power = constants.POWER_PER_POD["XDU1350"]
        liquid_cooling_type = self.liquid_cooling_type


        lighting_power = constants.PERCENTAGE["Lighting"] * it_power_per_pod * total_hours_in_month * num_pods
        ups_it_loss_power = constants.PERCENTAGE["UPS IT Loss"] * it_power_per_pod * total_hours_in_month * num_pods
        ups_mech_loss_power = constants.PERCENTAGE["UPS Mechanical Loss"] * xdu1350_power * constants.UNITS_PER_POD_XDU1350 * total_hours_in_month * num_pods
        hvac_power = constants.PERCENTAGE["HVAC"] * it_power_per_pod * total_hours_in_month * num_pods

        pw170_monthly_power = constants.POWER_PER_POD["PW170"] * constants.UNITS_PER_POD_PW170 * num_pods *total_hours_in_month
        xdu1350_monthly_power = constants.POWER_PER_POD["XDU1350"] * constants.UNITS_PER_POD_XDU1350 * total_hours_in_month * num_pods

        monthly_air_cooling_power = monthly_calculation.calculate_monthly_air_chiller_power(city_data, chillers_data, fws_air_temp, no_of_equipments_air,air_cooling_capacity_per_pod,num_pods, selected_chiller)
        monthly_liquid_cooling_power = monthly_calculation.calculate_monthly_liquid_chiller_power(city_data, chillers_data, dryer_data, fws_liquid_temp, no_of_equipments_liquid,no_of_equipments_liquid_dry_cooler,liquid_cooling_capacity_per_pod, num_pods, cooling_capacity_per_unit_dry_cooler, liquid_cooling_type, selected_chiller, selected_dryer)
        monthly_pue_values = []

        # Define the list of months matching your column names in `dallas_dry_bulb`
        month_columns = [
            "Hours in Jan", "Hours in Feb", "Hours in March", "Hours in April",
            "Hours in May", "Hours in June", "Hours in July", "Hours in August",
            "Hours in Sep", "Hours in Oct", "Hours in Nov", "Hours in Dec"
        ]

        for month_col in month_columns:  # Loop through the month columns directly

            # Calculate common power for the month
            common_power = monthly_calculation.calculate_monthly_common_power(lighting_power, ups_it_loss_power, hvac_power, it_power)

            # Calculate air cooling power consumption
            air_cooling_air_cooled, air_cooling_water_cooled = monthly_calculation.calculate_total_monthly_air_cooling_power(
                pw170_monthly_power, int(monthly_air_cooling_power[month_col])
            )

            # Calculate liquid cooling power consumption
            liquid_cooling_air_cooled, liquid_cooling_water_cooled = monthly_calculation.calculate_total_monthly_liquid_cooling_power(
                ups_mech_loss_power, xdu1350_monthly_power, int(monthly_liquid_cooling_power[month_col])
            )
            monthly_pue = monthly_calculation.calculate_monthly_pue( common_power, air_cooling_air_cooled, liquid_cooling_air_cooled, it_power)

            # Store monthly results with the exact column name (e.g., "Hours in Jan")
            monthly_power_data[month_col] = {
                "common_power": common_power,
                "air_cooling_air_cooled": air_cooling_air_cooled,
                "air_cooling_water_cooled": air_cooling_water_cooled,
                "liquid_cooling_air_cooled": liquid_cooling_air_cooled,
                "liquid_cooling_water_cooled": liquid_cooling_water_cooled,
                "monthly_pue": monthly_pue
            }
        print(monthly_power_data)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_pue_values = [data["monthly_pue"] for data in monthly_power_data.values()]

        self.plot_monthly_pue(month_names, monthly_pue_values)

        return monthly_power_data

    # Generic Toggle Handler
    def toggle_chart(self, chart_window, toggle_switch, model):
        """Toggle visibility of a chart and update the button color."""
        try:
            is_active = model.as_bool
            chart_window.visible = is_active
            print(f"Chart visibility set to: {is_active}")
        except Exception as e:
            print(f"Error toggling chart: {e}")

    def plot_monthly_pue(self, month_names, monthly_pue_values):
        # Ensure the PUE chart window is visible
        self._pue_chart_window.visible = True
        # Extract main city name without suffix (e.g., "Dublin" from "Dublin AP")
    # Get selected city’s full name and retrieve simplified name from mapping
        city_name_map = constants.city_name_map

        selected_city_full = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
        main_city_name = city_name_map.get(selected_city_full, selected_city_full)  # Default to full name if no mapping
        # Clear previous content from container
        self.pue_chart_container.clear()
        normal_style = {"font_size": 23, "color": cl("#FFFFFF")}  # Normal style
        hover_style = {"font_size": 25, "color": cl("#FFFFFF")}  # Hover style

        # Fetch Liquid Cooling Option and Dry Bulb temperature
        liquid_cooling_option = self.liquid_cooling_type
        air_cooling_option = "Chiller"
        dry_bulb = self.dry_bulb  # Ensure self.dry_bulb is updated before calling this function
        total_pue = sum(monthly_pue_values) / len(monthly_pue_values)

        # Fetch the window width for dynamic scaling
        window_width = self._pue_chart_window.width
        bar_width = max(20, window_width // (len(month_names) * 2))  # Calculate bar width dynamically
        spacing = max(2, window_width // 100)  # Dynamic spacing based on window width

        # Define the base height for a PUE of 1.0
        base_height = 30  # Starting height

        def calculate_bar_height(pue):
            """Calculate bar height based on tiered increments."""
            if 1.0 <= pue < 1.1:
                increment = 10
                height = base_height + ((pue - 1.0) * 10 * increment)
            elif 1.1 <= pue < 1.2:
                increment = 70
                height = base_height + (1 * 20) + ((pue - 1.1) * 10 * increment)
            elif 1.2 <= pue < 1.3:
                increment = 90
                height = base_height + (1 * 20) + (1 * 70) + ((pue - 1.2) * 10 * increment)
            else:
                increment = 90
                height = base_height + (1 * 20) + (1 * 70) + (1 * 90) + ((pue - 1.3) * 10 * increment)
            return height
       

            # Function to create a label with hover effect
        def create_hover_label(text):
            label = ui.Label(text, style=normal_style, alignment=ui.Alignment.LEFT)

            # Define the hover function to apply the hover style
            def on_hover(is_hovered):
                label.style = hover_style if is_hovered else normal_style

            # Set the hover function using set_mouse_hovered_fn
            label.set_mouse_hovered_fn(on_hover)

            return label
        # Render the PUE chart within the container
        with self.pue_chart_container:
            with ui.VStack(style=self.STYLES["main_container"], spacing=5):
                # Display the main title with the stripped city name
                ui.Label(f"{main_city_name}'s Monthly PUE Overview", style=self.STYLES["title"], alignment=ui.Alignment.CENTER)

                # Monthly PUE bar chart rendering
                with ui.HStack(spacing=5):
                    for month, pue in zip(month_names, monthly_pue_values):
                        with ui.VStack(alignment=ui.Alignment.CENTER):
                            # Display the PUE value label above each bar
                            ui.Label(f"{pue:.2f}", style=self.STYLES["highlight_label"], alignment=ui.Alignment.CENTER)

                            # Calculate bar height based on PUE value with tiered increments
                            bar_height = calculate_bar_height(pue)
                            bar_color = cl("#1dca3a")  # Consistent color

                            # Render the bar with fixed width and calculated height
                            ui.Rectangle(width=bar_width, height=bar_height, style={"background_color": bar_color})

                # Month labels below bars
                with ui.HStack(spacing=spacing, alignment=ui.Alignment.CENTER):
                    for month in month_names:
                        ui.Label(month, style=self.STYLES["label"], alignment=ui.Alignment.CENTER)

                # Add labels for Liquid Cooling Option and Dry Bulb temperature below the month labels
                ui.Spacer(height=spacing)  # Add some spacing between month labels and info labels
                with ui.VStack():
            # Labels with hover effects
                    create_hover_label(f"Annual PUE: {total_pue:.2f}")
                    create_hover_label(f"Dry Bulb Temperature: {dry_bulb} °C")
                    create_hover_label(f"Liquid Cooling Facility: {liquid_cooling_option}")
                    create_hover_label(f"Air Cooling Facility: {air_cooling_option}")

    def plot_capex(self, total_common_capex, total_ac_air_cooled_chiller_capex,total_ac_water_cooled_chiller_capex, total_lc_air_cooled_chiller_capex,
                total_lc_water_cooled_chiller_capex, total_pue, selected_pod_type):
        """Render a CAPEX bar chart with hover labels, tiered bar heights, and colored bars with a legend."""
        # Create the chart and legend containers side by side
        city_name_map = constants.city_name_map
        selected_city_full = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
        main_city_name = city_name_map.get(selected_city_full, selected_city_full)
        normal_style = {"font_size": 20, "color": cl("#FFFFFF")}  # Normal style
        hover_style = {"font_size": 22, "color": cl("#FFFFFF")}
        with self._capex_chart_window.frame:
            with ui.HStack():
                # Left side - Chart container
                with ui.VStack(width=ui.Fraction(0.6)):  # Takes 70% of the width
                    self.capex_chart_container = ui.VStack()
               
                # Right side - Legend container
                with ui.VStack(width=ui.Fraction(0.4)):  # Takes 30% of the width
                    self.legend_container = ui.VStack()
                   
        # Ensure the CAPEX chart window is visible
        self._capex_chart_window.visible = True

        # Clear previous content from both containers
        self.capex_chart_container.clear()
        self.legend_container.clear()

        # Calculate total CAPEX
        total_capex = total_common_capex + total_ac_air_cooled_chiller_capex + total_lc_air_cooled_chiller_capex

        # Define CAPEX categories and values
        capex_categories = ["Total Common CAPEX", "CAPEX Air Cooling", "CAPEX Liquid Cooling"]
        capex_values = [total_common_capex, total_ac_air_cooled_chiller_capex, total_lc_air_cooled_chiller_capex]
        abbreviations = ["Common", "Air Cooling", "Liquid Cooling"]
       
        # Define colors for each category
        capex_colors = [
            cl("#b2e061"),  # Light green for Common
            cl("#bd7ebe"),  # Purple for AC
            cl("#ffee65")   # Yellow for LC
        ]

        # Render the chart in the left container
        with self.capex_chart_container:
            with ui.VStack(style=self.STYLES["main_container"], spacing=5):
                # Chart Title
                ui.Label("CAPEX Overview", style=self.STYLES["title"],
                        alignment=ui.Alignment.CENTER)
               
                # CAPEX bars
                with ui.HStack(spacing=10, alignment=ui.Alignment.CENTER):
                    for value, color in zip(capex_values, capex_colors):
                        with ui.VStack(alignment=ui.Alignment.CENTER):
                            # Value label
                            formatted_value = helper.format_large_number(value)
                            ui.Label(f"${formatted_value}",
                                style=self.STYLES["highlight_label"],
                                alignment=ui.Alignment.CENTER)
                           
                            # Bar
                            bar_height = helper.calculate_bar_height_capex(value)
                            ui.Rectangle(width=20, height=bar_height,
                                    style={"background_color": color})
               
                # Category labels
                with ui.HStack(spacing=10, alignment=ui.Alignment.LEFT):
                    for abbr in abbreviations:
                        ui.Label(abbr, style=self.STYLES["label"],
                            alignment=ui.Alignment.LEFT)
               
            # Function to create a label with hover effect
            def create_hover_label(text):
                label = ui.Label(text, style=normal_style, alignment=ui.Alignment.LEFT)
                # Define the hover function to apply the hover style
                def on_hover(is_hovered):
                    label.style = hover_style if is_hovered else normal_style
                # Set the hover function using set_mouse_hovered_fn
                label.set_mouse_hovered_fn(on_hover)

                return label

        # Render the legend and summary in the right container
        with self.legend_container:
            with ui.VStack(width=ui.Fraction(1), height=ui.Fraction(1), spacing=5): # Use HStack to divide horizontally
                # Legend section with 30% width
                with ui.VStack(height=ui.Fraction(0.3), style=self.STYLES["main_container"], spacing=5):
                    ui.Label("Legend", style=self.STYLES["title"], alignment=ui.Alignment.LEFT)
                    for category, color in zip(capex_categories, capex_colors):
                        with ui.HStack(spacing=5):
                            ui.Rectangle(width=20, height=20, style={"background_color": color})
                            ui.Label(f"{category}", style=self.STYLES["label"], alignment=ui.Alignment.LEFT)

                # Summary section with 70% width
                with ui.VStack(height=ui.Fraction(0.7), style=self.STYLES["main_container"], spacing=5):
                    ui.Label("Summary", style=self.STYLES["title"], alignment=ui.Alignment.LEFT)
                    create_hover_label(f"City : {main_city_name}")
                    create_hover_label(f"Annual PUE : {total_pue:.2f}")
                    create_hover_label(f"Liquid Cooling Facility : {self.liquid_cooling_type}")
                    create_hover_label(f"POD type: {selected_pod_type}")
                    create_hover_label(f"Total CAPEX: ${helper.format_large_number(total_capex)}")
                    for category, value in zip(capex_categories, capex_values):
                        create_hover_label(f"{category}: ${helper.format_large_number(value)}")
                   
    def plot_opex(self, total_common_opex_nth_year, total_ac_chiller_opex_nth_year,
                total_ac_water_chiller_opex_nth_year, total_lc_opex_nth_year,
                total_lc_water_opex_nth_year, num_years, total_pue, selected_pod_type):
        """Render an OPEX bar chart with hover labels, tiered bar heights, and colored bars with a legend."""
        # Create the chart and legend containers side by side
        city_name_map = constants.city_name_map
        selected_city_full = self.unique_cities[self.city_menu.model.get_item_value_model().as_int]
        main_city_name = city_name_map.get(selected_city_full, selected_city_full)
        normal_style = {"font_size": 20, "color": cl("#FFFFFF")}  # Normal style
        hover_style = {"font_size": 22, "color": cl("#FFFFFF")}
        with self._opex_chart_window.frame:
            with ui.HStack():
                # Left side - Chart container
                with ui.VStack(width=ui.Fraction(0.6)):  # Takes 70% of the width
                    self.opex_chart_container = ui.VStack()
               
                # Right side - Legend container
                with ui.VStack(width=ui.Fraction(0.4)):  # Takes 30% of the width
                    self.legend_container = ui.VStack()

        # Ensure the OPEX chart window is visible
        self._opex_chart_window.visible = True

        # Clear previous content from both containers
        self.opex_chart_container.clear()
        self.legend_container.clear()

        # Dynamic naming for LC OPEX
        lc_air_cooled_word = "Dry Cooler" if self.liquid_cooling_type == "Dry Cooler" else "Air Cooled Chiller"
        lc_air_cooled_abbr = "LCD" if self.liquid_cooling_type == "Dry Cooler" else "LCA"

        # Calculate total OPEX
        total_opex = (total_common_opex_nth_year +
                    total_ac_chiller_opex_nth_year +
                    total_lc_opex_nth_year)

        # Define OPEX categories and values
        opex_categories = [
            "Total Common OPEX",
            "OPEX Air Cooling",
            "OPEX Liquid Cooling"
        ]
        opex_values = [
            total_common_opex_nth_year,
            total_ac_chiller_opex_nth_year,
            total_lc_opex_nth_year
        ]
        abbreviations = ["Common", "Air Cooling", "Liquid Cooling"]
       
        # Define colors for each category
        opex_colors = [
            cl("#b2e061"),  # Orange for Common
            cl("#bd7ebe"),  # Red for AC
            cl("#ffee65")   # Teal for LC
        ]

                # Function to create a label with hover effect
        def create_hover_label(text):
            label = ui.Label(text, style=normal_style, alignment=ui.Alignment.LEFT)

            # Define the hover function to apply the hover style
            def on_hover(is_hovered):
                label.style = hover_style if is_hovered else normal_style

            # Set the hover function using set_mouse_hovered_fn
            label.set_mouse_hovered_fn(on_hover)

            return label

        # Calculate dynamic bar heights
        max_value = max(opex_values) if opex_values else 1
        def calculate_bar_height(value):
            """Calculate bar height proportionally to the max value."""
            return (value / max_value) * 300  # max_bar_height = 400

        # Render the chart in the left container
        with self.opex_chart_container:
            with ui.VStack(style=self.STYLES["main_container"], spacing=5):
                # Chart Title
                ui.Label(f"OPEX for {num_years} years",
                        style=self.STYLES["title"],
                        alignment=ui.Alignment.CENTER)
               
                # OPEX bars
                with ui.HStack(spacing=10, alignment=ui.Alignment.CENTER):
                    for value, color in zip(opex_values, opex_colors):
                        with ui.VStack(alignment=ui.Alignment.CENTER):
                            # Value label
                            formatted_value = helper.format_large_number(value)
                            ui.Label(f"${formatted_value}",
                                style=self.STYLES["highlight_label"],
                                alignment=ui.Alignment.CENTER)
                           
                            # Bar
                            bar_height = calculate_bar_height(value)
                            ui.Rectangle(width=20, height=bar_height,
                                    style={"background_color": color})
               
                # Category labels
                with ui.HStack(spacing=10, alignment=ui.Alignment.LEFT):
                    for abbr in abbreviations:
                        ui.Label(abbr, style=self.STYLES["label"],
                            alignment=ui.Alignment.LEFT)

        # Render the legend and summary in the right container
        with self.legend_container:
            with ui.VStack(width=ui.Fraction(1), height=ui.Fraction(1), spacing=5): # Use HStack to divide horizontally
                # Legend section with 30% width
                with ui.VStack(height=ui.Fraction(0.3), style=self.STYLES["main_container"], spacing=5):
                    ui.Label("Legend", style=self.STYLES["title"], alignment=ui.Alignment.CENTER)
                    for category, color in zip(opex_categories, opex_colors):
                        with ui.HStack(spacing=5):
                            ui.Rectangle(width=20, height=20, style={"background_color": color})
                            ui.Label(f": {category}", style=self.STYLES["label"], alignment=ui.Alignment.LEFT)

                # Summary section with 70% width
                with ui.VStack(height=ui.Fraction(0.7), style=self.STYLES["main_container"], spacing=5):
                    ui.Label("Summary", style=self.STYLES["title"], alignment=ui.Alignment.CENTER)
                    create_hover_label(f"City : {main_city_name}")
                    create_hover_label(f"Annual PUE : {total_pue:.2f}")
                    create_hover_label(f"Liquid Cooling Facility : {self.liquid_cooling_type}")
                    create_hover_label(f"POD type: {selected_pod_type}")
                    create_hover_label(f"Total OPEX: ${helper.format_large_number(total_opex)}")
                    for category, value in zip(opex_categories, opex_values):
                        create_hover_label(f"{category}: ${helper.format_large_number(value)}")

    def plot_capex_comparison(self):
        """
        Render a CAPEX chart with horizontally stacked bars for three scenarios.
        Assumes self.capex_data, self.capex_data_1, and self.capex_data_2 contain
        the CAPEX values for scenarios 1, 2, and 3 respectively.
        """
        # Combine CAPEX data from all scenarios
        combined_capex_data = {}
        for category in self.capex_data:
            combined_capex_data[category] = [
                self.capex_data.get(category, 0),   # Scenario 1
                self.capex_data_1.get(category, 0), # Scenario 2
                self.capex_data_2.get(category, 0)  # Scenario 3
            ]

        # Calculate the maximum value for scaling bar widths
        max_value = max(max(values) for values in combined_capex_data.values()) if combined_capex_data else 1

        # Define colors for scenarios
        scenario_colors = [cl("#1f77b4"), cl("#ff7f0e"), cl("#2ca02c")]  # Blue, Orange, Green
        scenario_names = ["Scenario 1", "Scenario 2", "Scenario 3"]

        # Ensure the CAPEX chart window is visible
        self._capex_chart_window.visible = True

        # Clear the chart container
        self.capex_chart_container.clear()

        # Render the chart
        with self.capex_chart_container:
            with ui.VStack(style=self.STYLES["main_container"], spacing=20):
                # Chart Title
                ui.Label("CAPEX Comparison Across Scenarios", style=self.STYLES["title"], alignment=ui.Alignment.CENTER)

                # Categories and their bars
                for category, values in combined_capex_data.items():
                    with ui.VStack(spacing=5):
                        # Category Label
                        ui.Label(category, style=self.STYLES["highlight_label"], alignment=ui.Alignment.LEFT)

                        # Render the horizontally stacked bars for this category
                        with ui.HStack(spacing=10, alignment=ui.Alignment.LEFT):
                            for value, color in zip(values, scenario_colors):
                                bar_width = (value / max_value) * 400  # Scale to a max width of 400
                                ui.Rectangle(width=bar_width, height=30, style={"background_color": color})

                # Legend for Scenarios
                with ui.VStack(spacing=10, alignment=ui.Alignment.LEFT):
                    ui.Label("Legend", style=self.STYLES["title"], alignment=ui.Alignment.LEFT)
                    for name, color in zip(scenario_names, scenario_colors):
                        with ui.HStack(spacing=5):
                            ui.Rectangle(width=20, height=20, style={"background_color": color})
                            ui.Label(name, style=self.STYLES["label"], alignment=ui.Alignment.LEFT)


    def show_capex_comparison(self):
        """
        Handle the button click to display the CAPEX comparison chart.
        """
        try:
            # Hide other charts (optional)
            self._pue_chart_window.visible = False
            self._opex_chart_window.visible = False

            # Render the CAPEX comparison chart
            self.plot_capex_comparison()

            # Ensure the CAPEX chart window is visible
            self._capex_chart_window.visible = True
            print("CAPEX comparison chart displayed.")
        except Exception as e:
            print(f"Error displaying CAPEX comparison chart: {e}")


    def _clear_labels(self):
        self.country_label.text = "Country: N/A"
        self.state_label.text = "State: N/A"
        self.dry_bulb_label.text = "Dry Bulb: N/A"
        self.wet_bulb_label.text = "Wet Bulb: N/A"
        self.dew_point_label.text = "Dew Point: N/A"
        self.humidity_ratio_label.text = "Humidity Ratio: N/A"

    def on_shutdown(self):
        print("My Extension is shutting down")