# Conversation of .c3d files to OpenSim marker.trc and ground reaction forces
# grf.mot for the Sinergia data set. This script can be used for other data sets
# as well, however, the column names and transformation conventions may be
# different. Also, note that here we do not distinguish between left and right
# foot, therefore the setup_grf.xml file has to be manually updated.
#
# author: Dimitar Stanev <jimstanev@gmail.com>
# contributors: Celine Provins, George Papoulias
##
import os
import re
import opensim
import utils
import pandas as pd
import c3d
import numpy as np


def write_mot(analog_df, labels, mot_file):
    """
    Write analog data (samples, n_channels) to MOT.
    
    inputs:
        labels: The labels for the analog channels.
        analog_df: The DataFrame containing the analog data.
        
    """
    
    # make sure labels include time
    labels = ['time'] + labels

    # Crop dataframe to include only labels
    analog_df = analog_df[labels]
    num_samples, num_columns = analog_df.shape
    
    # create writer
    with open(mot_file, "w") as writer:
        # Header
        writer.write(f"{os.path.basename(writer.name)}\n")
        writer.write("version=1\n")
        writer.write(f"nRows={num_samples}\n")
        writer.write(f"nColumns={num_columns + 1}\n")  # +1 for time
        writer.write("in_degrees=yes\n")
        writer.write("endheader\n")

        # Column labels
        writer.write("\t".join(labels) + "\n")
    
        # Data rows
        for i, row in analog_df.iterrows():
            # breakpoint()
            writer.write(f"{row['time']:.6f}\t" + "\t".join([f"{val:.6f}" for val in row[1:]]) + "\n")

def export_emg(c3d_filepath):
    print(f"Reading C3D file: {c3d_filepath}")
    try:
        reader = c3d.Reader(open(c3d_filepath, "rb"))
    except Exception as e:
        print(f"Error: Could not open or read the C3D file. {e}")
        return 1

    # Rates and frames
    marker_rate = float(reader.header.frame_rate)
    first_frame = int(reader.header.first_frame)
    num_frames = int(reader.frame_count)
    
    # Units (fallback to 'mm' if not available)
    units = "mm"

    # Labels, clamped to available columns to avoid index errors
    marker_labels = [str(l or "").strip() for l in reader.point_labels]
    analog_labels = [str(l or "").strip() for l in reader.analog_labels]

    # create time vector
    initial_time = first_frame / marker_rate
    final_time = (first_frame + num_frames-1) / marker_rate
    time = np.linspace(initial_time, final_time, num_frames)
    
    analog_df = pd.DataFrame(index=range(num_frames),columns=analog_labels)
    analog_df['time'] = time

    # move time to first column
    cols = analog_df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    analog_df = analog_df[cols]
    
    # Collect frames
    for frame_no, points, analog in reader.read_frames():
        # get row number and print loading bar
        i_row = frame_no - first_frame
        # convert analog data to list
        analog_list  = analog.data.tolist()

        # loop through analog channels and add to dataframe
        for i_channel in range(len(analog_list)):
            channel_name = analog_labels[i_channel]
            
            # add channel to dataframe
            analog_df.loc[i_row, channel_name] = analog[i_channel][0]


    # save analog to csv
    analog_path = os.path.join(os.path.dirname(c3d_filepath), "analog.csv")
    analog_df.to_csv(analog_path, index=False)
    print(f"Successfully exported {analog_path}")


    # Write EMG MOT
    emg_indices = [i for i, lbl in enumerate(analog_labels) if "emg" in lbl.lower()]
    if emg_indices:
        emg_mot_path = os.path.join(os.path.dirname(c3d_filepath), "emg.mot")
        emg_labels = [analog_labels[i] for i in emg_indices]
        write_mot(analog_df, emg_labels, emg_mot_path)
        print(f"Successfully exported {emg_mot_path}")
    else:
        print("Warning: No EMG channels found among available analog channels.")
        
    # Write GRF MOT
    breakpoint()    
    grf_indices = [i for i, lbl in enumerate(analog_labels) if re.match(r'^[fpm]\d[xyz]$', lbl.lower())]

def transform_labels(labels):
    """
    Transforms a list of labels from a compact format to a more descriptive format.
    Example: 'f1x' -> 'ground_force_1_vx'
    """
    transformed = []
    # Define a mapping for the prefixes and their corresponding replacements.
    # The key is the original prefix (e.g., 'f'), and the value is a tuple
    # containing the new prefix (e.g., 'ground_force') and the new suffix (e.g., 'v').
    mapping = {
        'f': ('ground_force', 'v'),
        'p': ('ground_force', 'p'),
        'm': ('ground_moment', 'm'),
    }

    for label in labels:
        # Check if the label is at least 3 characters long and matches the pattern
        if len(label) >= 3 and label[0] in mapping and label[-1] in 'xyz':
            # Extract the original prefix (e.g., 'f'), number (e.g., '1'), and axis (e.g., 'x')
            original_prefix = label[0]
            number = label[1:-1]
            axis = label[-1]

            # Get the new prefix and suffix from the mapping
            new_prefix, new_suffix = mapping[original_prefix]

            # Construct the new label
            new_label = f'{new_prefix}_{number}_{new_suffix}{axis}'
            transformed.append(new_label)
        else:
            # If the label doesn't match the expected pattern, add it as is
            transformed.append(label)

    return transformed

def rotate_data_table(table, axis, deg):
    """Rotate OpenSim::TimeSeriesTableVec3 entries using an axis and angle.

    Parameters
    ----------
    table: OpenSim.common.TimeSeriesTableVec3

    axis: 3x1 vector

    deg: angle in degrees

    """
    R = opensim.Rotation(np.deg2rad(deg),
                         opensim.Vec3(axis[0], axis[1], axis[2]))
    for i in range(table.getNumRows()):
        vec = table.getRowAtIndex(i)
        vec_rotated = R.multiply(vec)
        table.setRowAtIndex(i, vec_rotated)

def export_markers(c3d_filepath, strings_to_remove=[]):
    print(f"Exporting markers for {c3d_filepath}")
    
    # OpenSim data adapters
    adapter = opensim.C3DFileAdapter()
    adapter.setLocationForForceExpression(
        opensim.C3DFileAdapter.ForceLocation_CenterOfPressure)
    trc_adapter = opensim.TRCFileAdapter()

    # get markers 
    task = adapter.read(c3d_filepath)
    markers_task = adapter.getMarkersTable(task)
    output_dir = os.path.dirname(c3d_filepath)

    # process markers of task and save to .trc file
    rotate_data_table(markers_task, [1, 0, 0], -90)

    # remove unwanted strings from labels
    labels = list(markers_task.getColumnLabels())
    for s in strings_to_remove:
        labels = [re.sub(s, '', lbl) for lbl in labels]
    
    markers_task.setColumnLabels(labels)

    trc_adapter = opensim.TRCFileAdapter()
    trc_adapter.write(markers_task, os.path.join(output_dir, 'markers_experimental.trc'))
    print(f"Successfully exported {os.path.join(output_dir, 'markers_experimental.trc')}")
    
def export_grf(c3d_filepath):
    print(f"Exporting ground reaction forces for {c3d_filepath}")
    adapter = opensim.C3DFileAdapter()
    adapter.setLocationForForceExpression(opensim.C3DFileAdapter.ForceLocation_CenterOfPressure)
    
    c3d_data = adapter.read(c3d_filepath)
    forces_table = adapter.getForcesTable(c3d_data)
    rotate_data_table(forces_table, [1, 0, 0], 180)
    time = forces_table.getIndependentColumn()
    forces_table = forces_table.flatten(['x', 'y', 'z'])
    
    # replace f,p,m for ground_force_v, ground_force_p, ground_torque
    labels = transform_labels(list(forces_table.getColumnLabels()))
    osimTools = utils.osimTools()
    force_sto = osimTools._create_opensim_storage(time, forces_table.getMatrix(), labels)
    force_sto.setName('grf')
    output_dir = os.path.dirname(c3d_filepath)
    force_sto.printResult(force_sto, 'grf', output_dir, 0.01, '.mot')
    print(f"Successfully exported {os.path.join(output_dir, 'grf_180.mot')}")

def define_time_range(trc_filepath, markers, algorithm):
    
    data = utils.load_any_data_file(trc_filepath)

    # Define time range based on markers and algorithm
    if algorithm == 'min-max':
        start_time = data['time'].min()
        end_time = data['time'].max()
    elif algorithm == 'deadlift':
        
        start_frame = int(data[markers].idxmin())
        
        # end frame is the first frame with minimal derivative after the start frame
        end_frame = int(data[markers].iloc[start_frame:].diff().idxmin())
        
        start_time = data['Time'].iloc[start_frame]
        end_time = data['Time'].iloc[end_frame]
        
    # write events.csv file
    data = [['start', start_time],
            ['end', end_time]]
    events = pd.DataFrame(data)
    events.to_csv(os.path.dirname(trc_filepath) + '/events.csv', index=False, header=False)
    print(f"Successfully exported {os.path.dirname(trc_filepath) + '/events.csv'}")
    return start_time, end_time

def main(c3d_filepath, plot=False):
    # trc_filepath = os.path.dirname(c3d_filepath) + '/markers_experimental.trc'
    # define_time_range(trc_filepath, markers=['SACROL'], algorithm='deadlift')
    # exit()
    # OpenSim data adapters
    export_markers(c3d_filepath, strings_to_remove = [])
    export_grf(c3d_filepath)
    
    # export_emg(c3d_filepath)

if __name__ == "__main__":

    c3d_filepath = input("Enter the path to the .c3d file: ").strip().strip('"')
    
    # Check if file exists
    if not os.path.exists(c3d_filepath):
        print(f"Error: File not found at {c3d_filepath}")
        exit(1)    
    
    # Check if it's a .c3d file
    if not c3d_filepath.lower().endswith('.c3d'):
        print(f"Error: File must be a .c3d file, got {c3d_filepath}")
        exit(1)
    
    print(f"Processing {c3d_filepath}")
    
    main(c3d_filepath, plot=False)

# END