#!/usr/bin/env python3
"""
Separate Generation Data Script

This script separates the combined generation data into:
1. Operational generation (currently running facilities)
2. Interconnection queue (planned/future projects)
"""

import json
import os

def separate_generation_data(input_file='webapp/public/generation_data.json'):
    """
    Separate generation data into operational and queue projects.
    
    Args:
        input_file: Path to the combined generation data JSON file
    """
    # Load the combined data
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r') as f:
        all_projects = json.load(f)
    
    # Separate by status
    operational = []
    queue = []
    
    for project in all_projects:
        if project.get('status') == 'Operational':
            operational.append(project)
        elif project.get('status') == 'Queue':
            queue.append(project)
        else:
            print(f"Warning: Project {project.get('project_name')} has unknown status: {project.get('status')}")
    
    # Print summary
    print(f"\nTotal projects: {len(all_projects)}")
    print(f"Operational: {len(operational)}")
    print(f"Queue: {len(queue)}")
    
    # Calculate capacity totals
    operational_capacity = sum(p.get('capacity_mw', 0) for p in operational)
    queue_capacity = sum(p.get('capacity_mw', 0) for p in queue)
    
    print(f"\nOperational Capacity: {operational_capacity:,.0f} MW")
    print(f"Queue Capacity: {queue_capacity:,.0f} MW")
    
    # Technology breakdown
    print("\n=== Operational by Technology ===")
    tech_breakdown_operational = {}
    for p in operational:
        tech = p.get('technology', 'Unknown')
        tech_breakdown_operational[tech] = tech_breakdown_operational.get(tech, 0) + p.get('capacity_mw', 0)
    
    for tech, capacity in sorted(tech_breakdown_operational.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tech}: {capacity:,.0f} MW")
    
    print("\n=== Queue by Technology ===")
    tech_breakdown_queue = {}
    for p in queue:
        tech = p.get('technology', 'Unknown')
        tech_breakdown_queue[tech] = tech_breakdown_queue.get(tech, 0) + p.get('capacity_mw', 0)
    
    for tech, capacity in sorted(tech_breakdown_queue.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tech}: {capacity:,.0f} MW")
    
    # Save separated files
    output_dir = 'webapp/public'
    os.makedirs(output_dir, exist_ok=True)
    
    operational_file = os.path.join(output_dir, 'generation_operational.json')
    queue_file = os.path.join(output_dir, 'generation_queue.json')
    
    print(f"\nSaving operational data to {operational_file}...")
    with open(operational_file, 'w') as f:
        json.dump(operational, f, indent=2)
    
    print(f"Saving queue data to {queue_file}...")
    with open(queue_file, 'w') as f:
        json.dump(queue, f, indent=2)
    
    print("\n✓ Separation complete!")
    
    return operational, queue

if __name__ == "__main__":
    separate_generation_data()
