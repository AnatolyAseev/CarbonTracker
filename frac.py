"""This python script consists of Frac class, which gets variables and constatnts of fracking components and estimates
CO2 emissions from one frack job. Currently available frack components for calculating overall emissions are:

primeMover - emissions associated with machinery that takes care of job on the site, e.g. pumps, blenders, etc.
sandMining - emissions associated with sand mining and delivering (scope 3 sand for contractors)
materialTransport - emissions associated with Water, Sand and Fuel transportation. They are different methods here
mobDemob - emissions associated with mobilization and demobilization of all the machinery and trucks
people - emissions associated with onsite workers .
land - emissions associated with the land disturbance (borrowed from Stanford's OPGEE calculator)
auxillary - emissions associated with all the auxillary equipment
"""


class Frac:
    """Frac class definition. This class takes input vaiables for all frac components and calculate CO2 emissions
    for the frac job in kilograms"""
    
    def __init__(self, frac_type, stage_time, num_stage, p, q, t_tanks, t_pumps, etta=0.9):
        """Class initialization and combination of all class methods.
        Arguments:
        frac_type - type of the fracking. List of strings ['conv', 'zip', 'sim']. Currently not used
        num_stage - number of stages. Integer
        stage_time - stage duration in min. Integer
        p  - bottomhole pressure, psi
        q - rate of pumping, barrel/min
        t_tanks - number of trucks
        t_pumps - number of pumps
        etta - pump efficiency, default is 0.9

       """

        self.frac_type = frac_type
        self.stage_time = stage_time
        self.num_stage = num_stage
        self.p = p
        self.q = q
        self.etta = etta

        self.hhp = (self.p * self.q) / (40.8 * self.etta)  # Horsepower/hr
        self.num_pumps = self.hhp / 2250  # 2250 is a constant???
        self.btu_hr = self.hhp * 2544.43  # convert HPP to BTU (British Thermal Unit)

        #Mob-Demob constants
        self.t_pumps = t_pumps  # Input that needs to match with first module
        self.t_tanks = t_tanks  # number of trucks to travel to location
        self.t_blender = 1
        self.t_pcm = 1
        self.t_silos = 4
        self.t_iron = 3
        self.t_missle = 2
        self.t_LAS = 2
        self.t_crane = 1
        self.t_wlu = 1
        self.t_commandunit = 1
        self.t_pickup = 10
        self.t_aux = 20

        # EMISSION CONSTANTS

        # Fuel constants DIESEL
        self.disCO2 = 10.21  # kg/gal
        self.disCH4E = 0.2 / 1000 * 25  # kg/gal
        self.disN2OE = 0.47 / 1000 * 298  # kg/gal

        # Fuel constants LNG
        self.lngCO2 = 4.5  # kg/gal
        self.lngCH4E = 1.05 / 1000 * 25  # kg/gal
        self.lngN2OE = 0.2 / 1000 * 298  # kg/gal based of the LPG really from the table , could be a little less for LNG

        # Fuel constants CNG
        self.cngCO2 = 10.21  # kg/gal
        self.cngCH4E = 0.2 / 1000 * 25  # kg/gal
        self.cngN2OE = 0.47 / 1000 * 298  # kg/gal

        # Fuel constants for electricity
        self.electCO2 = 4.5  # kg/gal
        self.electCH4E = 1.05 / 1000 * 25  # kg/gal
        self.electN2OE = 0.2 / 1000 * 298  # kg/gal based of the LPG really from the table , could be a little less for LNG

        self.disLHV = 129306  # BTU/gal, temporary Lower Heating Value for diesel
        self.lngHHV = 84810  # BTU/gal, temporary Higher Heating Value for lng
        self.cngHHV = 84810  # BTU/gal, temporary Higher Heating Value for cng
        self.electHHV = 84810  # BTU/gal, temporary Higher Heating Value for elect
        self.disHHV = 137381  # BTU/gal, temporary Higher Heating Value for diesel

        type_list = ['conv', 'zip', 'sim']  #currently available 'conv' only

        if frac_type not in type_list:
            raise RuntimeError("Your input is incorrect. Available frac_type: 'conv', 'zip' or 'sim'")


    def primeMover(self, tbs, dis_fraction, cng_fraction = 0, lng_fraction = 0, elect_fraction = 0):
        """Calculates emissions of Prime Movers using a number of variables and constants, which are below

        Arguments:
        dis_fraction - fraction of diesel fuel in operation, fraction
        cng_fraction - fraction of cng fuel in operation, fraction. Default is 0
        lng_fraction - fraction of lng fuel in operation, fraction. Default is 0
        elect_fraction - fraction of elect fuel in operation, fraction. Default is 0
        tbs - in minutes

        Return:
        total_primeMover_CO2 - CO2 emitted by Prime Movers, kg """


        V_CO2_dis = ((self.btu_hr / self.disLHV) * dis_fraction) * self.disCO2 + (
                (self.btu_hr / self.disLHV) * dis_fraction) * self.disCH4E + (
                (self.btu_hr / self.disLHV) * dis_fraction) * self.disN2OE
        V_CO2_lng = ((self.btu_hr / self.lngHHV) * lng_fraction) * self.lngCO2 + (
                (self.btu_hr / self.lngHHV) * lng_fraction) * self.lngCH4E + (
                (self.btu_hr / self.lngHHV) * lng_fraction) * self.lngN2OE
        V_CO2_cng = ((self.btu_hr / self.cngHHV) * cng_fraction) * self.cngCO2 + (
                (self.btu_hr / self.cngHHV) * cng_fraction) * self.cngCH4E + (
                (self.btu_hr / self.cngHHV) * cng_fraction) * self.cngN2OE
        V_CO2_elect = ((self.btu_hr / self.electHHV) * elect_fraction) * self.electCO2 + (
                (self.btu_hr / self.electHHV) * elect_fraction) * self.electCH4E + (
                (self.btu_hr / self.electHHV) * elect_fraction) * self.electN2OE

        total_primeMover_CO2 = (V_CO2_dis + V_CO2_lng + V_CO2_cng + V_CO2_elect) * self.stage_time / 60 * self.num_stage

        return total_primeMover_CO2

    def sandTransport(self, prop_per_stage, sand_load, dist_to_sand, truck_consumption):
        """Calculates emissions associated with sand transportation with the assumption of the diesel trucks

        Arguments:
        prop_per_stage  - amount of propant, ton.
        sand_load - sand load, ton.
        dist_to_sand - distance to sand source, mile
        truck_consumption - average fuel consumption


        Return:
        total_sandTransport_CO2 - CO2 emitted by sand transportation, kg """

        sand_number_of_loads = prop_per_stage * self.num_stage / sand_load
        sand_fuel = sand_number_of_loads * dist_to_sand / truck_consumption
        total_sandTransport_CO2 = sand_fuel * self.disCO2 + sand_fuel * self.disCH4E + sand_fuel * self.disN2OE

        return total_sandTransport_CO2

    def waterTransport(self, water_per_stage, water_load, dist_to_water, truck_consumption):
        """Calculates emissions associated with water transportation with the assumption of the diesel trucks.
        Only valid if water not locally sourced from in a pit

        Arguments:
        water_amount  - amount of water, gal.
        water_load -  water load in case of land by truck transportation, cubic meters.
        dist_to_water - distance to water source, mile
        truck_consumption - average fuel consumption


        Return:
        total_waterTransport_CO2 - CO2 emitted by water transportation, kg """

        water_number_of_loads = water_per_stage * 0.00378541 * self.num_stage / water_load
        water_fuel = water_number_of_loads * dist_to_water / truck_consumption
        total_waterTransport_CO2 = water_fuel * self.disCO2 + water_fuel * self.disCH4E + water_fuel * self.disN2OE

        return total_waterTransport_CO2

    def fuelTransport(self, fuel_load, dist_to_fuel, truck_consumption):
        """Calculates emissions associated with fuel transportation with the assumption of the diesel trucks.

        Arguments:
        fuel_per_hour  - fuel consumption per hour, .
        fuel_load -  fuel load, cubic meters.
        dist_to_fuel - distance to fuel source, mile
        truck_consumption - average fuel consumption


        Return:
        total_fuelTransport_CO2 - CO2 emitted by fuel transportation, kg """

        v_fuel_hr = self.btu_hr / self.disLHV
        fuel_number_of_loads = v_fuel_hr * 0.00378541 * self.stage_time / 60 * self.num_stage / fuel_load
        fuel_fuel = fuel_number_of_loads * dist_to_fuel / truck_consumption
        total_fuelTransport_CO2 = fuel_fuel * self.disCO2 + fuel_fuel * self.disCH4E + fuel_fuel * self.disN2OE

        return total_fuelTransport_CO2

    def mobDemob(self, mob_distance, truck_consumption):
        """Calculates emissions associated with fuel consumed by mobilization/demobilization
         with the assumption of the diesel trucks.

        Arguments:
        mob_distance - distance to base, mile
        truck_consumption - average fuel consumption


        Return:
        total_mobDemob_CO2 - CO2 emitted by mobilization operations, kg """

        v_fuel_mobDemob = (self.t_pumps + self.t_tanks + self.t_blender + self.t_pcm + self.t_silos + self.t_iron +
                           self.t_missle + self.t_LAS + self.t_crane + self.t_wlu + self.t_commandunit) * mob_distance \
                          / truck_consumption
        v_fuel_mobDemob = v_fuel_mobDemob + (self.t_pickup + self.t_aux) * mob_distance / truck_consumption
        total_mobDemob_CO2 = v_fuel_mobDemob * self.disCO2 + v_fuel_mobDemob * self.disCH4E + v_fuel_mobDemob * self.disN2OE

        return total_mobDemob_CO2

    def land(self):
        """We estimate land disturbance CO2 from coefficients from OPGEE. Since we have only one well, we use the
        smallest coefficient even if we have high carbon environment (like forest).
        We convert cumulative oil production from one well to mega jouls and then

        Return:
        total_land_CO2  - CO2 from land disturbance, kg"""

        oil_produced = 95000  # oil produced in tons. average on Eagle Ford
        co2_coeff = 0.03 # gCO2/MJ of oil from OPGEE for not intensiveley drilled oil fields
        mj_produced = oil_produced / 0.000024 #produced oil in mega jouls
        total_land_CO2 = mj_produced * co2_coeff / 10 ** 3

        return total_land_CO2

    def sandMining(self, prop_per_stage, sand_footprint):
        """We estimate Scope3 for sand using numbers from literature

        Arguments:
        prop_per_stage - amount of propant, ton.
        sand_footprint - tonCO2/ton_propant has to be replaced or assumed by contractor


        Return:
        sand_supplier_CO2 - CO2 emitted by sand mining and delivery, kg
        """

        sand_supplier_CO2 = prop_per_stage * self.num_stage * sand_footprint * 1000

        return sand_supplier_CO2

    def people(self):
        """No calculations so far"""
        return 6000

    def auxillary(self):
        """No calculations so far"""
        return 25000
