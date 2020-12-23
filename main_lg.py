'''
    Python Routines for COsmology and Data I/O (PyRCODIO) v0.2
    Edoardo Carlesi (2020)
    ecarlesi83@gmail.com

    main_lg: find LGs, extract and analyze their properties 
'''

import read_files as rf
import halo_utils as hu
import numpy as np
import seaborn as sns
import config as cfg
import pickle as pkl
import pandas as pd
import tools as t
import os


# Set some important global variables
global simu, ahf_base, ahf_file, ahf_file_csv, lgs_base
global i_ini_tot, i_end_tot, x_col, x_col_ahf, m_col, d_col
global m_min, v_max, masscut_pca


def analyze_mass_max():
    '''
    Once all the necessary data has been extracted and exported to csv, run some global analysis routine
    '''

    print('Running analysis only...')
    m_rad = np.zeros((n_lgs_pre, len(radii)))
    
    # Loop over the mass functions already extracted 
    for i_lg, row in df_lgs.iterrows():

        if simu == 'fullbox':
            lg_csv = lg_csv_file + i_str + '_lg_' + str(i_lg) + '.csv'  
            this_lgs_rad = lgs_base + i_str + '_radii.csv'  
            
        elif simu == 'lgf':
            num = str('%02d' % int(row['simu_code']))
            sub = str('%02d' % int(row['sub_code']))
            lg_x = row[x_col].values
            lg_csv = lg_csv_file + num + '_' + sub + '.' + str(i_lg) + '.csv'
            this_lgs_rad = lgs_base + '_radii.csv'  

        if os.path.isfile(lg_csv):
            df_tmp = pd.read_csv(lg_csv)
            print('Reading: ', lg_csv)
                
            for i_r, rad in enumerate(radii):
                df_tmp = df_tmp[df_tmp[d_col] > 2000.0]
                m_max = df_tmp[df_tmp[d_col] < rad][m_col].max()
                m_rad[i_lg, i_r] = m_max

    for i_r, r_col in enumerate(r_str):
        df_lgs_orig[r_col] = m_rad[:, i_r]

    print('Saving to: ', this_lgs_rad)
    df_lgs_orig.to_csv(this_lgs_rad)


def plot_mass_max():
    """ Plot the results of the analysis """

    label_fb = 'RAND'
    label_lg = 'CS'

    # Load FB data
    for i_cat in range(i_ini_tot, i_end_tot):
        i_str = '%02d' % i_cat
        this_lgs_rad = lgs_base_fb + i_str + '_radii.csv'  

        print('Reading from : ', this_lgs_rad)
        df_rad = pd.read_csv(this_lgs_rad)
        df_rad = df_rad[df_rad[r_str[0]] > 0.0]
        df_rm_all.append(df_rad)

    print('Merge all DFs...')
    df_fb = pd.concat(df_rm_all)
    print(df_fb.head())

    # Load CS data
    lgs_rad = lgs_base + '_radii.csv'  

    print('Reading from : ', lgs_rad, ' n_tot: ', len(lgs_rad))
    df_rad = pd.read_csv(lgs_rad)
    df_lg = df_rad[df_rad[r_str[0]] > 0.0]
    box_center = [5.0e+4] * 3
    df_lg['Dist'] = df_lg[x_col].T.apply(lambda x: t.distance(x, box_center))
    df_lg = df_lg[df_lg['Dist'] < d_max]
    print('New number: ', len(df_lg))

    slopes_fb = []; masses_fb = []; fracs_fb = []
    slopes_lg = []; masses_lg = []; fracs_lg = []
    meds_lg = np.zeros((len(r_str), 3))
    meds_fb = np.zeros((len(r_str), 3)) 

    for ir, rs in enumerate(r_str):
        f_out = 'output/masses_lg_cs_fb_' + rs + '.png'
        sns.distplot(np.log10(df_fb[rs]), color='orange', label=label_fb)
        sns.distplot(np.log10(df_lg[rs]), color='grey', label=label_lg)
        plt.xlabel(r'$\log_{10}M\quad [M_{\odot} h^{-1}]$')
        plt.legend()
        title = r'Max mass at R: ' + str(radii[ir]/1.e+3) + ' $h^{-1}$ Mpc'
        plt.title(title)
        plt.tight_layout()
        print('Saving file to: ', f_out)
        plt.savefig(f_out)
        plt.cla()
        plt.clf()

        percs = [10, 50, 90]

        med = np.percentile(np.log10(df_fb[rs]), percs)
        meds_fb[ir] = med
        masses_fb.append(med[1])
        medians_fb = '%.3f_{%.3f}^{+%.3f}' % (med[1], med[0]-med[1], med[2]-med[1]) 

        med = np.percentile(np.log10(df_lg[rs]), percs)
        meds_lg[ir] = med
        masses_lg.append(med[1])
        medians_lg = '%.3f_{%.3f}^{+%.3f}' % (med[1], med[0]-med[1], med[2]-med[1]) 
        print('LG:', medians_lg)
        print('FB:', medians_fb)
    
        m_cluster = 1.0e+14
        n_cluster = len(df_fb[df_fb[rs] > m_cluster])
        f_cluster = n_cluster / len(df_fb)
        print('Fractions of FB at ', rs, ' from a cluster: ',  f_cluster) 
        fracs_fb.append(f_cluster)

        n_cluster = len(df_lg[df_lg[rs] > m_cluster])
        f_cluster = n_cluster / len(df_lg)
        print('Fractions of LG at ', rs, ' from a cluster: ',  f_cluster) 
        fracs_lg.append(f_cluster)

    # Still in 'plots' mode
    print('FB: ')
    print(masses_fb)
    print(slopes_fb)
    print(fracs_fb)

    print('LG: ')
    print(masses_lg)
    print(slopes_lg)
    print(fracs_lg)

    '''
    plt.plot(masses, slopes, color='black')
    plt.xlabel(r'$\log_{10} M_{max}$')
    plt.ylabel(r'b')
    plt.tight_layout()
    plt.savefig('output/masses_vs_vtancorr.png')
    #plt.pause(3)
    plt.close()
    plt.cla()
    plt.clf()
    '''

    plt.plot(radii, masses_fb, color='red', label = label_fb)
    plt.fill_between(radii, meds_fb[:, 0], meds_fb[:, 2], color='orange', alpha=0.3)
    plt.plot(radii, masses_lg, color='black', label = label_lg)
    plt.fill_between(radii, meds_lg[:, 0], meds_lg[:, 2], color='grey', alpha=0.2)
    plt.xlabel(r'$R \quad [Mpc h^{-1}]$')
    plt.ylabel(r'$\log_{10}M \quad [M_{\odot} h^{-1}]$')
    plt.tight_layout()
    f_out = 'output/m_max_R_cs_vs_fb.png'
    plt.savefig(f_out) 

    delta_masses = (np.array(masses_fb) - np.array(masses_lg)) / np.array(masses_lg)
    delta_m = (np.array(masses_fb) - np.array(masses_lg)) 
    ratio_m = (np.array(masses_fb) / np.array(masses_lg)) 
    print(delta_masses)
    print(ratio_m)
    print(10 ** delta_m)
    #plt.savefig('output/frac_cl_vs_r.png')
    #plt.pause(3)
    #plt.close()
    #plt.cla()
    #plt.clf()


def fb_mass_functions(lg_model=None):
    """ Extract the mass functions around LG candidates in FB simulations """

    # FIXME
    lgs_base = '/home/edoardo/CLUES/PyRCODIO/output/lg_fb_new_'
    #lgs_base = '/home/edoardo/CLUES/PyRCODIO/output/LG_HALOS/halos_simu_periodic_'

    all_pca = []

    # Loop over halo catalogs and lg lists
    for i_cat in range(i_ini, i_end):

        i_str = '%02d' % i_cat
        print('Analyzing fullbox LG candidates mass functions ...')
        this_lgs = lgs_base + i_str + '.csv'  
 
        print('LGS FILE: ', this_lgs)
        df_lgs_orig = pd.read_csv(this_lgs)
        n_lgs_pre = len(df_lgs_orig)

        print('N pre: ', n_lgs_pre)
        df_lgs = df_lgs_orig.drop_duplicates(subset=['M_M31'])
        df_lgs = select_lgs(data=df_lgs, lg_model=lg_model)
        print('N post: ', len(df_lgs))

        # Loop over the mass functions already extracted 
        for i_lg, row in df_lgs.iterrows():
            lg_csv = lg_csv_file + i_str + '_lg_' + str(i_lg) + '.csv'  
            this_x = row[x_col].values

            if os.path.isfile(lg_csv):
                df_tmp = pd.read_csv(lg_csv)

                # Find the halo list
                df_tmp = df_tmp[df_tmp[d_col] < r_max]

                df_tmp[d_col] = df_tmp[x_col_ahf].T.apply(lambda x: t.distance(x, this_x))
                df_tmp = df_tmp[df_tmp[d_col] < r_max]

                pca = t.spatial_pca(data=df_tmp, cols=x_col_ahf)
                print('PCA result: ', pca)
            
                df_tmp = df_tmp[df_tmp['Mvir(4)'] > masscut_pca] 
                pca = t.spatial_pca(data=df_tmp, cols=x_col_ahf)
                print('PCA result mass: ', pca)
        
                all_pca.append(pca)
                x_bin, y_bin = t.check_df_bins(data=df_tmp, bins=mbins, binmode='log')

                for ib in range(0, n_bin-1):

                    v = y_bin[ib]

                    if v > 0:
                        all_bins[ib].append(v)

    f_pca = 'output/pca_fullbox.pkl'
    pickle.dump(all_pca, open(f_pca, 'wb'))
    print('Output PCA written to: ', f_pca)

    f_out = 'output/all_mass_functions_fullbox.pkl'
    pkl.dump(all_bins, open(f_out, 'wb'))
    print('Saving output MF to: ', f_out)

    f_out = 'output/all_mass_functions_x_bin_fullbox.pkl'
    pkl.dump(x_bin, open(f_out, 'wb'))
    print('Saving output MF x_bin to: ', f_out)


def lgf_mass_functions(resolution='1024', lg_model=None, d_max=5000.0, mbins=20):
    """ Read the individual mass functions and then dump them to a pkl file """

    lgs_lgf_base = '/home/edoardo/CLUES/PyRCODIO/output/LG_' + resolution + '/lg_center_'

    # Read the full list of halos
    df_lgs = pd.read_csv('output/lg_pairs_' + resolution + '.csv')
    print('TotLen Original File: ', len(df_lgs))

    # Select a halo subsample
    df_lgs = select_lgs(data=df_lgs, lg_model=lg_model, lgf=True)
    print('TotLen After selection: ', len(df_lgs))

    box_center = [5.0e+4]*3
    
    df_lgs[d_col] = df_lgs[x_col].T.apply(lambda x: t.distance(x, box_center))
    df_lgs = df_lgs[df_lgs[d_col] < d_max]
    print(f'TotLen within R={d_max}, n={len(df_lgs)}')

    n_lgs = len(df_lgs)
    print('Analyzing fullbox LG candidates mass functions ...')
    
    # Set some binning-related variables
    all_bins = [[] for i in range(0, mbins)]
    all_pca = []

    # Loop over halo catalogs and lg lists
    for ilg, row in df_lgs.iterrows():
        num = str('%02d' % int(row['simu_code']))
        sub = str('%02d' % int(row['sub_code']))
        this_x = row[x_col].values
        
        this_lg = lgs_lgf_base + num + '_' + sub + '.' + str(ilg) + '.csv'

        if os.path.isfile(this_lg):
            df_tmp = pd.read_csv(this_lg)

            print('Reading ', this_lg)
            df_tmp[d_col] = df_tmp[x_col_ahf].T.apply(lambda x: t.distance(x, this_x))
            df_tmp = df_tmp[df_tmp[d_col] < r_max]
    
            # Bin the mass function
            x_bin, y_bin = t.check_df_bins(data=df_tmp, bins=mbins, binmode='log')
            
            for ib in range(0, n_bin-1):
                v = y_bin[ib]

                if v > 0:
                    all_bins[ib].append(v)
        
            #pca = t.spatial_pca(data=df_tmp, cols=x_col_ahf)
            df_tmp = df_tmp[df_tmp['Mvir(4)'] > masscut_pca]
            pca = t.spatial_pca(data=df_tmp, cols=x_col_ahf)
            all_pca.append(pca)

    # Save the PCA values
    f_pca = 'output/pca_lgf.pkl'
    pickle.dump(all_pca, open(f_pca, 'wb'))
    print('Output PCA written to: ', f_pca)

    # Save the full mass function
    f_out = 'output/all_mass_functions_lgf_' + resolution + '.' + str(n_lgs) + '.pkl'
    pkl.dump(all_bins, open(f_out, 'wb'))
    print('Saving LGF MF output to: ', f_out)

    # Save the x bin values 
    f_out = 'output/all_mass_functions_x_bin_lgf_' + resolution + ' .pkl'
    pkl.dump(x_bin, open(f_out, 'wb'))
    print('Saving LGF MF x_bin output to: ', f_out)

    return x_bin, all_bins


def plot_mass_functions():
    """ Take the binned mass functions and do some plots """ 

    y_fb = 'output/all_mass_functions_fullbox.pkl'
    x_lg = 'output/all_mass_functions_x_bin_lgf.pkl'
    y_lg = 'output/all_mass_functions_lgf.160.pkl'
    #y_lg = 'output/all_mass_functions_lgf.338.pkl'
    #y_fb = 'output/all_mass_functions_lgf.223.pkl'

#    x_bin_fb = pkl.load(open(x_fb, 'rb'))
#    print(x_bin_fb)
    #print(y_bin_fb)
    x_bin_lg = pkl.load(open(x_lg, 'rb'))
    #print(x_bin_lg)
    y_bin_lg = pkl.load(open(y_lg, 'rb'))
    y_bin_fb = pkl.load(open(y_fb, 'rb'))
    #print(y_bin_lg)

    n_bins = len(x_bin_lg)
    perc_bins_y_lg = np.zeros((n_bins, 3))
    perc_bins_y_fb = np.zeros((n_bins, 3))
    percs = [10, 50, 90]

    radius = 5.0
    vol = 4.0 / 3.0 * np.pi * (radius ** 3.0)

    for i in range(0, n_bins):
        this_bin_lg = y_bin_lg[i]
        this_bin_fb = y_bin_fb[i]

        if len(this_bin_lg) > 2:
            pbin_lg = np.percentile(this_bin_lg, percs)
            perc_bins_y_lg[i] = pbin_lg / vol

        if len(this_bin_fb) > 2:
            pbin_fb = np.percentile(this_bin_fb, percs)
            perc_bins_y_fb[i] = pbin_fb / vol

    #plt.axis([9.5, 13.0, -0.1/vol, 3.25/vol])
    plt.axis([9.5, 13.0, -2.6, 0.65])
    plt.xlabel(r'$\log_{10} M \quad [M_{\odot} h^{-1}]$')
    plt.ylabel(r'$\log_{10} n \quad [h^3 Mpc^{-3}]$')
    plt.plot(x_bin_lg, np.log10(perc_bins_y_lg[:,1]), color='black')
    plt.plot(x_bin_lg, np.log10(perc_bins_y_fb[:,1]), color='red')
    plt.fill_between(x_bin_lg, np.log10(perc_bins_y_fb[:, 0]), np.log10(perc_bins_y_fb[:, 2]), facecolor='orange', alpha=0.3)
    plt.fill_between(x_bin_lg, np.log10(perc_bins_y_lg[:, 0]), np.log10(perc_bins_y_lg[:, 2]), facecolor='grey', alpha=0.2)
    plt.tight_layout()

    out_fig = 'output/mass_functions_5mpc_cs_vs_fb.png'
    plt.savefig(out_fig)
    plt.show(block=False)
    plt.pause(3)
    plt.close()


def plots_pca():
    '''
    Once the PCA has been applied to the halos' coordinates to look for flatness of the distribution, do a plot
    '''
    # TODO this does the full pca thing now
    '''
            MOVE THE PCA STUFF SOMEWHERE ELSE
        '''

    f_pca_lgf = 'output/pca_lgf.pkl'
    f_pca_fullbox = 'output/pca_fullbox.pkl'
    pca_lg = pickle.load(open(f_pca_lgf, 'rb'))
    pca_fb = pickle.load(open(f_pca_fullbox, 'rb'))

    pca_lg = np.array(pca_lg)
    pca_fb = np.array(pca_fb)

    sns.distplot(pca_lg[:,1])
    sns.distplot(pca_fb[:,1])
    sns.distplot(pca_lg[:,2])
    sns.distplot(pca_fb[:,2])
    plt.show()


def density_plots():
    '''
    Do a series of plots centered around LG-like pairs
    '''

    # Choose catalog type
    use_ahf = True; use_rs = False
    #use_ahf = False; use_rs = True

    # Simulation & catalog
    if use_ahf == True:
        file_single='snapshot_054.z0.000.AHF_halos'
        #file_single='snapshot_full_054.z0.000.AHF_halos'
        base_file_out = 'output/lg_fb_new_'    
        box_size = 100000.0
        #base_path = '/home/eduardo/CLUES/DATA/FullBox/catalogs/'
        base_path = '/home/edoardo/CLUES/DATA/FullBox/'
        #base_path='/media/edoardo/Elements/CLUES/DATA/2048/00_06/'
        sub_runs = cfg.gen_runs(0, 5)

    elif use_rs == True:
        box_size = 2500000.0
        file_single = '.part'
        base_file_out = 'output/lg_fullbox_rs_'    
        base_path = '/home/edoardo/CLUES/DATA/RS/out_79_csv/'
        #base_path = '/z/carlesi/STORE/MultiDark/RockStarCSV/BigMD_3840_Planck1/out_79_csv/'
        sub_runs = []

        n_start = 10
        n_parts = 20
        for i in range(n_start, n_parts):
            sub = '%04d' % i
            sub_runs.append(sub)
        '''
        sub_runs = ['0011']
        '''

    lg_models, index = cfg.lg_models()
    this_model = lg_models[index['GENERIC']]

    kpcFac = 1.0e+3
    radius = 7.0 * kpcFac
    side_buffer = 1.0 * kpcFac

    n_sub_x = int(np.ceil(box_size / radius))
    n_sub_y = int(n_sub_x)
    n_sub_z = int(n_sub_y)
    n_tot = np.power(n_sub_x, 3)

    print('Subdivision in ', n_sub_x, ' subcubes per axis, radius: ', radius, ' and side_buffer: ', side_buffer)

    for run in sub_runs:

        all_lgs = []
        if use_ahf:
            this_ahf = base_path + run + '/' + file_single
            print('Reading file: ', this_ahf)
            #halo_df = rf.read_ahf_halo(this_ahf, file_mpi=False)
            halo_df = rf.read_ahf_halo(this_ahf, file_mpi=True)
            print('Found: ', len(halo_df), ' objects.')

            x_min = 0.0;         y_min = 0.0;         z_min = 0.0

        elif use_rs:
            this_rs = base_path + run + file_single
            
            print('Reading file: ', this_rs)
            halo_df = pd.read_csv(this_rs)
            #halo_df = rf.read_rs_halo(read_file=this_rs, with_dask=True)
            halo_df.columns = t.header_rs2ahf(halo_df.columns)
            #print('Found: ', len(halo_df), ' objects.')

            # The file is divided in sub files, determine the extension
            x_max = halo_df['Xc(6)'].max() * kpcFac
            y_max = halo_df['Yc(7)'].max() * kpcFac
            z_max = halo_df['Zc(8)'].max() * kpcFac
            x_min = halo_df['Xc(6)'].min() * kpcFac
            y_min = halo_df['Yc(7)'].min() * kpcFac
            z_min = halo_df['Zc(8)'].min() * kpcFac

            print(x_min, y_min, z_min)
            print(x_max, y_max, z_max)

            n_sub_x = int(np.ceil((x_max - x_min) / radius))
            n_sub_y = int(np.ceil((y_max - y_min) / radius))
            n_sub_z = int(np.ceil((z_max - z_min) / radius))
            n_tot = n_sub_x * n_sub_y * n_sub_z

            print('N subcubes ', n_sub_x, n_sub_y, n_sub_z, ' Ntot: ', n_tot)

        #print(halo_df.head())
        n_count = 0
        old_time = time.time()
        for ix in range(0, int(n_sub_x)):
            for iy in range(0, n_sub_y):
                new_time = time.time()
                dif_time = '%.3f' % (new_time - old_time)
                percent = '%.3f' % (100.0 * n_count/n_tot) 
                print('Done: ', percent, '% in ', dif_time, ' seconds. Tot LGs: ', len(all_lgs), flush = True)
                #old_time = time.time()

                for iz in range(0, n_sub_z):
                    n_count += 1
                    this_center = np.array([radius * (0.5 + ix)+x_min, radius * (0.5 + iy)+y_min, radius * (0.5 + iz)+z_min])
                    this_radius = radius * 0.5 + side_buffer
                    #print('Subbox around center: ', this_center, ' rad: ', this_radius, flush=True)
                    these_lgs = hu.find_lg(halo_df, this_model, this_center, this_radius, center_cut=True, search='Box', verbose=False)
                    #print('FindLG: ', len(these_lgs))

                    for this_lg in these_lgs:
                        this_lg.code_simu = 'FB'
                        this_lg.code_sub = run

                        all_lgs.append(this_lg)

            #for ii in range(0, 10):
            #    print(ii, all_lgs[len(all_lgs) - ii - 1].info())

        this_lg_df = pd.DataFrame(columns = this_lg.header(dump=False))

        for lg in all_lgs:
            this_row = lg.info(dump=False)
            this_series = pd.Series(this_row, index = this_lg_df.columns)
            this_lg_df = this_lg_df.append(this_series, ignore_index=True)

        print(this_lg_df.head())
        this_csv = base_file_out + run + '.csv'
        this_lg_df.drop_duplicates(inplace = True)
        this_lg_df.to_csv(this_csv, float_format='%.3f')

        this_pkl = base_file_out + run + '.pkl'
        f_pkl = open(this_pkl, 'wb')
        pkl.dump(all_lgs, f_pkl)


def fb_find():
    """
    Find all the local groups in a full box simulation
    """

    # Choose catalog type
    use_ahf = True; use_rs = False
    #use_ahf = False; use_rs = True

    # Simulation & catalog
    if use_ahf == True:
        file_single='snapshot_054.z0.000.AHF_halos'
        #file_single='snapshot_full_054.z0.000.AHF_halos'
        base_file_out = 'output/lg_fb_new_'    
        box_size = 100000.0
        #base_path = '/home/eduardo/CLUES/DATA/FullBox/catalogs/'
        base_path = '/home/edoardo/CLUES/DATA/FullBox/'
        #base_path='/media/edoardo/Elements/CLUES/DATA/2048/00_06/'
        sub_runs = cfg.gen_runs(0, 5)

    elif use_rs == True:
        box_size = 2500000.0
        file_single = '.part'
        base_file_out = 'output/lg_fullbox_rs_'    
        base_path = '/home/edoardo/CLUES/DATA/RS/out_79_csv/'
        #base_path = '/z/carlesi/STORE/MultiDark/RockStarCSV/BigMD_3840_Planck1/out_79_csv/'
        sub_runs = []

        n_start = 10
        n_parts = 20
        for i in range(n_start, n_parts):
            sub = '%04d' % i
            sub_runs.append(sub)
        '''
        sub_runs = ['0011']
        '''

    lg_models, index = cfg.lg_models()
    this_model = lg_models[index['GENERIC']]

    kpcFac = 1.0e+3
    radius = 7.0 * kpcFac
    side_buffer = 1.0 * kpcFac

    n_sub_x = int(np.ceil(box_size / radius))
    n_sub_y = int(n_sub_x)
    n_sub_z = int(n_sub_y)
    n_tot = np.power(n_sub_x, 3)

    print('Subdivision in ', n_sub_x, ' subcubes per axis, radius: ', radius, ' and side_buffer: ', side_buffer)

    for run in sub_runs:

        all_lgs = []
        if use_ahf:
            this_ahf = base_path + run + '/' + file_single
            print('Reading file: ', this_ahf)
            #halo_df = rf.read_ahf_halo(this_ahf, file_mpi=False)
            halo_df = rf.read_ahf_halo(this_ahf, file_mpi=True)
            print('Found: ', len(halo_df), ' objects.')

            x_min = 0.0;         y_min = 0.0;         z_min = 0.0

        elif use_rs:
            this_rs = base_path + run + file_single
            
            print('Reading file: ', this_rs)
            halo_df = pd.read_csv(this_rs)
            #halo_df = rf.read_rs_halo(read_file=this_rs, with_dask=True)
            halo_df.columns = t.header_rs2ahf(halo_df.columns)
            #print('Found: ', len(halo_df), ' objects.')

            # The file is divided in sub files, determine the extension
            x_max = halo_df['Xc(6)'].max() * kpcFac
            y_max = halo_df['Yc(7)'].max() * kpcFac
            z_max = halo_df['Zc(8)'].max() * kpcFac
            x_min = halo_df['Xc(6)'].min() * kpcFac
            y_min = halo_df['Yc(7)'].min() * kpcFac
            z_min = halo_df['Zc(8)'].min() * kpcFac

            print(x_min, y_min, z_min)
            print(x_max, y_max, z_max)

            n_sub_x = int(np.ceil((x_max - x_min) / radius))
            n_sub_y = int(np.ceil((y_max - y_min) / radius))
            n_sub_z = int(np.ceil((z_max - z_min) / radius))
            n_tot = n_sub_x * n_sub_y * n_sub_z

            print('N subcubes ', n_sub_x, n_sub_y, n_sub_z, ' Ntot: ', n_tot)

        #print(halo_df.head())
        n_count = 0
        old_time = time.time()
        for ix in range(0, int(n_sub_x)):
            for iy in range(0, n_sub_y):
                new_time = time.time()
                dif_time = '%.3f' % (new_time - old_time)
                percent = '%.3f' % (100.0 * n_count/n_tot) 
                print('Done: ', percent, '% in ', dif_time, ' seconds. Tot LGs: ', len(all_lgs), flush = True)
                #old_time = time.time()

                for iz in range(0, n_sub_z):
                    n_count += 1
                    this_center = np.array([radius * (0.5 + ix)+x_min, radius * (0.5 + iy)+y_min, radius * (0.5 + iz)+z_min])
                    this_radius = radius * 0.5 + side_buffer
                    #print('Subbox around center: ', this_center, ' rad: ', this_radius, flush=True)
                    these_lgs = hu.find_lg(halo_df, this_model, this_center, this_radius, center_cut=True, search='Box', verbose=False)
                    #print('FindLG: ', len(these_lgs))

                    for this_lg in these_lgs:
                        this_lg.code_simu = 'FB'
                        this_lg.code_sub = run

                        all_lgs.append(this_lg)

            #for ii in range(0, 10):
            #    print(ii, all_lgs[len(all_lgs) - ii - 1].info())

        this_lg_df = pd.DataFrame(columns = this_lg.header(dump=False))

        for lg in all_lgs:
            this_row = lg.info(dump=False)
            this_series = pd.Series(this_row, index = this_lg_df.columns)
            this_lg_df = this_lg_df.append(this_series, ignore_index=True)

        print(this_lg_df.head())
        this_csv = base_file_out + run + '.csv'
        this_lg_df.drop_duplicates(inplace = True)
        this_lg_df.to_csv(this_csv, float_format='%.3f')

        this_pkl = base_file_out + run + '.pkl'
        f_pkl = open(this_pkl, 'wb')
        pkl.dump(all_lgs, f_pkl)


def lgf_find():
    """
    Given a set of catalogs find the LG-like objects and export the output
    """

    # Use AHF / csv catalogs
    csvAhf = True; hiResAhf = False
    #csvAhf = False; hiResAhf = True

    # Configure the LG model and subpaths
    if csvAhf == True:
        code_run = cfg.gen_runs(0, 100)
        sub_run = cfg.gen_runs(0, 100)
        [model_run, dict_model] = cfg.lg_models()
    elif hiResAhf == True:
        [model_run, dict_model] = cfg.lg_models()
        code_run = cfg.simu_runs()
        sub_run = cfg.sub_runs()

    # Local data path, file names and file format
    data_path = '/home/edoardo/CLUES/PyRCODIO/data/'
    file_ahf = 'snapshot_054.0000.z0.000.AHF_halos'

    #resolution = '512'
    resolution = '1024'

    # Full dataset base path
    if csvAhf == True:
        #base_path = '/home/edoardo/Elements/CLUES/DATA/CSV/' + resolution + '/'
        base_path = '/home/edoardo/CLUES/DATA/LGF/' + resolution + '/CSV/'
    elif hiResAhf == True:
        base_path = '/media/edoardo/Elements/CLUES/DATA/2048/'

    # Select a subsample from the full catalog to look for local groups
    facKpc = 1.0e+3
    radius = 7.0 * facKpc
    center = [50.0 * facKpc] * 3

    # Read the | Gyr / z / a | time conversion table
    time = rf.read_time(data_path)

    all_halo_mah = []

    # Output files 
    if csvAhf == True:
        out_base_pkl = base_path + 'lg_'
        out_all_lgs_csv = 'output/lg_pairs_' + resolution + '.csv'
    if hiResAhf == True:
        out_base_pkl = 'saved/lg_pair_'
        out_all_lgs_csv = 'output/lg_pairs_2048.csv'

    # All LG dataframe (to be dumped to csv later on), use a dummy halo to properly generate the file header, use a dummy halo to properly generate the file header
    h = hu.Halo('void')
    cols = hu.LocalGroup(h, h).header(dump=False)

    all_lgs_df = pd.DataFrame(columns=cols)

    # Now loop on all the simulations and gather data
    for code in code_run:

        for sub in sub_run:

            out_file_pkl = 'output/lg_' + resolution + '_' + code + '_' + sub + '.pkl'
            these_lgs = []

            if csvAhf == True:
                this_ahf = base_path + 'ahf_' + code + '_' + sub + '.csv'
            elif hiResAhf == True:
                this_path = base_path + code + '/' + sub + '/'
                this_ahf = this_path + file_ahf

            # Check that file exists
            if os.path.isfile(this_ahf):
                print('Reading AHF file: ', this_ahf)

                if os.path.isfile(out_file_pkl):
                    with open(out_file_pkl, 'rb') as f_pkl:
                        these_lgs = pkl.load(f_pkl)
                else:
                    if csvAhf == True:
                        halo_df = pd.read_csv(this_ahf)
                        this_model = model_run[dict_model['GENERIC']]

                    elif hiResAhf == True:
                        halos, halo_df = rf.read_ahf_halo(this_ahf)
                        this_model = model_run[dict_model[code]]

                    print('Looking for Local Group candidates...')

                    if len(halo_df) > 0:
                        these_lgs = hu.find_lg(halo_df, this_model, center, radius, center_cut=True, search='Box')
                    else:
                        print('Problems with file: ', this_ahf, '. Reading the file results in zero length.')

                # Check if there is at least one LG in the selection
                if len(these_lgs) > 0:

                    # Save simu info in LG object
                    for i in range(0, len(these_lgs)):
                        these_lgs[i].code_simu = code
                        these_lgs[i].code_sub = sub

                    print('Saving LG output to file: ', out_file_pkl)
                    out_f_pkl = open(out_file_pkl, 'wb')
                    pkl.dump(these_lgs, out_f_pkl)
                    out_f_pkl.close()

                    for lg in these_lgs:
                        try:
                            print(code, '_', sub, ' --> found a LG candidate with properties: ')
                            lg.info()
        
                            # Append the LG to the dataframe
                            this_row = lg.info(dump=False)
                            this_series = pd.Series(this_row, index=cols)
                            all_lgs_df = all_lgs_df.append(this_series, ignore_index=True)
                        except:
                            print('Error on simu ', code, '_', sub, ', skipping LG')

    # Save CSV output file
    all_lgs_df.to_csv(out_all_lgs_csv)


def lg_density_fb():
    """ Compute the density of LGs in a series of FB random simulations """

    i_simu_start = 0
    i_simu_end = 5
    
    lg_models, lgmd = cfg.lg_models()
    lg_model_names = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    tot_lgs = np.zeros(6, dtype=int)

    for i_simu in range(i_simu_start, i_simu_end):
        
        lg_file_csv = 'output/lg_fb_new_0' + str(i_simu) + '.csv'  
        fb_file_csv = '/home/edoardo/CLUES/DATA/FullBox/0' + str(i_simu) + '.csv'  
        data = pd.read_csv(lg_file_csv)
        data = data.drop_duplicates()

        for i, model in enumerate(lg_model_names):
            this_model = lg_models[lgmd[model]]

            lgs = select_lgs(data=data, lg_model=this_model)
            n_lgs = len(lgs)

            tot_lgs[i] += n_lgs

    for i in range(0, 6):
        print(f'{lg_model_names[i]} {tot_lgs[i]}')

    return tot_lgs


def halo_density_fb(lg_models=None):
    """ Density of halos within a given mass range in FB random simulations """

    i_simu_start = 0
    i_simu_end = 5
    tot_lgs = np.zeros(6, dtype=int)

    lg_models, lgmd = cfg.lg_models()
    lg_model_names = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    tot_lgs = np.zeros(6, dtype=int) 
 
    for i_simu in range(i_simu_start, i_simu_end):
        
        fb_file_csv = '/home/edoardo/CLUES/DATA/FullBox/0' + str(i_simu) + '/snapshot_054.z0.000.AHF_halos.csv'  
        data = pd.read_csv(fb_file_csv)

        for i, lg_model_name in enumerate(lg_model_names):
            lg_model = lg_models[lgmd[lg_model_name]]
            select = data[(data['Mvir(4)'] > lg_model.m_min) & (data['Mvir(4)'] < lg_model.m_max)]
            tot_lgs[i] += len(select)

    for i in range(0, 6):
        print(f'M{i} {tot_lgs[i]}')

    return tot_lgs


def lg_density_lgf(resolution='1024'):
    """ Density of LGs in LGF simulations """

    lg_models, lgmd = cfg.lg_models()
    lg_model_names = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    tot_lgs = np.zeros(6, dtype=int) 
    
    lg_file_csv = 'output/lg_pairs_' + resolution + '.csv'  
    data = pd.read_csv(lg_file_csv)
    data = data.drop_duplicates()

    for i, model in enumerate(lg_model_names):
        this_model = lg_models[lgmd[model]]

        lgs = select_lgs(data=data, lg_model=this_model, lgf=True)
        n_lgs = len(lgs)

        tot_lgs[i] += n_lgs

    for i in range(0, 6):
        print(f'res={resolution}, M{i}: {tot_lgs[i]}')

    return tot_lgs


def halo_density_lgf(resolution='512', r=6000.0, m_max=5.0e+12, m_min=0.5e+12): 
    """ Density of haloes within a given mass range in LGF runs """

    # FIXME halo density is A PRIORI so that we DO NOT have to read LG pairs.
    # We only look for haloes within 5/6 Mpcs of the box center!

    print(f'Running halo_density_lgf() for resolution={resolution}')

    vol = (r ** 3.0) * 4.0 / 3.0 * np.pi
    center = [5.0e+4]

    loc_center_path = '/media/edoardo/Elements/CLUES/DATA/CSV/' + resolution + '/ahf_'

    ntot = 0
    ncat = 0
    runs = cfg.gen_runs(0, 80)
    subs = cfg.gen_runs(0, 40)

    lg_models, lgmd = cfg.lg_models()
    lg_model_names = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
    tot_lgs = np.zeros(6, dtype=int) 

    # Loop over ALL simulation runs
    for run in runs:

        for sub in subs: 
            this_run = run + '_' + sub
            this_file = loc_center_path + this_run + '.csv'

            # Check if file exists
            if os.path.isfile(this_file):
                ncat += 1
                data = pd.read_csv(this_file)
                data['D'] = data[x_col_ahf].T.apply(lambda x: t.distance(x, center))

                # Select the halos within the chosen radius only
                select = data[data['D'] < r]

                if len(select) == 0:
                    new_center = [c/1.e+3 for c in center]
                    new_r = r / 1.e+3
                    data['D'] = data[x_col_ahf].T.apply(lambda x: t.distance(x, new_center))
                    select = data[data['D'] < new_r]
            
                for i, lg_model_name in enumerate(lg_model_names):
                    lg_model = lg_models[lgmd[lg_model_name]]

                    select = select[(select['Mvir(4)'] < lg_model.m_max) & (select['Mvir(4)'] > lg_model.m_min)]
                    tot_lgs[i] += len(select)

                    #print(f'M{i} -> Run: {this_run}, n:{tot_lgs[i]}')

    for i in range(0, 6):
        print(f'M{i+1}: {tot_lgs[i]}, Ncat: {ncat}')

    return tot_lgs


def select_lgs(data=None, lg_model=None, lgf=False, dist=6.0e+3):
    '''
    Pass a local group model and select lgs in a dataframe accordingly
    Returns a new dataframe with the selected halos 
    '''
    
    m_min = lg_model.m_min
    m_max = lg_model.m_max
    r_min = lg_model.r_min
    r_max = lg_model.r_max
    m_ratio = lg_model.mratio_max
    vrad_max = lg_model.vrad_max

    data['ratio'] = data['M_M31'] / data['M_MW']

    select = data[data['ratio'] < m_ratio]
    select = select[select['Vrad'] < vrad_max]
    select = select[select['R'] > r_min]
    select = select[select['R'] < r_max]
    select = select[select['M_M31'] < m_max]
    select = select[select['M_MW'] > m_min]

    if lgf:
        c = [5.0e+4 for i in range(0, 3)]
        c = np.array(c)

        select['D'] = select[x_col].apply(lambda x: t.distance(x, c), axis=1)
        select = select[select['D'] < dist]

    return select


if __name__ == "__main__":
    ''' Wrapper for LG operations '''

    # Define the global variables here
    simu = 'fullbox'
    x_col = ['Xc_LG', 'Yc_LG', 'Zc_LG']
    x_col_ahf = ['Xc(6)', 'Yc(7)', 'Zc(8)']
    n_fb = lg_density_fb()
    n_lgf_I = lg_density_lgf(resolution='512')
    n_lgf_II = lg_density_lgf(resolution='1024')
    n_simu_fb = 5
    n_simu_lgf_II = 314
    n_simu_lgf_I = 1000
    r = 6.0
    box = 100.0

    vol_fb = (box ** 3.0) * n_simu_fb
    vol_lgf_I = 4.0 / 3.0 * np.pi * (r ** 3.0) * n_simu_lgf_I

    print(f'FB: {vol_fb}, LGF: {vol_lgf_I}')

    for i in range(0, 6):
        print(f'{i} {n_fb[i]/vol_fb} {n_lgf_I[i]/vol_lgf_I}')

    #halo_density_lgf()
    halo_density_fb()

    '''
    density_plots()
    fb_find()
    lgf_find()
    '''


