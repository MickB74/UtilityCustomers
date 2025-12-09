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
    
    # Existing / Operational
    all_projects.extend(get_solar_projects())
    all_projects.extend(get_wind_projects())
    all_projects.extend(get_battery_projects())
    all_projects.extend(get_gas_projects())
    all_projects.extend(get_coal_projects())
    all_projects.extend(get_existing_fleet())
    
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
