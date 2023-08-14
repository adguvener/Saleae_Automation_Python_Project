from saleae import automation
import os
import os.path
from datetime import datetime
import numpy as np
import csv


with automation.Manager.connect(port=10430) as manager:
    # Configure the capturing device to record on digital channels 0 and 1,
    device_configuration = automation.LogicDeviceConfiguration(
        enabled_digital_channels=[0, 1],  # Adjust based on your digital channel setup
        digital_sample_rate=24000000,
    )

    # Record 5 seconds of data before stopping the capture
    capture_configuration = automation.CaptureConfiguration(
        capture_mode=automation.TimedCaptureMode(duration_seconds=1)
    )
    
    root_of_sequence_search = r'C:\Users\Administrator\Desktop\logic_2_automation\SequenceSearch-main'

    # Start a capture - the capture will be automatically closed when leaving the `with` block
    with manager.start_capture(
            device_id='C1FCCEA198FCB31F',
            device_configuration=device_configuration,
            capture_configuration=capture_configuration) as capture:

        # Wait until the capture has finished
        # This will take about 5 seconds because we are using a timed capture mode
        capture.wait()

        # Add an analyzer to the capture for async serial
        #  available settings: "Input Channel", "Bit Rate (Bits/s)", "Bits per Frame", "Stop Bits", "Parity Bit", "Significant Bit", "Signal inversion", "Mode"
        #  expected one of "No Parity Bit (Standard)", "Even Parity Bit", "Odd Parity Bit", received "None"
        
        async_serial_analyzer = capture.add_analyzer('Async Serial', label=f'Simulator Input', settings={
            'Input Channel': 0,
            'Bit Rate (Bits/s)': 115200,
            'Bits per Frame':8,
            'Stop Bits':1,
            'Parity Bit': 'No Parity Bit (Standard)',
            'Significant Bit': 'Least Significant Bit Sent First (Standard)',
            'Signal inversion': 'Non Inverted (Standard)',})
        
        sequence_finder = capture.add_high_level_analyzer(root_of_sequence_search,name='Sequence search',
                                                          input_analyzer= async_serial_analyzer,
                                                          label='S1_toSKB',
                                                          settings={'search_in_type': 'Hex','for_spi_test': 'MOSI',
                                                                    'search_for': '0xA8 0x06',})
        
        sequence_finder_2 = capture.add_high_level_analyzer(root_of_sequence_search,name='Sequence search',
                                                          input_analyzer= async_serial_analyzer,
                                                          label='S1_toAKB',
                                                          settings={'search_in_type': 'Hex','for_spi_test': 'MOSI',
                                                                    'search_for': '0xA8 0x07',})
        
        
        # Store output in a timestamped directory
        output_dir = r'C:\Users\Administrator\Desktop\logic_2_automation'
        file_dir = r'C:\Users\Administrator\Desktop\logic_2_automation\Test_Results.csv'
        # Open the file in write mode to clear its contents
        with open(file_dir, 'w') as file:
            pass 
        
        
        # Export analyzer data to a CSV file
        analyzer_export_filepath = os.path.join(output_dir, 'Test_Results.csv')
        capture.export_data_table(
            filepath=analyzer_export_filepath,
            analyzers=[sequence_finder,sequence_finder_2],
        )
        
        # # Export raw digital data to a CSV file
        # capture.export_raw_data_csv(directory=output_dir, digital_channels=[0, 1])

        
        # # Finally, save the capture to a file
        # capture_filepath = os.path.join(output_dir, 'example_capture.sal')
        # capture.save_capture(filepath=capture_filepath)
        
# Load CSV file using numpy
data = np.genfromtxt(file_dir, delimiter=',', dtype=str, skip_header=1)

# Find indices of rows where 'Name' column is 'S1_toSKB' or 'S1_toAKB'
indices_s1_to_skb = np.where(data[:, 0] == '"S1_toSKB"')[0]
indices_s1_to_akb = np.where(data[:, 0] == '"S1_toAKB"')[0]


# Get 'Start_time' values for 'S1_toSKB' and 'S1_toAKB'
start_time_s1_to_skb = data[indices_s1_to_skb, 2].astype(float)
start_time_s1_to_akb = data[indices_s1_to_akb, 2].astype(float)
s1_time_diff = start_time_s1_to_skb-start_time_s1_to_akb

pass_key = 'PASS'
fail_key = 'FAIL'
# print("S1 time:",s1_time_diff)

data = []

# Define the number of rows
num_rows = 24

# Generate the rows
for i in range(num_rows):
    row = [
        f'S{i+1} to SKB : PASS',
        f'S{i+1} to AKB : PASS',
        s1_time_diff
    ]
    data.append(row)

headers = ['to SKB'+ 'Result','to AKB'+ 'Result', 'Timing Difference']


# Write data to CSV file
csv_file = 'bpstattest.csv'  # Change the filename if needed

with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    writer.writerows(data)
