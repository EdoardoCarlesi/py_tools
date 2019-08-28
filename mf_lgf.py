import matplotlib.pyplot as plt
import scipy.stats as sp
import numpy as np
import os

from libio.read_ascii import *
from config import *
from libcosmo.utils import *
from libcosmo.halos import *
from libcosmo.find_halo import *
from libcosmo.lg_plot import *
import pickle


sub_ini = 0
sub_end = 1
#simuruns = simu_runs()
simuruns = ['37_11']
res='4096'
n_subrun = 10
snap_end = 54
snap_init = 0

for i_simu in range(sub_ini, sub_end):
    simu = simuruns[i_simu]
    n_simu = 0
    n_subs_min = [11111111, 1111111]
    n_subs_max = [0, 0]

    mfmw_z0_x = [];                 mfmw_z0_y = []
    mfm31_z0_x = [];                mfm31_z0_y = []
    mflg_z0_x = [];                 mflg_z0_y = []

    for i_sub in range(0, n_subrun):
        subrun = '%02d' % i_sub
        m_fname = 'saved/lgs_' + res + '_' + simu + '_' + subrun + '.pkl'
        s_fname = 'saved/subs_' + res + '_' + simu + '_' +  subrun + '.pkl'
        #m_fname='saved/'+simu+'_'+subrun+'_mains_all.pkl'
        #s_fname='saved/'+simu+'_'+subrun+'_sats.pkl'
        n_lg = 0

        try:
            hand_main = open(m_fname, 'rb')
            hand_sats = open(s_fname, 'rb')
            main = pickle.load(hand_main)
            sats = pickle.load(hand_sats)

            print('Found: ', s_fname)
            print('Found: ', m_fname)

            r_sub = 1.5
            n_lg = 2
            n_simu += 1
        except:
            print('Found nothing') #Nothing found'

        masses_z0 = []; lg_masses_z0 = [];

        gather_rad = 1500.0
        print('GatherRadius: ', gather_rad)

        full_lg = main[0]
        full_subs = find_halos_mass_radius(full_lg.geo_com(), sats, gather_rad, 0.0)

        for isub in full_subs:
            if isub.m != full_lg.LG1.m and isub.m != full_lg.LG2.m:
                masses_z0.append(isub.m)

        (this_lgz0_x, this_lgz0_y) = mass_function(masses_z0)
        mflg_z0_x.append(this_lgz0_x);                 mflg_z0_y.append(this_lgz0_y);

        masses_z0 = []

        for i_lg in range(0, 2):

            if i_lg == 0:
                this_halo = main[0].LG1
            if i_lg == 1:
                this_halo = main[0].LG2

            gather_rad = this_halo.r * r_sub #500.0
            print('GatherRadius: ', gather_rad)
            print(this_halo.info())
            subs = find_halos_mass_radius(this_halo.x, sats, gather_rad, 0.0)

            n_subs = len(subs)
        
            if n_subs_min[i_lg] > n_subs:
                n_subs_min[i_lg] = n_subs

            if n_subs_max[i_lg] < n_subs:
                n_subs_max[i_lg] = n_subs

            for sub in subs:
                if sub.m != this_halo.m:
                    masses_z0.append(sub.m)

            # End of the loop on i_main, still looping on i_lg
            (this_mfz0_x, this_mfz0_y) = mass_function(masses_z0)

            # Save informations on subhalo positions through time
            if i_lg == 0:
                print('M31 Max and min subhalos: ', n_subs_max[i_lg], n_subs_min[i_lg])
                mfmw_z0_x.append(this_mfz0_x);          mfmw_z0_y.append(this_mfz0_y)

            elif i_lg == 1:
                print('MW Max and min subhalos: ', n_subs_max[i_lg], n_subs_min[i_lg])
                mfm31_z0_x.append(this_mfz0_x);         mfm31_z0_y.append(this_mfz0_y)

    n_bins = 15
    f_mwz0 = simu + '_mf_z0_M31.png'
    plot_massfunctions(mfmw_z0_x, mfmw_z0_y, n_simu, f_mwz0, n_bins)

    f_m31z0 = simu + '_mf_z0_MW.png'
    plot_massfunctions(mfm31_z0_x, mfm31_z0_y, n_simu, f_m31z0, n_bins)

    f_lgz0 = simu + '_mf_z0_LG.png'
    plot_massfunctions(mflg_z0_x, mflg_z0_y, n_simu, f_lgz0, n_bins)
