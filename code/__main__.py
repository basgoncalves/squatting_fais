import os
from xml.etree import ElementTree as ET
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import utils
import openSim
import ceinms
import exportC3D

###############################################################################################
# Check settings.py before running this script
import settings
###############################################################################################

class Execute:
    ''' Logics for which analyses to execute '''
    def __init__(self):
        
        self.reset_settings_xml = False
        self.replace = True

        self.INCREASE_MUSCLE_FORCE = False
        self.SCALE_FACTOR = 3

        self.exportC3D = False

        self.IK = False
        self.ID = False
        self.MA = False
        self.MOMENT_ARMS = False
        self.SO = False
        self.JRA = False
        
        self.EMG_NORMALISE = False
        self.SCALE_EMG = False
        self.EMG_SCALE_FACTOR = 0.7
        
        self.CREATE_CEINMS_FILES = False
        self.CREATE_CEINMS_MODEL = False
        
        self.CEINMS_CALIBRATION = True
        self.CEINMS_CALIBRATION_PLOTS = False
        
        self.CEINMS_OPTIMISATION = False
        self.CEINMS_EXE = False
        self.CEINMS_EXE_LOOP = False
        
        self.JRA_CEINMS = False
        
        self.CREATE_PLOTS = False
        
        self.PLOT_EMG = False
          
        self.push_trial_to_git = False
        self.push_subject_to_git = False

    def update(self):
        ''' 
        Simple gui to quicly edit the Execute class attributes. Not intended for production use, just a quick way to edit settings without going into the code. 
        '''
        import tkinter as tk
        from tkinter import ttk
    
        exe = self
        root = tk.Tk()
        root.title("Execute Settings")
    
        bool_vars = {}
        num_vars = {}
    
        frame = ttk.Frame(root, padding=10)
        frame.grid(sticky='nsew')
    
        row = 0
        for attr, val in exe.__dict__.items():
            if isinstance(val, bool):
                var = tk.BooleanVar(value=val)
                ttk.Checkbutton(frame, text=attr, variable=var).grid(row=row, column=0, sticky='w')
                bool_vars[attr] = var
                row += 1
            elif isinstance(val, (int, float)):
                ttk.Label(frame, text=attr).grid(row=row, column=0, sticky='w')
                var = tk.StringVar(value=str(val))
                ttk.Entry(frame, textvariable=var, width=8).grid(row=row, column=1, sticky='w')
                num_vars[attr] = (var, type(val))
                row += 1
    
        def apply():
            for attr, var in bool_vars.items():
                setattr(exe, attr, var.get())
            for attr, (var, t) in num_vars.items():
                try:
                    setattr(exe, attr, t(var.get()))
                except ValueError:
                    pass
        
            import re
            script_path = os.path.abspath(__file__)
            with open(script_path, 'r') as f:
                source = f.read()
        
            for attr, val in exe.__dict__.items():
                if isinstance(val, bool):
                    source = re.sub(
                        rf'(self\.{re.escape(attr)}\s*=\s*)(True|False)',
                        rf'\g<1>{val}',
                        source
                    )
                elif isinstance(val, (int, float)):
                    source = re.sub(
                        rf'(self\.{re.escape(attr)}\s*=\s*)[^\n]+',
                        rf'\g<1>{val}',
                        source
                    )
        
            with open(script_path, 'w') as f:
                f.write(source)
        
            root.destroy()
    
        def cancel():
            root.destroy()
    
        btn_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        btn_frame.grid(sticky='ew')
        ttk.Button(btn_frame, text="Apply", command=apply).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=cancel).grid(row=0, column=1, padx=4)
    
        root.mainloop()
        return exe
        
def run_all_analysis_steps(analysis: utils.Analyse, execute: Execute):

    analysis._update_model()

    if execute.reset_settings_xml:
        analysis._reset_settings_xml()

    # Export c3d file
    if execute.exportC3D:
        subject_without_zero = analysis.subject.replace('0', '')
        exportC3D.export_markers(analysis.c3d,
                                strings_to_remove = ['Bar:', f'{subject_without_zero}:'])
        exportC3D.export_grf(analysis.c3d)
        exportC3D.export_emg(analysis.c3d)

    # Increase muscle forces
    if execute.INCREASE_MUSCLE_FORCE:
        analysis.increase_muscle_force(factor=execute.SCALE_FACTOR)

    # Run IK
    if execute.IK:
        analysis.run_ik()

    # Run ID
    if execute.ID: 
        analysis.run_id()

    # Run muscle analysis
    if execute.MA: 
        analysis.run_ma()

    # Check moment arms
    if execute.MOMENT_ARMS:
        analysis.check_moment_arms()
        analysis.adjust_moment_arms()

    # Run Static Optimization
    if execute.SO:
        if not analysis.model_dir.__contains__('_increased_3.00.osim'):
            new_model_name = analysis.model_name.replace('.osim', '_increased_3.00.osim')
            analysis.update_model(new_model_name)
        analysis.run_so()

    # Run Joint Reaction Analysis
    if execute.JRA:
        analysis.run_jra()
        
    # Create CEINMS setup files
    if execute.CREATE_CEINMS_FILES:

        if analysis.model_dir.__contains__('_increased_3.00.osim'):
            new_model_name = analysis.model_name.replace('_increased_3.00.osim', f'.osim')
            analysis.update_model(new_model_name)

        analysis.create_ceinms_input_data()
        
        analysis.create_ceinms_calibration_cfg(calibration_trial_names=settings.calibration_trials)

        analysis.create_ceinms_calibration_setup()

        analysis.create_excitation_generator()

        analysis.create_ceinms_exe_cfg()

        analysis.create_ceinms_exe_setup()
                
    # CEINMS calibration and optimization
    if execute.CEINMS_CALIBRATION and analysis.trial in settings.calibration_trials[0:1]:
        
        if execute.CREATE_CEINMS_MODEL:
            analysis.create_ceinms_model()
        
        try:        
            analysis.run_ceinms_calibration()
        
        except Exception as e:
            print(f"Error during CEINMS calibration: {e}")
            utils.print_to_log(f'Error during CEINMS calibration: {e}')

    # CEINMS optimisation
    if execute.CEINMS_OPTIMISATION:
        try:
            analysis.run_ceinms_optimise()
        except Exception as e:
            utils.print_to_log(f'Error during CEINMS optimisation: {e}')

    if execute.CEINMS_EXE:
        try:
           analysis.run_ceinms_exe()
        except Exception as e:
            utils.print_to_log(f'Error during CEINMS executable run: {e}')

        # Run Joint Reaction Analysis for CEINMS
    
    if execute.CEINMS_EXE_LOOP:
        analysis.run_ceinms_exe_loop()
    
    # Run Joint Reaction Analysis with CEINMS muscle forces
    if execute.JRA_CEINMS:
        analysis.run_jra_ceinms()
    
    # summary plot
    if execute.CREATE_PLOTS:
        analysis.plot_summary()

    # print to log
    utils.print_to_log(f'Completed analysis for: {analysis.path} \n {"-"*50} \n')

def _parallell_worker(trial, subject, session, execute: Execute):
    """Top-level function required for multiprocessing pickling."""
    import utils, os
    trialPath = os.path.join(utils.SIMULATIONS_DIR, subject, session, trial)
    analysis = utils.Analyse(trialPath=trialPath)

    # template_subject = '_'.join(subject.split('_')[0:2])
    # analysis.copy_input_files(src_subject=template_subject, replace=False)

    analysis.update_trial_attribute('replace', execute.replace)

    utils.print_to_log(f'Running analysis for: {trialPath}')
    try:
        run_all_analysis_steps(analysis, execute=execute)
        utils.print_to_log(f'Analysis completed for: {trialPath}')
        return trial, None
    except Exception as e:
        utils.print_to_log(f'Error during analysis for {trialPath}: {e}')
        return trial, str(e)

def run_parallel_analysis(tasks, execute: Execute):

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_parallell_worker, trial, subject, session, execute): (subject, session, trial)
            for trial, subject, session in tasks
        }
        for future in as_completed(futures):
            subject, session, trial = futures[future]
            try:
                _, error = future.result()
                if error:
                    print(f'[{subject}/{session}/{trial}] Failed: {error}')
                else:
                    print(f'[{subject}/{session}/{trial}] Completed.')
            except Exception as e:
                print(f'[{subject}/{session}/{trial}] Worker crashed: {e}')
    
def print_main_start_settings():
    utils.print_to_log("\n \n =============== \n")
    utils.print_to_log("Starting analysis with the following settings:")
    settings_to_print = {
        'Subjects': settings.subject_list,
        'Sessions': settings.session_list,
        'Trials': settings.trial_list,
        'Execute Settings': Execute().__dict__
    }
    for key, value in settings_to_print.items():
        utils.print_to_log(f"{key}: {value}")
    utils.print_to_log("Check settings.py for more details on the settings.")
    utils.print_to_log("--------------------------------------------------")

class GUI:
    ''' Logics for GUI '''
    def __init__(self):
        pass

    def select_subjects_to_analyse(self):
        '''
        Walk through simulations and find all subjects and sessions and trials.
        Presents 3 checkbox columns (subjects, sessions, unique trial names).
        Returns (subjects, sessions, trials) lists of selected items.
        '''
        import tkinter as tk
        from tkinter import ttk

        sim_dir = utils.SIMULATIONS_DIR

        # Build tree: subject -> session -> [trials]
        all_subjects = sorted([
            d for d in os.listdir(sim_dir)
            if os.path.isdir(os.path.join(sim_dir, d))
        ])
        tree = {}
        for subj in all_subjects:
            subj_path = os.path.join(sim_dir, subj)
            tree[subj] = {}
            for sess in sorted(os.listdir(subj_path)):
                sess_path = os.path.join(subj_path, sess)
                if os.path.isdir(sess_path):
                    tree[subj][sess] = sorted([
                        d for d in os.listdir(sess_path)
                        if os.path.isdir(os.path.join(sess_path, d))
                    ])

        all_sessions = sorted(set(s for subj in tree.values() for s in subj))
        all_trials   = sorted(set(t for subj in tree.values() for sess in subj.values() for t in sess))

        # Only unique trials (Ignore case)
        unique_trials = {}
        for trial in all_trials:
            lower_trial = trial.lower()
            if lower_trial not in unique_trials:
                unique_trials[lower_trial] = trial
        all_trials = sorted(unique_trials.values())

        result = {'subjects': [], 'sessions': [], 'trials': []}

        root = tk.Tk()
        root.withdraw()
        root.title("Select Subjects / Sessions / Trials")

        def _scrollable_checklist(parent, label, items, preselected):
            frame = ttk.LabelFrame(parent, text=label, padding=5)
            canvas = tk.Canvas(frame, width=200, highlightthickness=0)
            sb = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
            canvas.configure(yscrollcommand=sb.set)
            inner = ttk.Frame(canvas)
            inner_id = canvas.create_window((0, 0), window=inner, anchor='nw')

            vars_ = {}
            for item in items:
                v = tk.BooleanVar(value=(item in preselected))
                ttk.Checkbutton(inner, text=item, variable=v).pack(anchor='w')
                vars_[item] = v

            def _on_configure(e):
                canvas.configure(scrollregion=canvas.bbox('all'))
                canvas.itemconfig(inner_id, width=canvas.winfo_width())

            inner.bind('<Configure>', _on_configure)
            canvas.pack(side='left', fill='both', expand=True)
            sb.pack(side='right', fill='y')
            return frame, vars_

        main = ttk.Frame(root, padding=10)
        main.grid(row=0, column=0, sticky='nsew')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        subj_frame,  subj_vars  = _scrollable_checklist(main, 'Subjects', all_subjects, settings.subject_list)
        sess_frame,  sess_vars  = _scrollable_checklist(main, 'Sessions', all_sessions, settings.session_list)
        trial_frame, trial_vars = _scrollable_checklist(main, 'Trials',   all_trials,   settings.trial_list)

        subj_frame.grid( row=0, column=0, padx=5, sticky='nsew')
        sess_frame.grid( row=0, column=1, padx=5, sticky='nsew')
        trial_frame.grid(row=0, column=2, padx=5, sticky='nsew')
        for col in range(3):
            main.columnconfigure(col, weight=1)
        main.rowconfigure(0, weight=1)

        def apply():
            result['subjects'] = [k for k, v in subj_vars.items()  if v.get()]
            result['sessions'] = [k for k, v in sess_vars.items()  if v.get()]
            result['trials']   = [k for k, v in trial_vars.items() if v.get()]
            root.destroy()

        def cancel():
            root.destroy()
            print("Aborting processing. User cancelled the selection.")
            raise SystemExit(0)

        btn_frame = ttk.Frame(root, padding=(10, 0, 10, 10))
        btn_frame.grid(row=1, column=0, sticky='ew')
        ttk.Button(btn_frame, text='Apply',  command=apply).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text='Cancel', command=cancel).grid(row=0, column=1, padx=4)

        root.protocol("WM_DELETE_WINDOW", cancel)
        root.update_idletasks()
        root.minsize(640, 400)
        x = root.winfo_pointerx() - root.winfo_reqwidth() // 2
        y = root.winfo_pointery() - root.winfo_reqheight() // 2
        root.geometry(f'+{x}+{y}')
        root.deiconify()
        root.mainloop()

        return result['subjects'], result['sessions'], result['trials']

    def edit_xml_settings(self, xml_path):
        '''
        Simple GUI to edit XML settings files. Not intended for production use, just a quick way to edit settings without going into the code.
        '''
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # create 

if __name__ == "__main__":

    mode = 'sequential' # 'parallel' or 'sequential'

    execute = Execute().update()
    subjects, sessions, trials = GUI().select_subjects_to_analyse()

    utils.print_to_log("Starting analysis...")
    start_time = time.time()

    print(f'Check settings in {utils.__file__}')
    time.sleep(1)

    # Build all (subject, session, trial) combinations
    all_tasks = [
        (trial, subject, session)
        for subject in subjects
        for session in sessions
        for trial in trials
    ]

    print_main_start_settings()

    if mode == 'parallel':
        run_parallel_analysis(all_tasks, execute)

    elif mode == 'sequential':

        for trial, subject, session in all_tasks:

            trialPath = os.path.join(utils.SIMULATIONS_DIR, subject, session, trial)
            analysis = utils.Analyse(trialPath=trialPath)

            utils.print_to_log(f'Running analysis for: {trialPath}')
            analysis.update_trial_attribute('replace', execute.replace)

            try:
                run_all_analysis_steps(analysis, execute=execute)

            except Exception as e:
                utils.print_to_log(f'Error during analysis for {trialPath}: {e}')


    # If enabled, push results to git after processing each trial
    if execute.push_subject_to_git:
        for subject in settings.subject_list:
            last_trial_path = os.path.join(utils.SIMULATIONS_DIR, subject, settings.session_list[-1], settings.trial_list[-1])
            analysis = utils.Analyse(trialPath=last_trial_path)
            analysis.push_subject_results_to_git()

    end_time = time.time()
    elapsed_time = end_time - start_time
    utils.print_to_log(f"Total analysis time: {elapsed_time:.2f} seconds \n \n")

