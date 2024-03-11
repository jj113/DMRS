def dicom_to_png_dcmtk(dicom_path, image_path, selection_criteria={}, skip_existing=True):
  """Converts a dicom image to a grayscale 16-bit png image using dcmtk.

    Arguments:
        dicom_path(str): The path to the dicom file.
        image_path(str): The path where the image will be saved.
        selection_criteria (list or tuple): list or tuple of dictionaries where each dictionary describes a set of key:value selection criteria.
        skip_existing(bool): True to skip images which already exist.
    """

  if skip_existing and os.path.exists(image_path):
    return
  
  # Ensure dicom  fits the selection criteria and only has one slice
  if not (is_selected_dicom(dicom_path, selection_criteria)):
      return
  
  # Create directory for image if necessary
  create_directory_if_necessary(image_path)
  
  # Convert DICOM to PNG using dcmj2pnm (support.dcmtk.org/docs/dcmj2pnm.html)
  # from dcmtk library (dicom.offis.de/dcmtk.php.en)
  dcm_file = pydicom.dcmread(dicom_path)
  manufacturer = dcm_file.Manufacturer
  series = dcm_file.SeriesDescription
  if 'GE' in manufacturer:
    #try:
    #check_output(['dcmj2pnm', '+on2', '--use-voi-lut', '1', dicom_path, image_path])
  #except CalledProcessError:
    #print(f"{dicom_path}: No LUT found. Will use sigmoid transformation instead.")
    #Popen(['dcmj2pnm', '+on2', '--sigmoid-function', '--use-window', '1', dicom_path, image_path]).wait()
    Popen(['dcmj2pnm', '+on2', '--sigmoid-function', '--use-window', '1', dicom_path, image_path]).wait()
  elif 'C-View' in series:
    Popen(['dcmj2pnm', '+on2', '+Ww', DEFAULT_WINDOW_LEVEL, DEFAULT_WINDOW_WIDTH, dicom_path, image_path]).wait()
  else:
    Popen(['dcmj2pnm', '+on2', '--min-max-window', dicom_path, image_path]).wait()
