from modules.importer import *

def database_files(base_dir):
    file_list = []
    for root, dirs, files in os.walk(base_dir):
        file_list.extend(os.path.join(root, file) for file in files if file.endswith('.txt'))
    return file_list

def load_data(path):
    if isinstance(path, list):
        x = [i[0] for i in path]
        y = [i[1] for i in path]
    else:
        with open(path, 'r') as f:
            data = f.readlines()
            data = [line.split() for line in data]
            x = [float(line[0]) for line in data]
            y = [float(line[1]) for line in data]
    return x, y

def clear_y(y_test, guassian_filter : int = 0, normalization : str = 'MinMax'):
    if guassian_filter:
        y_test = scipy.ndimage.filters.gaussian_filter1d(y_test, guassian_filter) 
    if normalization == 'MinMax':
        minim = np.min(y_test)
        maxim = np.max(y_test)
        y_test = [y - minim for y in y_test] / maxim
    elif normalization == 'Stat':
        y_test = (y_test - np.mean(y_test)) / np.std(y_test)
    return y_test

def clear_y_V(x_test, y_test, guassian_filter : bool = True, normalization : str = 'MinMax', fluo_filter_bool : bool = False):
    if fluo_filter_bool:
        #y_test = fluo_filter(x_test, y_test)  
        y_test = remove_peaks(y_test) 
    if guassian_filter:
        y_test = scipy.ndimage.filters.gaussian_filter1d(y_test, 3) 
    if normalization == 'MinMax':
        minim = np.min(y_test)
        maxim = np.max(y_test)
        y_test = [y - minim for y in y_test] / maxim
    elif normalization == 'Stat':
        y_test = (y_test - np.mean(y_test)) / np.std(y_test)
    return y_test

def fluo_filter(x, y, *args, **kwargs):
    z = np.polyfit(x, y, 3)
    f = np.poly1d(z)
    return y - f(x) * 0.7

import numpy as np
from scipy.signal import savgol_filter, medfilt

# Define a function to remove Gaussian or pseudo-Gaussian peaks from a spectrum
def remove_peaks(spectrum):
    # Smooth the spectrum using a Savitzky-Golay filter
    smoothed_spectrum = savgol_filter(spectrum, 401, 3)
    
    # Subtract the smoothed spectrum from the original spectrum
    denoised_spectrum = spectrum - smoothed_spectrum
    
    # Return the denoised spectrum
    return denoised_spectrum

def select_intervall(x_1, y_1, x_2, y_2,min_max : list = [None,None], exclusion_zone : list = [None,None]):
    if len(x_1) != len(y_1) or len(x_2) != len(y_2):
        return 0
    # find same intervall
    x_min = max(x_1[0], x_2[0])
    x_max = min(x_1[-1], x_2[-1])
    if min_max[0]  and x_min < min_max[0]:
        x_min = min_max[0]
    if min_max[1] and x_max > min_max[1]:
        x_max = min_max[1]
    i_min = next((i for i in range(len(x_1)) if x_1[i] >= x_min), 0)
    for i in range(len(x_2)):
        if x_2[i] >= x_min:
            i_min = i
            break
    i_max = next((i for i in range(len(x_1)) if x_1[i] >= x_max), 0)
    for i in range(len(x_2)):
        if x_2[i] >= x_max:
            i_max = i
            break
    # cut
    x_1 = x_1[i_min:i_max]
    y_1 = y_1[i_min:i_max]
    x_2 = x_2[i_min:i_max]
    y_2 = y_2[i_min:i_max]
    # exclusion zone
    if exclusion_zone[0] and exclusion_zone[1] :
        j_min = next((i for i in range(len(x_1)) if x_1[i] >= exclusion_zone[0]), 0)
        j_max = next((i for i in range(len(x_1)) if x_1[i] >= exclusion_zone[1]), 0) 
        x_1 = x_1[:j_min] + x_1[j_max:]
        y_1 = y_1[:j_min] + y_1[j_max:]
        x_2 = x_2[:j_min] + x_2[j_max:]
        y_2 = y_2[:j_min] + y_2[j_max:]

    return x_1, y_1, x_2, y_2

def same_x_projection(x_1, y_1, x_2, y_2, deltaspace = 2):
    min_delta_x1 = min(x_1[i+1]-x_1[i] for i in range(len(x_1)-1))
    min_delta_x2 = min(x_2[i+1]-x_2[i] for i in range(len(x_2)-1))
    min_delta_x = min(min_delta_x1, min_delta_x2)
    new_x_1 = np.arange(x_1[0], x_1[-1], min_delta_x/deltaspace)
    new_x_2 = np.arange(x_2[0], x_2[-1], min_delta_x/deltaspace)
    y_1 = np.interp(new_x_2, x_1, y_1)
    y_2 = np.interp(new_x_2, x_2, y_2)
    return y_1, y_2, new_x_1, new_x_2

def pre_elaboration(x_1_i : list, y_1_i : list, x_2_i : list, y_2_i : list, divdelta : float = 1):
    x_1, y_1, x_2, y_2 = select_intervall(x_1_i, y_1_i, x_2_i, y_2_i)
    y_1 = clear_y(y_1, guassian_filter = 1, normalization = 'Stat')
    y_2 = clear_y(y_2, guassian_filter = 1, normalization = 'Stat')
    y_1, y_2, x_1, x_2 = same_x_projection(x_1, y_1, x_2, y_2, divdelta)
    return x_1, y_1, x_2, y_2

def pre_elaboration_V(x_1_i : list, y_1_i : list, x_2_i : list, y_2_i : list, divdelta : float = 1, filter : bool = True, norm : str = 'Stat', min_max : list = [None,None], exclusion_zone : list = [None,None], fluo_filter_bool : bool = False):
    x_1, y_1, x_2, y_2 = select_intervall(x_1_i, y_1_i, x_2_i, y_2_i, min_max, exclusion_zone)
    y_1 = clear_y_V(x_1, y_1, filter, normalization = norm, fluo_filter_bool = fluo_filter_bool)
    y_2 = clear_y_V(x_2, y_2, filter, normalization = norm, fluo_filter_bool = fluo_filter_bool)
    y_1, y_2, x_1, x_2 = same_x_projection(x_1, y_1, x_2, y_2, divdelta)
    return x_1, y_1, x_2, y_2