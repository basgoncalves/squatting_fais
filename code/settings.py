import os
from pathlib import Path


'''
For this to work folder structure is assumed:
powerlifing_model/
    code/
        settings.py
    models/
        subject1/
            session1/
                model_name 
        subject2/
    simulations/
        subject1/
            session1/
                trial1/
                trial2/
            session2/
        subject2/
        ...
    results/

'''

MODULE_DIR = Path(__file__).parent
SETUP_DIR = os.path.join(MODULE_DIR, 'setupFiles')
PROJECT_NAME = 'squatting_fais' # 'powerlifing_model' 'squatting_fais'

# INITIATE ALL VARIABLES
marker_weights = {}
DOFs = []
DOFs_moments = {}
Muscle_Groups = {}
JCF_Groups = {}
EMG_muscle_mapping = {}
plot = {}
emg_string_list = []
model_config = {}
        
class Inputs:
    def __init__(self, parentdir=None):
        
        self.setup_dir = os.path.relpath(SETUP_DIR, parentdir) if parentdir else SETUP_DIR
        self.model_name = 'scaled.osim'
        self.model_dir = ''
        self.time_range = '0.00 1.00'
        self.c3d = 'c3dfile.c3d'
        self.emg = 'emg.mot'
        self.grf_mot = 'grf.mot'
        self.markers = 'markers_experimental.trc'
        self.events = 'events.csv'
        
        # setups 
        self.setup_ik = 'setup_IK.xml'
        self.setup_grf = 'GRF.xml'   
        self.setup_id = 'setup_ID.xml'
        self.setup_ma = 'setup_MA.xml'
        self.actuators_so = 'actuators_so.xml' 
        self.setup_so = 'setup_SO.xml'
        self.jra_forces = 'SO_StaticOptimization_force.sto'
        self.setup_jra = 'setup_JRA.xml'
        
        self.ceinms_excitations = self.emg
        self.ceinms_uncalibrated_model= '..\subjectUncalibrated.xml'
        self.ceinms_calibrated_model = '..\subjectCalibrated.xml'
        self.ceinms_calibration_cfg = '..\calibrationCfg.xml'
        self.ceinms_calibration_setup = '..\calibrationSetup.xml'
        self.ceinms_input_data = 'inputData.xml'
        self.ceinms_excitation_generator = '..\excitationGenerator.xml'
        
        self.ceinms_optimise_setup = 'ceinms_setup_optimise.xml'
        self.ceinms_optimise_cfg = 'ceinms_cfg_optimise.xml'

        self.alpha = '10'
        self.beta = '1'
        self.gamma = '1000'
        
        self.ceinms_exe_cfg = 'ceinms_cfg.xml'
        self.ceinms_exe_setup = 'ceinms_setup.xml'
        
        self.ik = 'joint_angles.mot'
        self.model_markers = '_ik_model_marker_locations.sto'
        self.id = 'inverse_dynamics.sto'
        self.ma = 'muscleAnalysis'
        self.so_forces = 'SO_StaticOptimization_force.sto'
        self.so_activations = 'SO_StaticOptimization_activation.sto'
        self.jra = 'Analyse_JRA_ReactionLoads_SO.sto'
        
        self.ceinms_calibration_dir = '..\calibrationOutput'
        self.ceinms_optimisation_dir = 'Optimised'
        self.ceinms_exe_dir = 'Execution'
        
        self.ceinms_muscle_forces = os.path.join(f'{self.ceinms_exe_dir}_a{self.alpha}_b{self.beta}_g{self.gamma}', 'MuscleForces.sto')
        self.ceinms_activations = os.path.join(f'{self.ceinms_exe_dir}_a{self.alpha}_b{self.beta}_g{self.gamma}', 'Activations.sto')
        self.jra_ceinms = 'Analyse_JRA_ReactionLoads_CEINMS.sto'
        
        if parentdir:
            for attr, filename in self.__dict__.items():
                # filepath = os.path.join(parentdir, filename)
                filepath = Path(parentdir) / filename
                try:
                    relpath = os.path.relpath(filepath, parentdir)
                except Exception as e:
                    breakpoint()
                

                setattr(self, attr, relpath)

    def check(self, parentdir):
        fileExist = {}
        for attr, filename in self.__dict__.items():
            filepath = os.path.join(parentdir, filename)
            
            if not os.path.exists(filepath):
                print(f'Warning: Input file {filename} not found in {parentdir}')
                fileExist[attr] = False
            else:
                fileExist[attr] = True
        
        return fileExist    

    def _to_xml(self, parentdir):
        xml_elements = []
        for attr, filename in self.__dict__.items():
            filepath = os.path.join(parentdir, filename)
            xml_elements.append(f'<{attr}>{filepath}</{attr}>')
        
        return '\n'.join(xml_elements)


if PROJECT_NAME == 'powerlifing_model' or PROJECT_NAME == 'squatting_fais':
    
    subject_list = ['Athlete_03' , 'Athlete_03_Lernagopal','Athlete_03_GPK', 'Athlete_03_GPK_MRI']

    session_list = ['25_03_31'] # '25_03_31' '22_07_06' walking 09-03-2026

    trial_list = ['Walking_02','Squat_BW_01', 'Squat_BW_02']#['Walking_02', 'Squat_BW_01','Squat_35kg_01']

    calibration_trials = ['Walking_02', 'Squat_BW_01']

    marker_weights = {'pelvis': 10.0, 'femur_r': 1.0, 'tibia_r': 1.0, 'talus_r': 1.0, 'calcn_r': 2.0, 'toes_r': 2.0, 
                      'femur_l': 1.0, 'tibia_l': 1.0, 'talus_l': 1.0, 'calcn_l': 2.0, 'toes_l': 2.0}
        
    DOFs = ['pelvis_tilt', 'pelvis_list', 'pelvis_rotation',
            'hip_flexion_l', 'hip_flexion_r',
                    'hip_adduction_l', 'hip_adduction_r',
                    'hip_rotation_l', 'hip_rotation_r',
                    'knee_angle_l', 'knee_angle_r',
                    'knee_adduction_l', 'knee_adduction_r',
                    'ankle_angle_l', 'ankle_angle_r']

    DOFs_moments = {'hip_flexion_r': 'hip_flexion_r_moment',
                    'hip_adduction_r': 'hip_adduction_r_moment',
                    'hip_rotation_r': 'hip_rotation_r_moment',
                    'knee_angle_r': 'knee_angle_r_moment',
                    'knee_adduction_r': 'knee_adduction_r_moment',
                    'ankle_angle_r': 'ankle_angle_r_moment',
                    'hip_flexion_l': 'hip_flexion_l_moment',
                    'hip_adduction_l': 'hip_adduction_l_moment',
                    'hip_rotation_l': 'hip_rotation_l_moment',
                    'knee_angle_l': 'knee_angle_l_moment',
                    'knee_adduction_l': 'knee_adduction_l_moment',
                    'ankle_angle_l': 'ankle_angle_l_moment'}


    # To match Pürzel, A. et al. (2025) Scand. J. Med. Sci. Sports 35
    Muscle_Groups = {'R Gluteus maximus':['glmax1_r','glmax2_r','glmax3_r'],
                            'R Gluteus medius':['glmed1_r','glmed2_r','glmed3_r'],
                            'R Gluteus minimus':['glmin1_r','glmin2_r','glmin3_r'], 
                            'R Adductor Magnus': ['addmagDist_r','addmagIsch_r','addmagMid_r','addmagProx_r'],
                            'R Biceps Femoris': ['bflh_r','bfsh_r'],
                            'R Semimembranosus': ['semimem_r'],
                            'R Semitendinosus': ['semiten_r'],
                            'R Rectus Femoris': ['recfem_r'],
                            'R Vasti':['vasint_r','vaslat_r','vasmed_r'],
                            'R Gastrocnemius': ['gaslat_r','gasmed_r'],
                            'R Soleus': ['soleus_r'],
                            'L Gluteus maximus':['glmax1_l','glmax2_l','glmax3_l'],
                            'L Gluteus medius':['glmed1_l','glmed2_l','glmed3_l'],
                            'L Gluteus minimus':['glmin1_l','glmin2_l','glmin3_l'],
                            'L Adductor Magnus': ['addmagDist_l','addmagIsch_l','addmagMid_l','addmagProx_l'],
                            'L Biceps Femoris': ['bflh_l','bfsh_l'],
                            'L Semimembranosus': ['semimem_l'],
                            'L Semitendinosus': ['semiten_l'],
                            'L Rectus Femoris': ['recfem_l'],
                            'L Vasti':['vasint_l','vaslat_l','vasmed_l'],
                            'L Gastrocnemius': ['gaslat_l','gasmed_l'],
                            'L Soleus': ['soleus_l']}


    JCF_Groups = {'hip': ['hip_r_on_femur_r_in_femur_r_fx', 'hip_r_on_femur_r_in_femur_r_fy', 'hip_r_on_femur_r_in_femur_r_fz'],
                'knee': ['walker_knee_r_on_tibia_r_in_tibia_r_fx', 'walker_knee_r_on_tibia_r_in_tibia_r_fy', 'walker_knee_r_on_tibia_r_in_tibia_r_fz'],
                'ankle': ['ankle_r_on_talus_r_in_talus_r_fx', 'ankle_r_on_talus_r_in_talus_r_fy', 'ankle_r_on_talus_r_in_talus_r_fz']}

    EMG_muscle_mapping = {
        # Left Leg Muscles
        'Voltage_EMG1_vast_lat_l': ['vaslat_l', 'vasmed_l'],
        'Voltage_EMG3_rect_fem_l': ['recfem_l', 'sart_l', 'tfl_l'],
        'Voltage_EMG5_bic_fem_l': ['bflh_l', 'bfsh_l', 'semimem_l', 'semiten_l'],
        'Voltage_EMG7_glut_max_l': ['glmax1_l', 'glmax2_l', 'glmax3_l'],
        'Voltage_EMG9_gast_med_l': [],
        'Voltage_EMG13_add_mag_l': [],

        # Right Leg Muscles
        'Voltage_EMG2_vast_lat_r': ['vaslat_r', 'vasmed_r'],
        'Voltage_EMG4_rect_fem_r': ['recfem_r', 'sart_r', 'tfl_r'],
        'Voltage_EMG6_bic_fem_r': ['bflh_r', 'bfsh_r', 'semimem_r', 'semiten_r'],
        'Voltage_EMG8_glut_max_r': ['glmax1_r', 'glmax2_r', 'glmax3_r'],
        'Voltage_EMG10_gast_med_r': [],
        'Voltage_EMG14_add_mag_r': []
    }

    # session 2
    EMG_muscle_mapping = {
        # Left Leg Muscles
        'EMG_Channels_EMG01_vast_lat_l': ['vaslat_l', 'vasmed_l'],
        'EMG_Channels_EMG03_rect_fem_l': ['recfem_l', 'sart_l', 'tfl_l'],
        'EMG_Channels_EMG05_bic_fem_l': ['bflh_l', 'bfsh_l', 'semimem_l', 'semiten_l'],
        'EMG_Channels_EMG07_glut_l': ['glmax1_l', 'glmax2_l', 'glmax3_l'],
        'EMG_Channels_EMG09_gast_med_l': [],

        # Right Leg Muscles
        'EMG_Channels_EMG02_vast_lat_r': ['vaslat_r', 'vasmed_r'],
        'EMG_Channels_EMG04_rect_fem_r': ['recfem_r', 'sart_r', 'tfl_r'],
        'EMG_Channels_EMG06_bic_fem_r': ['bflh_r', 'bfsh_r', 'semimem_r', 'semiten_r'],
        'EMG_Channels_EMG08_glut_r': ['glmax1_r', 'glmax2_r', 'glmax3_r'],
        'EMG_Channels_EMG10_gast_med_r': []
    }

    # running session
    if PROJECT_NAME == 'running' :
        EMG_muscle_mapping = {
            'VM': ['vasmed_r'],
            'VL': ['vaslat_r'],
            'RF': ['recfem_r', 'sart_r', 'tfl_r'],
            'GRA': ['grac_r'],
            'ADDLONG': ['addlong_r', 'addbrev_r','addmagDist_r',
                        'addmagIsch_r','addmagMid_r','addmagProx_r'],
            'SEMIMEM': ['semimem_r', 'semiten_r'],
            'BF': ['bflh_r', 'bfsh_r'],
            'GM': ['gasmed_r'],
            'GL': ['gaslat_r'],
            'MG': ['soleus_r'],
        }

    model_config = {
            'Scaled (Cateli)':        {'subject': 'Athlete_03',          'color': 'green',  'force_type': 'SO',     'line_style': '-'},
            'Scaled (Cateli) - CEINMS':        {'subject': 'Athlete_03',          'color': 'green',  'force_type': 'CEINMS',     'line_style': '--'},
            'Scaled (Lernagopal)':    {'subject': 'Athlete_03_Lernagopal','color': 'blue',   'force_type': 'SO',     'line_style': '-'},
            'Scaled (Lernagopal) - CEINMS':    {'subject': 'Athlete_03_Lernagopal','color': 'blue',   'force_type': 'CEINMS',     'line_style': '--'},
            'Scaled (GPK)':           {'subject': 'Athlete_03_GPK',      'color': 'red',    'force_type': 'SO',     'line_style': '-.'},
            'Scaled (GPK) - CEINMS': {'subject': 'Athlete_03_GPK',      'color': 'red',    'force_type': 'CEINMS', 'line_style': '--'},
            'MRI (GPK)':       {'subject': 'Athlete_03_GPK_MRI',  'color': 'purple', 'force_type': 'SO',     'line_style': '-'},
            'MRI (GPK) - CEINMS':  {'subject': 'Athlete_03_GPK_MRI',  'color': 'magenta','force_type': 'CEINMS', 'line_style': '--'},
        }


# Varaible to define which variables to plot and how to summarise them in the plots
plot = {'Groups':
                    {'SO_StaticOptimization_force': Muscle_Groups,
                    'Analyse_SO_StaticOptimization_force_ReactionLoads': JCF_Groups,
                    'SO_StaticOptimization_force_normalised': Muscle_Groups,
                    'SO_StaticOptimization_activation': Muscle_Groups,
                    'MuscleForces_inputData': Muscle_Groups,
                    'inverse_dynamics': DOFs_moments},
                    
            'Summary': 
                    {'SO_StaticOptimization_force': 'Sum', 
                    'SO_StaticOptimization_force_normalised': 'mean',
                    'SO_StaticOptimization_activation': 'mean', 
                    'Analyse_SO_StaticOptimization_force_ReactionLoads': '3dsum',
                    'MuscleForces_inputData': 'Sum',
                    'inverse_dynamics': 'None' 
                    },
                    
                }