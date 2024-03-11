# DMRS

## Preprocessing
Python version 3.11.5

Install the requirement dependencies on requirements.txt
```
pip3 install -r requirements.txt
```
Specifics --
```
torch==2.2.1
torchaudio==2.0.2+rocm5.4.2
torchvision==0.17.1
tqdm==4.66.2
scikit-image==0.22.0
scikit-learn==1.4.1.post1
scipy==1.12.0
pandas==2.2.1
pillow==10.2.0
matplotlib==3.8.3
lifelines==0.28.0
imageio==2.34.0
numpy==1.26.4
```

Convert the DICOM files into 16-bit PNG directly using dcmtk function in python
```
python png/dcm_to_png.py /path/to/dicom/file.dcm /path/to/save/image.png
```

## Reproducing DMRS 
To validate DMRS you would need two datasets prepared:
 1. a long version with longitudinal mammograms time stamps
 2. a wide version with time-to-event and (optional) risk factors

For 1, see long_data/demo/sample_long.csv for an example. All the columns are required.
 * group_id: ID on the woman's level (1 unique ID per woman regardless of longitudinal observations)
 * since.bl.yr: number of years since the very first mammogram
 * visit_id: ID on the visit level (1 unique ID per longitudinal observation)
 * exam_id: ID for each of the 4 views of the mammogram
 * laterality: R or L for right and left side
 * view: MLO or CC only
 * file_path: path for the png16 for each view
 * split_group: test only
 * event: 0 = breast cancer free during the entire follow-up; 1 = breast cancer occured within follow-up

We note that the long version is an extension of OncoNet. 
Feature extraction is done for each of the mammograms separately based on ResNet-18:
```
python scripts/reformat.py  --model_name SSL_mod --img_encoder_snapshot snapshots/SSL_mod.p  --batch_size 1 --dataset csv_mammo_risk_all_full_future --img_mean 7047.99 --img_size 1664 2048 --img_std 12005.5 --metadata_path demo/sample_long.csv --test --prediction_save_path demo/output.csv
```

For 2, see wide_data/sample_wide.csv for an example. All the columns are required.
 * group_id: must correspond to the group_id in long version
 * event: must correspond to the event variable in long version
 * time: time of censoring or breast cancer event

To perform SSL and estimate the AUC:
```
Rscript SSL.R
```

In addition to the set of raw codes, a docker version is coming... (in process of building)


<!-- [1] A deep learning mammography-based model for improved breast cancer risk prediction. Radiology 292.1 (2019): 60-66. -->



