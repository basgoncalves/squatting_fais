import numpy as np
import opensim as osim
import pandas as pd
import utils
import os
import datetime
import matplotlib.pyplot as plt
import exportC3D
import settings
from xml.etree import ElementTree as ET


def terminal_warnings(mode='off'):
    """Set OpenSim terminal warnings on or off."""
    if mode == 'off':
        osim.Logger.setLevelString('warning')
        print("OpenSim terminal warnings turned OFF.")
    elif mode == 'on':
        osim.Logger.setLevelString('info')
        print("OpenSim terminal warnings turned ON.")
    else:
        print("Invalid mode. Use 'on' or 'off'.")

# Model editing functions
def scale_body_masses(osim_modelPath):
    """ 
    Scale the body masses of model_target to match the percentages of model_reference.
    """

    model_ref = osim.Model(osim_modelPath)

    model_targ_path = osim_modelPath.replace('.osim', '_scaledMasses.osim')
    model_targ = osim.Model(model_targ_path)

    state1 = model_ref.initSystem()
    state2 = model_targ.initSystem()

    # prnt model weight
    print(f"Model: {model_ref.getName()}, Weight: {model_ref.getTotalMass(state1)} kg")
    print(f"Model: {model_targ.getName()}, Weight: {model_targ.getTotalMass(state2)} kg")

    # Compare each body's mass between model1 and model2
    bodyset_ref = {body.getName(): body for body in model_ref.getBodySet()}
    bodyset_targ = {body.getName(): body for body in model_targ.getBodySet()}

    print("\nComparison of body masses between model1 and model2:")

    for body_name in bodyset_ref:
        if body_name in bodyset_targ:
            mass_ref = bodyset_ref[body_name].getMass()
            mass_targ = bodyset_targ[body_name].getMass()
            percent_mass_ref = (mass_ref / model_ref.getTotalMass(state1)) * 100
            percent_mass_targ = (mass_targ / model_targ.getTotalMass(state2)) * 100
            print(f"Body: {body_name}, Model1 Mass: {mass_ref} kg ({percent_mass_ref:.2f}%), Model2 Mass: {mass_targ} kg ({percent_mass_targ:.2f}%)")
            
            # change mass of body in model2 to match model1 percentage
            if percent_mass_ref != percent_mass_targ:
                new_body_mass_targ = (percent_mass_ref / 100) * model_targ.getTotalMass(state2)
                bodyset_targ[body_name].setMass(new_body_mass_targ)
                print(f"Updated Model2 {body_name} mass to: {new_body_mass_targ} kg, {percent_mass_ref:.2f}%")
            
        else:
            mass_ref = bodyset_ref[body_name].getMass()
            print(f"Body: {body_name}, Model1 Mass: {mass_ref} kg, Model2 Mass: Not Found")
            
    # save model2 with updated masses
    model_targ.setName(model_targ.getName() + "_updated_masses")
    model_targ.printToXML(model_targ_path)
    print(f"\nUpdated model saved to: {model_targ_path}")

        
    return model_targ

def add_mass_to_body(osim_modelPath, body_name, mass_to_add):
    """
    Add a specific mass to a body in the OpenSim model.
    """
    model = osim.Model(osim_modelPath)
    state = model.initSystem()

    save_path = osim_modelPath.replace('.osim', '_updatedMasses.osim')

    body = model.getBodySet().get(body_name)
    
    if body:
        current_mass = body.getMass()
        new_mass = current_mass + mass_to_add
        body.setMass(new_mass)
        model.printToXML(save_path)
        print(f"Updated {body_name} mass from {current_mass} kg to {new_mass} kg.")
    else:
        print(f"Body '{body_name}' not found in the model.")

def print_body_mass_per_segment(osim_modelPath=None):
    """ 
    Print the mass of each body segment in the OpenSim model.
    """
    if not osim_modelPath:
        osim_modelPath = input("Enter path to OpenSim model (.osim): ").strip('"')
    
    model = osim.Model(osim_modelPath)
    state = model.initSystem()

    print("Body Segment Masses:")
    for body in model.getBodySet():
        print(f"{body.getName()}: {body.getMass()} kg ({body.getMass() / model.getTotalMass(state) * 100:.2f}%)")

def increase_isometric_force(osim_modelPath=None, muscleList='all', factor: float = None):
    """
    Increase the isometric force of a specified muscle by a given factor.
    """
    if not osim_modelPath:
        osim_modelPath = input("Enter path to OpenSim model (.osim): ").strip('"')
    
    if not factor:
        factor = float(input("Enter factor to increase max isometric force (e.g., 1.2 for 20% increase): "))

    model = osim.Model(osim_modelPath)
    
    if muscleList == 'all':
        muscleList = []
        for muscle in model.getMuscles():
            muscleList.append(muscle.getName())
    
    for muscle_name in muscleList:
        muscle = model.getMuscles().get(muscle_name)
        if muscle:
            current_f0 = muscle.getMaxIsometricForce()
            new_f0 = current_f0 * factor
            muscle.setMaxIsometricForce(new_f0)
            print(f"Updated {muscle_name} max isometric force from {current_f0} N to {new_f0} N.")
        else:
            print(f"Muscle '{muscle_name}' not found in the model.")

    model.printToXML(osim_modelPath.replace('.osim', f'_increased_{factor:.2f}.osim'))

    print(f"Updated model saved to: {osim_modelPath.replace('.osim', f'_increased_{factor:.2f}.osim')}")

def lock_model_coordinates(osim_modelPath=None, coordinates_to_lock: list = None, save_path=None, unlock=False):
    """
    Lock specified coordinates in the OpenSim model.
    """
    if not osim_modelPath:
        osim_modelPath = input("Enter path to OpenSim model (.osim): ").strip('"')
    
    if not coordinates_to_lock:
        coordinates_to_lock = input("Enter coordinates to lock (comma-separated): ").split(',')

    model = osim.Model(osim_modelPath)
    state = model.initSystem()
    
    for coord_name in coordinates_to_lock:
        coord = model.getCoordinateSet().get(coord_name)
        if coord:
            if unlock:
                coord.setDefaultLocked(False)
                print(f"Unlocked coordinate: {coord_name}")
            else:
                coord.setDefaultLocked(True)
                print(f"Locked coordinate: {coord_name}")
        else:
            print(f"Coordinate '{coord_name}' not found in the model.")

    if not save_path:
        save_path = osim_modelPath.replace('.osim', '_lockedCoords.osim')
    model.printToXML(save_path)
    print(f"Updated model with locked coordinates saved to: {save_path}")

def coord_moment_arms(osim_model, muscle_list):
    '''Check which coordinates the muscles in the list have moment arms about (non-zero across the range of the model)'''

    model = osim.Model(osim_model)
    state = model.initSystem()
    coord_moment_arms = {}

    for muscle_name in muscle_list:
        try:
            muscle = model.getMuscles().get(muscle_name)
            moment_arms = {}
            for i in range(model.getNumCoordinates()):
                coord = model.getCoordinateSet().get(i)
                model.realizePosition(state)
                moment_arm_value = muscle.computeMomentArm(state, coord)
                if not np.isclose(moment_arm_value, 0):
                    moment_arms[coord.getName()] = moment_arm_value
            coord_moment_arms[muscle_name] = moment_arms
        except Exception as e:
            print(f"Error processing muscle {muscle_name}: {e}")
    
    coord_names = set()
    for muscle, mom_arms in coord_moment_arms.items():
        for coord in mom_arms.keys():
            if not np.isnan(mom_arms[coord]):
                coord_names.add(coord)

    return coord_names

def add_wrapping_surfaces(reference_model_path=None, target_model_path=None, output_model_path=None):
    """
    Add wrapping surfaces from reference OpenSim model to target model.
    
    Args:
        reference_model_path (str): Path to reference .osim file
        target_model_path (str): Path to target .osim file
        output_model_path (str): Path for output .osim file with wrapping surfaces
    """

    # prompt user for paths if not provided
    if not reference_model_path:
        reference_model_path = input("Enter path to reference OpenSim model (.osim): ").strip('"')
    if not target_model_path:
        target_model_path = input("Enter path to target OpenSim model (.osim): ").strip('"')
    if not output_model_path:
        output_model_path = input("Enter path to save output OpenSim model with wrapping surfaces (.osim): ").strip('"')

    # turn off OpenSim terminal warnings for cleaner output    terminal_warnings('off')
    try:
        # Load both models
        reference_model = osim.Model(reference_model_path)
        target_model = osim.Model(target_model_path)
        
        # Get wrapping surfaces from reference model
        reference_bodies = reference_model.getBodySet()
        target_bodies = target_model.getBodySet()
        
        # Add wrapping surfaces to target model
        for i in range(reference_bodies.getSize()):
            ref_body = reference_bodies.get(i)
            wrapping_surfaces = ref_body.getWrapObjectSet()
            
            if wrapping_surfaces.getSize() > 0:
                try:
                    # find matching body in target model
                    target_body = target_bodies.get(ref_body.getName())
                    target_wrap_set = target_body.getWrapObjectSet()
                    
                    for j in range(wrapping_surfaces.getSize()):
                        wrap_obj = wrapping_surfaces.get(j)
                        wrap_name = wrap_obj.getName()
                        
                        # Check if surface already exists
                        if target_wrap_set.getIndex(wrap_name) >= 0:
                            print(f"Skipped wrapping surface '{wrap_name}' on body '{target_body.getName()}' (already exists)")
                        else:
                            target_body.addWrapObject(wrap_obj)
                            print(f"Added wrapping surface '{wrap_name}' to body '{target_body.getName()}'")
                except RuntimeError:
                    print(f"Body '{ref_body.getName()}' not found in target model")
        
        # change model name to avoid confusion
        target_model.setName(target_model.getName() + "_with_wrapping")

        # Save output model
        target_model.printToXML(output_model_path)
        print(f"\nModel saved to: {output_model_path}")
        
    except ImportError:
        print("Error: OpenSim Python API not installed. Please install opensim package.")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

def edit_model_range_coordinates(osim_modelPath, coordinate_name, new_range: list, save_path):
    """
    Edit the range of motion for a specific coordinate in the OpenSim model.

    Args:
        osim_modelPath (str): Path to the .osim model file
        coordinate_name (str): Name of the coordinate to edit
        new_range (list): New range of motion as [min, max] in radians
        save_path (str): Path to save the modified model

    """
    model = osim.Model(osim_modelPath)
    state = model.initSystem()

    coordinate = model.getCoordinateSet().get(coordinate_name)

    if coordinate:
        current_range = (coordinate.getRangeMin(), coordinate.getRangeMax())
        coordinate.setRangeMin(new_range[0])
        coordinate.setRangeMax(new_range[1])
        model.printToXML(save_path)
        print(f"Updated {coordinate_name} range from {current_range} to {new_range}.")
    else:
        print(f"Coordinate '{coordinate_name}' not found in the model.")

def add_wrapping_surface_to_model(model_path, surface_name, wrap_name, save_path=None):
    """
    Add a wrapping surface to an OpenSim model.
    
    Args:
        model_path (str): Path to the .osim model file
        surface_name (str): Name of the wrapping surface to add
        wrap_name (str): Name of the wrap object to create
        save_path (str, optional): Path to save the modified model. If None, saves to model_path with '_wrap_added' suffix
    
    Returns:
        str: Path to the saved model file
    """
    
    # Load model
    model = osim.Model(model_path)
    
    # Initialize system
    state = model.initSystem()
    
    try:
        # Create wrapping surface (example: a cylinder)
        wrap_surface = osim.WrapCylinder(surface_name, 0.05, 0.1)  # name, radius, length
        
        # Add wrapping surface to model
        model.addWrapObject(wrap_surface)
        
        print(f"Added wrapping surface: {surface_name}")
        
    except Exception as e:
        print(f"Error adding wrapping surface '{surface_name}': {e}")
    
    # Finalize connections and initialize system
    model.finalizeConnections()
    
    # Determine save path
    if save_path is None:
        base_name = os.path.splitext(model_path)[0]
        save_path = f"{base_name}_wrap_added.osim"
    
    # change model name to indicate wrap added
    model.setName(model.getName() + "_wrap_added")

    # Save the modified model
    model.printToXML(save_path)
    
    print(f"Modified model saved to: {save_path}")
    
    return save_path

def add_muscles_to_model(source_model_path, target_model_path, muscle_names, save_path=None):
    """
    Add muscles from a source OpenSim model to a target OpenSim model.
    
    Args:
        source_model_path (str): Path to the source .osim model file
        target_model_path (str): Path to the target .osim model file
        muscle_names (list): List of muscle names to copy from source to target
        save_path (str, optional): Path to save the modified model. If None, saves to target_model_path with '_muscles_added' suffix
    
    Returns:
        str: Path to the saved model file
    """
    
    # Load models
    source_model = osim.Model(source_model_path)
    target_model = osim.Model(target_model_path)
    
    # Initialize systems
    source_state = source_model.initSystem()
    target_state = target_model.initSystem()
    
    muscles_added = []
    muscles_skipped = []
    
    for muscle_name in muscle_names:
        try:
            # Check if muscle already exists in target
            if target_model.getMuscles().contains(muscle_name):
                print(f"Muscle '{muscle_name}' already exists in target model. Skipping.")
                muscles_skipped.append(muscle_name)
                continue
            
            # Get muscle from source model
            source_muscle = source_model.getMuscles().get(muscle_name)
            
            # Clone the muscle
            cloned_muscle = source_muscle.clone()
            
            # Add to target model
            target_model.addForce(cloned_muscle)
            
            # Find wrap objects referenced by this muscle's geometry path
            source_path_wraps = source_muscle.getGeometryPath().getWrapSet()

            for i in range(source_path_wraps.getSize()):
                path_wrap = source_path_wraps.get(i)
                wrap_object_name = path_wrap.getWrapObjectName()

                # Search all bodies in source model for the wrap object
                source_wrap_obj = None
                source_body = None
                body_set = source_model.getBodySet()
                for b in range(body_set.getSize()):
                    body = body_set.get(b)
                    wrap_set = body.getWrapObjectSet()
                    for w in range(wrap_set.getSize()):
                        if wrap_set.get(w).getName() == wrap_object_name:
                            source_wrap_obj = wrap_set.get(w)
                            source_body = body
                            break
                    if source_wrap_obj is not None:
                        break

                if source_wrap_obj is None:
                    print(f"Wrap object '{wrap_object_name}' not found in source model. Skipping.")
                    continue

                target_body_name = source_body.getName()
                if not target_model.getBodySet().contains(target_body_name):
                    print(f"Body '{target_body_name}' not found in target model. Cannot add wrap object '{wrap_object_name}'.")
                    continue

                target_body = target_model.getBodySet().get(target_body_name)
                target_wrap_set = target_body.getWrapObjectSet()

                # Check if wrap object already exists on that body
                wrap_exists = any(target_wrap_set.get(w).getName() == wrap_object_name
                                  for w in range(target_wrap_set.getSize()))
                if not wrap_exists:
                    cloned_wrap = source_wrap_obj.clone()
                    target_body.addWrapObject(cloned_wrap)
                    print(f"Added wrap object: {wrap_object_name} to body: {target_body_name} for muscle: {muscle_name}")
                else:
                    print(f"Wrap object '{wrap_object_name}' already exists on body '{target_body_name}'. Skipping.")
            muscles_added.append(muscle_name)
            print(f"Added muscle: {muscle_name}")
     
        except Exception as e:
            print(f"Error adding muscle '{muscle_name}': {e}")
            muscles_skipped.append(muscle_name)
    
    # Finalize connections and initialize system
    target_model.finalizeConnections()
    
    # Determine save path
    if save_path is None:
        base_name = os.path.splitext(target_model_path)[0]
        save_path = f"{base_name}_muscles_added.osim"
    
    # change model name to indicate muscles added
    target_model.setName(target_model.getName() + "_muscles_added")

    # Save the modified model
    target_model.printToXML(save_path)
    
    print(f"\n=== Summary ===")
    print(f"Muscles added: {len(muscles_added)}")
    print(f"Muscles skipped: {len(muscles_skipped)}")
    print(f"Modified model saved to: {save_path}")
    
    return save_path

def copy_model_coordinate(src_model=None, target_model=None, coordinate_name=None, target_joint_name=None):
    """Copy one or more coordinates from a source model to a target model via XML manipulation.

    coordinate_name: str or list of str
    target_joint_name: str, list of str (matched by index to coordinate_name), or None
        If None, the source joint name is used for each coordinate.

    Adds each coordinate to the target joint's <coordinates> list and mirrors
    any SpatialTransform/TransformAxis references from the source joint.
    """
    import copy

    if not src_model:
        src_model = input("Enter the path to the source model (.osim): ")
    if not target_model:
        target_model = input("Enter the path to the target model (.osim): ")
    if not coordinate_name:
        coordinate_name = input("Enter coordinate name(s) (comma-separated): ").split(',')

    # Normalise to lists
    if isinstance(coordinate_name, str):
        coordinate_name = [coordinate_name]
    if target_joint_name is None:
        target_joint_name = [None] * len(coordinate_name)
    elif isinstance(target_joint_name, str):
        target_joint_name = [target_joint_name] * len(coordinate_name)

    src_tree = ET.parse(src_model)
    tar_tree = ET.parse(target_model)
    src_root = src_tree.getroot()
    tar_root = tar_tree.getroot()

    src_parent_map = {c: p for p in src_root.iter() for c in p}
    _skip_tags = {'CoordinateSet', 'coordinates', 'objects', 'groups', 'components'}

    for coord_name, joint_override in zip(coordinate_name, target_joint_name):

        # --- Find coordinate element and parent joint in source ---
        src_coord_elem = None
        for coord in src_root.iter('Coordinate'):
            if coord.get('name') == coord_name:
                src_coord_elem = coord
                break
        if src_coord_elem is None:
            print(f"Warning: Coordinate '{coord_name}' not found in source model. Skipping.")
            continue

        src_joint_name = None
        src_joint_elem = None
        elem = src_coord_elem
        while elem in src_parent_map:
            parent = src_parent_map[elem]
            if parent.get('name') and parent.tag not in _skip_tags:
                src_joint_name = parent.get('name')
                src_joint_elem = parent
                break
            elem = parent
        print(f"Found coordinate '{coord_name}' in joint '{src_joint_name}'.")

        # Find which TransformAxis names in source reference this coordinate
        src_axes_referencing = []
        if src_joint_elem is not None:
            for axis in src_joint_elem.iter('TransformAxis'):
                coords_elem = axis.find('coordinates')
                if coords_elem is not None and coords_elem.text and coord_name in coords_elem.text.split():
                    src_axes_referencing.append(axis.get('name'))
        print(f"Source TransformAxes referencing '{coord_name}': {src_axes_referencing}")

        # --- Locate target joint ---
        joint_to_find = joint_override if joint_override else src_joint_name
        tar_joint_elem = None
        for jelem in tar_root.iter():
            if jelem.get('name') == joint_to_find:
                tar_joint_elem = jelem
                break
        if tar_joint_elem is None:
            print(f"Warning: Joint '{joint_to_find}' not found in target model. Skipping '{coord_name}'.")
            continue

        # --- Add coordinate to target joint's <coordinates> list ---
        coords_container = tar_joint_elem.find('coordinates')
        if coords_container is None:
            coords_container = ET.SubElement(tar_joint_elem, 'coordinates')

        existing = None
        for coord in coords_container.findall('Coordinate'):
            if coord.get('name') == coord_name:
                existing = coord
                break

        if existing is not None:
            for child in list(existing):
                existing.remove(child)
            for child in src_coord_elem:
                existing.append(copy.deepcopy(child))
            print(f"Updated existing coordinate '{coord_name}'.")
        else:
            coords_container.append(copy.deepcopy(src_coord_elem))
            print(f"Appended coordinate '{coord_name}' to joint '{joint_to_find}'.")

        # --- Update SpatialTransform in target to reference coordinate ---
        for axis in tar_joint_elem.iter('TransformAxis'):
            if axis.get('name') in src_axes_referencing:
                coords_elem = axis.find('coordinates')
                if coords_elem is None:
                    coords_elem = ET.SubElement(axis, 'coordinates')
                coords_elem.text = coord_name
                print(f"Updated TransformAxis '{axis.get('name')}' to reference '{coord_name}'.")

    # --- Fix empty <translation> tags ---
    for elem in tar_root.iter('translation'):
        if not elem.text or not elem.text.strip():
            elem.text = '0 0 0'

    save_path = target_model.replace('.osim', '_modified.osim')
    tar_tree.write(save_path, encoding='unicode', xml_declaration=True)
    print(f"Saved modified model to: {save_path}")

    # Verify all coordinates exist in saved XML
    verify_root = ET.parse(save_path).getroot()
    saved_coords = {c.get('name') for c in verify_root.iter('Coordinate')}
    for coord_name in coordinate_name:
        if coord_name in saved_coords:
            print(f"Verified: '{coord_name}' exists in the modified model.")
        else:
            print(f"Error: '{coord_name}' not found in the modified model.")

    # Validate by loading with OpenSim API; save to separate file
    validated_path = save_path.replace('.osim', '_validated.osim')
    model = osim.Model(save_path)
    model.initSystem()
    model.setName('tps_transformed_with_added_coordinates')
    model.printToXML(validated_path)
    print(f"OpenSim-validated model saved to: {validated_path}")

def checkMuscleMomentArms(model_file_path=None, ik_file_path=None, leg = 'l', threshold = 0.005):
    '''
    Adapted from Willi Koller: https://github.com/WilliKoller/OpenSimMatlabBasic/blob/main/checkMuscleMomentArms.m
    Models Verified for:
        - Rajagopal 2015
        - Cateli 
    '''
    def get_model_coord(model, coord_name):
        try:
            index = model.getCoordinateSet().getIndex(coord_name)
            coord = model.updCoordinateSet().get(index)
        except:
            index = None
            coord = None
            print(f'Coordinate {coord_name} not found in model')
        
        return index, coord

    if not model_file_path or not os.path.isfile(model_file_path):
        model_file_path = input("Enter path to OpenSim model (.osim): ").strip('"')

    if not ik_file_path or not os.path.isfile(ik_file_path):
        ik_file_path = input("Enter path to OpenSim motion file (.mot or .sto): ").strip('"')

    # raise Exception('This function is not yet working. Please use the Matlab version for now or fix line containing " time_discontinuity.append(time_vector[discontinuity_indices]) "')

    # Load motions and model
    motion = osim.Storage(ik_file_path)
    model = osim.Model(model_file_path)

    # Initialize system and state
    model.initSystem()
    state = model.initSystem()

    # coordinate names
    flexIndexLHip, flexCoordLHip = get_model_coord(model, 'hip_flexion_' + leg)
    rotIndexLHip, rotCoordLHip = get_model_coord(model, 'hip_rotation_' + leg)
    addIndexLHip, addCoordLHip = get_model_coord(model, 'hip_adduction_' + leg)
    addIndexLKnee, addCoordLKnee = get_model_coord(model, 'knee_adduction_' + leg)
    flexIndexLKnee, flexCoordLKnee = get_model_coord(model, 'knee_angle_' + leg)
    flexIndexLAnk, flexCoordLAnk = get_model_coord(model, 'ankle_angle_' + leg)

    # get names of the hip muscles
    numMuscles = model.getMuscles().getSize()
    muscleIndices_hip = []
    muscleNames_hip = []
    for i in range(numMuscles):
        tmp_muscleName = str(model.getMuscles().get(i).getName())
        if ('add' in tmp_muscleName or 'gl' in tmp_muscleName or 'semi' in tmp_muscleName or 'bf' in tmp_muscleName or
                'grac' in tmp_muscleName or 'piri' in tmp_muscleName or 'sart' in tmp_muscleName or 'tfl' in tmp_muscleName or
                'iliacus' in tmp_muscleName or 'psoas' in tmp_muscleName or 'rect' in tmp_muscleName) and ('_' + leg in tmp_muscleName):
            muscleIndices_hip.append(i)
            muscleNames_hip.append(tmp_muscleName)

    flexMomentArms = np.zeros((motion.getSize(), len(muscleIndices_hip)))
    addMomentArms = np.zeros((motion.getSize(), len(muscleIndices_hip)))
    rotMomentArms = np.zeros((motion.getSize(), len(muscleIndices_hip)))

    # get names of the knee muscles
    numMuscles = model.getMuscles().getSize()
    muscleIndices_knee = []
    muscleNames_knee = []
    for i in range(numMuscles):
        tmp_muscleName = str(model.getMuscles().get(i).getName())
        if ('bf' in tmp_muscleName or 'gas' in tmp_muscleName or 'grac' in tmp_muscleName or 'sart' in tmp_muscleName or
                'semim' in tmp_muscleName or 'semit' in tmp_muscleName or 'rec' in tmp_muscleName or 'vas' in tmp_muscleName) and ('_' + leg in tmp_muscleName):
            muscleIndices_knee.append(i)
            muscleNames_knee.append(tmp_muscleName)

    kneeFlexMomentArms = np.zeros((motion.getSize(), len(muscleIndices_knee)))

    # get names of the ankle muscles
    numMuscles = model.getMuscles().getSize()
    muscleIndices_ankle = []
    muscleNames_ankle = []
    for i in range(numMuscles):
        tmp_muscleName = str(model.getMuscles().get(i).getName())
        print(tmp_muscleName)
        if ('edl' in tmp_muscleName or 'ehl' in tmp_muscleName or 'tibant' in tmp_muscleName or 'gas' in tmp_muscleName or
                'fdl' in tmp_muscleName or 'fhl' in tmp_muscleName or 'perb' in tmp_muscleName or 'perl' in tmp_muscleName or
                'sole' in tmp_muscleName or 'tibpos' in tmp_muscleName) and ('_' + leg in tmp_muscleName):
            muscleIndices_ankle.append(i)
            muscleNames_ankle.append(tmp_muscleName)

    ankleFlexMomentArms = np.zeros((motion.getSize(), len(muscleIndices_ankle)))

    # compute moment arms for each muscle and create time vector
    time_vector = []
    for i in range(1, motion.getSize()):
        flexAngleL = motion.getStateVector(i-1).getData().get(flexIndexLHip) / 180 * np.pi
        rotAngleL = motion.getStateVector(i-1).getData().get(rotIndexLHip) / 180 * np.pi
        addAngleL = motion.getStateVector(i-1).getData().get(addIndexLHip) / 180 * np.pi
        addAngleLKnee = motion.getStateVector(i-1).getData().get(addIndexLKnee) / 180 * np.pi
        flexAngleLknee = motion.getStateVector(i-1).getData().get(flexIndexLKnee) / 180 * np.pi
        flexAngleLank = motion.getStateVector(i-1).getData().get(flexIndexLAnk) / 180 * np.pi

        time_vector.append(motion.getStateVector(i-1).getTime())
        # Update the state with the joint angle
        coordSet = model.updCoordinateSet()
        coordSet.get(flexIndexLHip).setValue(state, flexAngleL)
        coordSet.get(rotIndexLHip).setValue(state, rotAngleL)
        coordSet.get(addIndexLHip).setValue(state, addAngleL)
        coordSet.get(flexIndexLKnee).setValue(state, flexAngleLknee)
        coordSet.get(addIndexLKnee).setValue(state, addAngleLKnee)
        coordSet.get(flexIndexLAnk).setValue(state, flexAngleLank)

        # Realize the state to compute dependent quantities
        model.computeStateVariableDerivatives(state)
        model.realizeVelocity(state)

        # Compute the moment arm hip
        for j in range(len(muscleIndices_hip)):
            muscleIndex = muscleIndices_hip[j]
            if muscleNames_hip[j][-1] == leg:
                flexMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, flexCoordLHip)
                flexMomentArms[i, j] = flexMomentArm

                rotMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, rotCoordLHip)
                rotMomentArms[i, j] = rotMomentArm

                addMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, addCoordLHip)
                addMomentArms[i, j] = addMomentArm

        # Compute the moment arm knee
        for j in range(len(muscleNames_knee)):
            muscleIndex = muscleIndices_knee[j]
            if muscleNames_knee[j][-1] == leg:
                kneeFlexMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, flexCoordLKnee)
                kneeFlexMomentArms[i, j] = kneeFlexMomentArm

                kneeAddMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, addCoordLKnee)
                addMomentArms[i, j] = kneeAddMomentArm

        # Compute the moment arm ankle
        for j in range(len(muscleNames_ankle)):
            muscleIndex = muscleIndices_ankle[j]
            if muscleNames_ankle[j][-1] == leg:
                ankleFlexMomentArm = model.getMuscles().get(muscleIndex).computeMomentArm(state, flexCoordLAnk)
                ankleFlexMomentArms[i, j] = ankleFlexMomentArm

    # check discontinuities
    discontinuity = []
    muscle_action = []
    time_discontinuity = []
    discontinuity_frames = []

    fDistC = plt.figure('Discontinuity', figsize=(8, 8))
    plt.title(ik_file_path)

    save_folder = os.path.join(os.path.dirname(ik_file_path),'momentArmsCheck')

    def find_discontinuities(momArms, threshold, muscleNames, action, discontinuity, muscle_action, time_discontinuity, discontinuity_frames):
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
                discontinuity_frames.append(discontinuity_indices)


        return discontinuity, muscle_action, time_discontinuity, discontinuity_frames

    # hip flexion
    discontinuity, muscle_action, time_discontinuity, discontinuity_frames = find_discontinuities(
        flexMomentArms, threshold, muscleNames_hip, 'flexion', discontinuity, muscle_action, time_discontinuity, discontinuity_frames)

    # hip adduction
    discontinuity, muscle_action, time_discontinuity, discontinuity_frames = find_discontinuities(
        addMomentArms, threshold, muscleNames_hip, 'adduction', discontinuity, muscle_action, time_discontinuity, discontinuity_frames)
    
    # hip rotation
    discontinuity, muscle_action, time_discontinuity, discontinuity_frames = find_discontinuities(
        rotMomentArms, threshold, muscleNames_hip, 'rotation', discontinuity, muscle_action, time_discontinuity, discontinuity_frames)
    
    # knee flexion
    discontinuity, muscle_action, time_discontinuity, discontinuity_frames = find_discontinuities(
        kneeFlexMomentArms, threshold, muscleNames_knee, 'flexion', discontinuity, muscle_action, time_discontinuity, discontinuity_frames)
    
    # knee adduction
    try:
        discontinuity, muscle_action, time_discontinuity, discontinuity_frames = find_discontinuities(
            addMomentArms, threshold, muscleNames_knee, 'adduction', discontinuity, muscle_action, time_discontinuity, discontinuity_frames)
    except Exception as e:
        print(f'Error in knee adduction discontinuity check: {e}')
    
    # ankle flexion
    discontinuity, muscle_action, time_discontinuity, discontinuity_frames = find_discontinuities(
        ankleFlexMomentArms, threshold, muscleNames_ankle, 'dorsiflexion', discontinuity, muscle_action, time_discontinuity, discontinuity_frames)
    
    # plot discontinuities
    if len(discontinuity) > 0:
        plt.legend(muscle_action)
        plt.ylabel('Muscle Moment Arms with discontinuities (m)')
        plt.xlabel('Frame (after start time)')
        utils.save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'discontinuities_' + leg + '.png'))
        print('\n\nYou should alter the model - most probably you have to reduce the radius of corresponding wrap objects for the identified muscles\n\n\n')

        # save txt file with discontinuities
        with open(os.path.join(save_folder, 'discontinuities_' + leg + '.txt'), 'w') as f:
            f.write(f"model file = {model_file_path}\n")
            f.write(f"motion file = {ik_file_path}\n")
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
    plt.title('All muscle moment arms in motion ' + ik_file_path)
    plt.legend(muscleNames_hip, loc='best')
    plt.ylabel('Hip Flexion Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    utils.save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'hip_flex_MomentArms_' + leg + '.png'))

    # hip adduction
    plt.figure('addMomentArms_' + leg, figsize=(8, 8))
    plt.plot(addMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_file_path)
    plt.legend(muscleNames_hip, loc='best')
    plt.ylabel('Hip Adduction Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    utils.save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'hip_add_MomentArms_' + leg + '.png'))

    # hip rotation
    plt.figure('rotMomentArms_' + leg, figsize=(8, 8))
    plt.plot(rotMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_file_path)
    plt.legend(muscleNames_hip, loc='best')
    plt.ylabel('Hip Rotation Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    utils.save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'hip_rot_MomentArms_' + leg + '.png'))

    # knee flexion
    plt.figure('kneeFlexMomentArms_' + leg, figsize=(8, 8))
    plt.plot(kneeFlexMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_file_path)
    plt.legend(muscleNames_knee, loc='best')
    plt.ylabel('Knee Flexion Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    utils.save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'knee_MomentArms_' + leg + '.png'))

    # ankle flexion
    plt.figure('ankleFlexMomentArms_' + leg, figsize=(8, 8))
    plt.plot(ankleFlexMomentArms)
    plt.title('All muscle moment arms in motion ' + ik_file_path)
    plt.legend(muscleNames_ankle, loc='best')
    plt.ylabel('Ankle Dorsiflexion Moment Arm (m)')
    plt.xlabel('Frame (after start time)')
    utils.save_fig(plt.gcf(), save_path=os.path.join(save_folder, 'ankle_MomentArms_' + leg + '.png'))

    print('Moment arms checked for ' + ik_file_path)
    print('Results saved in ' + save_folder + ' \n\n' )

    return momentArmsAreWrong, discontinuity, muscle_action, discontinuity_frames

def muscles_per_coordinate(osimModel=None):

    if osimModel is None:
        osimModel = input("Enter path to OpenSim model (.osim): ").strip('"')
        osimModel = osim.Model(osimModel)


    muscles = {}
    indexes = {}
    coordSet = osimModel.getCoordinateSet()

    for i in range(coordSet.getSize()):
        coord = coordSet.get(i)    
        coord_name = coord.getName()
        muscles[coord_name] = []
        indexes[coord_name] = []
        coord = osimModel.getCoordinateSet().get(coord_name)
        state = osimModel.initSystem()
        osimModel.realizePosition(state)

        for i in range(osimModel.getMuscles().getSize()):
            muscle = osimModel.getMuscles().get(i)
            if abs(muscle.computeMomentArm(state, coord)) > 1e-4:
                muscles[coord_name].append(muscle.getName())
                indexes[coord_name].append(i)

    if __name__ == "__main__":
        
        for coord_name in muscles.keys():
            print(f'coordinate: {coord_name} : \n')
            print(muscles[coord_name])
            print('\n')

    return muscles, indexes

def muscle_optimimizer_Modenese2015(osim_model_path=None, save_path=None):
    """
    Optimize muscle parameters in an OpenSim model using the Modenese 2015 method.
    
    Args:
        osim_model_path (str): Path to the input .osim model file
        save_path (str, optional): Path to save the optimized model. If None, saves to osim_model_path with '_optimized' suffix
    """

    # Optimiser functions

def optimMuscleParams(osimModel_ref_filepath, osimModel_targ_filepath, N_eval, log_folder):
    
    
    # results file identifier
    res_file_id_exp = '_N' + str(N_eval)
    
    # import models
    osimModel_ref = osim.Model(osimModel_ref_filepath)
    osimModel_targ = osim.Model(osimModel_targ_filepath)
    
    # models details
    name = Path(osimModel_targ_filepath).stem
    ext = Path(osimModel_targ_filepath).suffix
    
    # assigning new name to the model
    osimModel_opt_name = name + '_opt' + res_file_id_exp + ext
    osimModel_targ.setName(osimModel_opt_name)
    
    # initializing log file
    log_folder = Path(log_folder)
    log_folder.mkdir(parents=True, exist_ok=True)
    log_file_path = log_folder / (name + '_opt' + res_file_id_exp + '.log')
    
    # Check if log file exists and find last processed muscle
    processed_muscles = set()
    if log_file_path.exists():
        with open(log_file_path, 'r') as f:
            for line in f:
                if 'Calculated optimized muscle parameters for' in line:
                    muscle_name = line.split('Calculated optimized muscle parameters for')[1].split('in')[0].strip()
                    processed_muscles.add(muscle_name)
        print(f'Found {len(processed_muscles)} already processed muscles in log file')
    
    logging.basicConfig(filename=str(log_file_path), filemode='a', format='%(levelname)s:%(message)s', level=logging.INFO)
        
    # get muscles
    muscles = osimModel_ref.getMuscles()
    muscles_scaled = osimModel_targ.getMuscles()
    
    # initialize with recognizable values
    LmOptLts_opt = -1000*np.ones((muscles.getSize(),2))
    SimInfo = {}
    
    for n_mus in range(0, muscles.getSize()):
        
        # current muscle name (here so that it is possible to choose a single muscle when developing).
        curr_mus_name = muscles.get(n_mus).getName()
        
        # Skip if already processed
        if curr_mus_name in processed_muscles:
            print(f'Skipping muscle {n_mus+1}: {curr_mus_name} (already processed)')
            continue
        
        tic = time()
        print('processing mus ' + str(n_mus+1) + ': ' + curr_mus_name)
        
        # import muscles
        curr_mus = muscles.get(curr_mus_name)
        curr_mus_scaled = muscles_scaled.get(curr_mus_name)
        
        # extracting the muscle parameters from reference model
        LmOptLts = [curr_mus.getOptimalFiberLength(), curr_mus.getTendonSlackLength()]
        PenAngleOpt = curr_mus.getPennationAngleAtOptimalFiberLength()
        Mus_ref = sampleMuscleQuantities(osimModel_ref,curr_mus,'all',N_eval)
        
        # calculating minimum fiber length before having pennation 90 deg
        # acos(0.1) = 1.47 red = 84 degrees, chosen as in OpenSim
        limitPenAngle = np.arccos(0.1)
        # this is the minimum length the fiber can be for geometrical reasons.
        LfibNorm_min = np.sin(PenAngleOpt) / np.sin(limitPenAngle)
        # LfibNorm as calculated above can be shorter than the minimum length
        # at which the fiber can generate force (taken to be 0.5 Zajac 1989)
        if LfibNorm_min < 0.5:
            LfibNorm_min = 0.5
        
        # muscle-tendon paramenters value
        MTL_ref = [musc_param_iter[0] for musc_param_iter in Mus_ref]
        LfibNorm_ref = [musc_param_iter[1] for musc_param_iter in Mus_ref]
        LtenNorm_ref = [musc_param_iter[2]/LmOptLts[1] for musc_param_iter in Mus_ref]
        penAngle_ref = [musc_param_iter[4] for musc_param_iter in Mus_ref]
        # LfibNomrOnTen_ref = LfibNorm_ref.*cos(penAngle_ref)
        LfibNomrOnTen_ref = [(musc_param_iter[1]*np.cos(musc_param_iter[4])) for musc_param_iter in Mus_ref]         
        
        # checking the muscle configuration that do not respect the condition.
        okList = [pos for pos, value in enumerate(LfibNorm_ref) if value > LfibNorm_min]
        # keeping only acceptable values
        MTL_ref = np.array([MTL_ref[index] for index in okList])
        LfibNorm_ref = np.array([LfibNorm_ref[index] for index in okList])
        LtenNorm_ref = np.array([LtenNorm_ref[index] for index in okList])
        penAngle_ref = np.array([penAngle_ref[index] for index in okList])
        LfibNomrOnTen_ref = np.array([LfibNomrOnTen_ref[index] for index in okList])
        
        # in the target only MTL is needed for all muscles
        MTL_targ = sampleMuscleQuantities(osimModel_targ,curr_mus_scaled,'MTL',N_eval)
        evalTotPoints = len(MTL_targ)
        MTL_targ = np.array([MTL_targ[index] for index in okList])
        evalOkPoints  = len(MTL_targ)
        
        # The problem to be solved is: 
        # [LmNorm*cos(penAngle) LtNorm]*[Lmopt Lts]' = MTL;
        # written as Ax = b or their equivalent (A^T A) x = (A^T b)  
        A = np.array([LfibNomrOnTen_ref , LtenNorm_ref]).T
        b = MTL_targ
        
        # ===== LINSOL =======
        # solving the problem to calculate the muscle param 
        x = linalg.solve(np.dot(A.T , A) , np.dot(A.T , b))
        LmOptLts_opt[n_mus] = x
        
        # checking the results
        if np.min(x) <= 0:
            # informing the user
            line0 = ' '
            line1 = 'Negative value estimated for muscle parameter of muscle ' + curr_mus_name + '\n'
            line2 = '                         Lm Opt        Lts' + '\n'
            line3 = 'Template model       : ' + str(LmOptLts) + '\n'
            line4 ='Optimized param      : ' + str(LmOptLts_opt[n_mus]) + '\n'
            
            # ===== IMPLEMENTING CORRECTIONS IF ESTIMATION IS NOT CORRECT =======
            x = optimize.nnls(np.dot(A.T , A) , np.dot(A.T , b))
            x = x[0]
            LmOptLts_opt[n_mus] = x
            line5 = 'Opt params (optimize.nnls): ' + str(LmOptLts_opt[n_mus])
            
            logging.info(line0 + line1 + line2 + line3 + line4 + line5 + '\n')
            # In our tests, if something goes wrong is generally tendon slack 
            # length becoming negative or zero because tendon length doesn't change
            # throughout the range of motion, so lowering the rank of A.
            if np.min(x) <= 0:
                # analyzes of Lten behaviour
                Lten_ref = [musc_param_iter[2] for musc_param_iter in Mus_ref]
                Lten_ref = np.array([Lten_ref[index] for index in okList])
                if (np.max(Lten_ref) - np.min(Lten_ref)) < 0.0001:
                    logging.warning(' Tendon length not changing throughout range of motion')
                
                # calculating proportion of tendon and fiber
                Lten_fraction = Lten_ref/MTL_ref
                Lten_targ = Lten_fraction*MTL_targ
                
                # first round: optimizing Lopt maintaing the proportion of
                # tendon as in the reference model
                A1 = np.array([LfibNomrOnTen_ref , LtenNorm_ref*0]).T
                b1 = MTL_targ - Lten_targ
                x1 = optimize.nnls(np.dot(A1.T , A1) , np.dot(A1.T , b1))
                x[0] = x1[0][0]
                
                # second round: using the optimized Lopt to recalculate Lts
                A2 = np.array([LfibNomrOnTen_ref*0 , LtenNorm_ref]).T
                b2 = MTL_targ - np.dot(A1,x1[0])
                x2 = optimize.nnls(np.dot(A2.T , A2) , np.dot(A2.T , b2))
                x[1] = x2[0][1]
                
                LmOptLts_opt[n_mus] = x
            
        
        # Here tests about/against optimizers were implemented
        
        # calculating the error (mean squared errors)
        fval = mean_squared_error(b, np.dot(A,x), squared=False)
        
        # update muscles from scaled model
        curr_mus_scaled.setOptimalFiberLength(LmOptLts_opt[n_mus][0])
        curr_mus_scaled.setTendonSlackLength(LmOptLts_opt[n_mus][1])
        
        # PRINT LOGS
        toc = time() - tic
        line0 = ' '
        line1 = 'Calculated optimized muscle parameters for ' + curr_mus.getName() + ' in ' +  str(toc) + ' seconds.' + '\n'
        line2 = '                         Lm Opt        Lts' + '\n'
        line3 = 'Template model       : ' + str(LmOptLts) + '\n'
        line4 = 'Optimized param      : ' + str(LmOptLts_opt[n_mus]) + '\n'
        line5 = 'Nr of eval points    : ' + str(evalOkPoints) + '/' + str(evalTotPoints) + ' used' + '\n'
        line6 = 'fval                 : ' + str(fval) + '\n'
        line7 = 'var from template [%]: ' + str(100*(np.abs(LmOptLts - LmOptLts_opt[n_mus])) / LmOptLts) + '%' + '\n'
        
        logging.info(line0 + line1 + line2 + line3 + line4 + line5 + line6 + line7 + '\n')
              
        # SIMULATION INFO AND RESULTS
        
        SimInfo[n_mus] = {}
        SimInfo[n_mus]['colheader'] = curr_mus.getName()
        SimInfo[n_mus]['LmOptLts_ref'] = LmOptLts
        SimInfo[n_mus]['LmOptLts_opt'] = LmOptLts_opt[n_mus]
        SimInfo[n_mus]['varPercLmOptLts'] = 100*(np.abs(LmOptLts - LmOptLts_opt[n_mus])) / LmOptLts
        SimInfo[n_mus]['sampledEvalPoints'] = evalOkPoints
        SimInfo[n_mus]['sampledEvalPoints'] = evalTotPoints
        SimInfo[n_mus]['fval'] = fval
    
    # assigning optimized model as output
    osimModel_opt = osimModel_targ
            
    return osimModel_opt, SimInfo

def plot_optimization_results(intial_model_path, optimised_model_path):

    base_model = osim.Model(intial_model_path)
    optimized_model = osim.Model(optimised_model_path)
    
    muscles = base_model.getMuscles()
    n_muscles = muscles.getSize()
    
    params = ['optimal_fiber_length', 'tendon_slack_length', 'pennation_angle_at_optimal']
    fig, axes = plt.subplots(len(params), 1, figsize=(8, 12))
    
    for ax, param in zip(axes, params):
        ax.set_title(param.replace('_', ' ').title())
        ax.set_xlabel('Muscle Index')
        ax.set_ylabel(param.replace('_', ' ').title())
        for i in range(n_muscles):
            muscle = muscles.get(i)
            muscle_name = muscle.getName()
            base_muscle = base_model.getMuscles().get(muscle_name)
            optim_muscle = optimized_model.getMuscles().get(muscle_name)
            if param == 'optimal_fiber_length':
                base_value = base_muscle.getOptimalFiberLength()
                optim_value = optim_muscle.getOptimalFiberLength()
            elif param == 'tendon_slack_length':
                base_value = base_muscle.getTendonSlackLength()
                optim_value = optim_muscle.getTendonSlackLength()
            elif param == 'pennation_angle_at_optimal':
                base_value = base_muscle.getPennationAngleAtOptimalFiberLength()
                optim_value = optim_muscle.getPennationAngleAtOptimalFiberLength()
            
            # bar plot
            ax.bar(i - 0.2, base_value, width=0.4, label='Base' if i == 0 else "", color='b')
            ax.bar(i + 0.2, optim_value, width=0.4, label='Optimized' if i == 0 else "", color='r')

            # setting x-ticks
            ax.set_xticks(range(n_muscles))
            ax.set_xticklabels([muscles.get(i).getName() for i in range(n_muscles)], rotation=90, size=6)

        ax.legend()    
    plt.tight_layout()
    
    save_path = optimised_model_path.replace('.osim', '_muscle_params.png')
    plt.savefig(save_path)
    print(f'Optimization results plot saved to {save_path}')


    def main(osim_model_ref_filepath=None, osim_model_targ_filepath=None):
        # ========= USER SETTINGS =======
        # model files with paths
        if osim_model_ref_filepath is None:
            osim_model_ref_filepath = input("Please provide the path to the reference model: ").strip('"')
        if osim_model_targ_filepath is None:
            osim_model_targ_filepath = input("Please provide the path to the target model: ").strip('"')
        optimized_model_folder = os.path.dirname(osim_model_targ_filepath)
        
        # evaluations
        n_eval = 10
        # ===============================

        # initializing folders and log file
        log_folder = optimized_model_folder
        
        # checking if results folder exists. If not, create it.
        if not os.path.isdir(optimized_model_folder):
            warnings.warn(f'Folder {optimized_model_folder} does not exist. It will be created.')
            os.makedirs(optimized_model_folder)

        # optimizing target model based on reference model for n_eval points per
        # degree of freedom
        osim_model_opt, sims_info = optimMuscleParams(osim_model_ref_filepath,
                                                        osim_model_targ_filepath,
                                                        n_eval,
                                                        log_folder)

        # printing the optimized model
        output_path = osim_model_targ_filepath.replace('.osim', f'_opt_N{n_eval}.osim')
        osim_model_opt.printToXML(output_path)
        print(f'Optimized model saved to: {output_path}')
        
        # plotting optimization results
        plot_optimization_results(osim_model_targ_filepath, output_path)

    
    model = osim.Model(osim_model_path)
    state = model.initSystem()

    # Call the Modenese 2015 optimization method
    try:
        main(osim_model_ref_filepath=osim_model_path, osim_model_targ_filepath=osim_model_path)
        print("Muscle optimization completed successfully.")
    except Exception as e:
        print(f"Error during muscle optimization: {e}")
        return

    # Determine save path
    if save_path is None:
        save_path = osim_model_path.replace('.osim', '_optimized.osim')

    # Save the optimized model
    model.printToXML(save_path)
    print(f"Optimized model saved to: {save_path}")

def compare_osim_models(model_list=None):

    if not model_list:
        model_list = []
        while True:
            model_path = input("Enter the path to an OpenSim model (.osim) (or 'done' to finish): ").strip('"')
            if model_path.lower() == 'done':
                break
            if model_path.strip():
                model_list.append(model_path)


    # Load all models and extract muscles
    models = []
    model_names = []
    all_muscles_set = set()
    
    for idx, model_path in enumerate(model_list):
        model = osim.Model(model_path)
        models.append(model)
        model_name = f"Model {idx + 1}"
        model_names.append(model_name)
        
        muscles = model.getMuscles()
        print(f"{model_name}: {model_path} has {muscles.getSize()} muscles")
        
        for i in range(muscles.getSize()):
            all_muscles_set.add(muscles.get(i).getName())
    
    # Compare muscle properties 
    muscle_properties_list = []
    for muscle_name in all_muscles_set:
        for model, model_name in zip(models, model_names):
            muscles = model.getMuscles()
            muscle = None
            for i in range(muscles.getSize()):
                if muscles.get(i).getName() == muscle_name:
                    muscle = muscles.get(i)
                    break
            
            if muscle:
                optimal_fiber_length = muscle.getOptimalFiberLength()
                tendon_slack_length = muscle.getTendonSlackLength()
                pennation_angle = muscle.getPennationAngleAtOptimalFiberLength()
                max_isometric_force = muscle.getMaxIsometricForce()
                muscle_properties_list.append({
                    'Muscle': muscle_name,
                    'Model': model_name,
                    'Optimal Fiber Length': optimal_fiber_length,
                    'Tendon Slack Length': tendon_slack_length,
                    'Pennation Angle at Optimal Fiber Length': pennation_angle,
                    'Maximum Isometric Force': max_isometric_force
                })
    
    muscle_properties = pd.DataFrame(muscle_properties_list)
    
    # Create spider plots for each property
    properties = ['Optimal Fiber Length', 'Tendon Slack Length', 'Pennation Angle at Optimal Fiber Length', 'Maximum Isometric Force']

    # Use the full sorted union of muscles so all models share the same axis
    all_muscle_names = sorted(all_muscles_set)
    num_vars = len(all_muscle_names)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    # Pivot to wide format: index=Muscle, columns=Model — missing entries become 0
    n_props = len(properties)
    fig, axes = plt.subplots(1, n_props, figsize=(6 * n_props, 6), subplot_kw=dict(projection='polar'))

    for idx, prop in enumerate(properties):
        ax = axes[idx]
        wide = (
            muscle_properties[['Muscle', 'Model', prop]]
            .pivot(index='Muscle', columns='Model', values=prop)
            .reindex(all_muscle_names)
            .fillna(0)
        )
        for model_name in model_names:
            if model_name not in wide.columns:
                continue
            values = wide[model_name].tolist()
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=2, label=model_name)
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(all_muscle_names, size=8)
        ax.set_title(f'Spider Plot: {prop}', size=14, weight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.grid(True)

    plt.tight_layout()

    # count coordinates
    coordinate_presence = {}  # coord_name -> list of model names that have it
    for model, model_name in zip(models, model_names):
        coordSet = model.getCoordinateSet()
        for i in range(coordSet.getSize()):
            coord_name = coordSet.get(i).getName()
            coordinate_presence.setdefault(coord_name, []).append(model_name)
    print("\nCoordinate counts across models:")
    for coord_name, present_in in sorted(coordinate_presence.items()):
        missing = [m for m in model_names if m not in present_in]
        missing_str = f"  [MISSING in: {', '.join(missing)}]" if missing else ""
        print(f"{coord_name}: {len(present_in)}/{len(models)} ({', '.join(present_in)}){missing_str}")

    plt.show()

def optimize_moment_arms(ref_model_path=None, target_model_path=None):
    '''Optimize muscle parameters in the target model to match the moment arms of the reference model.
    
    NOT FINNISED!!!
    
    '''

    if ref_model_path is None:
        ref_model_path = input("Enter the path to the reference .osim model file: ").strip('"')
    if target_model_path is None:
        target_model_path = input("Enter the path to the target .osim model file: ").strip('"')

    ref_model = osim.Model(ref_model_path)
    target_model = osim.Model(target_model_path)
    optimized_model = osim.Model(target_model_path)

    def compute_moment_arms(model):
        state = model.initSystem()
        model.realizePosition(state)
        moment_arms = {}
        for i in range(model.getMuscles().getSize()):
            muscle = model.getMuscles().get(i)
            muscle_name = muscle.getName()
            moment_arms[muscle_name] = {}
            for j in range(model.getCoordinateSet().getSize()):
                coord = model.getCoordinateSet().get(j)
                coord_name = coord.getName()
                moment_arms[muscle_name][coord_name] = muscle.computeMomentArm(state, coord)
        return moment_arms
    
    def optimize_moment_arm(muscle_name, coord_name, ref_arm, target_arm):
        # Placeholder for optimization logic
        # In a real implementation, this would adjust muscle parameters in the target model to minimize the difference in moment arms
        optimized_arm = target_arm
        return optimized_arm
    
    ref_moment_arms = compute_moment_arms(ref_model)
    target_moment_arms = compute_moment_arms(target_model)

    for muscle_name in ref_moment_arms.keys():
        if muscle_name in target_moment_arms:
            for coord_name in ref_moment_arms[muscle_name].keys():
                if coord_name in target_moment_arms[muscle_name]:
                    ref_arm = ref_moment_arms[muscle_name][coord_name]
                    target_arm = target_moment_arms[muscle_name][coord_name]
                    if abs(ref_arm - target_arm) > 0.01:  # Threshold for optimization
                        print(f"Optimizing {muscle_name} for {coord_name}: Ref={ref_arm:.4f}, Target={target_arm:.4f}")
                        optimized_arm = optimize_moment_arm(muscle_name, coord_name, ref_arm, target_arm)



    # save the optimized model
    optimized_model_path = target_model_path.replace('.osim', '_optimized.osim')
    optimized_model.printToXML(optimized_model_path)
    print(f"Optimized model saved to: {optimized_model_path}")


    # Compare moment arms and plot results
    model1 = osim.Model(ref_model_path)
    model2 = osim.Model(target_model_path)
    model3 = osim.Model(optimized_model_path)

    optimized_arms = compute_moment_arms(model3)


    n_muscles = len(ref_moment_arms)
    n_cols = 5
    n_rows = (n_muscles + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6, n_rows * 3))
    axes = axes.flatten() if n_muscles > 1 else [axes]
    for idx, muscle_name in enumerate(ref_moment_arms.keys()):
        ax = axes[idx]
        ref_arms = list(ref_moment_arms[muscle_name].values())
        target_arms = list(target_moment_arms[muscle_name].values())
        optimized_arms_values = list(optimized_arms[muscle_name].values())
        
        coords = list(ref_moment_arms[muscle_name].keys())
        
        ax.plot(coords, ref_arms, 'o-', label='Reference')
        ax.plot(coords, target_arms, 'x-', label='Target')
        ax.plot(coords, optimized_arms_values, 's-', label='Optimized')
        
        ax.set_title(muscle_name)
        ax.set_ylabel('Moment Arm (m)')
        ax.tick_params(axis='x', rotation=45)
    
    utils.mmfn(fig, n_cols=n_cols, n_rows=n_rows)
    plt.tight_layout()

    save_path = target_model_path.replace('.osim', '_moment_arms_comparison.png')
    plt.savefig(save_path)
    print(f"Moment arms comparison plot saved to: {save_path}")

    # make a spider plot for each coordinate with the moment arms of all muscles and save the figure
    n_coords = ref_model.getCoordinateSet().getSize()
    n_cols = 3
    n_rows = (n_coords + n_cols - 1) // n_cols
    fig, ax = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6, n_rows * 6), subplot_kw=dict(projection='polar'))
    ax = ax.flatten() if n_coords > 1 else [ax]
    for i in range(n_coords):
        coord = ref_model.getCoordinateSet().get(i)
        coord_name = coord.getName()
        ax_coord = ax[i]
        ref_arms = [ref_moment_arms[muscle_name][coord_name] for muscle_name in ref_moment_arms.keys()]
        target_arms = [target_moment_arms[muscle_name][coord_name] for muscle_name in target_moment_arms.keys()]
        optimized_arms_values = [optimized_arms[muscle_name][coord_name] for muscle_name in optimized_arms.keys()]
        
        muscles = list(ref_moment_arms.keys())
        angles = np.linspace(0, 2 * np.pi, len(muscles), endpoint=False).tolist()
        angles += angles[:1]
        
        ax_coord.plot(angles, ref_arms + [ref_arms[0]], 'o-', label='Reference')
        ax_coord.plot(angles, target_arms + [target_arms[0]], 'x-', label='Target')
        ax_coord.plot(angles, optimized_arms_values + [optimized_arms_values[0]], 's-', label='Optimized')
        
        ax_coord.set_title(coord_name)
        ax_coord.set_xticks(angles[:-1])
        ax_coord.set_xticklabels(muscles, rotation=90, size=8)

    save_path = target_model_path.replace('.osim', '_moment_arms_comparison_spider.png')
    plt.savefig(save_path)
    print(f"Moment arms comparison spider plot saved to: {save_path}")

# c3d export functions
def export_c3d(c3d_file_path, emg_string_list=['emg'], create_folder=True):
    """
    Export a C3D file using the exportC3D module.
    
    Args:
        c3d_file_path (str): Path to the C3D file to export.
    """
    try:
        exportC3D.main(c3d_file_path, emg_string_list=emg_string_list, create_folder=create_folder)
        print(f"C3D file exported successfully: {c3d_file_path}")
    except Exception as e:
        print(f"Error exporting C3D file: {e}")


def convert_trc_os3_to_os4(trc_file_path: str = '', output_trc_file_path: str = ''):
    """
    Convert a .trc file from OpenSim 3 format to OpenSim 4 format.

    Parameters:
    trc_file_path (str): Path to the input .trc file in OpenSim 3 format.
    output_trc_file_path (str): Path to save the converted .trc file in OpenSim 4 format.
    """

    if not os.path.isfile(trc_file_path):
        trc_file_path = input("Enter the path to the .trc file to convert: ").strip('"')

    if not output_trc_file_path:
        output_trc_file_path = trc_file_path.replace('.trc', '_os4.trc')

    trc_df = utils.load_any_data_file(trc_file_path)  # This will raise an error if the file is not found or not a valid .trc file

    def load_trc_metadata_os3(trc_file_path):
        with open(trc_file_path, 'r') as file:
            lines = file.readlines()
        
        metadata = {}
        for i, line in enumerate(lines):
            parts = line.strip().split('\t')
            if parts[0] == "DataRate" and i + 1 < len(lines):
                values = lines[i + 1].strip().split('\t')
                keys = parts
                type_map = {'DataRate': float, 'CameraRate': float, 'NumFrames': int,
                            'NumMarkers': int, 'Units': str, 'OrigDataRate': float,
                            'DataStartFrame': int, 'OrigNumFrames': int}
                for key, val in zip(keys, values):
                    if key in type_map:
                        metadata[key] = type_map[key](val)
                break
        
        return metadata
    
    trc_metadata = load_trc_metadata_os3(trc_file_path)

    # remove columnn 'Frame#' if it exists
    if 'Frame#' in trc_df.columns:
        trc_df = trc_df.drop(columns=['Frame#'])

    utils.write_trc(trc_df,
                    trc_file=output_trc_file_path,
                    units=trc_metadata.get('Units'),
                    frame_rate=trc_metadata.get('DataRate'),
                    first_frame=trc_metadata.get('DataStartFrame'))

    print(f"Converted .trc file saved to: {output_trc_file_path}")

# Marker data and inverse kinematics functions
def add_joint_centers_to_trc(input_trc_path=None, output_trc_path=None, marker_map=None):
    """
    Add hip, knee, and ankle joint centre markers to a TRC file.

    New markers added (if computable):
      - RHJC, LHJC (hip joint centres)
      - RKJC, LKJC (knee joint centres)
      - RAJC, LAJC (ankle joint centres)

    Inputs:
        - input_trc_path: path to input TRC file 
        - output_trc_path: path to output TRC file (if None, will save in same directory with suffix '_with_JointCenters')
        - marker_map: dictionary specifying marker names for pelvis, knee pairs, ankle pairs, and existing hip markers.

    """
    if input_trc_path is None:
        input_trc_path = input("Enter path to input TRC file: ").strip('"')

    if output_trc_path is None:
        output_trc_path = input_trc_path.replace(".trc", "_with_JointCenters.trc")

    # -----------------------------
    # TRC read
    # -----------------------------
    with open(input_trc_path, "r") as f:
        lines = f.readlines()

    if len(lines) < 6:
        raise ValueError(f"Invalid TRC file: {input_trc_path}")

    header_1 = lines[0].rstrip("\n")
    header_keys = [x for x in lines[1].strip().split("\t") if x != ""]
    header_vals = [x for x in lines[2].strip().split("\t") if x != ""]

    marker_header = lines[3].rstrip("\n")
    coord_header = lines[4].rstrip("\n")

    df = pd.read_csv(input_trc_path, sep="\t", skiprows=5, header=None)

    marker_names = [m for m in marker_header.split("\t")[2:] if m.strip()]
    cols = ["Frame#", "Time"]
    for m in marker_names:
        cols.extend([f"{m}_X", f"{m}_Y", f"{m}_Z"])

    df = df.iloc[:, :len(cols)]
    df.columns = cols

    # -----------------------------
    # helpers
    # -----------------------------
    def has_marker(m):
        return all(c in df.columns for c in [f"{m}_X", f"{m}_Y", f"{m}_Z"])

    def get_marker_xyz(m):
        return df[[f"{m}_X", f"{m}_Y", f"{m}_Z"]].to_numpy(dtype=float)

    def set_marker_xyz(m, xyz):
        df[f"{m}_X"] = xyz[:, 0]
        df[f"{m}_Y"] = xyz[:, 1]
        df[f"{m}_Z"] = xyz[:, 2]

    def midpoint(m1, m2):
        return 0.5 * (get_marker_xyz(m1) + get_marker_xyz(m2))

    def first_valid_pair(pairs):
        for a, b in pairs:
            if has_marker(a) and has_marker(b):
                return a, b
        return None

    # -----------------------------
    # default marker map
    # -----------------------------
    default_map =  {
        "pelvis": {"LASI": "LASI", "RASI": "RASI", "LPSI": "LPSI", "RPSI": "RPSI"},
        "knee_r_pairs": [("RLFC", "RMFC"), ("RKNE", "RKNM"), ("RKNE", "RKNI"), ("RLK", "RMK")],
        "knee_l_pairs": [("LLFC", "LMFC"), ("LKNE", "LKNM"), ("LKNE", "LKNI"), ("LLK", "LMK")],
        "ankle_r_pairs": [("RANK", "RMED"), ("RANK", "RANM"), ("RANK", "RANKM"), ("RLA", "RMA")],
        "ankle_l_pairs": [("LANK", "LMED"), ("LANK", "LANM"), ("LANK", "LANKM"), ("LLA", "LMA")],
        "existing_hip_r": ["RHJC", "RHIP"],
        "existing_hip_l": ["LHJC", "LHIP"],
        }
    if marker_map is None:
        marker_map = default_map

    # -----------------------------
    # hip centres (Harrington-style pelvis-frame estimate)
    # -----------------------------
    rhjc_added = False
    lhjc_added = False

    # Use existing hip markers if present
    for m in marker_map["existing_hip_r"]:
        if has_marker(m):
            set_marker_xyz("RHJC", get_marker_xyz(m))
            rhjc_added = True
            break

    for m in marker_map["existing_hip_l"]:
        if has_marker(m):
            set_marker_xyz("LHJC", get_marker_xyz(m))
            lhjc_added = True
            break

    # If not available, estimate from pelvis landmarks
    pelvis = marker_map["pelvis"]
    if (not rhjc_added or not lhjc_added) and all(has_marker(pelvis[k]) for k in ["LASI", "RASI", "LPSI", "RPSI"]):
        LASI = get_marker_xyz(pelvis["LASI"])
        RASI = get_marker_xyz(pelvis["RASI"])
        LPSI = get_marker_xyz(pelvis["LPSI"])
        RPSI = get_marker_xyz(pelvis["RPSI"])

        mid_asis = 0.5 * (LASI + RASI)
        mid_psi = 0.5 * (LPSI + RPSI)

        # pelvis axes
        z_axis = RASI - LASI  # left -> right
        z_axis /= np.linalg.norm(z_axis, axis=1, keepdims=True)

        x_axis = mid_asis - mid_psi  # posterior -> anterior
        x_axis /= np.linalg.norm(x_axis, axis=1, keepdims=True)

        y_axis = np.cross(z_axis, x_axis)  # superior
        y_axis /= np.linalg.norm(y_axis, axis=1, keepdims=True)

        # re-orthogonalize x
        x_axis = np.cross(y_axis, z_axis)
        x_axis /= np.linalg.norm(x_axis, axis=1, keepdims=True)

        pelvis_width = np.linalg.norm(RASI - LASI, axis=1)   # mm
        pelvis_depth = np.linalg.norm(mid_asis - mid_psi, axis=1)  # mm

        # Harrington-like offsets (mm)
        x_post = -0.24 * pelvis_depth - 9.9
        y_inf = -0.30 * pelvis_width - 10.9
        z_lat = 0.33 * pelvis_width + 7.3

        # right(+z), left(-z)
        RHJC = mid_asis + x_axis * x_post[:, None] + y_axis * y_inf[:, None] + z_axis * z_lat[:, None]
        LHJC = mid_asis + x_axis * x_post[:, None] + y_axis * y_inf[:, None] - z_axis * z_lat[:, None]

        if not rhjc_added:
            set_marker_xyz("RHJC", RHJC)
        if not lhjc_added:
            set_marker_xyz("LHJC", LHJC)

    # -----------------------------
    # knee centres
    # -----------------------------
#     breakpoint()
    pair = first_valid_pair(marker_map["knee_r_pairs"])
    if pair is not None:
        set_marker_xyz("RKJC", midpoint(*pair))

    pair = first_valid_pair(marker_map["knee_l_pairs"])
    if pair is not None:
        set_marker_xyz("LKJC", midpoint(*pair))

    # -----------------------------
    # ankle centres
    # -----------------------------
    pair = first_valid_pair(marker_map["ankle_r_pairs"])
    if pair is not None:
        set_marker_xyz("RAJC", midpoint(*pair))

    pair = first_valid_pair(marker_map["ankle_l_pairs"])
    if pair is not None:
        set_marker_xyz("LAJC", midpoint(*pair))

    # -----------------------------
    # TRC write
    # -----------------------------
    out_marker_names = [c[:-2] for c in df.columns if c.endswith("_X")]
    num_markers = len(out_marker_names)

    # update header values
    header_map = dict(zip(header_keys, header_vals))
    if "NumFrames" in header_map:
        header_map["NumFrames"] = str(len(df))
    if "NumMarkers" in header_map:
        header_map["NumMarkers"] = str(num_markers)

    updated_vals = [header_map.get(k, "") for k in header_keys]
    line2 = "\t".join(header_keys) + "\n"
    line3 = "\t".join(updated_vals) + "\n"

    # marker + coord header
    line4_parts = ["Frame#", "Time"]
    for m in out_marker_names:
        line4_parts.extend([m, "", ""])
    line4 = "\t".join(line4_parts).rstrip() + "\n"

    line5_parts = ["", ""]
    for i in range(1, num_markers + 1):
        line5_parts.extend([f"X{i}", f"Y{i}", f"Z{i}"])
    line5 = "\t".join(line5_parts).rstrip() + "\n"

    with open(output_trc_path, "w") as f:
        f.write(header_1 + "\n")
        f.write(line2)
        f.write(line3)
        f.write(line4)
        f.write(line5)
        df.to_csv(f, sep="\t", index=False, header=False, float_format="%.6f", lineterminator="\n")

    print(f"Saved TRC with joint centres: {output_trc_path}")

def validate_markers_used(osim_modelPath, ikTool, markers_path):

    def get_all_marker_parent_frames(model_path):
        model = osim.Model(model_path)
        model.initSystem()

        marker_set = model.getMarkerSet()
        result = {}
        for i in range(marker_set.getSize()):
            marker = marker_set.get(i)
            result[marker.getName()] = marker.getParentFrameName()
        return result

    model =  osim.Model(osim_modelPath)
    markerSet = model.get_MarkerSet() 
    markers_model = [marker.getName() for marker in markerSet]

    task_set_template = ikTool.upd_IKTaskSet()
    markers_df = utils.load_trc(markers_path)
    markers_trc = markers_df.columns.get_level_values(0).unique().tolist()
    
    for marker_name in markers_model:
        if marker_name not in markers_trc:
            print(f"Warning: Marker '{marker_name}' not found in TRC file.")

    markers_in_task = [task.getName() for task in task_set_template if isinstance(task, osim.IKMarkerTask)]
    markers_parent_frames = get_all_marker_parent_frames(osim_modelPath)

    for marker_name in markers_model:
        if marker_name in markers_in_task:
            if marker_name in markers_trc:
                task = task_set_template.get(marker_name)
                task.setApply(True)
            else:
                task = task_set_template.get(marker_name)
                task.setApply(False)
                print(f"Marker '{marker_name}' not found in TRC file. Disabling task.")
        else:
            newTask = osim.IKMarkerTask()
            newTask.setName(marker_name)
            parent_frame = markers_parent_frames.get(marker_name).replace("/bodyset/", "")
            
            try:
                newTask.setWeight(settings.marker_weights.get(parent_frame))
                print(f"Set weight for marker '{marker_name}' (parent frame: '{parent_frame}') to {settings.marker_weights.get(parent_frame)}")
            except Exception as e:
                newTask.setWeight(1.0)
                print(f"Warning: No weight found for parent frame '{parent_frame}' of marker '{marker_name}'. Setting weight to 1.0")

            if marker_name in markers_trc:
                newTask.setApply(True)
                print(f"Marker '{marker_name}' found in TRC file. Adding and applying with weight 1.0.")
            else:
                newTask.setApply(False)
                print(f"Marker '{marker_name}' in Model not found in TRC file. Disabling task.")
                
            task_set_template.adoptAndAppend(newTask)


    
    return ikTool

def compare_marker_locations(marker_experimental_path=None, marker_virtual_path=None):
    """
    Calculates the root mean square error between experimental and virtual markers.

    Args:
        marker_experimental_path (str, optional): Path to the experimental .trc file.
        marker_virtual_path (str, optional): Path to the virtual .sto markers file.
    """

    # Select the trials if needed
    if not marker_experimental_path:
        marker_experimental_path = input("Enter path to experimental .trc markers file: ").strip('"')
        if not marker_experimental_path: return # User cancelled

    if not marker_virtual_path:
        marker_virtual_path = input("Enter path to virtual .sto markers file: ").strip('"')
        if not marker_virtual_path: return # User cancelled

    # Load marker data
    virtual_markers_df = utils.load_sto(marker_virtual_path)
    experimental_markers_df = utils.load_trc(marker_experimental_path,
                                combine_headers=True)

    exp_marker_names = experimental_markers_df.columns.get_level_values(0).unique().tolist()
    
    # Find frames to plot in the experimental data
    time = virtual_markers_df['time']
    
    # Find the closest indices in experimental time to the start and end of virtual time
    exp_time = experimental_markers_df['time']
    initial_index = (exp_time - time.iloc[0]).abs().idxmin()
    final_index = (exp_time - time.iloc[-1]).abs().idxmin()

    distances = pd.DataFrame({'time': time.values})
    
    output_dir = os.path.dirname(marker_experimental_path)
    mean_errors_filename = os.path.join(output_dir, '_ik_marker_errors_mean.txt')

    print('Calculating marker errors for all markers...')
    with open(mean_errors_filename, 'w') as f_mean_errors:
        f_mean_errors.write('mean errors for each marker (m)\n\n')

        for marker_name in exp_marker_names:

            if 'time' in marker_name.lower() or 'frame' in marker_name.lower():
                continue

            try:
                marker_name = marker_name.split('_')[0]
                exp_cols = [col for col in exp_marker_names if col.split('_')[0] == marker_name]
                virtual_cols = [col for col in virtual_markers_df.columns if col.split('_')[0] == marker_name]

                if not exp_cols or not virtual_cols:
                    continue

                # Get experimental data for the current time range and convert mm to m
                exp_slice = experimental_markers_df.iloc[initial_index:final_index + 1]
                x1 = pd.to_numeric(exp_slice[exp_cols[0]], errors='coerce').values / 1000.0
                y1 = pd.to_numeric(exp_slice[exp_cols[1]], errors='coerce').values / 1000.0
                z1 = pd.to_numeric(exp_slice[exp_cols[2]], errors='coerce').values / 1000.0

                # Get virtual data
                x2 = virtual_markers_df[virtual_cols[0]].values
                y2 = virtual_markers_df[virtual_cols[1]].values
                z2 = virtual_markers_df[virtual_cols[2]].values
                
                # Ensure arrays are the same length by trimming the longer one
                min_len = min(len(x1), len(x2))
                x1, y1, z1 = x1[:min_len], y1[:min_len], z1[:min_len]
                x2, y2, z2 = x2[:min_len], y2[:min_len], z2[:min_len]
                
                # Calculate the 3D distance
                dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
                distances[marker_name] = pd.Series(dist)

                # Write mean error to file
                mean_error_text = f'{marker_name} = {np.mean(dist):.4f} m\n'
                f_mean_errors.write(mean_error_text)

            except (KeyError, IndexError) as e:
                print(f"Could not process marker '{marker_name}'. It might be missing in one of the files. Error: {e}")

    # Write all distance data to a .sto file
    all_errors_filename = os.path.join(output_dir, '_ik_marker_errors_all.sto')
    utils.write_sto_file(distances.dropna(axis=1, how='all'), all_errors_filename)
    print(f"Mean errors saved to: {mean_errors_filename}")
    print(f"All error data saved to: {all_errors_filename}")
    
    # plot marker errors over time    
    plt.figure(figsize=(12, 6))
    for marker_name in distances.columns:
        if marker_name != 'time':
            plt.plot(distances['time'], distances[marker_name], label=marker_name)
    
    # plot mean error as a dashed line
    mean_errors = distances.drop(columns='time').mean(axis=1)
    plt.plot(distances['time'], mean_errors, label='Mean Error', linestyle='--', color='black')
    
    plt.xlabel('Time (s)')
    plt.ylabel('Marker Error (m)')
    plt.title('Marker Errors Over Time')
    plt.legend()
    plt.grid()
    
    # save fig
    plt.savefig(os.path.join(output_dir, '_ik_marker_errors_plot.png'))
    plt.close()
    print(f"Marker errors plot saved to: {os.path.join(output_dir, '_ik_marker_errors_plot.png')}")

def create_grf_xml(grf_mot_path, output_xml_path=None,
                   marker_trc_path=None,
                   right_foot_markers=None, left_foot_markers=None,
                   right_foot_body='calcn_r', left_foot_body='calcn_l',
                   vert_force_threshold=10.0,
                   filter_cutoff=6,
                   datafile=None):
    """
    Create a working OpenSim ExternalLoads XML (GRF.xml) from a GRF .mot file.

    Automatically detects force-plate column names, assigns each plate to the
    left or right foot using marker TRC data or COP Z-position heuristic, and
    writes a correctly-formatted GRF.xml.

    Parameters
    ----------
    grf_mot_path : str
        Path to the GRF .mot file containing force plate data.
    output_xml_path : str, optional
        Output XML path. Defaults to GRF.xml next to the .mot file.
    marker_trc_path : str, optional
        Marker TRC file used to assign plates to feet by comparing COP
        positions to foot marker Z-positions.
    right_foot_markers : list of str, optional
        Marker names for the right foot (e.g. ['RHEE', 'RTOE']).
        If None, common names are tried automatically.
    left_foot_markers : list of str, optional
        Marker names for the left foot (e.g. ['LHEE', 'LTOE']).
        If None, common names are tried automatically.
    right_foot_body : str
        OpenSim body for the right foot (default 'calcn_r').
    left_foot_body : str
        OpenSim body for the left foot (default 'calcn_l').
    vert_force_threshold : float
        Minimum vertical force (N) to consider a plate active (default 10.0).
    filter_cutoff : float
        Low-pass filter cut-off for load kinematics in the XML (default 6 Hz).
    datafile : str, optional
        Value for the <datafile> tag. Defaults to the basename of grf_mot_path.
    """
    import re
    import xml.etree.ElementTree as ET

    if not os.path.exists(grf_mot_path):
        raise FileNotFoundError(f"GRF .mot file not found: {grf_mot_path}")

    if output_xml_path is None:
        output_xml_path = os.path.join(os.path.dirname(grf_mot_path), 'GRF.xml')

    if datafile is None:
        datafile = os.path.basename(grf_mot_path)

    # ------------------------------------------------------------------ #
    # 1. Load .mot and detect column name patterns per force plate
    # ------------------------------------------------------------------ #
    grf_df = utils.load_any_data_file(grf_mot_path)
    cols = grf_df.columns.tolist()

    # plates[plate_number] = {'force_id': ..., 'point_id': ..., 'torque_id': ...}
    plates = {}

    for col in cols:
        if col.lower() == 'time':
            continue

        # Force columns: end in vx/vy/vz (e.g. ground_force3_vx)
        if re.search(r'vx$', col, re.IGNORECASE) and 'force' in col.lower():
            identifier = col[:-1]   # strip trailing 'x' → e.g. 'ground_force3_v'
            nums = re.findall(r'\d+', col)
            if nums:
                plates.setdefault(nums[0], {})['force_id'] = identifier
            continue

        # Point columns: end in px/py/pz (e.g. ground_force3_px)
        if re.search(r'px$', col, re.IGNORECASE) and 'force' in col.lower():
            identifier = col[:-1]   # → e.g. 'ground_force3_p'
            nums = re.findall(r'\d+', col)
            if nums:
                plates.setdefault(nums[0], {})['point_id'] = identifier
            continue

        # Torque columns: contain 'torque' and end in x (e.g. ground_torque3_x or ground_torque3_mx)
        if re.search(r'x$', col, re.IGNORECASE) and 'torque' in col.lower():
            identifier = col[:-1]   # → e.g. 'ground_torque3_' or 'ground_torque3_m'
            nums = re.findall(r'\d+', col)
            if nums:
                plates.setdefault(nums[0], {})['torque_id'] = identifier

    if not plates:
        raise ValueError("No force plate columns detected in the .mot file. "
                         "Expected columns like 'ground_force1_vx', 'ground_force1_px', etc.")

    print(f"Detected force plates: {sorted(plates.keys(), key=lambda x: int(x))}")
    for n, ids in sorted(plates.items(), key=lambda x: int(x[0])):
        print(f"  Plate {n}: force_id='{ids.get('force_id','')}', "
              f"point_id='{ids.get('point_id','')}', torque_id='{ids.get('torque_id','')}'")

    # ------------------------------------------------------------------ #
    # 2. Assign each plate to a foot
    # ------------------------------------------------------------------ #
    DEFAULT_RIGHT = ['RHEE', 'RTOE', 'RANK', 'RANM', 'RKNE', 'RKNM', 'RMT2', 'RCAL']
    DEFAULT_LEFT  = ['LHEE', 'LTOE', 'LANK', 'LANM', 'LKNE', 'LKNM', 'LMT2', 'LCAL']

    right_z = None
    left_z  = None

    if marker_trc_path and os.path.exists(marker_trc_path):
        trc_df = utils.load_trc(marker_trc_path, combine_headers=True)
        trc_cols = trc_df.columns.tolist()

        def _find_markers(candidates, user_list):
            found = user_list if user_list else []
            if not found:
                found = [m for m in candidates
                         if any(c.upper().startswith(m.upper() + '_') or c.upper() == m.upper()
                                for c in trc_cols)]
            return found

        r_markers = _find_markers(DEFAULT_RIGHT, right_foot_markers or [])
        l_markers = _find_markers(DEFAULT_LEFT,  left_foot_markers  or [])
        print(f"Right foot markers found in TRC: {r_markers}")
        print(f"Left  foot markers found in TRC: {l_markers}")

        def _mean_z(marker_names):
            zs = []
            for name in marker_names:
                z_col = next((c for c in trc_cols
                              if c.upper() == (name + '_Z').upper()), None)
                if z_col:
                    vals = pd.to_numeric(trc_df[z_col], errors='coerce').dropna()
                    if not vals.empty:
                        # TRC uses mm; convert to m
                        zs.append(vals.mean() / 1000.0)
            return np.nanmean(zs) if zs else None

        right_z = _mean_z(r_markers)
        left_z  = _mean_z(l_markers)

        if right_z is None or left_z is None:
            print("Warning: Could not extract Z positions from markers — falling back to COP Z heuristic.")
            right_z = left_z = None
        else:
            print(f"Right foot mean Z: {right_z:.4f} m | Left foot mean Z: {left_z:.4f} m")

    plate_to_body = {}

    for plate_num, ids in plates.items():
        if 'force_id' not in ids or 'point_id' not in ids:
            print(f"Warning: Plate {plate_num} is missing force or point columns — skipping.")
            continue

        # Find vertical force and COP-Z columns (case-insensitive)
        def _find_col(target):
            if target in grf_df.columns:
                return target
            for c in grf_df.columns:
                if c.lower() == target.lower():
                    return c
            return None

        vy_col  = _find_col(ids['force_id'] + 'y')
        pz_col  = _find_col(ids['point_id'] + 'z')
        cop_z_mean = 0.0

        if vy_col and pz_col:
            vy = pd.to_numeric(grf_df[vy_col], errors='coerce')
            pz = pd.to_numeric(grf_df[pz_col], errors='coerce')
            active = vy.abs() > vert_force_threshold
            if active.any():
                cop_z_mean = float(pz[active].mean())

        if right_z is not None and left_z is not None:
            # Assign to closest foot
            if abs(cop_z_mean - right_z) <= abs(cop_z_mean - left_z):
                plate_to_body[plate_num] = right_foot_body
                side_label = 'R'
            else:
                plate_to_body[plate_num] = left_foot_body
                side_label = 'L'
        else:
            # Heuristic: positive COP Z → right, negative → left
            if cop_z_mean >= 0:
                plate_to_body[plate_num] = right_foot_body
                side_label = 'R'
            else:
                plate_to_body[plate_num] = left_foot_body
                side_label = 'L'

        print(f"  Plate {plate_num}: COP Z mean = {cop_z_mean:.4f} m → "
              f"{side_label} ({plate_to_body[plate_num]})")

    # ------------------------------------------------------------------ #
    # 3. Build XML tree
    # ------------------------------------------------------------------ #
    root = ET.Element('OpenSimDocument')
    root.set('Version', '40000')

    ext_loads = ET.SubElement(root, 'ExternalLoads')
    ext_loads.set('name', 'externalloads')
    objects_el = ET.SubElement(ext_loads, 'objects')

    for plate_num in sorted(plates.keys(), key=lambda x: int(x)):
        ids = plates[plate_num]
        if 'force_id' not in ids or 'point_id' not in ids:
            continue

        body = plate_to_body.get(plate_num, right_foot_body)
        side = 'r' if body == right_foot_body else 'l'
        force_name = f'grf_{side}_{plate_num}'

        ef = ET.SubElement(objects_el, 'ExternalForce')
        ef.set('name', force_name)
        ET.SubElement(ef, 'applied_to_body').text          = body
        ET.SubElement(ef, 'force_expressed_in_body').text  = 'ground'
        ET.SubElement(ef, 'point_expressed_in_body').text  = 'ground'
        ET.SubElement(ef, 'force_identifier').text         = ids['force_id']
        ET.SubElement(ef, 'point_identifier').text         = ids['point_id']
        ET.SubElement(ef, 'torque_identifier').text        = ids.get('torque_id', '')
        ET.SubElement(ef, 'data_source_name').text         = ''

    ET.SubElement(ext_loads, 'groups')
    ET.SubElement(ext_loads, 'datafile').text = datafile
    ET.SubElement(ext_loads, 'external_loads_model_kinematics_file').text = ''
    ET.SubElement(ext_loads, 'lowpass_cutoff_frequency_for_load_kinematics').text = str(filter_cutoff)

    # ------------------------------------------------------------------ #
    # 4. Save using utils pretty-printer
    # ------------------------------------------------------------------ #
    tree = ET.ElementTree(root)
    utils.save_pretty_xml(tree, output_xml_path)

    print(f"\nGRF XML saved to: {os.path.abspath(output_xml_path)}")
    print(f"Plates: {sorted(plates.keys(), key=lambda x: int(x))}  |  Data file: {datafile}")
    return os.path.abspath(output_xml_path)

def convert_mot_to_sto(mot_file_path = None):
    """
    Convert a .mot file to a .sto file.
    """
    if not mot_file_path:
        mot_file_path = input("Enter path to .mot file: ").strip('"')
    
    sto_file_path = mot_file_path.replace('.mot', '.sto')
    
    if not os.path.exists(mot_file_path):
        print(f".mot file not found: {mot_file_path}")
        return

    if os.path.exists(sto_file_path):
        print(f".sto file already exists: {sto_file_path}")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sto_file_path = mot_file_path.replace('.mot', f'_{timestamp}.sto')
    
    mot_data = utils.load_any_data_file(mot_file_path)
    utils.write_sto_file(mot_data, sto_file_path)
    
    print(f"Converted {mot_file_path} to {sto_file_path}")

    return sto_file_path

def scale_model_from_xml(setup_xml_path, generic_model_path, static_trc_path, scaled_model_path, mass=None):
    """
    Scale an OpenSim model using a pre-existing ScaleTool setup XML (preserving its
    MeasurementSet, MarkerPlacer IK tasks, etc.) while overriding the key file paths
    and optionally the subject mass.

    Args:
        setup_xml_path (str): Path to the ScaleTool setup XML file.
        generic_model_path (str): Path to the unscaled generic .osim model.
        static_trc_path (str): Path to the static trial TRC file.
        scaled_model_path (str): Absolute path for the output scaled .osim model.
        mass (float, optional): Subject mass in kg. Defaults to model total mass.
    """
    scale_tool = osim.ScaleTool(setup_xml_path)

    base_folder = os.path.dirname(setup_xml_path)

    if mass is not None:
        scale_tool.setSubjectMass(mass)

    # GenericModelMaker
    scale_tool.getGenericModelMaker().setModelFileName(generic_model_path)

    # ModelScaler
    model_scaler = scale_tool.getModelScaler()
    model_scaler.setApply(True)
    model_scaler.setMarkerFileName(os.path.basename(static_trc_path))
    model_scaler.setOutputModelFileName(os.path.relpath(scaled_model_path, base_folder))
    model_scaler.setOutputScaleFileName('scale_set.xml')

    # MarkerPlacer
    marker_placer = scale_tool.getMarkerPlacer()
    marker_placer.setApply(True)
    marker_placer.setMarkerFileName(os.path.basename(static_trc_path))
    marker_placer.setOutputModelFileName(os.path.relpath(scaled_model_path, base_folder))
    marker_placer.setOutputMarkerFileName('static_output.trc')

    # print scale tool setup xml
    os.chdir(base_folder)
    scale_tool.printToXML(os.path.join(base_folder, 'setup_scale.xml'))
    print(f"Modified ScaleTool setup saved to: {os.path.join(os.path.dirname(scaled_model_path), 'setup_scale.xml')}")

    output = scale_tool.run()
    
    if not output:
        print(f"Scaled model saved to: {scaled_model_path}")
    else:
        print("Error: Scaling failed. Check the ScaleTool setup and input files.")

    return scale_tool

def scale_model(generic_opensim_model_path, static_trc_path, scaled_model_path, mass=None, time_range=None, marker_set_file=None):
    """
    Scale an OpenSim model using the ScaleTool based on static marker data from a TRC file.
    """
    model = osim.Model(generic_opensim_model_path)
    state = model.initSystem()
    subject_mass = mass if mass is not None else model.getTotalMass(state)

    # Resolve time range from TRC if not provided
    storage = osim.Storage(static_trc_path)
    t0, t1 = (time_range[0], time_range[1]) if time_range else (storage.getFirstTime(), storage.getFirstTime())
    osim_time_range = osim.ArrayDouble()
    osim_time_range.append(t0)
    osim_time_range.append(t1)

    scaleTool = osim.ScaleTool()
    scaleTool.setName("ModelScaling")
    scaleTool.setSubjectMass(subject_mass)

    # GenericModelMaker — sets the unscaled model (and optionally a marker set)
    gmm = scaleTool.getGenericModelMaker()
    gmm.setModelFileName(generic_opensim_model_path)
    if marker_set_file:
        gmm.setMarkerSetFileName(marker_set_file)

    # ModelScaler
    modelScaler = scaleTool.getModelScaler()
    modelScaler.setApply(True)
    modelScaler.setMarkerFileName(static_trc_path)
    modelScaler.setTimeRange(osim_time_range)
    modelScaler.setOutputModelFileName(scaled_model_path)
    modelScaler.setOutputScaleFileName(
        os.path.join(os.path.dirname(scaled_model_path), 'scale_set.xml')
    )

    # MarkerPlacer
    markerPlacer = scaleTool.getMarkerPlacer()
    markerPlacer.setApply(True)
    markerPlacer.setMarkerFileName(static_trc_path)
    markerPlacer.setTimeRange(osim_time_range)
    markerPlacer.setOutputModelFileName(scaled_model_path)
    markerPlacer.setOutputMarkerFileName(
        os.path.join(os.path.dirname(scaled_model_path), 'static_output.trc')
    )

    scaleTool.run()
    print(f"Scaled model saved to: {scaled_model_path}")
    
# --- Inverse Kinematics ---
def create_setup_IK(osim_modelPath=None, marker_trc=None,
                    ik_output=None, taskSetPath=None, time_range=None,
                    saveXMLPath=None):
    """
    Create an Inverse Kinematics (IK) setup XML file for OpenSim.
    """
    if not osim_modelPath:
        osim_modelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')
    
    if not marker_trc:
        marker_trc = input("Enter the path to the marker TRC file (.trc): ").strip('"')
        
    if time_range is None:
        time_range_input = input("Enter the time range for IK calculation as 'start,end' (or press Enter to use full range): ").strip('"').strip("'")
        if time_range_input:
            try:
                start_str, end_str = time_range_input.split(',')
                time_range = (float(start_str), float(end_str))
            except ValueError:
                print("Invalid time range format. Using full range.")
                time_range = None
        else:
            time_range = None
            
    if not os.path.exists(osim_modelPath):
        print(f"OpenSim model file not found: {osim_modelPath}")
        return
    
    # Load the model
    model = osim.Model(osim_modelPath)
    
    # Load markers
    markers = osim.Storage(marker_trc)

    # Create the Inverse Kinematics tool
    ikTool = osim.InverseKinematicsTool()
    
    if taskSetPath:
        ikTaskSet_template = osim.IKTaskSet(taskSetPath) 
        ikTool.set_IKTaskSet(ikTaskSet_template)    
    
    # simple function to validate the markers used in the IK setup
    ikTool = validate_markers_used(osim_modelPath, ikTool, marker_trc)

    # Set the model and parameters
    ikTool.setModel(model)
    ikTool.set_model_file(osim_modelPath)
    # Set the marker data file and time range
    ikTool.setMarkerDataFileName(marker_trc)
    ikTool.set_report_marker_locations(True)
    ikTool.set_report_errors(True)
    
    # # check time range is valid and set it
    if time_range is not None:
        if time_range[0] < markers.getFirstTime() or time_range[1] > markers.getLastTime():
            print("Warning: Specified time range is outside the bounds of the marker data. Using full range instead.")
            time_range = [markers.getFirstTime(), markers.getLastTime()]
        
        ikTool.setStartTime(time_range[0])  # Set start time
        ikTool.setEndTime(time_range[1])    # Set end time
    else:
        ikTool.setStartTime(markers.getFirstTime())  # Default start time
        ikTool.setEndTime(markers.getLastTime())    # Default end time
    
    # Set the output motion file name relative to the results directory
    ikTool.setResultsDir('./')
    resultsDir = os.path.dirname(ik_output)
    ikTool.setOutputMotionFileName(os.path.relpath(ik_output, resultsDir))
    if saveXMLPath is None:
        saveXMLPath = ik_output.replace('.mot', '_ik_setup.xml')
    ikTool.printToXML(saveXMLPath)
    print(f"Inverse Kinematics setup saved to {os.path.abspath(saveXMLPath)}")

def run_ik(osim_modelPath=None, setup_xml=None, resultsDir=None):
    
    if osim_modelPath is None:
        osim_modelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')
    if setup_xml is None:
        setup_xml = input("Enter the path to save the IK setup XML file (.xml): ").strip('"')
        
    if not os.path.exists(osim_modelPath):
        utils.print_to_log(f"OpenSim model file not found: {osim_modelPath}")

    # Load the model
    model = osim.Model(osim_modelPath)
    
    # Reload tool from xml
    ikTool = osim.InverseKinematicsTool(setup_xml)
    ikTool.setModel(model)
    
    # Run the inverse kinematics calculation
    ikTool.run()
    
    print(f"Inverse Kinematics calculation completed. Results saved to {resultsDir}")

# --- Muscle Analysis ---
def find_non_zero_mom_arm_muscles(ma_data: pd.DataFrame, muscles: list) -> list:
    '''
    Find the muscles that have non-zero moment arms in the given data.
    '''
    
    non_zero_muscles = []
    for muscle in muscles:
        if ma_data is None:
            continue
        if muscle not in ma_data.columns:
            continue
        if ma_data[muscle].abs().sum() > 0:
            non_zero_muscles.append(muscle)
    return non_zero_muscles

# --- Static optimisation --
def edit_pelvis_com_actuators(osim_modelPath, actuatorsFilePath):
    """
    Edit the pelvis center of mass actuator in the OpenSim model.
    """ 
    model = osim.Model(osim_modelPath)
    model.initSystem()

    # Find the pelvis center of mass actuator
    pelvis = model.getBodySet().get('pelvis')
    com = pelvis.get_mass_center().to_numpy()

    actuators = utils.read_xml(actuatorsFilePath)
    point_actuators = actuators.find('ForceSet').find('objects').findall('PointActuator')
    
    for actuator in point_actuators:
        if actuator.get('name') in ['FX', 'FY', 'FZ']:
            # Update the point in the actuator to match the pelvis center of mass
            point = actuator.find('point')
            point.text = f"{com[0]} {com[1]} {com[2]}"
    
    # Save the modified actuators file
    utils.save_pretty_xml(actuators, actuatorsFilePath)
    
    print(f"Updated pelvis center of mass actuator in {actuatorsFilePath} to {com}")

def normalise_muscle(muscle_forces_path, osim_modelPath):
    
    muscle_forces = utils.load_any_data_file(muscle_forces_path)
    model = osim.Model(osim_modelPath)
    model_muscles = model.getMuscles()
    for muscle in muscle_forces.columns:
        try:
            muscle_obj = model_muscles.get(muscle)
        except Exception as e:
            print(f"Error retrieving muscle '{muscle}': {e}")
            continue
                
        # Normalize the muscle forces
        normalized_forces = muscle_forces[muscle] / muscle_obj.getMaxIsometricForce()
        
        # Save the normalized forces back to the DataFrame
        muscle_forces[muscle] = normalized_forces
    
    # Save the normalized muscle forces to a new file
    header = utils.load_sto_header(muscle_forces_path)
    utils.write_sto_file(muscle_forces, muscle_forces_path.replace('.sto', '_normalised.sto'), header=header)
    
    print(f"Normalized muscle forces saved to {muscle_forces_path.replace('.sto','_normalised.sto')}")

# --- Joint Reaction Analysis ---
def create_analysis_tool(marker_trc, externalloadsfile, osim_modelPath, 
                         results_directory, actuators=None):
    """Creates and configures an OpenSim AnalyzeTool object.

    Args:
    coordinates_file: Path to the motion data file (e.g., .trc or .mot).
    model_path: Path to the OpenSim model file (.osim).
    results_directory: Path to the directory for storing results.
    force_set_files (optional): List of paths to actuator force set files.

    Returns:
    OpenSim AnalyzeTool object.

    # Example usage:
        coordinates_file = "your_motion_data.trc"
        model_path = "your_model.osim"
        results_directory = "analysis_results"
        force_set_files = ["actuator1_forces.xml", "actuator2_forces.xml"]  # Optional

        analysis_tool = create_analysis_tool(coordinates_file, model_path, results_directory, force_set_files)

        # Run the analysis
        analysis_tool.run()
    """

    # Load the motion data
    mot_data = osim.Storage(marker_trc)

    # Get initial and final time
    initial_time = mot_data.getFirstTime()
    final_time = mot_data.getLastTime()

    # Create and set model
    model = osim.Model(osim_modelPath)
    analyze_tool = osim.AnalyzeTool()
    analyze_tool.setModel(model)

    # Set other parameters
    relpath_modelfile = os.path.relpath(osim_modelPath, start=os.path.dirname(marker_trc))
    analyze_tool.setModelFilename(relpath_modelfile)
    analyze_tool.setReplaceForceSet(False)
    
    # set results directory
    relpath_results_directory = os.path.relpath(results_directory, start=os.path.dirname(marker_trc))
    analyze_tool.setResultsDir(relpath_results_directory)
    analyze_tool.setOutputPrecision(8)

    # Set actuator force files (if provided)
    if actuators:
        force_set = osim.ArrayStr()
        for file in actuators:
            force_set.append(file)
        analyze_tool.setForceSetFiles(force_set)

    # Set initial and final time
    analyze_tool.setInitialTime(initial_time)
    analyze_tool.setFinalTime(final_time)

    # Set analysis parameters
    analyze_tool.setSolveForEquilibrium(False)
    analyze_tool.setMaximumNumberOfSteps(20000)
    analyze_tool.setMaxDT(1)
    analyze_tool.setMinDT(1e-8)
    analyze_tool.setErrorTolerance(1e-5)

    # Set external loads and coordinates files
    relpath_externalloadsfile = os.path.relpath(externalloadsfile, start=os.path.dirname(marker_trc))
    relpath_coordinates_file = os.path.relpath(marker_trc, start=os.path.dirname(marker_trc))
    analyze_tool.setExternalLoadsFileName(relpath_externalloadsfile)  # Replace with your filename
    analyze_tool.setCoordinatesFileName(relpath_coordinates_file)

    # Set filter cutoff frequency
    analyze_tool.setLowpassCutoffFrequency(6)


    # Return the analysis tool
    return analyze_tool

# --- Induced Acceleration Analysis ---
def create_iaa_tool(osim_modelPath=None, ik_output=None, grf_xml=None, setup_file_path=None, so_controls_file=None, actuators=None):
    """
    Create and configure an OpenSim Induced Acceleration Tool object.

    Args:
        osim_modelPath (str): Path to the OpenSim model file (.osim).
        ik_output (str): Path to the Inverse Kinematics output file (.mot).
        grf_xml (str): Path to the Ground Reaction Forces XML file (.xml).
        setup_file_path (str): Path to the Induced Acceleration setup XML file (.xml).
        so_controls_file (str, optional): Path to the Static Optimization controls file (.sto).

    Returns:
        OpenSim InducedAccelerationTool object.
    """

    if not osim_modelPath:
        osim_modelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')

    if not ik_output:
        ik_output = input("Enter the path to the Inverse Kinematics output file (.mot): ").strip('"')

    if not grf_xml:
        grf_xml = input("Enter the path to the Ground Reaction Forces XML file (.xml): ").strip('"')

    if not setup_file_path:
        setup_file_path = os.path.join(os.path.dirname(os.path.abspath(ik_output)), 'setup_IAA.xml')

    if not so_controls_file:
        so_controls_file = input("Enter the path to the Static Optimization controls file (.sto): ").strip('"')

        activation_file = input("Enter the path to the Static Optimization activations file (.sto) (or press Enter to skip): ").strip('"')

    # Create and set model
    model = osim.Model(osim_modelPath)
    breakpoint()
    tool = osim.AnalyzeTool(model)
    tool.setName("InducedAccelerations_Tool")
    tool.setModelFilename(osim_modelPath)

    # Load motion to get start/end times
    motion = osim.Storage(ik_output)
    initial_time = motion.getFirstTime()
    final_time = motion.getLastTime()

    # Set Tool Parameters
    tool.setInitialTime(initial_time)
    tool.setFinalTime(final_time)
    tool.setCoordinatesFileName(ik_output)
    tool.setExternalLoadsFileName(grf_xml)
    tool.setControlsFileName(so_controls_file)
    tool.setSolveForEquilibrium(True)
    tool.setLowpassCutoffFrequency(6.0) # Filter coordinates

    tool.setStatesFileName(activation_file)
    tool.setSolveForEquilibrium(False)
    
    # Set results directory relative to where the setup file will be, or absolute
    results_dir = os.path.join(os.path.dirname(setup_file_path), "IAA_Results")
    tool.setResultsDir(results_dir)

    # Set actuator force files (if provided)
    if actuators:
        force_set = osim.ArrayStr()
        for file in actuators:
            force_set.append(os.path.abspath(file))
        tool.setForceSetFiles(force_set)
        tool.setReplaceForceSet(False)

    # 3. Configure the InducedAccelerations Analysis
    iaa_analysis = osim.InducedAccelerations()
    iaa_analysis.setName("InducedAccelerations")
    iaa_analysis.setStartTime(initial_time)
    iaa_analysis.setEndTime(final_time)
    
    # Add the Analysis to the Tool
    tool.getAnalysisSet().adoptAndAppend(iaa_analysis)

    # Save the setup file for reference
    tool.printToXML(setup_file_path)
    print(f"IAA Tool configured. Setup file saved to: {setup_file_path}")
    tool.run()
    return tool

# --- Main OSIM Analysis ---
def run_id(osimModelPath=None, ikOutputPath=None, grfXmlPath=None, 
         setupXmlPath=None):
    """
    Example usage:
    main(osim_modelPath='path/to/model.osim', 
         ik_output='path/to/ik_output.mot', 
         grf_xml='path/to/grf.xml', 
         setup_xml='path/to/setup.xml', 
         resultsDir='path/to/results')
    
    """
    if not osimModelPath:
        osimModelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')
    if not ikOutputPath:
        ikOutputPath = input("Enter the path to the Inverse Kinematics output file (.mot): ").strip('"')
    if not grfXmlPath:
        grfXmlPath = input("Enter the path to the Ground Reaction Forces XML file (.xml): ").strip('"')
    if not setupXmlPath:
        setupXmlPath = input("Enter the path to save the Inverse Dynamics setup XML file (.xml): ").strip('"')
    
    resultsDir = os.path.dirname(os.path.abspath(setupXmlPath))
    
    if not os.path.exists(osimModelPath):
        raise FileNotFoundError(f"OpenSim model file not found: {osimModelPath}")
    
    if not os.path.exists(ikOutputPath):
        raise FileNotFoundError(f"Inverse Kinematics motion file not found: {ikOutputPath}")

    if not os.path.exists(grfXmlPath):
        raise FileNotFoundError(f"Ground Reaction Forces XML file not found: {grfXmlPath}")
    
    if not os.path.exists(resultsDir):
        os.makedirs(resultsDir)
    
    # Load the model
    print(f"Loading OpenSim model from {osimModelPath}")
    model = osim.Model(osimModelPath)
    model.initSystem()

    # Load the motion data
    motion = osim.Storage(ikOutputPath)

    # Create the Inverse Dynamics tool
    idTool = osim.InverseDynamicsTool()
    idTool.setModel(model)
    idTool.setOutputGenForceFileName("inverse_dynamics.sto") # Output file name for the forces
    idTool.setModelFileName(os.path.relpath(osimModelPath, start=os.path.dirname(setupXmlPath)))
    idTool.setCoordinatesFileName(os.path.relpath(ikOutputPath, start=os.path.dirname(setupXmlPath)))
    idTool.setStartTime(motion.getFirstTime()) # Start time
    idTool.setEndTime(motion.getLastTime()) # end time
    idTool.setExternalLoadsFileName(os.path.relpath(grfXmlPath, start=os.path.dirname(setupXmlPath)))
    idTool.setResultsDir(os.path.relpath(resultsDir, start=os.path.dirname(setupXmlPath)))
    
    # Set lowpass filter frequency
    idTool.setLowpassCutoffFrequency(6)
    
    # Print the setup to XML
    idTool.printToXML(setupXmlPath)
    print(f"Inverse Dynamics setup saved to {setupXmlPath}")
    
    # Load xml and edit forces to exclude
    xml = utils.read_xml(setupXmlPath)
    xml.find('.//forces_to_exclude').text = 'Muscles'
    utils.save_pretty_xml(xml, setupXmlPath)

    # Reload tool from xml
    idTool = osim.InverseDynamicsTool(setupXmlPath)   
    idTool.printToXML(setupXmlPath)  # Print to XML again to ensure changes are saved
    
    # Run the inverse dynamics calculation
    os.chdir(resultsDir)
    idTool.run()
    idTool.setModel(model)  # Set the model again after running

    print(f"Inverse Dynamics calculation completed. Results saved to {resultsDir}\\inverse_dynamics.sto")

def run_ma(osim_modelPath=None, ik_output=None, 
         grf_xml=None):

    if osim_modelPath is None:
        osim_modelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')
    if ik_output is None:
        ik_output = input("Enter the desired output path for the IK results (.mot): ").strip('"')
    if grf_xml is None:
        grf_xml = input("Enter the path to the GRF XML file (.xml): ").strip('"')
    
    ikParentDir = os.path.dirname(os.path.abspath(ik_output))
    resultsDir = os.path.join(ikParentDir, 'MuscleAnalysis')
    setup_xml = os.path.join(ikParentDir, 'setup_ma.xml')
    

    if not os.path.exists(osim_modelPath):
        raise FileNotFoundError(f"OpenSim model file not found: {osim_modelPath}")
    
    if not os.path.exists(ik_output):
        raise FileNotFoundError(f"Inverse Kinematics motion file not found: {ik_output}")
    
    if not os.path.exists(grf_xml):
        raise FileNotFoundError(f"Ground Reaction Forces XML file not found: {grf_xml}")
        
    if not os.path.exists(resultsDir):
        os.makedirs(resultsDir, exist_ok=True)
    
    # Load the model
    print(f"Loading OpenSim model from {osim_modelPath}")
    model = osim.Model(osim_modelPath)
    model.initSystem()

    # Load the motion data
    motion = osim.Storage(ik_output)

    # Create a MuscleAnalysis object
    muscleAnalysis = osim.MuscleAnalysis()
    muscleAnalysis.setModel(model)
    muscleAnalysis.setStartTime(motion.getFirstTime())
    muscleAnalysis.setEndTime(motion.getLastTime())

    # Create the muscle analysis tool
    maTool = osim.AnalyzeTool()
    maTool.setModel(model)
    maTool.setModelFilename(os.path.relpath(osim_modelPath,  start=os.path.dirname(setup_xml)))
    maTool.setLowpassCutoffFrequency(6)
    maTool.setCoordinatesFileName(os.path.relpath(ik_output, start=os.path.dirname(setup_xml)))
    maTool.setName('')
    maTool.setMaximumNumberOfSteps(20000)
    maTool.setStartTime(motion.getFirstTime())
    maTool.setFinalTime(motion.getLastTime())
    maTool.getAnalysisSet().cloneAndAppend(muscleAnalysis)
    maTool.setResultsDir(os.path.relpath(resultsDir, start=os.path.dirname(setup_xml)))
    maTool.setInitialTime(motion.getFirstTime())
    maTool.setFinalTime(motion.getLastTime())
    maTool.setExternalLoadsFileName(os.path.relpath(grf_xml, start=os.path.dirname(setup_xml)))
    maTool.setSolveForEquilibrium(False)
    maTool.setReplaceForceSet(False)
    maTool.setMaximumNumberOfSteps(20000)
    maTool.setOutputPrecision(8)
    maTool.setMaxDT(1)
    maTool.setMinDT(1e-008)
    maTool.setErrorTolerance(1e-005)
    maTool.removeControllerSetFromModel()
    maTool.setLowpassCutoffFrequency(6)
    maTool.printToXML(setup_xml)

    # Reload analysis from xml
    maTool = osim.AnalyzeTool(setup_xml)
    maTool.getModel().initSystem()
    # Run the muscle analysis calculation
    maTool.run()

def run_so(osim_modelPath=None, ik_output=None, grf_xml=None, 
           setup_xml=None, actuators=None, resultsDir=None):

    if not osim_modelPath:
        osim_modelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')
    
    if not ik_output:
        ik_output = input("Enter the desired output path for the IK results (.mot): ").strip('"')

    if not grf_xml:
        grf_xml = input("Enter the path to the GRF XML file (.xml): ").strip('"')

    if not setup_xml:
        setup_xml = input("Enter the path to the setup XML file (.xml): ").strip('"')

    if not actuators:
        actuators = input("Enter the path to the actuators file (.xml): ").strip('"')
    
    if not resultsDir:
        resultsDir = os.path.dirname(ik_output)

    if not os.path.exists(resultsDir):
        os.makedirs(resultsDir)
    
    # Load the model
    print(f"Loading OpenSim model from {osim_modelPath}")
    
    model = osim.Model(osim_modelPath)
    # model.initSystem()
    
    # load the motion data
    motion = osim.Storage(ik_output)
    
    # Create a StaticOptimization object
    so = osim.StaticOptimization()
    so.setStartTime(motion.getFirstTime())
    so.setEndTime(motion.getLastTime())
    so.setInDegrees(True)
    so.setUseMusclePhysiology(True)
    so.setUseModelForceSet(True)
    
    
    # Create analyze tool for static optimization
    so_analyze_tool = osim.AnalyzeTool()
    so_analyze_tool.setName("SO")

    # Set model file, motion files and external load file names
    so_analyze_tool.setModelFilename(os.path.relpath(osim_modelPath, start=os.path.dirname(setup_xml)))
    so_analyze_tool.setCoordinatesFileName(os.path.relpath(ik_output, start=os.path.dirname(setup_xml)))
    so_analyze_tool.setExternalLoadsFileName(os.path.relpath(grf_xml, start=os.path.dirname(setup_xml)))
    so_analyze_tool.setReplaceForceSet(False)
    so_analyze_tool.getForceSetFiles().append(os.path.relpath(actuators, start=os.path.dirname(setup_xml)))

    so_analyze_tool.setLowpassCutoffFrequency(6)
    
    # Add StaticOptimization analysis to the tool
    so_analyze_tool.updAnalysisSet().cloneAndAppend(so)

    # Configure analyze tool
    so_analyze_tool.setReplaceForceSet(False)
    so_analyze_tool.setStartTime(motion.getFirstTime())
    so_analyze_tool.setFinalTime(motion.getLastTime())

    # Set results directory
    so_analyze_tool.setResultsDir(os.path.relpath(resultsDir, start=os.path.dirname(setup_xml)))

    # Print configuration to XML file
    so_analyze_tool.printToXML(setup_xml)
    print("\n \n Static Optimization setup saved to:", setup_xml)
    
    # change optimizer_max_iterations in the xml file
    xml = utils.read_xml(setup_xml)
    static_opt = xml.getroot().find('.//StaticOptimization/optimizer_max_iterations')
    static_opt.text = '100'  # Set to 10 iterations
    utils.save_pretty_xml(xml, setup_xml)
    
    # run the Static Optimization
    so_analyze_tool = osim.AnalyzeTool(setup_xml)
    try:
        os.chdir(resultsDir)
        so_analyze_tool.run()
        print(f"Static Optimization calculation completed. Results saved to {resultsDir}")
    except Exception as e:
        print(f"Error during Static Optimization: {e}")

def run_jra(osim_modelPath=None, ik_output=None, 
         grf_xml=None, setup_xml=None, actuators=None, 
         muscle_force_path=None, saveFileName=None):
    
    if not osim_modelPath:
        osim_modelPath = input("Enter the path to the OpenSim model file (.osim): ").strip('"')
    if not ik_output:
        ik_output = input("Enter the path to the coordinates motion file (.mot or .trc): ").strip('"')
    if not grf_xml:
        grf_xml = input("Enter the path to the external loads file (.xml): ").strip('"')
    if not setup_xml:
        setup_xml = input("Enter the path to save the JRA setup XML file (.xml): ").strip('"')
    if not muscle_force_path:
        muscle_force_path = input("Enter the path to the muscle forces file (.sto): ").strip('"')
    
    setup_xml_parent = os.path.dirname(os.path.abspath(ik_output))
    
    # start model
    osimModel = osim.Model(osim_modelPath)
    
    # Get mot data to determine time range
    motData = osim.Storage(ik_output)

    # Get initial and intial time
    initial_time = motData.getFirstTime()
    final_time = motData.getLastTime()
    
    # start joint reaction analysis
    jr = osim.JointReaction(setup_xml)
    
    # add muscle forces file name to joint reaction analysis
    jr.setName('JRA')
    
    # define JRA 
    inFrame = osim.ArrayStr()
    onBody = osim.ArrayStr()
    jointNames = osim.ArrayStr()
    inFrame.set(0, 'child')
    onBody.set(0, 'child')
    jointNames.set(0, 'all')

    jr.setInFrame(inFrame)
    jr.setOnBody(onBody)
    jr.setJointNames(jointNames)

    # Set other parameters as needed
    jr.setStartTime(initial_time)
    jr.setEndTime(final_time)
    jr.setForcesFileName(os.path.relpath(muscle_force_path, start=os.path.dirname(os.path.abspath(setup_xml)))) # Has to be absolute path

    # add to analysis tool
    analyzeTool_JR = create_analysis_tool(marker_trc = ik_output,
                                          externalloadsfile = grf_xml,
                                          osim_modelPath = osim_modelPath, 
                                          results_directory = setup_xml_parent, 
                                          actuators=actuators)
    
    analyzeTool_JR.setName('Analyse')
    analyzeTool_JR.getAnalysisSet().cloneAndAppend(jr)
    osimModel.addAnalysis(jr)

    # save setup file and run
    analyzeTool_JR.printToXML(setup_xml)
    analyzeTool_JR = osim.AnalyzeTool(setup_xml)
    print('jra for', setup_xml)
    analyzeTool_JR.run()
    
    # rename output file
    output_jra_file = os.path.join(setup_xml_parent, 'Analyse_JRA_ReactionLoads.sto')
    if saveFileName:
        new_jra_file = os.path.abspath(saveFileName)
        if os.path.exists(output_jra_file) and new_jra_file != output_jra_file:
            if os.path.exists(new_jra_file):
                os.remove(new_jra_file)
            os.rename(output_jra_file, new_jra_file)
            print(f"Joint Reaction Analysis results saved to: {new_jra_file}")
    else:
        if os.path.exists(output_jra_file):
            print(f"Joint Reaction Analysis results saved to: {output_jra_file}")

def run_emg_normalise(target_emg_path=None, normalise_emg_list=None):
    """
    Normalises EMG data based on a target EMG file.
    The target EMG file is used to scale the other EMG files in the list.
    """
    
    if not target_emg_path:
        target_emg_path = input("Enter the path to the target EMG .mot file to normalise: ").strip('"')
        
    if not normalise_emg_list:
        normalise_emg_list = []
        print("Enter paths to EMG .mot files to use for normalisation (one per line). Enter an empty line to finish:")
        while True:
            emg_file = input().strip('"')
            if emg_file == "":
                break
            if os.path.exists(emg_file):
                normalise_emg_list.append(emg_file)
            else:
                print(f"File not found: {emg_file}. Please try again.")
    
    target_emg = utils.load_any_data_file(target_emg_path)
    max_values = pd.DataFrame(columns=target_emg.columns)

    # Calculate the max of each EMG channel in normalise_emg_list
    for emg_file in normalise_emg_list:
        if not os.path.exists(emg_file):
            utils.print_to_log(f"EMG file not found: {emg_file}")
            continue
        emg_data = utils.load_any_data_file(emg_file)
        if emg_data is not None:
            max_values = pd.concat([max_values, pd.DataFrame([emg_data.max()])], ignore_index=True)
        else:
            print(f"Warning: Could not load EMG data from {emg_file}")
            
    if max_values.empty:
        utils.print_to_log("No valid EMG data found in the provided list.")
    
    
    if target_emg is None:
        utils.print_to_log(f"Target EMG file not found or could not be loaded: {target_emg_path}")

    
    # Normalise the target EMG to its own max values
    max_per_column = max_values.max(axis=0)
    target_emg_norm = target_emg.divide(max_per_column, axis=1)
    target_emg_norm['time'] = target_emg['time']  # Ensure time column is preserved
    
    # Save the normalised target EMG
    ext = os.path.splitext(target_emg_path)[1]
    savePath = os.path.abspath(target_emg_path.replace(ext, f'_normalised{ext}'))   
    utils.write_sto_file(dataFrame=target_emg_norm, 
                         file_path=savePath)

    utils.print_to_log(f"Normalised EMG data saved to: {savePath}")

def run_iaa(osim_modelPath=None, ik_output=None, grf_xml=None, setup_file_path=None, so_controls_file=None, actuators=None, setup_xml=None):
    """
    Run an Induced Acceleration Analysis (IAA) using OpenSim.
    """

    if os.path.exists(setup_xml):
        try:
            tool = osim.AnalyzeTool(setup_xml)
            tool.run()
            utils.print_to_log(f"IAA run successfully with existing setup XML: {setup_xml}")
            return
        except Exception as e:
            print(f"Error running IAA with existing setup XML: {e}")
            print("Falling back to creating a new IAA tool.")
            utils.print_to_log(f"Error running IAA with existing setup XML: {e}. Falling back to creating a new IAA tool.")
    
    try:
        tool = create_iaa_tool(osim_modelPath, ik_output, grf_xml, setup_file_path, so_controls_file, actuators)
        tool.run()
        utils.print_to_log("IAA run successfully.")
    except Exception as e:
        print(f"Error running IAA: {e}")
        utils.print_to_log(f"Error running IAA: {e}")

if __name__ == "__main__":
    
    LocalFuncs = [f for f in dir() if callable(globals()[f])]

    # Command loop
    while True:
        print("Available commands:", LocalFuncs)
        command = input("Enter command: ")

        if not command in LocalFuncs:
            print("Invalid command. Please try again.")
            continue

        try:
            globals()[command]()
        except Exception as e:
            print(f"Error executing {command}: {e}")

        print("Command executed successfully.")