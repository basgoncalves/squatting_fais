import os 
import shutil

original_database = r'E:\DataFolder\Running_FAI\c3d_files'
destination_database = r'C:\Git\research_data\Projects\squatting_fais\c3dfiles'

files_of_interest = ['Squat', 'SJ', 'SLS']

target_subjetcs = [
    "009", "010", "013", "015", "018", "019", "021", "022", 
    "024", "026", "029", "030", "031", "033", "036", "038", 
    "039", "040", "041", "043", "044", "047", "048", "050", 
    "052", "054", "056", "058", "061", "064", "070", "072", 
    "073", "074", "075", "076", "077", "079"
]


for root, dirs, files in os.walk(original_database):
    for file in files:
        if file.endswith('.c3d'):
            
            # add path to txt file
            c3d_path = os.path.join(root, file)
            subject = os.path.basename(os.path.dirname(os.path.dirname(c3d_path)))
            if subject not in target_subjetcs:
                continue
            
            trial_name = os.path.basename(c3d_path).split('.')[0]
            
            is_interesting = [file_of_interest in trial_name for file_of_interest in files_of_interest]
            
            if any(is_interesting):
                true_idx = [index for index, value in enumerate(is_interesting) if value][0]
                
                destination_file = os.path.join(destination_database, subject, files_of_interest[true_idx],trial_name + '.c3d')
                
                if os.path.exists(destination_file):
                   continue
            
                try:
                    os.makedirs(os.path.dirname(destination_file))
                except FileExistsError:
                    pass
                shutil.copyfile(c3d_path, destination_file)
                print(f'Copied {c3d_path} to {destination_file}')
                
print('Done')
# # # END
            