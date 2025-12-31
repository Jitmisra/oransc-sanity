import json
import sys
import os
import csv
import glob

def extract_unique_from_file(json_file_path):
    """
    Extracts vulnerabilities from a single file and removes 
    duplicates found WITHIN that specific file based on moduleName only.
    Multiple titles and severities for the same moduleName are combined.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping '{json_file_path}': {e}")
        return []
    
    # Dictionary to store vulnerabilities by moduleName
    module_dict = {}
    
    if not isinstance(data, list):
        data = [data]
    
    for item in data:
        if isinstance(item, dict) and 'vulnerabilities' in item:
            for vuln in item['vulnerabilities']:
                module_name = vuln.get('moduleName', 'N/A')
                
                # If this module hasn't been seen yet in this file
                if module_name not in module_dict:
                    module_dict[module_name] = {
                        'id': vuln.get('id', 'N/A'),
                        'titles': [vuln.get('title', 'N/A')],
                        'severities': [vuln.get('severity', 'N/A')],
                        'moduleName': module_name,
                        'fixedIn': vuln.get('fixedIn', []),
                        'source_file': os.path.basename(json_file_path)
                    }
                else:
                    # Module already exists, add the title if it's different
                    existing_title = vuln.get('title', 'N/A')
                    if existing_title not in module_dict[module_name]['titles']:
                        module_dict[module_name]['titles'].append(existing_title)
                    
                    # Add severity if it's different
                    existing_severity = vuln.get('severity', 'N/A')
                    if existing_severity not in module_dict[module_name]['severities']:
                        module_dict[module_name]['severities'].append(existing_severity)
    
    # Convert dictionary to list and merge titles and severities
    file_results = []
    for module_data in module_dict.values():
        # Join multiple titles with " | " separator
        module_data['title'] = ' | '.join(module_data['titles'])
        # Join multiple severities with " | " separator
        module_data['severity'] = ' | '.join(module_data['severities'])
        
        del module_data['titles']  # Remove the temporary list
        del module_data['severities']  # Remove the temporary list
        file_results.append(module_data)
    
    return file_results

def process_directory(folder_path):
    search_path = os.path.join(folder_path, "*.json")
    json_files = glob.glob(search_path)
    
    if not json_files:
        print(f"No JSON files found in: {folder_path}")
        return []

    all_data = []
    for file_path in json_files:
        # Get unique findings for this specific file
        file_vulns = extract_unique_from_file(file_path)
        print(f"Processed {os.path.basename(file_path)}: Found {len(file_vulns)} unique modules.")
        
        # Add all of them to our master list
        all_data.extend(file_vulns)

    return all_data

def save_to_csv(vulnerabilities, filename='aggregated_vulnerabilities.csv'):
    if not vulnerabilities:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'severity', 'moduleName', 'fixedIn', 'source_file']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for vuln in vulnerabilities:
            vuln_copy = vuln.copy()
            vuln_copy['fixedIn'] = ', '.join(vuln['fixedIn']) if vuln['fixedIn'] else 'N/A'
            writer.writerow(vuln_copy)
    
    print(f"\nSuccessfully combined everything into: {filename}")

if __name__ == "__main__":
    target_folder = sys.argv[1] if len(sys.argv) > 1 else "."
    
    if not os.path.isdir(target_folder):
        print(f"Error: {target_folder} is not a valid directory.")
        sys.exit(1)

    results = process_directory(target_folder)
    save_to_csv(results)