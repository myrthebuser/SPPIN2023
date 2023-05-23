#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  9 12:16:30 2023

@author: myrthebuser
"""

import sys
sys.path.append('/Users/myrthebuser/opt/anaconda3/lib/python3.8/site-packages')
import dicom2nifti
import glob
import os
dicom2nifti.settings.disable_validate_slice_increment()

path = '/Volumes/pmc_wijnen/Buser/3. SPPIN/Data/SPPIN_dataset/Reformatted/'  # PAS AAN
filenames=glob.glob(path+'*/*/mobiview_t_b100')


for filename in filenames[100:]:
    try:
        pt=filename.split('/')[8]
        date=filename.split('/')[9]
        new_name=os.path.join('/Volumes/pmc_wijnen/Buser/3. SPPIN/Data/SPPIN_dataset/Final/',pt,date,'DWI_b100')
        if not os.path.exists(os.path.join('/Volumes/pmc_wijnen/Buser/3. SPPIN/Data/SPPIN_dataset/Final/',pt,date)):
            os.makedirs(os.path.join('/Volumes/pmc_wijnen/Buser/3. SPPIN/Data/SPPIN_dataset/Final/',pt,date))
        dicom2nifti.dicom_series_to_nifti(filename, new_name, reorient_nifti=True)
    except:
        continue
