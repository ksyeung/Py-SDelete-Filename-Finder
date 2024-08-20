"""
sdelete_filename_finder.py

This program helps identify $J artifacts created during SDelete execution
by analyzing the NTFS Change Journal.

Note:
- The '-f' and '-o' args expect full paths, ie, 'C:\\Users\\Dan\\DFIR\\$J.csv'
- The '-o' arg is optional.
"""

import pandas as pd
import argparse
import re

def has_sdelete_pattern(name):
    """
    Identifies the 26 alphabetical, repeating letters in file names that 
    are a distinct artifact of SDelete execution.

    Breakdown of the expression:
    ^ start of string
    \1* match 0 or more occurrences of the same letter
    ([A-Z]) match single uppercase letter
    \. match a literal dot (.)
    \1{3}$ match exactly 3 occurrences of the same letter after the dot
    $ end of string
    """
    pattern = r'^([A-Z])\1*\.\1{3}$'
    return bool(re.match(pattern, name))

def process_usn_data(file_path):
    """
    Loads, filters, and processes the USN data to identify and extract 
    relevant SDelete artifacts.
    """
    usn_data = pd.read_csv(file_path)

    # Filter the data based on UpdateReasons and duplicate UpdateTimestamp
    sdelete_reasons = [
        'DataOverwrite', 'DataOverwrite|Close', 'RenameNewName', 
        'RenameNewName|Close', 'RenameOldName', 'FileDelete|Close'
    ]
    filtered_usn_data = usn_data[
        usn_data['UpdateTimestamp'].duplicated(keep=False) &
        usn_data['UpdateReasons'].isin(sdelete_reasons)
    ].copy()

    # Identify rows that match the SDelete pattern
    filtered_usn_data['IsSDeletePattern'] = filtered_usn_data['Name'].apply(
        has_sdelete_pattern
    )
    matching_rows = filtered_usn_data[
        filtered_usn_data['IsSDeletePattern']
    ]

    # Remove rows that match the SDelete pattern from filtered_usn_data
    relevant_usn_data = filtered_usn_data[
        ~filtered_usn_data['IsSDeletePattern']
    ]

    # Find relevant rows with the same EntryNumber and UpdateTimestamp
    # but not in matching_rows
    matching_entry_timestamps = matching_rows[
        ['EntryNumber', 'UpdateTimestamp']
    ].drop_duplicates()
    relevant_usn_data = usn_data.merge(
        matching_entry_timestamps, 
        on=['EntryNumber', 'UpdateTimestamp'], 
        how='inner'
    )

    # Deduplicate relevant_usn_data with matching_rows
    relevant_usn_data = relevant_usn_data[
        ~relevant_usn_data.set_index(
            ['EntryNumber', 'UpdateTimestamp', 'Name']
        ).index.isin(
            matching_rows.set_index(
                ['EntryNumber', 'UpdateTimestamp', 'Name']
            ).index
        )
    ]

    # Drop duplicates and return relevant columns
    relevant_usn_data = relevant_usn_data.drop_duplicates(
        subset=['Name'], keep='first'
    )

    # Return sorted DataFrame
    return relevant_usn_data.sort_values(
        by=['EntryNumber', 'UpdateTimestamp']
    )[
        ['EntryNumber', 'UpdateTimestamp', 'Name', 
         'UpdateSequenceNumber', 'ParentPath']
    ]

def main():
    parser = argparse.ArgumentParser(
        description="Process, filter USN Journal data for SDelete artifacts."
    )
    parser.add_argument(
        '-f', '--file', required=True, 
        help="Path to the input CSV file containing USN Journal data."
    )
    parser.add_argument(
        '-o', '--output', required=False, 
        help="Path to the CSV file where the filtered data will be saved."
    )

    args = parser.parse_args()
    file_path = args.file
    output_file = args.output

    # Process USN data
    relevant_usn_data = process_usn_data(file_path)

    # Count and print the number of results
    num_results = len(relevant_usn_data)
    print(f"Number of files with SDelete artifacts: {num_results}")

    if num_results > 0:
        print("Details of the results:")
        for _, row in relevant_usn_data.iterrows():
            print(f"- Name: {row['Name']}, Path: {row['ParentPath']}\\"
                  f"{row['Name']}, UpdateTimestamp: {row['UpdateTimestamp']}")
        
        # Write to CSV only if there are results & an output file is specified
        if output_file:
            relevant_usn_data.to_csv(output_file, index=False)
            print(f"CSV file has been successfully exported to: {output_file}")
    else:
        print("No SDelete artifacts were found.")

if __name__ == "__main__":
    main()
