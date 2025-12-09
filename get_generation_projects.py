    #!/usr/bin/env python3
"""
ERCOT Generation Project Data Generator

This script generates a dataset of power generation projects in the ERCOT region.
It includes specific known major projects (Solar, Wind, Battery, Gas) and reasonable
estimates for the broader interconnection queue to simulate the scale of activity.

Data Sources:
- Public Press Releases (2023-2025)
- ERCOT GIS Reports (General Volume)
- Major Developer Announcements
"""

import json
import os
import random

class GenerationProject:
    def __init__(self, name, technology, mw, county, city, status, cod_year, developer="Unknown", notes=""):
        self.name = name
        self.technology = technology
        self.mw = mw
        self.county = county
        self.city = city
        self.hub = get_hub_from_county(county)
        self.status = status # "Operational" or "Queue"
        self.cod_year = cod_year
        self.developer = developer
        self.notes = notes

    def to_dict(self):
        return {
            "project_name": self.name,
            "technology": self.technology,
            "capacity_mw": self.mw,
            "county": self.county,
            "city": self.city,
            "hub": self.hub,
            "status": self.status,
            "cod_year": self.cod_year,
            "developer": self.developer,
            "notes": self.notes
        }

def get_hub_from_county(county):
    # Approximate ERCOT Hub/Zone Mapping
    west_counties = [
        "Pecos", "Reeves", "Andrews", "Upton", "Scurry", "Sterling", "Nolan", "Taylor", "Jones", "Concho", 
        "Crane", "Ector", "Midland", "Ward", "Winkler", "Loving", "Crockett", "Tom Green", "Howard",
        "Lubbock", "Sutton", "Schleicher", "Menard", "Kimble", "Mason", "McCulloch", "San Saba", "Terrell", "Val Verde"
    ]
    # Removed Panhandle counties (SPP)
    
    south_counties = [
        # Valley & Coast
        "Cameron", "Hidalgo", "Starr", "Webb", "Kenedy", "Willacy", "Bee", "Wharton", "Matagorda", "Nueces", 
        "San Patricio", "Kleberg", "Brooks", "Zapata", "Duval", "Jim Wells", "Live Oak", "Jim Hogg", 
        "Aransas", "Refugio", "Goliad", "Victoria", "Calhoun", "Jackson",
        # San Antonio Area
        "Bexar", "Comal", "Guadalupe", "Wilson", "Atascosa", "Medina", "Bandera", "Kendall", "Kerr",
        # Austin Area (LZ_SOUTH)
        "Travis", "Hays", "Caldwell", "Bastrop", "Fayette", "Lee", "Williamson", "Burnet", "Llano", "Gillespie"
    ]
    
    houston_counties = [
        "Harris", "Fort Bend", "Brazoria", "Chambers", "Galveston", "Liberty", "Orange", "Montgomery", "Waller", "Austin", "Colorado"
    ]
    
    # Logic
    if county in west_counties: return "West"
    if county in south_counties: return "South"
    if county in houston_counties: return "Houston"
    
    # Default everything else to North (DFW, East, Central, North Central)
    return "North"

def get_solar_projects():
    # Major Solar Projects (Operational & Queue)
    projects = [
        # Operational (Recent Large)
        GenerationProject("Danish Fields Solar", "Solar", 720, "Matagorda", "Blessing", "Operational", 2024, "TotalEnergies", "Paired with Battery"),
        GenerationProject("Roadrunner Solar", "Solar", 497, "Upton", "McCamey", "Operational", 2020, "Enel Green Power", "Solar + Storage"),
        GenerationProject("Permian Energy Center", "Solar", 460, "Andrews", "Andrews", "Operational", 2021, "Orsted", "Solar + Storage"),
        GenerationProject("Roscoe Solar", "Solar", 330, "Nolan", "Roscoe", "Operational", 2022, "RWE", "Co-located with wind"),
        GenerationProject("Samson Solar Energy Center", "Solar", 250, "Lamar", "Paris", "Operational", 2023, "Invenergy", "Part of 1.3GW complex"),
        GenerationProject("Galloway Solar", "Solar", 200, "Concho", "Paint Rock", "Operational", 2022, "8minute", "Solar"),
        GenerationProject("Anson Solar", "Solar", 200, "Jones", "Anson", "Operational", 2021, "Engie", "Solar"),
        
        # Queue / Under Construction
        GenerationProject("Aktina Solar (Exp)", "Solar", 500, "Wharton", "El Campo", "Queue", 2025, "Tokyo Gas", "Expansion"),
        GenerationProject("Mockingbird Solar", "Solar", 471, "Lamar", "Paris", "Queue", 2025, "Orsted", "Construction"),
        GenerationProject("Fighting Jays Solar", "Solar", 350, "Fort Bend", "Needville", "Queue", 2026, "AP Solar", "Near Houston"),
        GenerationProject("Greasewood Solar", "Solar", 300, "Pecos", "Fort Stockton", "Queue", 2026, "Copenhagen IP", "West Texas"),
        GenerationProject("Sparta Solar", "Solar", 250, "Bee", "Beeville", "Queue", 2026, "Avangrid", "South Texas"),
        GenerationProject("Bluebell Solar II", "Solar", 200, "Milam", "Rockdale", "Queue", 2026, "NextEra", "Central Texas"),
    ]
    return projects

def get_wind_projects():
    # Major Wind Projects
    projects = [
        # Operational
        GenerationProject("Los Vientos Wind", "Wind", 912, "Starr", "Rio Grande City", "Operational", 2016, "Duke Energy", "Multi-phase"),
        GenerationProject("Roscoe Wind Farm", "Wind", 781, "Nolan", "Roscoe", "Operational", 2009, "RWE", "historical giant"),
        GenerationProject("Horse Hollow Wind", "Wind", 735, "Taylor", "Abilene", "Operational", 2006, "NextEra", "historical giant"),
        GenerationProject("Capricorn Ridge", "Wind", 662, "Sterling", "Sterling City", "Operational", 2008, "NextEra", "West Texas"),
        GenerationProject("Sweetwater Wind", "Wind", 585, "Nolan", "Sweetwater", "Operational", 2007, "Leeward", "West Texas"),
        GenerationProject("Peñascal Wind", "Wind", 605, "Kenedy", "Sarita", "Operational", 2010, "Avangrid", "Coastal"),
        
        # Queue / Repowering
        GenerationProject("Great Prairie Wind", "Wind", 1027, "Hansford", "Spearman", "Operational", 2024, "NextEra", "Largest in Americas"),
        GenerationProject("South Plains Wind", "Wind", 500, "Floyd", "Lockney", "Operational", 2016, "First Wind", "Panhandle"),
        GenerationProject("Aviator Wind", "Wind", 525, "Coke", "Robert Lee", "Operational", 2020, "CMS Energy", "Facebook Offtaker"),
        GenerationProject("Santa Rita East", "Wind", 300, "Reagan", "Big Lake", "Operational", 2019, "Invenergy", "West Texas"),
        GenerationProject("Torrecillas Wind", "Wind", 300, "Webb", "Laredo", "Operational", 2019, "Avangrid", "South Texas"),
        GenerationProject("Gulf Wind Repower", "Wind", 250, "Kenedy", "Armstrong", "Queue", 2026, "Pattern Energy", "Repowering"),
        GenerationProject("Coyote Wind", "Wind", 200, "Scurry", "Snyder", "Queue", 2026, "Invenergy", "New Build"),
        GenerationProject("Maverick Wind", "Wind", 300, "Young", "Graham", "Queue", 2027, "Apex Clean Energy", "North Texas"),
    ]
    return projects

def get_battery_projects():
    # Battery Storage (Booming)
    projects = [
        # Queue / Planned (Major)
        GenerationProject("Gemini Energy Storage", "Battery", 600, "Harrison", "Marshall", "Queue", 2026, "Quinbrook", "East Texas"),
        GenerationProject("Blackjack Creek BESS", "Battery", 500, "Bee", "Beeville", "Queue", 2026, "LS Power", "South Texas"),
        GenerationProject("Helios Energy Storage", "Battery", 450, "Nueces", "Corpus Christi", "Queue", 2026, "Plus Power", "Coastal"),
        GenerationProject("Permian Energy Storage", "Battery", 400, "Andrews", "Andrews", "Queue", 2027, "Intersect Power", "West Texas"),
        GenerationProject("Wildfire Energy BESS", "Battery", 350, "Brazos", "Bryan", "Queue", 2026, "Jupiter Power", "ERCOT South"),
        GenerationProject("Maverick BESS", "Battery", 300, "Young", "Graham", "Queue", 2027, "NextEra", "North Texas"),
        
        # Operational
        GenerationProject("DeCordova Energy Storage", "Battery", 260, "Hood", "Granbury", "Operational", 2022, "Vistra", "Near Granbury"),
        GenerationProject("Sierrita BESS", "Battery", 200, "Pecos", "Fort Stockton", "Operational", 2023, "RWE", "West Texas"),
        GenerationProject("Crossett BESS", "Battery", 200, "Crane", "Crane", "Operational", 2023, "Broad Reach", "West Texas"),
        GenerationProject("Gambit Energy Storage", "Battery", 100, "Brazoria", "Angleton", "Operational", 2021, "Plus Power", "Houston Area"),
    ]
    return projects

def get_gas_projects():
    # Natural Gas
    projects = [
        # Operational (Large Fleet)
        GenerationProject("Cedar Bayou", "Gas", 1750, "Chambers", "Baytown", "Operational", 2000, "NRG", "Combined Cycle"),
        GenerationProject("Forney Energy Center", "Gas", 1700, "Kaufman", "Forney", "Operational", 2003, "Vistra", "Combined Cycle"),
        GenerationProject("Colorado Bend II", "Gas", 1100, "Wharton", "Wharton", "Operational", 2024, "Calpine", "New CCGT"),
        GenerationProject("Barney Davis", "Gas", 925, "Nueces", "Corpus Christi", "Operational", 2002, "Talen Energy", "Coastal"),
        GenerationProject("Tenaska Gateway", "Gas", 845, "Rusk", "Henderson", "Operational", 2000, "Tenaska", "East Texas"),
        GenerationProject("Odessa Ector", "Gas", 1000, "Ector", "Odessa", "Operational", 2001, "Invenergy", "Permian"),
        GenerationProject("Stryker Creek", "Gas", 1175, "Cherokee", "Jacksonville", "Operational", 1958, "Luminant", "Legacy Gas"),
        GenerationProject("Graham Power", "Gas", 630, "Young", "Graham", "Operational", 2008, "Luminant", "Combined Cycle"),
        GenerationProject("Sim Gideon", "Gas", 600, "Bastrop", "Bastrop", "Operational", 1972, "LCRA", "Legacy Gas"),
        
        # Queue / Construction
        GenerationProject("CPV Basin Ranch", "Gas", 1350, "Ward", "Monahans", "Queue", 2028, "CPV", "Dispatchable"),
        GenerationProject("Cedar Bayou 4 (New)", "Gas", 721, "Chambers", "Baytown", "Queue", 2028, "NRG", "Peaker/CCGT"),
        GenerationProject("Orange County Adv Power", "Gas", 1200, "Orange", "Orange", "Queue", 2027, "Entergy", "Proposed CCGT"),
        GenerationProject("Sandow Lakes Gas", "Gas", 800, "Milam", "Rockdale", "Queue", 2027, "WattBridge", "Peaker"),
        GenerationProject("PHR Peaker", "Gas", 400, "Harris", "Pasadena", "Queue", 2026, "WattBridge", "Peaker"),
    ]
    return projects

def get_coal_projects():
    # Major Coal Fleet (Operational)
    projects = [
        GenerationProject("WA Parish", "Coal", 3690, "Fort Bend", "Thompsons", "Operational", 1977, "NRG", "Largest Coal Plant"),
        GenerationProject("Martin Lake", "Coal", 2250, "Rusk", "Tatum", "Operational", 1977, "Luminant", "East Texas"),
        GenerationProject("Oak Grove", "Coal", 1600, "Robertson", "Franklin", "Operational", 2010, "Luminant", "Modern Lignite"),
        GenerationProject("Limestone", "Coal", 1570, "Limestone", "Jewett", "Operational", 1985, "NRG", "Lignite"),
        GenerationProject("Fayette Power", "Coal", 1600, "Fayette", "La Grange", "Operational", 1979, "LCRA/Austin", "Colorado River"),
        GenerationProject("JK Spruce", "Coal", 1300, "Bexar", "San Antonio", "Operational", 1992, "CPS Energy", "San Antonio"),
        GenerationProject("Tolk Station", "Coal", 1060, "Lamb", "Muleshoe", "Operational", 1982, "Xcel", "West Texas Panhandle"),
        GenerationProject("Welsh Station", "Coal", 1000, "Titus", "Pittsburg", "Operational", 1977, "AEP", "East Texas"),
        GenerationProject("Harrington", "Coal", 1000, "Potter", "Amarillo", "Operational", 1976, "Xcel", "Panhandle"),
        GenerationProject("Sandy Creek", "Coal", 900, "McLennan", "Riesel", "Operational", 2013, "Sandy Creek Services", "Modern Coal"),
    ]
    return projects

def generate_confidential_queue():
    # Simulate the massive interconnection queue (1000+ projects)
    # We will generate ~300 entries to represent the "Long Tail" of the queue
    projects = []
    
    counties = [
        "Pecos", "Reeves", "Andrews", "Wharton", "Matagorda", "Fort Bend", "Dallas", "Tarrant", "Harris", 
        "Hidalgo", "Starr", "Webb", "Nueces", "Lamar", "Red River"
    ]
    
    # Simple city map approximation for confidential projects
    city_map = {
        "Pecos": "Fort Stockton", "Reeves": "Pecos", "Andrews": "Andrews", "Wharton": "Wharton", 
        "Matagorda": "Bay City", "Fort Bend": "Rosenberg", "Dallas": "Dallas", "Tarrant": "Fort Worth", 
        "Harris": "Houston", "Hidalgo": "McAllen", "Starr": "Rio Grande City", "Webb": "Laredo", 
        "Nueces": "Corpus Christi", "Lamar": "Paris", "Red River": "Clarksville"
    }

    # Solar Queue (Lots of 100-300MW projects)
    for i in range(1, 101):
        mw = random.choice([50, 100, 150, 200, 250, 300])
        cty = random.choice(counties)
        city = city_map.get(cty, "Unknown")
        projects.append(GenerationProject(f"Confidential Solar {cty} {i}", "Solar", mw, cty, city, "Queue", 2026+random.randint(0,2), "Confidential", "Queue Position 2x-xxxx"))

    # Battery Queue (Booming 100-200MW)
    for i in range(1, 121):
        mw = random.choice([10, 50, 100, 150, 200])
        cty = random.choice(counties)
        city = city_map.get(cty, "Unknown")
        projects.append(GenerationProject(f"Confidential Storage {cty} {i}", "Battery", mw, cty, city, "Queue", 2026+random.randint(0,1), "Confidential", "Queue Position 2x-xxxx"))

    # Wind Queue (Fewer, larger)
    for i in range(1, 31):
        mw = random.choice([200, 300, 400])
        cty = random.choice(counties)
        city = city_map.get(cty, "Unknown")
        projects.append(GenerationProject(f"Confidential Wind {cty} {i}", "Wind", mw, cty, city, "Queue", 2027, "Confidential", "Queue Position 2x-xxxx"))

    # Gas Queue (Specific peakers)
    for i in range(1, 21):
        mw = random.choice([100, 200, 400])
        cty = random.choice(counties)
        city = city_map.get(cty, "Unknown")
        projects.append(GenerationProject(f"Confidential Gas Peaker {cty} {i}", "Gas", mw, cty, city, "Queue", 2027, "Confidential", "Dispatchable"))

    return projects

def get_existing_fleet():
    # Aggregate entries to represent the wider ERCOT fleet (Matching User Targets)
    # Target: Gas ~56GW, Wind ~41GW, Solar ~37GW, Coal ~13GW, Battery ~14GW, Nuclear ~5GW
    fleet = [
        # Nuclear (~5.1 GW)
        GenerationProject("Comanche Peak Nuclear", "Nuclear", 2400, "Somervell", "Glen Rose", "Operational", 1990, "Vistra", "Base Load"),
        GenerationProject("South Texas Project", "Nuclear", 2700, "Matagorda", "Bay City", "Operational", 1988, "NRG/CPS/Austin", "Base Load"),
        
        # Major Gas Fleet (Replaces Aggregates with Real Plants)
        GenerationProject("Midlothian Energy Center", "Gas", 1650, "Ellis", "Midlothian", "Operational", 2000, "Vistra", "Combined Cycle"),
        GenerationProject("Handley Gen Station", "Gas", 1265, "Tarrant", "Fort Worth", "Operational", 2000, "Excelon", "Urban Plant"),
        GenerationProject("Wolf Hollow I & II", "Gas", 1115, "Hood", "Granbury", "Operational", 2003, "Excelon", "Combined Cycle"),
        GenerationProject("Hays Energy", "Gas", 1100, "Hays", "San Marcos", "Operational", 2000, "Vistra", "Combined Cycle"),
        GenerationProject("Magic Valley Gen", "Gas", 1068, "Hidalgo", "Edinburg", "Operational", 2000, "Calpine", "Combined Cycle"),
        GenerationProject("Freestone Energy", "Gas", 1000, "Freestone", "Fairfield", "Operational", 2002, "Calpine", "Combined Cycle"),
        GenerationProject("Lamar Power", "Gas", 1000, "Lamar", "Paris", "Operational", 2000, "Vistra", "Combined Cycle"),
        GenerationProject("Montgomery County Power", "Gas", 993, "Montgomery", "Willis", "Operational", 2021, "Entergy", "Modern CCGT"),
        GenerationProject("Rio Nogales", "Gas", 800, "Guadalupe", "Seguin", "Operational", 2002, "Vistra", "Combined Cycle"),
        GenerationProject("Johnson County Gen", "Gas", 800, "Johnson", "Cleburne", "Operational", 2000, "Constellation", "Combined Cycle"),
        GenerationProject("Bosque Energy Ctr", "Gas", 800, "Bosque", "Laguna Park", "Operational", 2000, "Vistra", "Combined Cycle"),
        GenerationProject("Wise County Power", "Gas", 750, "Wise", "Poolville", "Operational", 2000, "Vistra", "Combined Cycle"),
        GenerationProject("Temple 1", "Gas", 750, "Bell", "Temple", "Operational", 2000, "Temple Gen", "Combined Cycle"),
        GenerationProject("Temple 2", "Gas", 750, "Bell", "Temple", "Operational", 2000, "Temple Gen", "Combined Cycle"),
        GenerationProject("Altura Cogen", "Gas", 600, "Harris", "Channelview", "Operational", 1985, "Calpine", "Cogen"),
        GenerationProject("Bastrop Energy Ctr", "Gas", 550, "Bastrop", "Bastrop", "Operational", 2000, "WattBridge", "Peaker"),
        GenerationProject("Frontera", "Gas", 500, "Hidalgo", "Mission", "Operational", 2000, "Invenergy", "Combined Cycle"),
        GenerationProject("Los Fresnos", "Gas", 500, "Cameron", "Los Fresnos", "Operational", 2000, "Calpine", "Peaker"),
        GenerationProject("Mountain Creek", "Gas", 800, "Dallas", "Dallas", "Operational", 2000, "Excelon", "Urban Peaker"),
        GenerationProject("Lake Creek", "Gas", 500, "McLennan", "Riesel", "Operational", 2000, "Luminant", "Peaker"),
        
        # Aggregate Gas Remainder (Peakers/Small Units to reach ~56GW)
        GenerationProject("Aggregate Gas Peakers (Distributed)", "Gas", 20000, "Various", "System Wide", "Operational", 1990, "Various", "Distributed Peaker Fleet"),

        # Major Wind Fleet (Replaces Aggregates with Real Plants)
        GenerationProject("Javelina Wind", "Wind", 748, "Webb", "Laredo", "Operational", 2015, "NextEra", "South Texas Giant"),
        GenerationProject("Buffalo Gap Wind", "Wind", 523, "Taylor", "Abilene", "Operational", 2006, "AES", "West Texas"),
        GenerationProject("Lone Star Wind", "Wind", 400, "Shackelford", "Albany", "Operational", 2008, "EDP", "West Texas"),
        GenerationProject("Papalote Creek", "Wind", 380, "San Patricio", "Odem", "Operational", 2010, "E.ON", "Coastal"),
        GenerationProject("Panther Creek", "Wind", 458, "Howard", "Big Spring", "Operational", 2009, "E.ON", "West Texas"),
        GenerationProject("Penascal Wind", "Wind", 605, "Kenedy", "Sarita", "Operational", 2010, "Avangrid", "Coastal"),
        GenerationProject("Sherbino Wind", "Wind", 300, "Pecos", "Fort Stockton", "Operational", 2008, "BP Wind", "West Texas"),
        GenerationProject("King Mountain", "Wind", 280, "Upton", "McCamey", "Operational", 2001, "NextEra", "Mesa"),
        GenerationProject("Gulf Wind", "Wind", 283, "Kenedy", "Armstrong", "Operational", 2009, "Pattern", "Coastal"),
        GenerationProject("Wildcat Wind", "Wind", 200, "Clay", "Henrietta", "Operational", 2010, "Enel", "North Texas"),
        GenerationProject("Bull Creek", "Wind", 180, "Borden", "Gail", "Operational", 2008, "E.ON", "West Texas"),
        GenerationProject("Hackberry Wind", "Wind", 166, "Shackelford", "Albany", "Operational", 2008, "RES", "West Texas"),
        GenerationProject("Goat Mountain", "Wind", 150, "Sterling", "Sterling City", "Operational", 2009, "NextEra", "Mesa"),
        GenerationProject("Camp Springs", "Wind", 130, "Scurry", "Snyder", "Operational", 2007, "Invenergy", "West Texas"),
        GenerationProject("Brazos Wind", "Wind", 160, "Scurry", "Snyder", "Operational", 2003, "Shell", "West Texas"),
        GenerationProject("South Trent", "Wind", 100, "Nolan", "Sweetwater", "Operational", 2009, "AEP", "West Texas"),
        GenerationProject("Wharton Wind", "Wind", 120, "Wharton", "El Campo", "Operational", 2010, "Invenergy", "Coastal"),
        GenerationProject("Keechi Wind", "Wind", 110, "Jack", "Jacksboro", "Operational", 2015, "Enbridge", "North Texas"),
        GenerationProject("Santa Rita", "Wind", 300, "Reagan", "Big Lake", "Operational", 2018, "Invenergy", "West Texas"),
        GenerationProject("Tahoka Wind", "Wind", 300, "Lynn", "Tahoka", "Operational", 2018, "Xcel", "West Texas"),
        GenerationProject("Torrecillas", "Wind", 150, "Webb", "Laredo", "Operational", 2019, "Avangrid", "South Texas"),
        GenerationProject("Karankawa", "Wind", 300, "San Patricio", "Mathis", "Operational", 2020, "Avangrid", "Coastal"),
        GenerationProject("Stella Wind", "Wind", 201, "Kenedy", "Sarita", "Operational", 2018, "Orsted", "Coastal"),
        GenerationProject("Elbow Creek", "Wind", 120, "Howard", "Big Spring", "Operational", 2008, "NRG", "West Texas"),
        
        # Aggregate Wind Remainder (Smaller legacy farms to reach ~41GW)
        GenerationProject("Aggregate Wind Fleet (West)", "Wind", 15000, "Various", "West Hub", "Operational", 2015, "Various", "Small Legacy Wind Farms"),
        GenerationProject("Aggregate Wind Fleet (South)", "Wind", 5000, "Various", "South Hub", "Operational", 2015, "Various", "Small Coastal Wind Farms"),

        # Major Solar Fleet (Real Projects)
        GenerationProject("Prospero Solar I & II", "Solar", 679, "Andrews", "Andrews", "Operational", 2020, "Longroad", "West Texas Giant"),
        GenerationProject("Taygete Energy", "Solar", 255, "Pecos", "Fort Stockton", "Operational", 2021, "7X Energy", "West Texas"),
        GenerationProject("Phoebe Solar", "Solar", 250, "Winkler", "Wink", "Operational", 2019, "Innergex", "West Texas"),
        GenerationProject("Misae Solar", "Solar", 240, "Childress", "Childress", "Operational", 2020, "CIP", "Panhandle/North"),
        GenerationProject("Titan Solar", "Solar", 260, "Culberson", "Van Horn", "Operational", 2020, "Idemitsu", "West Texas"),
        GenerationProject("Holstein Solar", "Solar", 200, "Nolan", "Sweetwater", "Operational", 2020, "Duke Energy", "West Texas"),
        GenerationProject("Rambler Solar", "Solar", 200, "Tom Green", "San Angelo", "Operational", 2020, "Duke Energy", "West Texas"),
        GenerationProject("Buckthorn West", "Solar", 200, "Pecos", "Fort Stockton", "Operational", 2018, "Clearway", "West Texas"),
        GenerationProject("Midway Solar", "Solar", 163, "Pecos", "McCamey", "Operational", 2018, "174 Power", "West Texas"),
        GenerationProject("Oberon Solar", "Solar", 150, "Ector", "Odessa", "Operational", 2020, "174 Power", "Permian"),
        GenerationProject("Upton 2", "Solar", 150, "Upton", "McCamey", "Operational", 2018, "Vistra", "Solar+Storage"),
        GenerationProject("Bluebell Solar", "Solar", 140, "Sterling", "Sterling City", "Operational", 2021, "NextEra", "West Texas"),
        GenerationProject("East Pecos Solar", "Solar", 100, "Pecos", "Fort Stockton", "Operational", 2017, "Southern Power", "West Texas"),
        GenerationProject("Lapetus Energy", "Solar", 100, "Andrews", "Andrews", "Operational", 2019, "Duke Energy", "West Texas"),
        GenerationProject("RE Pearl", "Solar", 100, "Pecos", "Fort Stockton", "Operational", 2018, "Recurrent", "West Texas"),
        
        # Aggregate Solar Remainder (To reach ~37GW)
        GenerationProject("Aggregate Solar Fleet (West)", "Solar", 15000, "Various", "West Hub", "Operational", 2022, "Various", "Aggregated Solar Farms"),
        GenerationProject("Aggregate Solar Fleet (South)", "Solar", 10000, "Various", "South Hub", "Operational", 2022, "Various", "Aggregated Solar Farms"),
        GenerationProject("Aggregate Solar Fleet (North)", "Solar", 3000, "Various", "North Hub", "Operational", 2022, "Various", "Aggregated Solar Farms"),
        GenerationProject("Aggregate Solar Fleet (Distributed)", "Solar", 4000, "Various", "System Wide", "Operational", 2022, "Various", "Aggregated Distributed/Rooftop"),

        # Major Battery Fleet (Real Projects)
        GenerationProject("Jupiter Power Fleet", "Battery", 600, "Various", "System Wide", "Operational", 2023, "Jupiter Power", "Distributed Storage"),
        GenerationProject("Key Capture Fleet", "Battery", 500, "Various", "System Wide", "Operational", 2023, "KCE", "Distributed Storage"),
        GenerationProject("Hunt Energy Fleet", "Battery", 400, "Various", "System Wide", "Operational", 2023, "Hunt", "Distributed Storage"),
        GenerationProject("Enel Storage Fleet", "Battery", 300, "Various", "System Wide", "Operational", 2023, "Enel", "Distributed Storage"),
        
        # Aggregate Battery Remainder (To reach ~14GW)
        GenerationProject("Aggregate Battery Fleet (West)", "Battery", 5000, "Various", "West Hub", "Operational", 2023, "Various", "Aggregated BESS"),
        GenerationProject("Aggregate Battery Fleet (South)", "Battery", 4000, "Various", "South Hub", "Operational", 2023, "Various", "Aggregated BESS"),
        GenerationProject("Aggregate Battery Fleet (North)", "Battery", 2500, "Various", "North Hub", "Operational", 2023, "Various", "Aggregated BESS"),
        GenerationProject("Aggregate Battery Fleet (Houston)", "Battery", 1000, "Various", "Houston Hub", "Operational", 2023, "Various", "Aggregated BESS"),
    ]
    return fleet

def generate_all_projects():
    all_projects = []
    all_projects.extend(get_solar_projects())
    all_projects.extend(get_wind_projects())
    all_projects.extend(get_battery_projects())
    all_projects.extend(get_gas_projects())
    all_projects.extend(get_coal_projects())
    all_projects.extend(get_existing_fleet())
    all_projects.extend(generate_confidential_queue())
    
    return sorted(all_projects, key=lambda x: x.mw, reverse=True)

if __name__ == "__main__":
    projects = generate_all_projects()
    
    print(f"Generated {len(projects)} generation projects.")
    
    dict_data = [p.to_dict() for p in projects]
    
    os.makedirs("webapp/public", exist_ok=True)
    with open("webapp/public/generation_data.json", "w") as f:
        json.dump(dict_data, f, indent=2)
        
    print("Exported to webapp/public/generation_data.json")
