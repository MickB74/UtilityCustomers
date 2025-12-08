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
        
        # Queue / Construction
        GenerationProject("Cedar Bayou 4 (New)", "Gas", 721, "Chambers", "Baytown", "Queue", 2028, "NRG", "Peaker/CCGT"),
        GenerationProject("Orange County Adv Power", "Gas", 1200, "Orange", "Orange", "Queue", 2027, "Entergy", "Proposed CCGT"),
        GenerationProject("Sandow Lakes Gas", "Gas", 800, "Milam", "Rockdale", "Queue", 2027, "WattBridge", "Peaker"),
        GenerationProject("PHR Peaker", "Gas", 400, "Harris", "Pasadena", "Queue", 2026, "WattBridge", "Peaker"),
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
        
        # Aggregate Gas Fleets (~50 GW + Individual Projects = ~56 GW)
        GenerationProject("Aggregate Gas Fleet (North)", "Gas", 22000, "Various", "North Hub", "Operational", 2000, "Various", "Aggregated Fleet Capacity"),
        GenerationProject("Aggregate Gas Fleet (Houston)", "Gas", 14000, "Various", "Houston Hub", "Operational", 2000, "Various", "Aggregated Fleet Capacity"),
        GenerationProject("Aggregate Gas Fleet (South)", "Gas", 10000, "Various", "South Hub", "Operational", 2000, "Various", "Aggregated Fleet Capacity"),
        GenerationProject("Aggregate Gas Fleet (West)", "Gas", 4000, "Various", "West Hub", "Operational", 2000, "Various", "Aggregated Fleet Capacity"),
        
        # Aggregate Coal Fleet (~13 GW Target)
        GenerationProject("Aggregate Coal Fleet (North)", "Coal", 8500, "Various", "North Hub", "Operational", 1980, "Various", "Martin Lake, Monticello, etc."),
        GenerationProject("Aggregate Coal Fleet (South)", "Coal", 4500, "Various", "South Hub", "Operational", 1980, "Various", "Fayette, Oak Grove"),

        # Aggregate Wind Fleet (~41 GW Target - requires huge boost)
        GenerationProject("Aggregate Wind Fleet (West)", "Wind", 25000, "Various", "West Hub", "Operational", 2015, "Various", "Aggregated West Texas Wind"),
        GenerationProject("Aggregate Wind Fleet (South)", "Wind", 10000, "Various", "South Hub", "Operational", 2015, "Various", "Aggregated Coastal Wind"),
        GenerationProject("Aggregate Wind Fleet (North)", "Wind", 4000, "Various", "North Hub", "Operational", 2015, "Various", "Aggregated North Wind"),

        # Aggregate Solar Fleet (~37 GW Target - requires huge boost)
        GenerationProject("Aggregate Solar Fleet (West)", "Solar", 15000, "Various", "West Hub", "Operational", 2022, "Various", "Aggregated Solar Farms"),
        GenerationProject("Aggregate Solar Fleet (South)", "Solar", 10000, "Various", "South Hub", "Operational", 2022, "Various", "Aggregated Solar Farms"),
        GenerationProject("Aggregate Solar Fleet (North)", "Solar", 5000, "Various", "North Hub", "Operational", 2022, "Various", "Aggregated Solar Farms"),
        GenerationProject("Aggregate Solar Fleet (Distributed)", "Solar", 5000, "Various", "System Wide", "Operational", 2022, "Various", "Aggregated Distributed/Rooftop"),

        # Aggregate Battery Fleet (~14 GW Target)
        GenerationProject("Aggregate Battery Fleet (West)", "Battery", 5000, "Various", "West Hub", "Operational", 2023, "Various", "Aggregated BESS"),
        GenerationProject("Aggregate Battery Fleet (South)", "Battery", 4000, "Various", "South Hub", "Operational", 2023, "Various", "Aggregated BESS"),
        GenerationProject("Aggregate Battery Fleet (North)", "Battery", 3000, "Various", "North Hub", "Operational", 2023, "Various", "Aggregated BESS"),
        GenerationProject("Aggregate Battery Fleet (Houston)", "Battery", 1500, "Various", "Houston Hub", "Operational", 2023, "Various", "Aggregated BESS"),
    ]
    return fleet

def generate_all_projects():
    all_projects = []
    all_projects.extend(get_solar_projects())
    all_projects.extend(get_wind_projects())
    all_projects.extend(get_battery_projects())
    all_projects.extend(get_gas_projects())
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
