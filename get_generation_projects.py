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
- Interconnection Queue (CSV Source)
"""

import json
import os
import csv
import datetime

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
        "Lubbock", "Sutton", "Schleicher", "Menard", "Kimble", "Mason", "McCulloch", "San Saba", "Terrell", "Val Verde",
        "Glasscock"
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
    ]
    return projects

def get_battery_projects():
    # Battery Storage (Booming)
    projects = [
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

def load_queue_from_csv(file_path):
    projects = []
    
    # Technology Mapping
    tech_map = {
        'WIN': 'Wind',
        'SOL': 'Solar',
        'BAT': 'Battery',
        'GAS': 'Gas',
        'COA': 'Coal',
        'NUC': 'Nuclear'
    }

    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found. Returning empty queue.")
        return []

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                name = row.get('Project Name', '').strip()
                if not name:
                    continue
                
                # Tech
                raw_fuel = row.get('Fuel', '').upper().strip()
                technology = tech_map.get(raw_fuel, 'Other')
                
                # Capacity
                try:
                    mw = float(row.get('Capacity (MW)', 0))
                except ValueError:
                    mw = 0.0
                
                # Location
                county = row.get('County', 'Unknown').title().strip()
                # Try to extract city from POI or Location if available, else blank
                city = "" # CSV doesn't have city directly, leave blank or infer? leaving blank for now.

                # Status & Year
                # The file is "projects in queue", so status is Queue.
                status = "Queue"
                
                cod_str = row.get('Projected COD', '')
                cod_year = 2026 # Default
                if cod_str:
                    try:
                        # Attempt to parse YYYY-MM-DD or MM/DD/YYYY
                        # The snippet showed '2025-12-31 00:00:00'
                        if '-' in cod_str:
                             dt = datetime.datetime.strptime(cod_str.split(' ')[0], '%Y-%m-%d')
                             cod_year = dt.year
                        elif '/' in cod_str:
                             dt = datetime.datetime.strptime(cod_str.split(' ')[0], '%m/%d/%Y')
                             cod_year = dt.year
                    except:
                        pass
                
                developer = row.get('Interconnecting Entity', 'Unknown').strip()
                notes = row.get('GIM Study Phase', '').strip()

                projects.append(GenerationProject(
                    name=name,
                    technology=technology,
                    mw=mw,
                    county=county,
                    city=city,
                    status=status,
                    cod_year=cod_year,
                    developer=developer,
                    notes=notes
                ))
            except Exception as e:
                print(f"Error parsing row: {row.get('Project Name')}: {e}")
                continue
                
    return projects

def get_existing_fleet():
    # Use absolute path or relative to script dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    eia_file = os.path.join(script_dir, "webapp/public/generation_operational_eia.json")
    
    if os.path.exists(eia_file):
        print(f"Loading existing fleet from {eia_file}...")
        with open(eia_file, 'r') as f:
            data = json.load(f)
        
        projects = []
        for d in data:
            projects.append(GenerationProject(
                name=d.get('name'),
                technology=d.get('technology'),
                mw=d.get('mw'),
                county=d.get('county'),
                city="",
                status="Operational",
                cod_year=d.get('cod_year'),
                developer=d.get('developer'),
                notes=d.get('notes')
            ))
        return projects
        
    return [
        GenerationProject("Existing Nuclear Fleet", "Nuclear", 4960, "Matagorda/Somervell", "Bay City/Glen Rose", "Operational", 1988, "Vistra/NRG"),
        GenerationProject("Existing Coal Fleet", "Coal", 13600, "Various", "", "Operational", 1980, "Various"),
        GenerationProject("Existing Gas Fleet", "Gas", 54000, "Various", "", "Operational", 1995, "Various"),
     ]
    return fleet

def generate_all_projects():
    all_projects = []
    
    # Existing / Operational
    # Try to load from EIA JSON first
    existing_fleet = get_existing_fleet()
    
    if len(existing_fleet) > 100:
        # High confidence we have a full dataset
        print(f"Using {len(existing_fleet)} operational projects from EIA data.")
        all_projects.extend(existing_fleet)
    else:
        # Fallback to hardcoded lists if EIA data is missing or too small
        print("EIA data missing or incomplete. Using hardcoded fleet data.")
        all_projects.extend(get_solar_projects())
        all_projects.extend(get_wind_projects())
        all_projects.extend(get_battery_projects())
        all_projects.extend(get_gas_projects())
        all_projects.extend(get_coal_projects())
        all_projects.extend(get_existing_fleet()) # This returns the small hardcoded list in fallback mode
    
    # New Queue Data from CSV
    csv_path = "projects_in_queue_all_generators.csv"
    if os.path.exists(csv_path):
        print(f"Loading queue from {csv_path}...")
        queue_projects = load_queue_from_csv(csv_path)
        print(f"Loaded {len(queue_projects)} projects from queue.")
        all_projects.extend(queue_projects)
    else:
        print("CSV Source not found. Skipping queue data.")
    
    return sorted(all_projects, key=lambda x: x.mw, reverse=True)

if __name__ == "__main__":
    projects = generate_all_projects()
    
    print(f"Total Generated Projects: {len(projects)}")
    
    dict_data = [p.to_dict() for p in projects]
    
    os.makedirs("webapp/public", exist_ok=True)
    with open("webapp/public/generation_data.json", "w") as f:
        json.dump(dict_data, f, indent=2)
        
    print("Exported to webapp/public/generation_data.json")
