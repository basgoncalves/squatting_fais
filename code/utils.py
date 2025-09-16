from pyexpat import model
import shutil
import time
from tkinter import filedialog, messagebox, simpledialog
from matplotlib import pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
import sys
import pandas as pd
import re
import c3d
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import opensim as osim
import tkinter as tk
import re
import os
import opensim
import pandas as pd
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.offsetbox import AnchoredText


MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

def print_to_log(message):
    """
    Prints a message to the console and logs it to a file.
    
    Args:
        message (str): The message to print and log.
    """
    timestamp = time.strftime('%d.%m.%Y_%H:%M:%S', time.localtime()) + f":{int((time.time() % 1) * 1000):03d}"
    print(f'{timestamp} {message}')
    with open(MODULE_DIR + '\\log.txt', 'a') as log_file:
        log_file.write(f'{timestamp}: {message}\n')

def rel_path(path, relative_to):
    """
    Returns the relative path from the given path to the code directory.
    
    Args:
        path (str): The path to convert.
        relative_to (str): The base path to which the relative path is calculated.
        
    Returns:
        str: The relative path.
    """
    return os.path.relpath(path, relative_to)

def check_path(path, create=False, isdir=False):
    """Check if a path exists and is a directory."""
    if not os.path.exists(path):        
        if create:
            try:
                os.makedirs(path)
                print("[INFO] Created directory:", path)
            except Exception as e:
                print("[ERROR] Could not create directory:", path, "Error:", e)
        else:
            print("[ERROR] Path does not exist:", path)
    if isdir and not os.path.isdir(path):
        print("[ERROR] Path is not a directory:", path)

    return path, os.path.isdir(path)

def load_c3d(path=None, output=0):
    """
    Load a .c3d file into a pandas DataFrame.

    Args:
        path (str): The path to the .c3d file. If None, prompts for input.
        output (int): If 1, prints the columns of the DataFrame.

    Returns:
        pd.DataFrame: The loaded data from the .c3d file.
    """
    
    if not check_path(path):
        path = input("Please provide the path to the .c3d file: ")

    try:
        reader = c3d.Reader(open(path, 'rb'))
        
        return reader 
    except Exception as e:
        print(f"Error: Could not read the file at {path}. Please check the file format and try again.")
        print(f"Details: {e}")
    
def load_trc(path=None, output=False, combine_headers=False):
    
    if not check_path(path):
        path = input("Please provide the path to the .trc file: ")

    # find line with '#Frame' to skip the header
    try:
        with open(path, 'r') as file:
            for i, line in enumerate(file):
                if 'Frame#' in line:
                    header_start_line = i
                    break
    except:
        print(f"Error: Could not read the file at {path}. Please check the path and try again.")
        return None
    
    df = pd.read_csv(path,sep='\t',skiprows=header_start_line,index_col=False)
    
    # Create a temporary frame from the multi-index, forward-fill, and get values
    markers = df.columns.tolist()
    coordinates = df.iloc[0].to_list()  # First row contains sub-headers

    # replace Unnamed with empty cells
    for idx, marker in enumerate(markers):
        if marker.startswith('Unnamed'):
            markers[idx] = markers[idx-1]
    
    coordinates = [coord if not pd.isna(coord) else '' for coord in coordinates]

    # create multi-index dataFrame and delete row 0
    df.columns = pd.MultiIndex.from_tuples(zip(markers, coordinates), names=['Marker', 'Coordinate'])
    df = df.iloc[2:]
    
    # if needed make 'time' lower case (only)
    if 'Time' in df.columns:
        df = df.rename(columns={'Time': 'time'})
        
    # if needed combine headers
    if combine_headers:
        df.columns = df.columns.map(lambda x: f"{x[0]}_{x[1]}" if x[1] else x[0])

    if output == 1: print(df.columns)

    return df

def load_sto(path=None, output=0):
    """
    Load a .sto file into a pandas DataFrame.

    Args:
        path (str): The path to the .sto file. If None, prompts for input.
        output (int): If 1, prints the columns of the DataFrame.

    Returns:
        pd.DataFrame: The loaded data from the .sto file.
    """
    
    if not check_path(path):
        path = input("Please provide the path to the .sto file: ")

    # find line with 'endheader' to skip the header
    try:
        with open(path, 'r') as file:
            for i, line in enumerate(file):
                if 'endheader' in line or i > 100:  # Limit to first 100 lines to avoid long files
                        break
    except:
        print(f"Error: Could not read the file at {path}. Please check the path and try again.")
        return None

    # read the file into a pandas DataFrame, skipping the header
    try:
        columns = []
        offset = -3
        while 'time' not in columns:
            try:    
                data = pd.read_csv(path, sep= '\s+', header=i+offset)
                columns = data.columns
                offset += 1
                if offset > 100:
                    print(f"Error: Could not find 'time' column in the file {path}. Please check the file format.")
                    return None
            except pd.errors.ParserError:
                offset += 1
                
    except Exception as e:
        print(f"Error: Could not read the file at {path}. Please check the file format and try again.")
        print(f"Details: {e}")
        return None

    if output == 1: print(data.columns)

    return data

def load_grf_mot(path=None, output=0):
    
    if not check_path(path):
        path = input("Please provide the path to the .mot file: ")

    # find line with 'endheader' to skip the header
    try:
        with open(path, 'r') as file:
            for i, line in enumerate(file):
                if 'endheader' in line:
                        break
    except:
        print(f"Error: Could not read the file at {path}. Please check the path and try again.")
        return None

    # read the file into a pandas DataFrame, skipping the header
    try:
        data = pd.read_csv(path, sep= '\s+', header=i+1)
    except Exception as e:
        print(f"Error: Could not read the file at {path}. Please check the file format and try again.")
        print(f"Details: {e}")
        return None

    if output == 1: print(data.columns)

    return data

def load_data_file(file_path):
    """
    Loads the motion capture data file into a pandas DataFrame.

    This function reads the header to extract metadata and then loads the
    actual data into a structured DataFrame.

    Args:
        file_path (str): The path to the data file.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The loaded data.
            - dict: A dictionary with the file's metadata.
    """
    metadata = {}
    header_lines = []
    
    # Read the header part of the file first to extract metadata
    with open(file_path, 'r') as f:
        for i in range(5):  # First 5 lines are metadata or headers
            line = f.readline().strip()
            header_lines.append(line)
            if i < 2: # The first two lines contain key-value metadata
                parts = line.split('\t')
                for j in range(0, len(parts), 2):
                    if j + 1 < len(parts) and parts[j]:
                        metadata[parts[j]] = parts[j+1]

    # The 4th line contains the main column headers (FHD, RBHD, etc.)
    # The 5th line contains the sub-column headers (X1, Y1, etc.)
    main_headers = re.split(r'\s+', header_lines[3].strip())[2:] # Skip first two empty items
    sub_headers = re.split(r'\s+', header_lines[4].strip())[2:] # Skip first two items

    # Create a MultiIndex (hierarchical column names) for the DataFrame
    # This matches your file's structure (e.g., FHD -> X1, Y1, Z1)
    header_tuples = []
    i = 0
    for main_header in main_headers:
        if main_header: # Check if it's not an empty string
            # Each main header corresponds to a set of sub-headers (e.g., X, Y, Z coordinates)
            num_sub_headers = 3 # Assuming X, Y, Z for markers. Adjust if needed.
            for j in range(num_sub_headers):
                header_tuples.append((main_header, sub_headers[i]))
                i += 1

    # Define the column names for the first two columns
    final_column_names = [('Frame', '#'), ('Time', '')] + header_tuples

    # Load the actual data, skipping the header rows
    data = pd.read_csv(
        file_path,
        sep='\t',        # Data is separated by tabs
        header=None,     # We are providing our own column names
        skiprows=6,      # Skip the metadata and header lines we already processed
        engine='python'  # Use python engine for more flexibility with separators
    )
    
    # Assign the hierarchical column names to the DataFrame
    data.columns = pd.MultiIndex.from_tuples(final_column_names)

    return data, metadata

def load_any_data_file(file_path):
    """
    Loads any data file (TRC, MOT, STO, C3D) into a pandas DataFrame.

    Args:
        file_path (str): The path to the data file.

    Returns:
        pd.DataFrame: The loaded data.
    """
    if file_path.endswith('.trc'):
        return load_trc(file_path)
    
    elif file_path.endswith('.mot'):
        return load_sto(file_path)
    
    elif file_path.endswith('.sto'):
        return load_sto(file_path)
    
    elif file_path.endswith('.c3d'):
        return load_c3d(file_path)
    
    elif file_path.endswith('.csv'):
        return pd.read_csv(file_path)
        
    elif file_path.endswith('.txt'):
        # Assuming these are plain text files with tab-separated values
        return pd.read_csv(file_path, sep='\t', header=0)
    
    elif file_path.endswith('.xml'):
        # For XML files, we can use the XML_tools module to read them
        tree = ET.parse(file_path)
        if tree is not None:
            return pd.DataFrame([elem.attrib for elem in tree.findall('.//')])
        else:
            raise ValueError(f"Could not read XML file: {file_path}")
    else:
        try:
            # Try to read as a generic text file
            with open(file_path, 'r') as f:
                data = f.readlines()
            # Assuming the first line is a header
            header = data[0].strip().split('\t')
            # Load the rest of the data into a DataFrame
            data = [line.strip().split('\t') for line in data[1:]]
            return pd.DataFrame(data, columns=header)
        
        except Exception as e:
            print(f"Error: Could not read the file at {file_path}. Please check the file format and try again.")
            print(f"Details: {e}")
            
def save_data_file(file_path, data, metadata):
    """
    Saves the DataFrame back to a file in the original format.

    Args:
        file_path (str): The path where the file will be saved.
        data (pd.DataFrame): The DataFrame to save.
        metadata (dict): The metadata to write to the header.
    """
    with open(file_path, 'w') as f:
        # Write metadata lines
        # This part reconstructs the first two header lines from the metadata dictionary
        # It's a bit manual to match the format exactly.
        f.write(f"PathFileType\t4\t(X/Y/Z)\t{metadata.get('PathFileType', '')}\n")
        f.write(f"DataRate\t{metadata.get('DataRate', '')}\tCameraRate\t{metadata.get('CameraRate', '')}\tNumFrames\t{metadata.get('NumFrames', '')}\tNumMarkers\t{metadata.get('NumMarkers', '')}\tUnits\t{metadata.get('Units', '')}\tOrigDataRate\t{metadata.get('OrigDataRate', '')}\tOrigDataStartFrame\t{metadata.get('OrigDataStartFrame', '')}\tOrigNumFrames\t{metadata.get('OrigNumFrames', '')}\n")
        f.write('\n') # The empty line
        
        # Reconstruct the column headers
        main_headers = data.columns.get_level_values(0)
        sub_headers = data.columns.get_level_values(1)
        
        # Write main headers line
        f.write("Frame#\tTime\t")
        unique_main_headers = main_headers.unique()
        # This logic ensures each main header is printed once and padded correctly
        header_line = ""
        last_main = ""
        for main in main_headers[2:]: # Skip Frame and Time
            if main != last_main:
                header_line += f"{main}\t\t\t" # Assuming 3 sub-columns, hence 3 tabs
                last_main = main
        f.write(header_line.strip() + '\n')

        # Write sub-headers line
        f.write("\t\t") # Align with the data columns
        f.write('\t'.join(sub_headers[2:]) + '\n')
        f.write('\n') # The final empty line before data

    # Append the data to the file
    data.to_csv(
        file_path,
        mode='a',          # Append to the file we just created with the header
        header=False,      # Don't write DataFrame headers again
        index=False,       # Don't write the DataFrame index
        sep='\t',          # Use tabs as separators
        float_format='%.6f'# Format floats to 6 decimal places
    )

def load_sto_header(file_path):
    """
    Loads the header of a .sto file and returns it as a list of strings.

    Args:
        file_path (str): The path to the .sto file.

    Returns:
        list: A list of strings representing the header lines.
    """
    header = []
    break_next = False
    with open(file_path, 'r') as f:
        for line in f:
            if break_next:
                break
            if 'endheader' in line:
                break_next = True
            header.append(line.strip())
    
    return header

def write_trc(markers_df, trc_file, units, frame_rate, first_frame):
    """
    Write marker data (frames, n_markers, 3) to TRC.
    """
    
    # remove time column
    time = markers_df["time"]
    markers_df = markers_df.drop(columns=["time"])
    
    num_frames = markers_df.shape[0]
    marker_labels = markers_df.columns.droplevel(1).to_list()
    
    # only unique labels
    marker_labels = list(dict.fromkeys(marker_labels))
    n_markers = len(marker_labels)

    with open(trc_file, "w") as writer:
        # Header
        writer.write(f"PathFileType\t4\t(X/Y/Z)\t{os.path.basename(writer.name)}\n")
        writer.write("DataRate\tCameraRate\tNumFrames\tNumMarkers\tUnits\tOrigDataRate\tOrigDataStartFrame\tOrigNumFrames\n")
        writer.write(f"{frame_rate}\t{frame_rate}\t{num_frames}\t{n_markers}\t{units}\t{frame_rate}\t{first_frame}\t{num_frames}\n")

        # Marker names
        header = "Frame#\tTime\t" + "\t".join([f"{name}\t\t" for name in marker_labels]) + "\n"
        writer.write(header)

        # Coordinate labels
        coord_line = "\t\t" + "\t".join([f"X{i+1}\tY{i+1}\tZ{i+1}" for i in range(n_markers)]) + "\n"
        writer.write(coord_line)

        # Data rows
        for i in range(num_frames):
            frame_num = first_frame + i
            time_val = time.iloc[i]
            row = [f"{frame_num}", f"{time_val:.6f}"]
            row.extend([f"{coord:.6f}" for coord in markers_df.iloc[i].values])
            writer.write("\t".join(row) + "\n")

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
        writer.write(f"nColumns={num_columns}\n") 
        writer.write("in_degrees=yes\n")
        writer.write("endheader\n")

        # Column labels
        writer.write("\t".join(labels) + "\n")
    
        # Data rows
        for i, row in analog_df.iterrows():
            # breakpoint()
            writer.write(f"{row['time']:.6f}\t" + "\t".join([f"{val:.6f}" for val in row[1:]]) + "\n")

def write_sto_header(writer, dataFrame):
    """
    Writes the header for a .sto file.

    Args:
        writer (TextIOWrapper): The file writer object.
        dataFrame (pd.DataFrame): The DataFrame containing the data.
    """
    writer.write(f"{os.path.basename(writer.name)}\n")
    writer.write("version=1\n")
    writer.write(f"nRows={dataFrame.shape[0]}\n")
    writer.write(f"nColumns={dataFrame.shape[1]}\n")
    writer.write("in_degrees=yes\n")
    writer.write("endheader\n")

def write_sto_file(dataFrame, file_path):
    """
    Writes a pandas DataFrame to a .sto file with a specified header.

    Args:
        dataFrame (pd.DataFrame): The DataFrame to write.
        file_path (str): The path where the .sto file will be saved.
        header (list): A list of strings representing the header lines to write.
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
        print(f"Created directory: {os.path.dirname(file_path)}")
        
    # make time lowercase
    if 'Time' in dataFrame.columns:
        dataFrame = dataFrame.rename(columns={"Time": "time"})
        

    with open(file_path, 'w', newline='') as f:
        # Write the header lines
        write_sto_header(f, dataFrame)

        # bring time column to front
        dataFrame = dataFrame[['time'] + [col for col in dataFrame.columns if col != 'time']]

        # Write the data without extra line spaces
        dataFrame.to_csv(f, sep='\t', index=False, float_format='%.6f')

def read_xml(path):
    """
    Reads an XML file and returns its content as a string.

    Args:
        path (str): The path to the XML file.

    Returns:
        str: The content of the XML file.
    """
    try:
        tree = ET.parse(path)
        return tree
    except FileNotFoundError:
        print(f"Error: The file at {path} does not exist.")
        return None
    except Exception as e:
        print(f"Error reading the file at {path}: {e}")
        return None

def save_pretty_xml(tree, save_path):
            """Saves the XML tree to a file with proper indentation and no blank lines."""
            rough_string = ET.tostring(tree.getroot(), 'utf-8')
            reparsed = xml.dom.minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="   ")
            # Remove blank lines
            pretty_xml_no_blanks = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])
            with open(save_path, 'w') as file:
                file.write(pretty_xml_no_blanks)

# cmd easy commands
def activate_cmd_env():
    path = input("Please provide the path to the environment: ")
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.startswith('activate') and filename.endswith('.bat'):
                cmd_file = os.path.join(root, filename)
                os.startfile(cmd_file)

# opensim 
def select_osim_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select OpenSim Model File",
        filetypes=[("OpenSim Model Files", "*.osim")]
    )
    root.destroy()
    return file_path

def muscles_per_coordinate(osimModel, coord_name):
    muscles = []
    indexes = []
    coord = osimModel.getCoordinateSet().get(coord_name)
    state = osimModel.initSystem()
    osimModel.realizePosition(state)

    for i in range(osimModel.getMuscles().getSize()):
        muscle = osimModel.getMuscles().get(i)
        if abs(muscle.computeMomentArm(state, coord)) > 1e-4:
            muscles.append(muscle.getName())
            indexes.append(i)

    return muscles, indexes

def checkMuscleMomentArms(osim_modelPath, ik_output, leg = 'l', threshold = 0.005):
# Adapted from Willi Koller: https://github.com/WilliKoller/OpenSimMatlabBasic/blob/main/checkMuscleMomentArms.m
# Only checked if works for for the Rajagopal and Catelli models

    def get_model_coord(model, coord_name):
        try:
            index = model.getCoordinateSet().getIndex(coord_name)
            coord = model.updCoordinateSet().get(index)
        except:
            index = None
            coord = None
            print(f'Coordinate {coord_name} not found in model')
        
        return index, coord

    def muscle_crosses_coordinate(muscle, coord_name):
        
        coord = model.getCoordinateSet().get(coord_name)
        # Check if the muscle crosses the specified coordinate
        for path in muscle.getGeometryPath().getAllPoints():
            if path.getName() == coord_name:
                return True
        return False

    # Load motions and model
    motion = osim.Storage(ik_output)
    model = osim.Model(osim_modelPath)

    # Initialize system and state
    model.initSystem()
    state = model.initSystem()

    # coordinate names
    HipflexIndex, HipflexCoord = get_model_coord(model, 'hip_flexion_' + leg)
    HiprotIndex, HipRotCoord = get_model_coord(model, 'hip_rotation_' + leg)
    HipAddIndex, HipAddCoord = get_model_coord(model, 'hip_adduction_' + leg)
    flexIndexLknee, flexCoordLknee = get_model_coord(model, 'knee_angle_' + leg)
    addIndexLknee, addCoordLknee = get_model_coord(model, 'knee_adduction_' + leg)
    flexIndexLank, flexCoordLank = get_model_coord(model, 'ankle_angle_' + leg)

    # get hip flexion muscles
    muscleNames_Hipflex, muscleIndices_Hipflex = muscles_per_coordinate(model, HipflexCoord.getName())
    flexMomentArms = np.zeros((motion.getSize(), len(muscleIndices_Hipflex)))

    muscleNames_HipAdd, muscleIndices_HipAdd = muscles_per_coordinate(model, HipAddCoord.getName())
    addMomentArms = np.zeros((motion.getSize(), len(muscleIndices_HipAdd)))

    # get hip rotation muscles
    muscleNames_HipRot, muscleIndices_HipRot = muscles_per_coordinate(model, HipRotCoord.getName())
    rotMomentArms = np.zeros((motion.getSize(), len(muscleIndices_HipRot)))

    # get names of the knee muscles
    muscleNames_knee, muscleIndices_knee = muscles_per_coordinate(model, flexCoordLknee.getName())
    kneeFlexMomentArms = np.zeros((motion.getSize(), len(muscleIndices_knee)))

    # get names of the ankle muscles
    muscleNames_ankle, muscleIndices_ankle = muscles_per_coordinate(model, flexCoordLank.getName())
    ankleFlexMomentArms = np.zeros((motion.getSize(), len(muscleIndices_ankle)))

    # compute moment arms for each muscle and create time vector
    time_vector = []
    initial_time = time.time()
    for i in range(1, motion.getSize()):
        
        flexAngleL = motion.getStateVector(i-1).getData().get(HipflexIndex) / 180 * np.pi
        rotAngleL = motion.getStateVector(i-1).getData().get(HiprotIndex) / 180 * np.pi
        addAngleL = motion.getStateVector(i-1).getData().get(HipAddIndex) / 180 * np.pi
        flexAngleLknee = motion.getStateVector(i-1).getData().get(flexIndexLknee) / 180 * np.pi
        flexAngleLank = motion.getStateVector(i-1).getData().get(flexIndexLank) / 180 * np.pi

        time_vector.append(motion.getStateVector(i-1).getTime())
        # Update the state with the joint angle
        coordSet = model.updCoordinateSet()
        coordSet.get(HipflexIndex).setValue(state, flexAngleL)
        coordSet.get(HiprotIndex).setValue(state, rotAngleL)
        coordSet.get(HipAddIndex).setValue(state, addAngleL)
        coordSet.get(flexIndexLknee).setValue(state, flexAngleLknee)
        coordSet.get(flexIndexLank).setValue(state, flexAngleLank)

        # Realize the state to compute dependent quantities
        model.computeStateVariableDerivatives(state)
        model.realizeVelocity(state)

        # Compute the moment arm hip
        for j in range(len(muscleIndices_Hipflex)):
            muscleIndex = muscleIndices_Hipflex[j]
            if muscleNames_Hipflex[j][-1] == leg:
                flexMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, HipflexCoord)
                flexMomentArms[i, j] = flexMomentArm

        # Compute the moment arm hip rotation
        for j in range(len(muscleIndices_HipRot)):
            muscleIndex = muscleIndices_HipRot[j]
            if muscleNames_HipRot[j][-1] == leg:
                rotMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, HipRotCoord)
                rotMomentArms[i, j] = rotMomentArm

                addMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, HipAddCoord)
                addMomentArms[i, j] = addMomentArm

        # Compute the moment arm knee
        for j in range(len(muscleNames_knee)):
            muscleIndex = muscleIndices_knee[j]
            if muscleNames_knee[j][-1] == leg:
                kneeFlexMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, flexCoordLknee)
                kneeFlexMomentArms[i, j] = kneeFlexMomentArm

        # Compute the moment arm ankle
        for j in range(len(muscleNames_ankle)):
            muscleIndex = muscleIndices_ankle[j]
            if muscleNames_ankle[j][-1] == leg:
                ankleFlexMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, flexCoordLank)
                ankleFlexMomentArms[i, j] = ankleFlexMomentArm

        # print time to compute one frame
        if i % 50 == 0:
            elapsed_time = time.time() - initial_time
            print(f"Time to compute frame {i}/{motion.getSize()}: {elapsed_time:.6f} seconds")
    # check discontinuities
    discontinuity = []
    muscle_action = []
    time_discontinuity = []

    fDistC = plt.figure('Discontinuity', figsize=(8, 8))
    plt.title(ik_output)

    save_folder = os.path.join(os.path.dirname(ik_output),'momentArmsCheck')

    def find_discontinuities(momArms, threshold, muscleNames, action, discontinuity, muscle_action, time_discontinuity):
        for i in range(momArms.shape[1]):
            dy = np.diff(momArms[:, i])
            discontinuity_indices = np.where(np.abs(dy) > threshold)[0]
            if discontinuity_indices.size > 0:
                print('Discontinuity detected at', muscleNames[i], 'at ', action, ' moment arm')
                plt.plot(momArms[:, i])
                plt.plot(discontinuity_indices, momArms[discontinuity_indices, i], 'rx')
                discontinuity.append(i)
                muscle_action.append(str(muscleNames[i] + ' ' + action + ' at frames: ' + str(discontinuity_indices)))
                time_discontinuity.append([time_vector[index] for index in discontinuity_indices])


        return discontinuity, muscle_action, time_discontinuity

    # hip flexion
    discontinuity, muscle_action, time_discontinuity = find_discontinuities(
        flexMomentArms, threshold, muscleNames_Hipflex, 'flexion', discontinuity, muscle_action, time_discontinuity)

    # hip adduction
    discontinuity, muscle_action, time_discontinuity = find_discontinuities(
        addMomentArms, threshold, muscleNames_HipAdd, 'adduction', discontinuity, muscle_action, time_discontinuity)

    # hip rotation
    discontinuity, muscle_action, time_discontinuity = find_discontinuities(
        rotMomentArms, threshold, muscleNames_HipRot, 'rotation', discontinuity, muscle_action, time_discontinuity)

    # knee flexion
    discontinuity, muscle_action, time_discontinuity = find_discontinuities(
        kneeFlexMomentArms, threshold, muscleNames_knee, 'flexion', discontinuity, muscle_action, time_discontinuity)
    
    # ankle flexion
    discontinuity, muscle_action, time_discontinuity = find_discontinuities(
        ankleFlexMomentArms, threshold, muscleNames_ankle, 'dorsiflexion', discontinuity, muscle_action, time_discontinuity)
    
    # plot discontinuities
    if len(discontinuity) > 0:
        plt.legend(muscle_action)
        plt.ylabel('Muscle Moment Arms with discontinuities (m)')
        plt.xlabel('Frame (after start time)')
        save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'discontinuities_' + leg + '.png'))
        print('\n\nYou should alter the model - most probably you have to reduce the radius of corresponding wrap objects for the identified muscles\n\n\n')

        # save txt file with discontinuities
        with open(os.path.join(save_folder, 'discontinuities_' + leg + '.txt'), 'w') as f:
            f.write(f"model file = {osim_modelPath}\n")
            f.write(f"motion file = {ik_output}\n")
            f.write(f"leg checked = {leg}\n")
            
            f.write("\n muscles with discontinuities \n", ) 
            
            for i in range(len(muscle_action)):
                try:
                    f.write("%s : time %s \n" % (muscle_action[i], time_discontinuity[i]))
                except:
                    print('no discontinuities detected')

        momentArmsAreWrong = 1
    else:
        plt.close(fDistC)
        print('No discontinuities detected')
        momentArmsAreWrong = 0

    # plot hip flexion
    plt.figure('flexMomentArms_' + leg, figsize=(8, 8))
    plt.plot(flexMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_output)
    plt.legend(muscleNames_Hipflex, loc='best')
    plt.ylabel('Hip Flexion Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'hip_flex_MomentArms_' + leg + '.png'))

    # hip adduction
    plt.figure('addMomentArms_' + leg, figsize=(8, 8))
    plt.plot(addMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_output)
    plt.legend(muscleNames_HipAdd, loc='best')
    plt.ylabel('Hip Adduction Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'hip_add_MomentArms_' + leg + '.png'))

    # hip rotation
    plt.figure('rotMomentArms_' + leg, figsize=(8, 8))
    plt.plot(rotMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_output)
    plt.legend(muscleNames_HipRot, loc='best')
    plt.ylabel('Hip Rotation Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'hip_rot_MomentArms_' + leg + '.png'))

    # knee flexion
    plt.figure('kneeFlexMomentArms_' + leg, figsize=(8, 8))
    plt.plot(kneeFlexMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_output)
    plt.legend(muscleNames_knee, loc='best')
    plt.ylabel('Knee Flexion Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'knee_MomentArms_' + leg + '.png'))

    # ankle flexion
    plt.figure('ankleFlexMomentArms_' + leg, figsize=(8, 8))
    plt.plot(ankleFlexMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_output)
    plt.legend(muscleNames_ankle, loc='best')
    plt.ylabel('Ankle Dorsiflexion Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'ankle_MomentArms_' + leg + '.png'))

    print('Moment arms checked for ' + ik_output)
    print('Results saved in ' + save_folder + ' \n\n' )

    return momentArmsAreWrong,  discontinuity, muscle_action

def compareMomentArms(osimModelPath1, osimModelPath2, m, ikPath2, coord_name):

    osimModel1 = osim.Model(osimModelPath1)
    osimModel2 = osim.Model(osimModelPath2)
    
    muscles1, indexes1 = muscles_per_coordinate(osimModel1, coord_name)
    muscles2, indexes2 = muscles_per_coordinate(osimModel2, coord_name)

    common_muscles = set(muscles1).intersection(set(muscles2))
    unique_to_model1 = set(muscles1) - common_muscles
    unique_to_model2 = set(muscles2) - common_muscles
    
    for muscle in unique_to_model1:
        print(f"Muscle {muscle} is only in model 1")

    return common_muscles, unique_to_model1, unique_to_model2

def get_factor():
    '''Prompt the user to enter a factor to increase muscle force.'''
    root = tk.Tk()
    root.withdraw()
    factor = simpledialog.askfloat(
        "Increase Factor",
        "Enter factor to multiply max isometric force (e.g., 1.2):",
        minvalue=0.0
    )
    root.destroy()
    return factor

def increase_muscle_force(osim_file=None, factor=None, save_path=None):
    '''Increase the max isometric force of muscles in the given osim file.'''
    root = tk.Tk() # prevent the main window from appearing
    root.withdraw()
    if osim_file is None:
        osim_file = select_osim_file()
        
    if not osim_file:
        messagebox.showinfo("Cancelled", "No file selected.")
        return
    
    if factor is None:
        factor = get_factor()
        
    if not factor:
        messagebox.showinfo("Cancelled", "No factor entered.")
        return

    model = osim.Model(osim_file)
    muscles = model.getMuscles()
    for i in range(muscles.getSize()):
        muscle = muscles.get(i)
        orig_force = muscle.getMaxIsometricForce()
        muscle.setMaxIsometricForce(orig_force * factor)

    if save_path is None:
        new_file = osim_file.replace('.osim', f'_increased_{factor:.2f}.osim')
    else:
        new_file = save_path
        
    model.printToXML(new_file)
    messagebox.showinfo("Done", f"Saved new model to:\n{new_file}")

def get_muscle_params(osimModelPath, muscleNamesList, printOutput=False):
    """Get the parameters of the specified muscles from the OpenSim model."""
    
    osimModel = osim.Model(osimModelPath)
    muscleSet = osimModel.getMuscles()
    musclesList = []

    for i, muscleName in enumerate(muscleNamesList):
        muscle = muscleSet.get(muscleName)
        if muscle:
            muscle.max_isometric_force = muscle.getMaxIsometricForce()
            muscle.optimal_fiber_length = muscle.getOptimalFiberLength()
            muscle.tendon_slack_length = muscle.getTendonSlackLength()
            muscle.specific_tension_N_cm2 = 15  # 150 and 155 kN/m2 DOI 10.1152/jappl.2001.90.3.865
            muscle.pennation_angle_rad = muscle.getPennationAngleAtOptimalFiberLength()
            muscle.physiological_cross_sectional_area_cm2 = muscle.getMaxIsometricForce() / muscle.specific_tension_N_cm2

            musclesList.append(muscle)
        
    print(f'[WARNING] for this muscle set, specific tension was assumed as {muscle.specific_tension_N_cm2} N/cm2')
    
    if printOutput:
        for i, muscleName in enumerate(muscleNamesList): 
            muscle = musclesList[i]
            print(f"Muscle parameters for {muscleName}: {muscle.getName()}")
            print(f"  Max Isometric Force: {muscle.getMaxIsometricForce()} N")
            print(f"  Optimal Fiber Length: {muscle.getOptimalFiberLength()} m")
            print(f"  Tendon Slack Length: {muscle.getTendonSlackLength()} m")
            print(f"  Physiological Cross-Sectional Area: {muscle.physiological_cross_sectional_area_cm2} cm^2")
    
    # return both model and muscleList so muscles keep attributes
    return osimModel, musclesList

def check_arg(arg=None,name=None):
    if arg is None:
        arg = input(f"Please provide a value for {name}: ").strip('"')
    
    if arg.startswith('[') and arg.endswith(']'):
        arg = [float(x.strip()) for x in arg.strip('[]').split(',')]

    return arg

# plotting
def save_fig(fig, save_path):
    """Saves the figure to the specified path."""
    if not os.path.exists(os.path.dirname(save_path)):
        os.makedirs(os.path.dirname(save_path))
    fig.savefig(save_path, bbox_inches='tight')
    print(f"Figure saved to {save_path}")

def get_screen_size():

    try:
        import tkinter as tk
        root = tk.Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return width, height
    except Exception as e:
        print(f"Error getting screen size: {e}")
        return None

def calculate_nRows_nCold(n_subplots):
    """
    Calculate the number of rows and columns for subplots based on the number of subplots.

    Args:
        n_subplots (int): The total number of subplots.

    Returns:
        tuple: (nrows, ncols) where nrows is the number of rows and ncols is the number of columns.
    """
    import numpy as np
    # Find the smallest nrows and ncols such that nrows * ncols >= n_subplots and (nrows-1) * ncols < n_subplots
    ncols = int(np.ceil(np.sqrt(n_subplots)))
    nrows = int(np.ceil(n_subplots / ncols))
    while (nrows - 1) * ncols >= n_subplots:
        nrows -= 1
    return nrows, ncols

# data manipulation
def time_normalise_df(df, fs=''):

    if not type(df) == pd.core.frame.DataFrame:
        raise Exception('Input must be a pandas DataFrame')
    
    if not fs:
        try:
            fs = 1/(df['time'][1]-df['time'][0])
        except  KeyError as e:
            raise Exception('Input DataFrame must contain a column named "time"')
    
    normalised_df = pd.DataFrame(columns=df.columns)

    for column in df.columns:
        normalised_df[column] = np.zeros(101)

        currentData = df[column]
        currentData = currentData[~np.isnan(currentData)]
        
        if currentData.empty:
            currentData = np.zeros(len(df))
        
        timeTrial = np.arange(0, len(currentData)/fs, 1/fs)           
        Tnorm = np.arange(0, timeTrial[-1], timeTrial[-1]/101)
        
        if len(Tnorm) == 102:
            Tnorm = Tnorm[:-1]
        normalised_df[column] = np.interp(Tnorm, timeTrial, currentData)
    
    return normalised_df

def get_unique_names(paths):
    # Split each path into parts
    split_paths = [p.split(os.sep) for p in paths]

    # Transpose to compare columns
    columns = list(zip(*split_paths))

    # Find the indices where not all elements are the same
    diff_indices = [i for i, col in enumerate(columns) if len(set(col)) > 1]

    # Create unique names using the differing parts
    unique_names = []
    for parts in split_paths:
        unique = "_".join([parts[i] for i in diff_indices])
        unique_names.append(unique)
    return unique_names

def create_color_and_style_dict(labels):
    """Creates a color and style dictionary based on unique labels.
    Args:
        labels (list): List of unique labels.
        Returns:
        tuple: Two dictionaries, one for colors and one for styles.
            
    Example:
        labels = ['Athlete_03_sq_70', 'Athlete_03_sq_75', 'Athlete_03_sq_80']
        color_dict, style_dict = create_color_and_style_dict(labels)
        
    """
    
    
    color_dict = {}
    style_dict = {}
    # Extract the number (e.g., 70, 75, 80, 85, 90) from each label for color assignment
    # Assume the number is always at the end after an underscore
    numbers = [label.split('_')[-1] for label in labels]
    unique_numbers = sorted(set(numbers), key=lambda x: int(x))
    color_map = matplotlib.colormaps['tab10']
    number_to_color = {num: color_map.colors[i % 10] for i, num in enumerate(unique_numbers)}
    for label, num in zip(labels, numbers):
        color_dict[label] = number_to_color[num]
        if 'mri' in label.lower():
            style_dict[label] = '--'
        else:
            style_dict[label] = '-'
    return color_dict, style_dict

# dir manipulation
def rename_all_files_in_dir(dir_path, old_str, new_str):
    """
    Renames all files in the specified directory by replacing old_str with new_str in their names.
    
    Args:
        dir_path (str): The path to the directory containing the files.
        old_str (str): The substring to be replaced in the file names.
        new_str (str): The substring to replace old_str with.
    """
    if not os.path.isdir(dir_path):
        raise ValueError(f"The provided path '{dir_path}' is not a valid directory.")
    
    for filename in os.listdir(dir_path):
        if old_str in filename:
            new_filename = filename.replace(old_str, new_str)
            try:
                os.rename(os.path.join(dir_path, filename), os.path.join(dir_path, new_filename))
                print(f"Renamed '{filename}' to '{new_filename}'")
            except Exception as e:
                print(f"Error renaming '{filename}': {e}")


class osimTools():
    """A collection of utility functions for OpenSim and data processing.
    
    functions with '_' the object to be created first because they refer to self
    Example:
        tools = osimTools()
        tools._printHello()
        
        osimTools.calculate_emg_linear_envelope(x)
        # katya
        # Utility functions.
        #
        # author: Dimitar Stanev <jimstanev@gmail.com>
        ##
    
    """
    
    def __init__(self, filepath=None):
        self.filepath = filepath

    def _printHello(self):
        print("Hello from osimTools!")

    def calculate_emg_linear_envelope(x, f_sampling=1000, f_band_low=30,
                                    f_band_high=300, f_env=6, to_normalize=True,
                                    plot=False):
        """Calculates the EMG linear envelope by applying the following
        transformations to the raw signal:

        1) Remove mean
        2) Band-pass 4th order Butterworth filter to remove low and high frequencies
        3) Full rectification (use of abs)
        4) Normalization based on max value (if to_normalize=True)
        5) Low-pass filter to calculate the envelope
        6) (optional) plot the raw and envelop signals (if plot=True); does not show plot just in the background

        """
        f_nyq = f_sampling / 2
        # 1) remove mean
        y = x - x.mean()
        # 2) band-pass
        b, a = signal.butter(4, [f_band_low / f_nyq, f_band_high / f_nyq], 'band')
        y = signal.filtfilt(b, a, y)
        # 3) rectify
        y = np.abs(y)
        # 4) normalize
        if to_normalize:
            y = y / y.max()

        # 5) low-pass
        b, a = signal.butter(2, f_env / f_nyq, 'low')
        env = signal.filtfilt(b, a, y)
        if plot:
            plt.figure()
            plt.plot(y, label='raw')
            plt.plot(env, label='envelop')
            plt.legend()
            
        return env


    def normalize_interpolate_dataframe(df, interp_column='time', method='linear'):
        """Normalizes time between [0, 1] and then re-samples data frame at
        constant interval.

        """
        # normalize between 0, 1
        time_old = df.time.to_numpy()
        time_new = (time_old - time_old[0]) / (time_old[-1] - time_old[0])
        df.loc[:, 'time'] = time_new
        # re-sample time with specific interval
        df = df.set_index(interp_column)
        at = np.arange(0, 1.01, 0.01)
        df = df.reindex(df.index | at)
        df = df.interpolate(method=method).loc[at]
        df = df.reset_index()
        df = df.rename(columns={'index': interp_column})
        return df

    def osim_vector_to_list(array):
        """Convert SimTK::Vector to Python list.
        """
        temp = []
        for i in range(array.size()):
            temp.append(array[i])

        return temp


    def vector_vec3_to_nparray(vector):
        temp = []
        for i in range(vector.size()):
            temp.append([vector[i][0], vector[i][1], vector[i][2]])

        return np.array(temp)


    def osim_array_to_list(array):
        """Convert OpenSim::Array<T> to Python list.
        """
        temp = []
        for i in range(array.getSize()):
            temp.append(array.get(i))

        return temp


    def list_to_osim_array_str(self, list_str):
        """Convert Python list of strings to OpenSim::Array<string>."""
        arr = opensim.ArrayStr()
        for element in list_str:
            arr.append(element)

        return arr


    def np_array_to_simtk_matrix(array):
        """Convert numpy array to SimTK::Matrix"""
        n, m = array.shape
        M = opensim.Matrix(n, m)
        for i in range(n):
            for j in range(m):
                M.set(i, j, array[i, j])

        return M


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


    def mm_to_m(table, label):
        """Scale from units in mm for units in m.

        Parameters
        ----------
        label: string containing the name of the column you want to convert

        """
        c = table.updDependentColumn(label)
        for i in range(c.size()):
            c[i] = opensim.Vec3(c[i][0] * 0.001, c[i][1] * 0.001, c[i][2] * 0.001)


    def mirror_z(table, label):
        """Mirror the z-component of the vector.

        Parameters
        ----------
        label: string containing the name of the column you want to convert

        """
        c = table.updDependentColumn(label)
        for i in range(c.size()):
            c[i] = opensim.Vec3(c[i][0], c[i][1], -c[i][2])


    def lowess_bell_shape_kern(x, y, tau=0.0005):
        """lowess_bell_shape_kern(x, y, tau = .005) -> y_est Locally weighted
        regression: fits a nonparametric regression curve to a scatterplot. The
        arrays x and y contain an equal number of elements; each pair (x[i], y[i])
        defines a data point in the scatterplot. The function returns the estimated
        (smooth) values of y.  The kernel function is the bell shaped function with
        parameter tau. Larger tau will result in a smoother curve.

        """
        n = len(x)
        y_est = np.zeros(n)

        # initializing all weights from the bell shape kernel function
        w = np.array([np.exp(- (x - x[i]) ** 2 / (2 * tau)) for i in range(n)])

        # looping through all x-points
        for i in range(n):
            weights = w[:, i]
            b = np.array([np.sum(weights * y), np.sum(weights * y * x)])
            A = np.array([[np.sum(weights), np.sum(weights * x)],
                        [np.sum(weights * x), np.sum(weights * x * x)]])
            theta = np.linalg.solve(A, b)
            y_est[i] = theta[0] + theta[1] * x[i]

        return y_est

    def _storage_to_dataframe(self, sto):
        print('Converting OpenSim Storage to pandas DataFrame')
        
        # for i in range(sto.getSize()):print(sto.getStateVector(i).getTime())
        for i in range(sto.getSize()):print(sto.getData(i))
        sto.printToFile()
        
        breakpoint()
        
    def _create_opensim_storage(self, time, data, column_names):
        """Creates a OpenSim::Storage.

        Parameters
        ----------
        time: SimTK::Vector

        data: SimTK::Matrix

        column_names: list of strings

        Returns
        -------
        sto: OpenSim::Storage

        """
        sto = opensim.Storage()
        sto.setColumnLabels(osimTools().list_to_osim_array_str(['time'] + column_names))
        for i in range(data.nrow()):
            row = opensim.ArrayDouble()
            for j in range(data.ncol()):
                value = data.getElt(i, j)
                if np.isnan(value):
                    value = 0
                row.append(value)
            sto.append(time[i], row)
        
        # self._storage_to_dataframe(sto)
        return sto


    def annotate_plot(ax, text):
        """Annotate a figure by adding a text.
        """
        at = AnchoredText(text, frameon=True, loc='upper left')
        at.patch.set_boxstyle('round, pad=0, rounding_size=0.2')
        ax.add_artist(at)


    def rmse_metric(s1, s2):
        """Root mean squared error between two time series.

        """
        # Signals are sampled with the same sampling frequency. Here time
        # series are first aligned.
        # if s1.index[0] < 0:
        #     s1.index = s1.index - s1.index[0]

        # if s2.index[0] < 0:
        #     s2.index = s2.index - s2.index[0]

        t1_0 = s1.index[0]
        t1_f = s1.index[-1]
        t2_0 = s2.index[0]
        t2_f = s2.index[-1]
        t_0 = np.round(np.max([t1_0, t2_0]), 3)
        t_f = np.round(np.min([t1_f, t2_f]), 3)
        x = s1[(s1.index >= t_0) & (s1.index <= t_f)].to_numpy()
        y = s2[(s2.index >= t_0) & (s2.index <= t_f)].to_numpy()
        return np.round(np.sqrt(np.mean((x - y) ** 2)), 3)


    def refine_ground_reaction_wrench(self,data_table, label_triplet, stance_threshold,
                                    tau, debug=True):
        """Clean and filter raw ground reaction forces at a single leg as specified by
        label triplet. This algorithm checks when the foot is in touch with the
        ground (stance phase). When the foot is not in touch then the original data
        contain noise with very small SNR. Therefore, the data is either set to zero
        or to nan. Then, the data is interpolated in case of nan. Finally, the
        signals are low pass filtered using lowess_bell_shape_kern.

        Parameters
        ----------

        data_table: OpenSim::DataTable<Vec3> containing [force, point, moment] for
        each leg

        label_triplet: column identifiers for the wrench triplet (e.g., ['f1', 'p1', 'm1'])

        stance_threshold: values to consider the foot in touch with the ground

        tau: kernel standard divination (filtering)

        debug: Boolean to visualize filtering result

        Returns
        -------

        This function mutates the original data_table

        """
        # get data of single leg
        t = np.array(data_table.getIndependentColumn())
        f = data_table.updDependentColumn(label_triplet[0])
        p = data_table.updDependentColumn(label_triplet[1])
        m = data_table.updDependentColumn(label_triplet[2])
        f_l = self.vector_vec3_to_nparray(f)
        p_l = self.vector_vec3_to_nparray(p)
        m_l = self.vector_vec3_to_nparray(m)

        # debugging
        if debug:
            plt.figure()
            f1 = plt.gca()
            f1.plot(t, f_l)
            plt.figure()
            f2 = plt.gca()
            f2.plot(t, p_l)
            plt.figure()
            f3 = plt.gca()
            f3.plot(t, m_l)

        # remove information when the foot is not touching the ground
        t0 = None
        tf = None
        for i in range(len(f_l)):
            # remove noise
            if f_l[i, 1] < stance_threshold:
                for j in range(3):
                    f_l[i, j] = 0
                    p_l[i, j] = np.nan
                    m_l[i, j] = 0

            # detect heel strike
            if t0 is None and f_l[i, 1] >= stance_threshold:
                t0 = t[i]

            # detect toe off
            if tf is None and t0 is not None and f_l[i, 1] <= stance_threshold:
                tf = t[i]

        # interpolate nan values for points and moments
        f_l = pd.DataFrame(f_l).interpolate(limit_direction="both", kind="cubic").to_numpy()
        p_l = pd.DataFrame(p_l).interpolate(limit_direction="both", kind="cubic").to_numpy()
        m_l = pd.DataFrame(m_l).interpolate(limit_direction="both", kind="cubic").to_numpy()

        # filter data
        for j in range(3):
            # f_l[:, j] = signal.medfilt(f_l[:, j], median)
            f_l[:, j] = lowess_bell_shape_kern(t, f_l[:, j], tau)
            p_l[:, j] = lowess_bell_shape_kern(t, p_l[:, j], tau)
            m_l[:, j] = lowess_bell_shape_kern(t, m_l[:, j], tau)

        # debugging
        if debug:
            f1.plot(t, f_l)
            f2.plot(t, p_l)
            f3.plot(t, m_l)

        # update columns in the original data
        for i in range(f_l.shape[0]):
            f[i] = opensim.Vec3(f_l[i, 0], f_l[i, 1], f_l[i, 2])
            p[i] = opensim.Vec3(p_l[i, 0], p_l[i, 1], p_l[i, 2])
            m[i] = opensim.Vec3(m_l[i, 0], m_l[i, 1], m_l[i, 2])

        return t0, tf, p_l.mean(axis=0)

    def read_from_storage(self, file_name, sampling_interval=0.01,
                        to_filter=False):
        """Read OpenSim.Storage files.

        Parameters
        ----------
        file_name: (string) path to file

        sampling_interval: resample the data with a given interval (0.01)

        to_filter: use low pass 4th order FIR filter with 6Hz cut off
        frequency

        Returns
        -------
        df: pandas data frame

        """
        sto = opensim.Storage(file_name)
        sto.resampleLinear(sampling_interval)
        if to_filter:
            sto.lowpassFIR(4, 6)

        labels = osim_array_to_list(sto.getColumnLabels())
        time = opensim.ArrayDouble()
        sto.getTimeColumn(time)
        time = osim_array_to_list(time)
        data = []
        for i in range(sto.getSize()):
            temp = osim_array_to_list(sto.getStateVector(i).getData())
            temp.insert(0, time[i])
            data.append(temp)

        df = pd.DataFrame(data, columns=labels)
        df.index = df.time
        return df


    def index_containing_substring(list_str, pattern):
        """For a given list of strings finds the index of the element that
        contains the substring.

        Parameters
        ----------
        list_str: list of str

        pattern: str
            pattern


        Returns
        -------
        indices: list of int
            the indices where the pattern matches

        """
        return [i for i, item in enumerate(list_str)
                if re.search(pattern, item)]


    def _plot_sto_file(self,file_name, plot_file, plots_per_row=4, pattern=None,
                    title_function=lambda x: x):
        """Plots the .sto file (OpenSim) by constructing a grid of subplots.

        Parameters
        ----------
        sto_file: str
            path to file
        plot_file: str
            path to store result
        plots_per_row: int
            subplot columns
        pattern: str, optional, default=None
            plot based on pattern (e.g. only pelvis coordinates)
        title_function: lambda
            callable function f(str) -> str
        """
        df = osimTools().read_from_storage(file_name)
        labels = df.columns.to_list()
        data = df.to_numpy()

        if pattern is not None:
            indices = index_containing_substring(labels, pattern)
        else:
            indices = range(1, len(labels))

        n = len(indices)
        ncols = int(plots_per_row)
        nrows = int(np.ceil(float(n) / plots_per_row))
        pages = int(np.ceil(float(nrows) / ncols))
        if ncols > n:
            ncols = n

        with PdfPages(plot_file) as pdf:
            for page in range(0, pages):
                fig, ax = plt.subplots(nrows=ncols, ncols=ncols,
                                    figsize=(8, 8))
                ax = ax.flatten()
                for pl, col in enumerate(indices[page * ncols ** 2:page *
                                                ncols ** 2 + ncols ** 2]):
                    ax[pl].plot(data[:, 0], data[:, col])
                    ax[pl].set_title(title_function(labels[col]))

                fig.tight_layout()
                pdf.savefig(fig)
                plt.close()


    def adjust_model_mass(model_file, mass_change):
        """Given a required mass change adjust all body masses accordingly.

        """
        rra_model = opensim.Model(model_file)
        rra_model.setName('model_adjusted')
        state = rra_model.initSystem()
        current_mass = rra_model.getTotalMass(state)
        new_mass = current_mass + mass_change
        mass_scale_factor = new_mass / current_mass
        for body in rra_model.updBodySet():
            body.setMass(mass_scale_factor * body.getMass())

        # save model with adjusted body masses
        rra_model.printToXML(model_file)


    def replace_thelen_muscles_with_millard(model_file, target_folder):
        """Replaces Thelen muscles with Millard muscles so that we can disable
        tendon compliance and perform MuscleAnalysis to compute normalized
        fiber length/velocity without spikes.

        """
        model = opensim.Model(model_file)
        new_force_set = opensim.ForceSet()
        force_set = model.getForceSet()
        for i in range(force_set.getSize()):
            force = force_set.get(i)
            muscle = opensim.Muscle.safeDownCast(force)
            millard_muscle = opensim.Millard2012EquilibriumMuscle.safeDownCast(
                force)
            thelen_muscle = opensim.Thelen2003Muscle.safeDownCast(force)
            if muscle is None:
                new_force_set.adoptAndAppend(force.clone())
            elif millard_muscle is not None:
                millard_muscle = millard_muscle.clone()
                millard_muscle.set_ignore_tendon_compliance(True)
                new_force_set.adoptAndAppend(millard_muscle)
            elif thelen_muscle is not None:
                millard_muscle = opensim.Millard2012EquilibriumMuscle()
                # properties
                millard_muscle.set_default_activation(
                    thelen_muscle.getDefaultActivation())
                millard_muscle.set_activation_time_constant(
                    thelen_muscle.get_activation_time_constant())
                millard_muscle.set_deactivation_time_constant(
                    thelen_muscle.get_deactivation_time_constant())
                # millard_muscle.set_fiber_damping(0)
                # millard_muscle.set_tendon_strain_at_one_norm_force(
                #     thelen_muscle.get_FmaxTendonStrain())
                millard_muscle.setName(thelen_muscle.getName())
                millard_muscle.set_appliesForce(thelen_muscle.get_appliesForce())
                millard_muscle.setMinControl(thelen_muscle.getMinControl())
                millard_muscle.setMaxControl(thelen_muscle.getMaxControl())
                millard_muscle.setMaxIsometricForce(
                    thelen_muscle.getMaxIsometricForce())
                millard_muscle.setOptimalFiberLength(
                    thelen_muscle.getOptimalFiberLength())
                millard_muscle.setTendonSlackLength(
                    thelen_muscle.getTendonSlackLength())
                millard_muscle.setPennationAngleAtOptimalFiberLength(
                    thelen_muscle.getPennationAngleAtOptimalFiberLength())
                millard_muscle.setMaxContractionVelocity(
                    thelen_muscle.getMaxContractionVelocity())
                # millard_muscle.set_ignore_tendon_compliance(
                #     thelen_muscle.get_ignore_tendon_compliance())
                millard_muscle.set_ignore_tendon_compliance(True)
                millard_muscle.set_ignore_activation_dynamics(
                    thelen_muscle.get_ignore_activation_dynamics())
                # muscle path
                pathPointSet = thelen_muscle.getGeometryPath().getPathPointSet()
                geomPath = millard_muscle.updGeometryPath()
                for j in range(pathPointSet.getSize()):
                    pathPoint = pathPointSet.get(j).clone()
                    geomPath.updPathPointSet().adoptAndAppend(pathPoint)

                # append
                new_force_set.adoptAndAppend(millard_muscle)
            else:
                raise RuntimeError(
                    'cannot handle the type of muscle: ' + force.getName())

        new_force_set.printToXML(os.path.join(target_folder, 'muscle_set.xml'))


    def subject_specific_isometric_force(generic_model_file, subject_model_file,
                                        height_generic, height_subject):
        """Adjust the max isometric force of the subject-specific model based on results
        from Handsfield et al. 2014 [1] (equation from Fig. 5A). Function adapted
        from Rajagopal et al. 2015 [2].

        Given the height and mass of the generic and subject models, we can
        calculate the total muscle volume [1]:

        V_total = 47.05 * mass * height + 1289.6

        Since we can calculate the muscle volume and the optimal fiber length of the
        generic and subject model, respectively, we can calculate the force scale
        factor to scale the maximum isometric force of each muscle:

        scale_factor = (V_total_subject / V_total_generic) / (l0_subject / l0_generic)

        F_max_i = scale_factor * F_max_i

        [1] http://dx.doi.org/10.1016/j.jbiomech.2013.12.002
        [2] http://dx.doi.org/10.1109/TBME.2016.2586891

        """
        model_generic = opensim.Model(generic_model_file)
        state_generic = model_generic.initSystem()
        mass_generic = model_generic.getTotalMass(state_generic)

        model_subject = opensim.Model(subject_model_file)
        state_subject = model_subject.initSystem()
        mass_subject = model_subject.getTotalMass(state_subject)

        # formula for total muscle volume
        V_total_generic = 47.05 * mass_generic * height_generic + 1289.6
        V_total_subject = 47.05 * mass_subject * height_subject + 1289.6

        for i in range(0, model_subject.getMuscles().getSize()):
            muscle_generic = model_generic.updMuscles().get(i)
            muscle_subject = model_subject.updMuscles().get(i)

            l0_generic = muscle_generic.getOptimalFiberLength()
            l0_subject = muscle_subject.getOptimalFiberLength()

            force_scale_factor = (V_total_subject / V_total_generic) / (l0_subject /
                                                                        l0_generic)
            muscle_subject.setMaxIsometricForce(force_scale_factor *
                                                muscle_subject.getMaxIsometricForce())

        model_subject.printToXML(subject_model_file)

    ####
    
    
# CEINMS

def read_excitation_generator(file):
    """Reads a CEINMS excitation generator file and returns a dictionary
    containing the osim_muscles that match with each EMG signal

    """
    tree = ET.parse(file)
    root = tree.getroot()

    # look for '\excitationGenerator\mapping'
    excitations = root.findall('.//excitation')
    emg_to_muscles = dict()
    for excitation in excitations:
        muscle = excitation.get('id')
        try:
            emg_name = excitation.find('.//input').text
        except:
            emg_name = None
        emg_to_muscles[muscle] = emg_name

    return emg_to_muscles

# ObjectOrientation
class Plotter():
    def __init__(self):
        self.dataList = []
    
    def addDataFrame(self, dataframe):
        self.dataList.append(dataframe)

    def plotListDataFrames(self, xColumn, yColumns, labels):
        # Example plotting function
        for df, label in zip(self.dataList, labels):
            plt.plot(df[xColumn], df[yColumns], label=label)

        plt.legend()
        plt.show()




if __name__ == "__main__":
    
    # Command line interface for the utils module
    if len(sys.argv) < 1:
        command = input("Please provide a command from the list: ")
    else:
        command = sys.argv[1] # Use arguments from the command line
    
    if command is not None:
        
        if command == "hello":
            print("hello")

        elif command == "load_trc":
            if len(sys.argv) > 2:
                path = sys.argv[2]
                data = load_trc(path, output=1)
            else:
                print("Please provide the path to the .trc file. Example: python utils.py load_trc path/to/file.trc")
        elif command == "load_mot":
            if len(sys.argv) > 2:
                path = sys.argv[2]
                data = load_mot(path, output=1)
            else:
                print("Please provide the path to the .mot file. Example: python utils.py load_mot path/to/file.mot")
        elif command == "load_sto":
            if len(sys.argv) > 2:
                path = sys.argv[2]
                data = load_sto(path, output=1)
            else:
                print("Please provide the path to the .sto file. Example: python utils.py load_sto path/to/file.sto")
        elif command == "load_c3d":
            if len(sys.argv) > 2:
                path = sys.argv[2]
                data = load_c3d(path, output=1)
            else:
                print("Please provide the path to the .c3d file. Example: python utils.py load_c3d path/to/file.c3d")
        elif command == "load_data_file":
            if len(sys.argv) > 2:
                path = sys.argv[2]
                data, metadata = load_data_file(path)
                print("Data loaded successfully.")
                print("Metadata:", metadata)
            else:
                print("Please provide the path to the data file. Example: python utils.py load_data_file path/to/file.txt")
                
        elif command == "save_data_file":
            if len(sys.argv) > 3:
                path = sys.argv[2]
                data = pd.read_csv(sys.argv[3], sep='\t')

        elif command == "activate_cmd_env":
            activate_cmd_env()

        elif command == "get_screen_size":
            screen_size = get_screen_size()
            if screen_size:
                print(f"Screen size: {screen_size[0]}x{screen_size[1]}")
            else:
                print("Could not determine screen size.")      
        
        elif command == "calculate_nRows_nCols":
            if len(sys.argv) > 2:
                n_subplots = int(sys.argv[2])
                nrows, ncols = calculate_nRows_nCold(n_subplots)
                print(f"Calculated rows: {nrows}, columns: {ncols} for {n_subplots} subplots.")
            else:
                print("Please provide the number of subplots. Example: python utils.py calculate_nRows_nCols 9")
        elif command == "increase_muscle_force":
            if len(sys.argv) > 2:
                osim_file = sys.argv[2]
                factor = float(sys.argv[3]) if len(sys.argv) > 3 else None
                save_path = sys.argv[4] if len(sys.argv) > 4 else None
                increase_muscle_force(osim_file, factor, save_path)
            else:
                print("Please provide the OpenSim model file path and optionally a factor and save path. Example: python utils.py increase_muscle_force path/to/model.osim 1.2 path/to/save.osim")
        elif command == "rename_all_files_in_dir":
            if len(sys.argv) > 4:
                dir_path = sys.argv[2]
                old_str = sys.argv[3]
                new_str = sys.argv[4]
                rename_all_files_in_dir(dir_path, old_str, new_str)
            else:
                print("Please provide the directory path, old string, and new string. Example: python utils.py rename_all_files_in_dir path/to/dir old_string new_string")
        elif command == "read_excitation_generator":
            read_excitation_generator(sys.argv[2])
        elif command == 'compareMomentArms':
            modelpath1 = input("Enter path to first model: ")
            modelpath2 = input("Enter path to second model: ")
            joint = input("Enter coordinate name: ")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: ")
            print("  hello")
            print("  load_trc")
            print("  load_mot")
            print("  load_sto")
            print("  load_c3d")
            print("  load_data_file")
            print("  save_data_file")
            print("  get_screen_size")
            print("  calculate_nRows_nCols")
            print("  increase_muscle_force")
            print("  rename_all_files_in_dir")
            print("  read_excitation_generator")
# END



