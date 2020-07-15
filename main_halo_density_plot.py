'''
    Python Routines for COsmology and Data I/O
    PyRCODIO Pandas Version
    Edoardo Carlesi 2020
    ecarlesi83@gmail.com

    main_halo_density_plot.py: produce a large number of plots centered around individual objects (halos, clusters...)
'''

import read_files as rf
import halo_utils as hu
import plot_utils as pu
import config as cfg
import pickle as pkl
import pandas as pd
import tools as t
import os

# Local data path
data_path = '/home/edoardo/CLUES/PyRCODIO/data/'

# Full dataset
#base_path = '/media/edoardo/data1/DATA/'
base_path = '/media/edoardo/Elements/CLUES/DATA/2048/'
snap_path = 'snapshot_054'

mpc2kpc = 1.e+3

# Plot properties
side_size = 3.0 * mpc2kpc
thickness = 1.5 * mpc2kpc
n_files = 1
frac = 1.00
units = 'kpc'
part_types = [4]
grid_size = 800
rand_seed = 1
fig_size = 4
version = 'fig4size800side3.0thick1.5'
show_plot = False
velocity = False
augment = False
shift = False
legend = False
vel_components = ['Vx', 'Vy', 'Vz']

n_min_part = 1000

# Configure the LG model and subpaths
code_run = cfg.simu_runs()
sub_run = cfg.gen_runs(0, 10)

# Now loop on all the simulations and gather data
for code in code_run:

    for sub in sub_run:

        this_path = base_path + code + '/' + sub + '/'
        this_snap = this_path + snap_path
        input_all_csv = 'output/clusters_' + code + '_' + sub + '.csv' 

        try:
            data_all = pd.read_csv(input_all_csv)
            com = ['Xc(6)', 'Yc(7)', 'Zc(8)']
            these_com = data_all[com].values

        except:
            print('Error, file: ', input_all_csv, ' could not be found.')

        # Check that file exists
        if os.path.isfile(this_snap) and os.path.isfile(input_all_csv):

            print('Found: ', len(these_com), ' clusters in ', this_snap)

            # Read the full snapshot here
            part_df = rf.read_snap(file_name=this_snap, velocity=velocity, part_types=part_types, n_files=1)

            for i, this_com in enumerate(these_com):

                for z_axis in range(0, 3):

                    # Select particles for the plot, do a selection first. z_axis is orthogonal to the plane of the projection
                    ax0 = (z_axis + 1) % 3
                    ax1 = (z_axis + 2) % 3

                    if shift == True:
                        'Implement this function'
                        center = t.shift(this_com, side_size * 0.5)
                        this_fout = 'output/cluster_shift_' + code + '_' + sub + '.' + str(i) + '.'
                    else:
                        center = this_com
                        this_fout = 'output/cluster_' + version + code + '_' + sub + '.' + str(i) + '.'

                    print('Plot axes, z=', z_axis, ' ax0=', ax0, ' ax1=', ax1, ' center of mass: ', this_com)
            
                    try:
                        # Select a slab around a given axis, this function returns a dataframe
                        slab_part_df = t.find_slab(part_df=part_df, side=side_size, thick=thickness, center=center, reduction_factor=frac, z_axis=z_axis, rand_seed=rand_seed)
                    except:
                        print('Could not generate a plot for: ', this_snap, '. Data read error.')

                    # Do a plot only if there are enough particles
                    if len(slab_part_df) > n_min_part:

                        # Feed the previously chosen dataframe and plot its 2D density projection
                        pu.plot_density(data=slab_part_df, axes_plot=[ax0, ax1], file_name=this_fout, show_plot=show_plot, legend=legend,
                            grid_size=grid_size, margin=0.1, data_augment=augment, fig_size=fig_size, velocity=velocity, vel=vel_components)
