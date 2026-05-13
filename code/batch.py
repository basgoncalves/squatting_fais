import os
import utils
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import ceinms
import openSim
import pandas as pd
import shutil
import opensim as osim
import settings


subjects = os.listdir(utils.SIMULATIONS_DIR)

for subject in subjects:
    trials = os.listdir(os.path.join(utils.SIMULATIONS_DIR, subject))
    for trial in trials:
        trial = 'SJ_pre4'
        print(f'  {trial}')
        trialPath = os.path.join(utils.SIMULATIONS_DIR, subject, trial)
        if not os.path.isdir(trialPath):
            continue

        analysis = utils.Analyse(trialPath)
        analysis._reset_settings_xml()
           
        print("Main inputs:")
        print(f"Model file: {os.path.join(analysis.path, analysis.model_dir)}")
        print(f"time range: {analysis.time_range}")
        print(f"Body mass: {analysis.body_mass} kg")
        print(f"Body mass grf: {analysis.get_body_mass_from_grf(update=True)} kg")
        print(f"Body mass osim: {analysis.get_body_mass()} kg")

        # open settings.xml in the editor
        settings_xml_path = os.path.join(trialPath, 'trial_settings.xml')
        os.startfile(settings_xml_path)

        analysis.export_c3d()
        analysis.run_ik()
        analysis.run_id()
        analysis.run_so()
        exit()


