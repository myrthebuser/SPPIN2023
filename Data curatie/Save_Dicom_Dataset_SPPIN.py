#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 16 09:32:15 2021

@author: myrthebuser
"""

""" 
Script om ongesorteerde dicom data te sorteren op patient, sequentie en scanmoment.
Los gebasseerd op https://towardsdatascience.com/a-python-script-to-sort-dicom-files-f1623a7f40b8

"""

# Importeer relevante packaages
import os  # Path manamgment
import pydicom  # Dicom specifiek package
from tqdm import tqdm
import glob


def clean_text(string):
    # clean and standardize text descriptions, which makes searching files easier
    forbidden_symbols = ["*", ".", ",", "\"", "\\", "/", "|", "[", "]", ":", ";", " "]
    for symbol in forbidden_symbols:
        string = string.replace(symbol, "_")  # replace everything with an underscore
    return string.lower()


path = '/Volumes/pmc_wijnen/Buser/3. SPPIN/Data/SPPIN_dataset/Original/Anonymous_Male_2017_2376216'  # PAS AAN
dst = "/Volumes/pmc_wijnen/Buser/3. SPPIN/Data/SPPIN_dataset/WIP/PT_86"  # PAS AAN

# Loop over je bestandsnamen heen.
filenames = glob.glob(path + '/*NEUROBLA')
filenames = filenames + glob.glob(path + '/*ABDOMEN')

count = 86  # Pas aan

for scan in tqdm(filenames[:]):  # Loopt over je subfolders heen.
    scan = scan.split('/')[-1]
    patientName = 'PT_' + str(count)  # Pas aan als je een andere naam wil.
    # patientName='PT_'
    print('reading file list...')

    src = os.path.join(path, scan)
    unsortedList = []
    for root, dirs, files in os.walk(src):
        for file in files:
            # print(file)
            if ".dcm" in file:  # exclude non-dicoms, good for messy folders
                unsortedList.append(os.path.join(root, file))

    print('%s files found.' % len(unsortedList))

    for dicom_loc in unsortedList:
        # read the file
        ds = pydicom.read_file(dicom_loc, force=True)

        # get patient, study, and series information
        patientID = clean_text(ds.get("PatientID", "NA"))
        studyDate = clean_text(ds.get("StudyDate", "NA"))
        seriesDescription = clean_text(ds.get("SeriesDescription", "NA"))

        # generate new, standardized file name
        modality = ds.get("Modality", "NA")
        studyInstanceUID = ds.get("StudyInstanceUID", "NA")
        seriesInstanceUID = ds.get("SeriesInstanceUID", "NA")
        instanceNumber = str(ds.get("InstanceNumber", "0"))
        fileName = modality + "." + seriesInstanceUID + "." + instanceNumber + ".dcm"

        # uncompress files (using the gdcm package)
        try:
            ds.decompress()
        except:
            print('an instance in file %s - %s - %s " could not be decompressed. exiting.' % (
            patientID, studyDate, seriesDescription))
        # save files to a 4-tier nested folder structure
        if not os.path.exists(os.path.join(dst, patientName)):
            os.makedirs(os.path.join(dst, patientName))

        if not os.path.exists(os.path.join(dst, patientName, studyDate)):
            os.makedirs(os.path.join(dst, patientName, studyDate))

        if not os.path.exists(os.path.join(dst, patientName, studyDate, seriesDescription)):
            os.makedirs(os.path.join(dst, patientName, studyDate, seriesDescription))
            print('Saving out file: %s - %s - %s.' % (patientName, studyDate, seriesDescription))
        save_path = os.path.join(dst, patientName, studyDate, seriesDescription)
        ds.save_as(os.path.join(save_path, fileName))

        # Het kan handig zijn om wat informatie over je patienten op te slaan in de mappen, maar dit is geen essentiele stap.
        # text= open(save_path+"/patientID.txt","w+")
        # text.write('PatientID: '+str(patientID))
        # text.write('Original name:'+str(scan))
        # text.close
        # count=count+1 #Nummer door
import beepy

beepy.beep(3)
print('Koffiepauze is over, je dataset is klaar.')
