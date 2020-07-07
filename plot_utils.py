'''
    Python Routines for COsmology and Data I/O
    PyRCODIO Pandas Version
    Edoardo Carlesi 2020
    ecarlesi83@gmail.com

    plot_utils.py = functions and routines used to plot
'''

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as colors
import seaborn as sns
import pandas as pd
import numpy as np
import math
from pygadgetreader import *
from matplotlib import rc


'''
    Find the particles belonging to a slab around a given point in space.
    Slab size, thickness and so on need to be specified.
'''
def find_slab(file_name=None, center=None, side=None, thick=None, velocity=False, rand_seed=69,
        reduction_factor=1.0, z_axis=2, part_type=1, units='kpc', n_files=1):

    # Set some parameters
    kpcThresh = 1.e+4
    kpc2Mpc = 1.e-3

    minima = np.zeros((3))
    maxima = np.zeros((3))

    # TODO: fix for more files (n_files > 1 needs to be implemented)
    if n_files > 1:
        print('Multiple files are not supported yet.')
        return -1       

    # Do we want to read in velocity data as well? Or positions only?
    if velocity == True:
        print('Reading velocity and position particle info...')
        particles = readsnap(file_name, 'pos', part_type)
        velocities = readsnap(file_name, 'vel', part_type)
    
        # Concatenate the columns 
        full_data = np.concatenate((particles, velocities), axis=1)
        cols = ['X', 'Y', 'Z', 'Vx', 'Vy', 'Vz']

    else:
        print('Reading position particle info...')
        particles = readsnap(file_name, 'pos', part_type)
        full_data = particles
        cols = ['X', 'Y', 'Z']

    # Read the snapshot
    n_part = len(full_data)

    print('Found ', n_part, ' particles in total.')
    part_df = pd.DataFrame(data=full_data, columns=cols)

    # Select the two axes for the 2D projection
    ax0 = (z_axis + 1) % 3
    ax1 = (z_axis + 2) % 3
    ax2 = z_axis

    # Column names
    col0 = cols[ax0]
    col1 = cols[ax1]
    col2 = cols[ax2]

    # Sanity check on the units
    half_n = int(n_part * 0.5)
    sum_coord = particles[half_n][0] + particles[half_n][1] + particles[half_n][2]
    
    # Make sure the units are consistent
    if sum_coord < kpcThresh:
        side = side * kpc2Mpc
        center = center * ([kpc2Mpc] *3) 
        thick = thick * kpc2Mpc

    # Set the minima and maxima for the particles to be used in the plot
    minima[ax0] = center[ax0] - side * 0.5
    minima[ax1] = center[ax1] - side * 0.5
    minima[ax2] = center[ax2] - thick * 0.5

    maxima[ax0] = center[ax0] + side * 0.5
    maxima[ax1] = center[ax1] + side * 0.5
    maxima[ax2] = center[ax2] + thick * 0.5

    # Find the particles in the slab
    condition_x = (part_df[col0] > minima[ax0]) & (part_df[col0] < maxima[ax0])
    condition_y = (part_df[col1] > minima[ax1]) & (part_df[col1] < maxima[ax1])
    condition_z = (part_df[col2] > minima[ax2]) & (part_df[col2] < maxima[ax2])
    part_select = part_df[(condition_x) & (condition_y) & (condition_z)]

    print('Found: ', len(part_select), ' particles in the slab')

    # Now select a random subsample of the full particle list
    if reduction_factor < 1.0:
        part_select = part_select.sample(frac=reduction_factor, random_state=rand_seed)

        print('The number of particles to be used has been reduced to: ', len(part_select))

    # Return the selected particles' properties in a dataframe
    return part_select


'''
    This function plots the simple mass density starting from a particle distribution.
    The plot is a 2D projection.
'''
def plot_density(data=None, axes_plot=None, file_name=None, legend=False, show_plot=False, grid_size=100, margin=0.5, data_augment=False, fig_size=10, velocity=False, vel=None):
    print('Plotting density slices...')

    if (velocity == False) and (vel != None):
        print('Velocity is set to false but vel= is different than None! Seting vel to None...')
        vel = None

    # Plot properties
    colorscale = 'inferno'
    #colorscale = 'gray'
    #colorscale = 'hot'
    #colorscale = 'gist_gray'
    #colorscale = 'bwr'
    ax0 = axes_plot[0]
    ax1 = axes_plot[1]
    coord = ['X', 'Y', 'Z']
    axis_label = ['SGX', 'SGY', 'SGZ']

    plt.figure(figsize=(fig_size, fig_size))

    # If we are going to use the images with CNNs then by default legend is set to False
    if legend == True:
        axis_size = fig_size * 2
        plt.rc({'text.usetex': True})
        plt.rc('axes',  labelsize=axis_size)
        plt.rc('xtick', labelsize=axis_size)
        plt.rc('ytick', labelsize=axis_size)
        plt.xlabel(r'$h^{-1}$Mpc')
        plt.ylabel(r'$h^{-1}$Mpc')
        #plt.xlabel(axis_label[ax0]+' '+axis_units)
        #plt.ylabel(axis_label[ax1]+' '+axis_units)

        file_out = file_name + 'density_' + axis_label[ax0] + axis_label[ax1]
    else:
        axis_size = 0
        file_out = file_name + 'rho_no_labels_' + axis_label[ax0] + axis_label[ax1]

    # Find the maxima and minima of the plot, reduce by a small margin to remove border imperfections
    x_min = data[coord[ax0]].min() + margin
    y_min = data[coord[ax1]].min() + margin
    x_max = data[coord[ax0]].max() - margin
    y_max = data[coord[ax1]].max() - margin

    # Set the axis maxima and minima
    plt.axis([x_min, x_max, y_min, y_max])

    # Unset the ticks and set margins to zero if legend is true
    if legend == False:
        plt.margins(0.0) 
        plt.xticks([])
        plt.yticks([])
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    else:
        plt.tight_layout()

    # Do the plot using hexagonal bins
    plt.hexbin(data[coord[ax0]], data[coord[ax1]], gridsize=grid_size, cmap=colorscale, bins='log')
    
    # Actually show the plot, otherwise we will just save it to a .png file
    if show_plot == True:
        plt.show()
    
    # Save the file
    if legend == False:
        plt.tight_layout()

    plt.savefig(file_out + '.png')
    print('File saved to: ', file_out + '.png')

    # Check if we want to plot velocities as well
    if velocity == True:
        if vel == None:
            print('Error: vel keyword is not set and velocity is set to True.')
            return 0
        else:
            # Check if vel is a list, otherwise make it a list
            if isinstance(vel, list) == False:
                vel = [vel]
    
            # Loop on velocity projections
            for vx in vel:
                file_v_out = file_name + 'V_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_' + vx
                plt.hexbin(data[coord[ax0]], data[coord[ax1]], C=data[vx], gridsize=grid_size, cmap=colorscale)
                plt.savefig(file_v_out + '.png')
                print('File saved to: ', file_v_out + '.png')

    # Do some transformations on the data to increase the number of samples
    if data_augment == True:
        print('Data augmentation is set to True, printing additional images...')

        file_out = file_name + 'rho_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_augment0'
        plt.axis([x_max, x_min, y_min, y_max])
        plt.hexbin(data[coord[ax0]], data[coord[ax1]], gridsize=grid_size, cmap=colorscale, bins='log')
        plt.savefig(file_out + '.png')
        #print('File saved to: ', file_out + '.png')

        file_out = file_name + 'rho_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_augment1'
        plt.axis([x_min, x_max, y_max, y_min])
        plt.hexbin(data[coord[ax0]], data[coord[ax1]], gridsize=grid_size, cmap=colorscale, bins='log')
        plt.savefig(file_out + '.png')
        #print('File saved to: ', file_out + '.png')

        file_out = file_name + 'rho_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_augment2'
        plt.axis([x_max, x_min, y_max, y_min])
        plt.hexbin(data[coord[ax0]], data[coord[ax1]], gridsize=grid_size, cmap=colorscale, bins='log')
        plt.savefig(file_out + '.png')
        #print('File saved to: ', file_out + '.png')

        # Print also "augmented" velocity maps in case
        if velocity == True:
            for vx in vel:
                plt.axis([x_max, x_min, y_min, y_max])
                file_v_out = file_name + 'V_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_' + vx + '_augment0'
                plt.hexbin(data[coord[ax0]], data[coord[ax1]], C=data[vx], gridsize=grid_size, cmap=colorscale)
                plt.savefig(file_v_out + '.png')

                plt.axis([x_min, x_max, y_max, y_min])
                file_v_out = file_name + 'V_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_' + vx + '_augment1'
                plt.hexbin(data[coord[ax0]], data[coord[ax1]], C=data[vx], gridsize=grid_size, cmap=colorscale)
                plt.savefig(file_v_out + '.png')

                plt.axis([x_max, x_min, y_max, y_min])
                file_v_out = file_name + 'V_no_labels_' + axis_label[ax0] + axis_label[ax1] + '_' + vx + '_augment2'
                plt.hexbin(data[coord[ax0]], data[coord[ax1]], C=data[vx], gridsize=grid_size, cmap=colorscale)
                plt.savefig(file_v_out + '.png')


'''
    Plot the MAH of a single halo
'''
def plot_mass_accretion(time, mah, f_out):
    size_x = 20
    size_y = 20
    lnw = 1.0
    col = 'b'

    x_min = np.min(time); x_max = np.max(time)
    y_min = np.min(mah); y_max = np.max(mah)

    plt.yscale('log')
    plt.axis([x_min, x_max, y_min, y_max])

    plt.plot(time, mah, linewidth=lnw, color=col)

    # Save the figure and clean plt
    plt.savefig(f_out)
    plt.clf()
    plt.cla()
    plt.close()


'''
    Plot the MAH for an ensamble of halos
'''
def plot_mass_accretions(time, mahs, f_out, percentiles=[25, 50, 75], size=10, scale='lin'):

    # Plot properties
    (fig, axs) = plt.subplots(ncols=1, nrows=1, figsize=(size, size))
    lnw = 1.0
    col = 'b'
    plt.yscale('log')
    plt.rc({'text.usetex': True})
    plt.xlabel('GYr')
    plt.ylabel('M')

    # Set plot max and min 
    x_min = np.min(time); x_max = np.max(time)
    y_min = np.min(mahs); y_max = np.max(mahs)

    # Set axes
    axs.axis([x_min, x_max, y_min, y_max])

    # Change x axis scale
    if scale == 'log':
        axs.set_xscale('log')

    # TODO: what is this??
    if y_min < 1.e+5:
        y_min = y_max / 200.

    # Find number of steps and plots
    n_steps = len(time)
    n_plots = len(mahs[:,0])

    # Initialize empty list
    all_mahs = [[] for i in range(0, n_steps)]

    # Initialize all_mah list
    for istep in range(0, n_steps):
        for iplot in range(0, n_plots):
            this_mahs = mahs[iplot, istep]
            all_mahs[istep].append(this_mahs)

    # Initialize some empty lists
    med_mah = [[] for i in range(0, n_steps)];
    min_mah = [[] for i in range(0, n_steps)];
    max_mah = [[] for i in range(0, n_steps)];

    # For each step of the MAH find the percentiles (min, med, max) corresponding to that mass bin
    for istep in range(0, n_steps):
        min_mah[istep] = np.percentile(all_mahs[istep], percentile[0])
        med_mah[istep] = np.percentile(all_mahs[istep], percentile[1])
        max_mah[istep] = np.percentile(all_mahs[istep], percentile[2])

    # Plot the median with a solid line + the gray shaded area
    axs.plot(time, med_mah, color='black')
    axs.fill_between(time, min_mah, max_mah, facecolor='grey')

    # Save the figure and clean plt
    plt.tight_layout()
    plt.savefig(f_out)
    plt.clf()
    plt.cla()
