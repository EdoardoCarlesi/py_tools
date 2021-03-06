#!/usr/bin/python

import matplotlib.pyplot as plt
import scipy.stats as sp
import numpy as np
import os

from libio.read_ascii import *
from config import *
from libcosmo.utils import *
from libcosmo.halos import *
from libcosmo.find_halos import *
from libcosmo.lg_plot import *
import pickle

resolution='2048'
simuruns = simu_runs()

# Which realisation
this_simu = 0
simu_init = 0
simu_end = 10

# Number of subrun
sub_init = 0
sub_end = 10

# Snapshots
snap_init = 0
snap_end = 54

#base_path = '/home/eduardo/CLUES/PyRCODIO/'
base_path = '/home/edoardo/CLUES/PyRCODIO/'
outp_path = 'output/'
save_path = 'saved/'

file_web = 'zoom_2048_054.000064.Vweb-ascii'; grid_web = 64; box_web = 100000.0

file_m_bins = save_path + 'm_bins.pkl'
file_n_bins = save_path + 'n_bins.pkl'
file_masses = save_path + 'masses.pkl'
file_n_subs = save_path + 'n_subs.pkl'

m_sub_min = 1.e+8
min_part = 30
stepMyr = 0.25

'''
	SELECT WHAT KIND OF ANALYSIS NEEDS TO BE DONE
'''
# Plot mass accretion histories and evolution of satellite anisotropy
#do_evolution = True
do_evolution = False

# General combined statistics of all LG realisations (gathers data on mass/nsub bins etc.)
do_all_lgs = True
#do_all_lgs = False

# Do plots of the mass - subhalo scatter for MW and M31
do_plots_mass_sub = True
#do_plots_mass_sub = False

# Subhalo trajectories
#do_trajectories = True
do_trajectories = False

# Plot sub halo mass functions and anisotropies
#do_sub_plots = True
do_sub_plots = False

# Plot mass accretion functions
#do_plot_mfs = True
do_plot_mfs = False

# Save informations about subhalos at different steps
#do_subs = True
do_subs = False

# Compute the cosmic web at each LG position
#do_vweb = True
do_vweb = False

# Use the pre-computed cosmic web to 
#do_subs_web = True
do_subs_web = False

# Load the pkl files and plot some statistical properties
#do_satellite_anisotropy_plots = True
do_satellite_anisotropy_plots = False

# Use the collected data on subhalos to do some statistics
#do_subs_stats = True
do_subs_stats = False


'''
	START THE ACTUAL PROGRAM AFTER CHOOSING THE ANALYSIS OPTIONS
	
'''

lg_names = ['MW', 'M31', 'LG']
#n_lg = len(lg_names)
n_lg = 2

mass_histories = np.zeros((n_lg, sub_end - sub_init, snap_end-snap_init))
anisotropies = np.zeros((n_lg, sub_end - sub_init, snap_end-snap_init, 3))

all_lgs = []

n_sub_stat = 8		# Properties being tracked: mass, mass at infall, number of Rvir crossings etc.

n_dyn_stat = 6		# Velocity and position (histories!) in the MW / M31 reference frame

time = np.zeros((snap_end-snap_init))

for i_time in range(0, snap_end-snap_init):
	time[i_time] = (snap_end - i_time) * stepMyr

# This skips the following loop on the halo evolution
true_sub_init = sub_init
true_sub_end = sub_end

if do_evolution == False:
	i_sub = 0
	sub_init = 0
	sub_end = 0


for this_simu in range(simu_init, simu_end):
	simurun = simuruns[this_simu]

	print 'Doing simulation N=', simurun

	# Total mass functions of ALL subhaloes
	n_simu = 0; 			sub_skip = 0
	
	for i_sub in range(sub_init, sub_end):

		sub_skip = 0
		subrun = '%02d' % i_sub
		subs_stats = [[] for i in(0, 2)]
		dyns_stats = [[] for i in(0, 2)]

		s_fname='saved/'+simurun+'_'+subrun+'_sats.pkl'
		#m_fname='saved/'+simurun+'_'+subrun+'_mains.pkl'
		m_fname='saved/'+simurun+'_'+subrun+'_mains_all.pkl'
		print 'Loading file... ', s_fname
	
		# Try to load the pre-saved pickle format binary output
		try:
			hand_main = open(m_fname, 'r')
			hand_sats = open(s_fname, 'r')
			main = pickle.load(hand_main)
			sats = pickle.load(hand_sats)

			n_main = len(main)
			r_sub = 1.5
			n_lg = 2
			n_simu += 1

		except:	
			n_lg = 0

		# The first two are the main LG members
		for i_lg in range(0, n_lg):
			this_lg = main[i_lg]
			this_center = this_lg.x_t()
			this_run = '%02d' % i_lg
			lg_r = this_lg.halo[0].r
			this_mt = this_lg.m_t()

			# Plot mass accretion history of the main halo
			out_mah = outp_path + lg_names[i_lg] + '_main_' + simurun + '_' + subrun + '_mah.png'

			try:
				mass_histories[i_lg, i_sub] = this_mt
			except:		
				sub_skip += 0.5
				print 'MT not found, skipping ', sub_skip

			# For each LG member we are appending subhalo positions and histories
			subs = []; 		n_subs = 0
			subs_xt = []; 		subs_yt = []; 		subs_zt = []
			masses_max = []; 	masses_z0 = [];		

			# This is a loop on all the other haloes stored at z=0
			for i_main in range(n_lg, n_main):
				this_main = main[i_main]
				this_x = this_main.halo[0].x
				this_d = this_lg.halo[0].distance(this_x) 
				dist_rvir = this_d / lg_r

				# This halo is within the range from the virial radius
				if this_d < lg_r * r_sub:
					this_xt = main[i_main].x_t_center(this_center)
					this_mt = main[i_main].m_t()
					n_steps = main[i_main].n_steps
			
					this_sub_z = SubHaloThroughZ(snap_end-snap_init)

					this_sub_z.host = this_lg
					this_sub_z.assign_halo_z(this_main)
					acc_time = this_sub_z.accretion_time()
					m_z0 = this_sub_z.halo[0].m
					n_cross = len(acc_time)
					#print i_main, m_z0/m_sub_min
	
					# This halo actually crossed the main halo's virial radius at some point
					if n_cross > 0:
						n_subs += 1
						first_cross = acc_time[n_cross-1] / 1000.
						(r_min, m_rmin, istep) = this_sub_z.r_min(this_center)
						m_max = this_sub_z.m_max()

						masses_max.append(m_max)
						masses_z0.append(m_z0)

						subs.append(this_sub_z)
						subs_xt.append(this_xt[0, :])
						subs_yt.append(this_xt[1, :])
						subs_zt.append(this_xt[2, :])

						# Check for the number of particle
						if m_max > m_sub_min:
			
						# Stat: (0 = mz0), (1=mmax), (2=n cross), (3=first cross), (4=dist rvir), (5=r_min/rvir), (6=m_rmin), (7=rvir)
							sub_stat = np.zeros((n_sub_stat))
							sub_stat[0] = m_z0
							sub_stat[1] = m_max
							sub_stat[2] = float(n_cross)
							sub_stat[3] = first_cross
							sub_stat[4] = dist_rvir
							sub_stat[5] = r_min/lg_r
							sub_stat[6] = m_rmin
							sub_stat[7] = lg_r

							subs_stats[i_lg].append(sub_stat)
							dyns_stats[i_lg].append(this_xt)

			'''	
				Save informations on subhalo positions through time
			'''
			if do_trajectories == True:
				file_trajectory = outp_path + 'trajectories_lg' + this_run + '_' + simurun + '_' + subrun + '.png'
				plot_trajectory(subs_xt, subs_yt, 'x', 'y', file_trajectory)

			#Planes of satellites in substructure
			for i_snap in range(0, snap_end-snap_init):

				# Only computes the inertia tensor considering satellites above N=min_part particles
				if sats[i_lg][i_snap].n_sub > 5:
					try:
						(evals, red_evals, evecs, red_evecs) = sats[i_lg][i_snap].anisotropy('part', min_part)
						anisotropies[i_lg, i_sub, i_snap] = evals
					except:
						evals = (0, 0, 0)
		
			'''
				Save some informations on most massive subhalo statistics
			'''
			dyn_fname='saved/dyn_stats_'+simurun+'_'+subrun+'.pkl'
			print 'Saving subhalo dynamics to file: ', dyn_fname
			f_dyns = open(dyn_fname, 'w')
			pickle.dump(dyns_stats, f_dyns)

			sub_fname='saved/sub_stats_'+simurun+'_'+subrun+'_mains.pkl'
			print 'Saving subhalo statistics to file: ', sub_fname
			#print simurun, this_run, len(subs_stats[i_lg])
			f_subs = open(sub_fname, 'w')
			pickle.dump(subs_stats, f_subs)

	# The loop on the subrun is over

	# Plot all the subhalo mass function for a given LG run
	if do_plot_mfs == True and i_sub == sub_end-1:
		print 'Plotting mass functions...'
		fout_mwz0 = 'saved/stats_' + simurun + '_' + lg_names[0] + '_mz0_subs.pkl'
		fout_m31z0 = 'saved/stats_' + simurun + '_' + lg_names[1] + '_mz0_subs.pkl'
		fout_mwmax = 'saved/stats_' + simurun + '_' + lg_names[0] + '_mmax_subs.pkl'
		fout_m31max = 'saved/stats_' + simurun + '_' + lg_names[1] + '_mmax_subs.pkl'

		sub_skip = int(sub_skip)

	# Plot mass accretion histories and evolution of satellite anisotropy
	if i_sub == sub_end-1 and do_sub_plots == True:

		for i_lg in range(0, 2):
			out_fname = 'output/anisotropy_' + simurun + '_' + lg_names[i_lg] + '_' + subrun + '_' + this_run + '.png'
			plot_anisotropies(anisotropies, i_lg, sub_end-sub_skip, snap_end, out_fname)

		out_fname = 'output/mah_' + simurun + '_' + lg_names[0] + '.png'
		plot_mass_accretions(time, mass_histories[0, :, :], out_fname)
		out_fname = 'output/mah_' + simurun + '_' + lg_names[1] + '.png'
		plot_mass_accretions(time, mass_histories[1, :, :], out_fname)
		print 'Plotting mass accretions: ', out_fname

'''
	This section computes some GLOBAL statistics, i.e. taking into account all of the LG simulations
'''
if do_all_lgs == True:
	print 'Do all lgs only.'
	n_bins = np.zeros((simu_end-simu_init, 3, 5))
	m_bins = np.zeros((simu_end-simu_init, 3, 5))
	all_masses = [[] for ijk in range(0, 3)] 
	all_n_subs = [[] for ijk in range(0, 3)] 

	#for simurun in simuruns: 
	for i_simu in range(simu_init, simu_end): 
		simurun = simuruns[i_simu]
		these_lgs = []
		these_masses = [[] for ijk in range(0, 3)] 
		these_n_subs = [[] for ijk in range(0, 3)] 

		print 'Loading .pkl files for ', simurun

		for i_sub in range(true_sub_init, true_sub_end):
			this_lg = LocalGroup(simurun)
			subrun = '%02d' % i_sub

			s_fname='saved/'+simurun+'_'+subrun+'_sats.pkl'
			m_fname='saved/'+simurun+'_'+subrun+'_mains_all.pkl'
	
			if do_subs == True:
				sub_fname_mw='saved/sub_stats_'+lg_names[0]+'_'+simurun+'_'+subrun+'_mains.pkl'
				sub_fname_m31='saved/sub_stats_'+lg_names[1]+'_'+simurun+'_'+subrun+'_mains.pkl'

				try:
					f_subs_mw = open(sub_fname_mw, 'r')
					subs_stats_mw = pickle.load(f_subs_mw)
					f_subs_m31 = open(sub_fname_m31, 'r')
					subs_stats_m31 = pickle.load(f_subs_m31)
				except:
					print f_subs_mw
					print f_subs_m31

			# Try to load the pre-saved pickle format binary output
			try:
			#	print 'Loading ', m_fname
				hand_main = open(m_fname, 'r')
				main = pickle.load(hand_main)
				this_lg.init_halos(main[0].halo[0], main[1].halo[0])
				these_lgs.append(this_lg)

				for ijk in range(0, 3):
					if ijk == 2:
						these_masses[ijk].append(main[0].halo[0].m + main[1].halo[0].m)
						these_n_subs[ijk].append(main[0].halo[0].nsub + main[1].halo[0].nsub)
					else:
						these_masses[ijk].append(main[ijk].halo[0].m)
						these_n_subs[ijk].append(main[ijk].halo[0].nsub)

				n_main = len(main)
				r_sub = 1.35
				n_lg = 2
			except:	
				n_lg = 0

		for ijk in range(0, 3):
			all_masses[ijk].append(these_masses[ijk])
			all_n_subs[ijk].append(these_n_subs[ijk])

		(m_bin, n_bin) = bin_lg_sub(these_lgs)
		
		n_bins[i_simu, :, :] = n_bin
		m_bins[i_simu, :, :] = m_bin

	file_m = open(file_m_bins, 'w')
	file_n = open(file_n_bins, 'w')
	file_ms = open(file_masses, 'w')
	file_ns = open(file_n_subs, 'w')

	pickle.dump(m_bins, file_m)
	pickle.dump(n_bins, file_n)
	pickle.dump(all_masses, file_ms)
	pickle.dump(all_n_subs, file_ns)

'''
	PLOT THE THE MASS vs. SATELLITE FLUCTUATIONS 
'''
if do_plots_mass_sub == True:
	file_m = open(file_m_bins, 'r')
	file_n = open(file_n_bins, 'r')
	m_bins = pickle.load(file_m)
	n_bins = pickle.load(file_n)

	tot_bin = simu_end
	
	var_m = np.zeros((tot_bin, 3, 2))
	var_n = np.zeros((tot_bin, 3, 2))
	
	for ibin in range(0, tot_bin):
		for ilg in range(0, 3):
			med_m = m_bins[ibin, ilg, 1]
			min_m = m_bins[ibin, ilg, 0]
			max_m = m_bins[ibin, ilg, 2]

			var_m[ibin, ilg, 0] = abs(med_m - min_m)/med_m
			var_m[ibin, ilg, 1] = abs(med_m - max_m)/med_m

			med_n = n_bins[ibin, ilg, 3]
			min_n = n_bins[ibin, ilg, 0]
			max_n = n_bins[ibin, ilg, 4]

			var_n[ibin, ilg, 0] = abs(med_n - min_n)/med_n
			var_n[ibin, ilg, 1] = abs(med_n - max_n)/med_n

	f_out = 'output/sat_n_bins.png'
	plot_lg_bins(m_bins, n_bins, f_out)

	'''
		NOW PLOT THE HISTOGRAMS OF THE MASS & SATELLITE FLUCTUATIONS WRT THE MEDIAN
	'''
	file_ms = open(file_masses, 'r')
	file_ns = open(file_n_subs, 'r')
	masses = pickle.load(file_ms)
	n_subs = pickle.load(file_ns)

	delta_m = [[] for ijk in range(0, 3)] 
	delta_n = [[] for ijk in range(0, 3)] 

	n_runs = len(n_subs[0])

	for ijk in range(0, 3):
		for i_run in range(0, n_runs):
			this_m_med = np.median(masses[ijk][i_run])
			this_n_med = np.median((n_subs[ijk][i_run]))
			n_lgs = len(masses[ijk][i_run])

			for ilg in range(0, n_lgs):
				#print i_run, n_lgs, this_m_med
				this_ms = abs(masses[ijk][i_run][ilg] - this_m_med) / this_m_med
				this_ns = abs(float(n_subs[ijk][i_run][ilg]) - float(this_n_med)) / this_n_med

				delta_m[ijk].append(this_ms)
				delta_n[ijk].append(this_ns)

	for ijk in range(0, 3):
		print 'MedianDeltaM= %.3f, MeanDeltaM= %.3f' % (np.median(delta_m[ijk]), np.mean(delta_m[ijk]))
		print 'MedianDeltaN= %.3f, MeanDeltaN= %.3f' % (np.median(delta_n[ijk]), np.mean(delta_n[ijk]))

		n_bins = 30

		# Plot Msub difference histograms
		(mny, mbins, mpat) = plt.hist(delta_m[ijk], n_bins)
		fout_m = 'output/hist_' + lg_names[ijk] + '_delta_m.png'
	        plt.rc({'text.usetex': True})
		plt.xlabel('$\Delta M$')
		plt.ylabel('N')
		plt.title(lg_names[ijk])
		plt.savefig(fout_m)
	        plt.clf()
        	plt.cla()
		plt.close()
	
		# Plot Nsub differences histograms
		(nny, nbins, npat) = plt.hist(delta_n[ijk], n_bins)
		fout_n = 'output/hist_' + lg_names[ijk] + '_delta_n.png'	
	        plt.rc({'text.usetex': True})
		plt.xlabel('$\Delta N_{sub}$')
		plt.ylabel('N')
		plt.title(lg_names[ijk])
		plt.savefig(fout_n)
	        plt.clf()
        	plt.cla()
	        
'''
		ANALYSIS OF THE COSMIC WEB
'''
# Output / input filenames for alignment angles et al.
angles_fname = 'saved/all_angles.pkl'

if do_vweb == True:
	print 'Cosmic web computation'

#	read_web_ascii = True
	read_web_ascii = False

	all_e3_angles = np.zeros((2, simu_end))
	all_evals = np.zeros((3, 3, simu_end))
	evals_evecs = np.zeros((4, 3))

	for i_simu in range(simu_init, simu_end):	
		main_run = simuruns[i_simu]
		this_e3_angle = []
		this_e3_deg = []
		this_evals = []

		#TODO look for the XX_XX modes
		for i_sub in range(true_sub_init, true_sub_end):
			
			this_sub = '%02d' % i_sub
			lg_fname = 'saved/lg_' + main_run + '_' + this_sub + '.pkl'
			web_fname = 'saved/web_' + main_run + '_' + this_sub + '.pkl'

			try:
				lg_file = open(lg_fname, 'r')
				this_lg = pickle.load(lg_file)
				this_com = this_lg.get_com()
				search_web = True
			except:
			#	print 'LG data not available at this step.'
				search_web = False
		
			# Read the v-web from the original file
			if read_web_ascii == True and search_web == True:

				# This is triggered only if the v-web file is found
				if search_web == True:
					file_web='/home/eduardo/CLUES/DATA/2048/' + main_run + '/' + this_sub + '/zoom_2048_054.000064.Vweb-ascii'; 
					this_grid = read_vweb(file_web, grid_web, box_web)
					vel = this_grid.velPos(this_com)
					evals = this_grid.evalPos(this_com)
					evecs = this_grid.evecPos(this_com)
					evals_evecs[0, :] = evals
					evals_evecs[1:4, :] = evecs

					print 'Saving evals/evecs at LG position to: ', web_fname
					web_file = open(web_fname, 'w')
					pickle.dump(evals_evecs, web_file)

			# Not reading from an ascii file, loading pkl format 
			else:
				
				try:
					web_file = open(web_fname, 'r')
					evals_evecs = pickle.load(web_file)
					evals = evals_evecs[0, :]
					evecs = evals_evecs[1:4, :]
					search_web = True
				except:	
				#	print 'Webfile not found.'	
					search_web = False
			
			if search_web == True:
				virgo_x = [48000.0, 61000.0, 49000.0]
				to_virgo = vec_subt(virgo_x, this_com)
				virgo_n = vec_norm(to_virgo)
				#print evals[:]
				#print vec_module(to_virgo)
				this_evals.append(evals)
				e3 = evecs[2, :]; ang3 = abs(angle(virgo_n, e3)); 
				this_e3_angle.append(ang3)

					
#		print this_evals[0]
		ang_med = np.median(this_e3_angle)
		ang_std = np.std(this_e3_angle)
		all_e3_angles[0, i_simu] = ang_med
		all_e3_angles[1, i_simu] = ang_std

		print 'Median: %.3f, Stddev: %.3f, Degrees= %.3f' % (ang_med, ang_std, np.arccos(ang_med) * rad2deg())

	f_angles = open(angles_fname, 'w')
	pickle.dump(all_e3_angles, f_angles)

	#print np.median(np.arccos(all_e3_angles[0, 0:6-8])) * rad2deg()

'''
	Analyze subhalo properties in the LSS environment
'''		
# These properties and file names are general regardless of the kind of analysis
step_num = 0
this_step = '%02d' % step_num
anis_pkl = 'saved/percentiles_satellite_anisotropy_'+this_step+'_LG.pkl'	
angles_pkl = 'saved/angles_align_satellite_anisotropy_'+this_step+'_LG.pkl'	
medians_pkl = 'saved/medians_'+this_step+'_LG.pkl'	
nsub_asph_pkl = 'saved/nsub_asph_eval_'+this_step+'_LG.pkl'	

if do_subs_web == True:

	# Selection criteria on subhalos
	m_min = 7.e+8
	t_max = 10.0
	d_max = 0.8

	save_pkl = True
	#save_pkl = False

	lg_perc_anis = [[] for i in range(0, 2)]
	lg_angles_anis = [[] for i in range(0, 3)]

	# Median percentile of asphericity compared to random
	perc_asph = np.zeros((simu_end, 2, 3))
# 10 elements saved: n_subhalos, a/c, vweb-evals, angles web/plane, mass m31/mw, m31/mw position
	nsub_asph_eval = np.zeros((2, simu_end * true_sub_end, 12))	
	i_sub_asph = np.zeros((2))

	median_over_simu = np.zeros((simu_end, 2, 10))  # 10 simulations, 2 LGs, 5 mean values = mass, + angles, a_on_c

	for i_simu in range(simu_init, simu_end):	
		main_run = simuruns[i_simu]

		for i_lg in range(0, 2):
		
			for i_sub in range(true_sub_init, true_sub_end):
		
				subrun = '%02d' % i_sub
				sub_fname='saved/sub_stats_'+main_run+'_'+subrun+'_mains.pkl'
				dyn_fname='saved/dyn_stats_'+main_run+'_'+subrun+'.pkl'
				lg_fname = 'saved/lg_' + main_run + '_' + subrun + '.pkl'
				web_fname = 'saved/web_' + main_run + '_' + subrun + '.pkl'
				min_mz0 = 1.0; min_tacc = 1.0; min_mmax = 1.0

				try:
					print 'Loading pkl files at ', sub_fname, dyn_fname
					f_lg = open(lg_fname, 'r')
					f_web = open(web_fname, 'r')
					f_sub = open(sub_fname, 'r')
					f_dyn = open(dyn_fname, 'r')

					# Stat: (0 = mz0), (1=mmax), (2=n cross), (3=first cross), (4=dist rvir), (5=r_min/rvir), (6=m_rmin), (7=rvir)
					all_sats = pickle.load(f_sub)
					all_dyns = pickle.load(f_dyn)
					this_lg = pickle.load(f_lg)
					vweb = pickle.load(f_web)

					dyns = all_dyns[i_lg]
					sats = all_sats[i_lg]
					nsats = len(sats)
					nselect = 0	

					print 'N substructure in total: ', nsats
					positions = np.zeros((1,3))			
					masses = np.zeros((1))
					all_mass = np.zeros((nsats))
					all_pos	= np.zeros((nsats, 3))

					for isat in range(0, nsats):
						selected = False
						this_sat = sats[isat]
						this_pos = dyns[isat]
						this_mz0 = this_sat[0]
						this_mmax = this_sat[1]
						this_tacc = this_sat[3]
						this_dist = this_sat[4]
			
						if this_mmax > min_mmax:
							min_mmax = this_mmax
							min_tacc = this_tacc
							min_mz0 = this_mz0
			
						all_mass[isat] = 1.0
						all_pos[isat, :] = this_pos[:, step_num]

						if this_dist < d_max and this_mmax > m_min and this_tacc < t_max:
						# 	print 'selected ', nselect, this_tacc, this_mmax, this_dist
							nselect += 1
							selected = True

						if selected == True:
							if nselect == 1:	
								positions[nselect-1, :] = this_pos[:, step_num]
								masses[nselect-1] = 1.0
							else:
								positions.resize((nselect, 3))
								positions[nselect-1, :] = this_pos[:, step_num]
								masses.resize((nselect))
								masses[nselect-1] = 1.0


					# Compute the moment of inertia of all the satellites or only of those accreted before tmax
					(sel_evals, sel_evecs) = moment_inertia(positions, masses)
					(all_evals, all_evecs) = moment_inertia(all_pos, all_mass)

					evs = vweb[0, :] #; ev2 = vweb[2, :]; ev3 = vweb[3, :]
					a_on_c = sel_evals[0]/sel_evals[2]

					#(sel_rand_eval, sel_rand_disp, perc_eval) = random_triaxialities(nselect, n_rand_runs, sel_evals[0]/sel_evals[2])
					rand_evals = random_table_triaxialities(nselect, 10000, True)
					perc_eval = sp.percentileofscore(rand_evals[0, :], a_on_c) 

					lg_perc_anis[i_lg].append(perc_eval)

					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 0] = nselect
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 1] = a_on_c
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 2] = evs[0]
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 3] = evs[1]
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 4] = evs[2]
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 5] = min_tacc
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 6] = min_mmax
					nsub_asph_eval[i_lg, i_sub_asph[i_lg], 7] = min_mz0
	
					#print 'I_web  I_IT  ev * evec  vweb  IM evals'
					for ix in range(1, 4):
						ev = vweb[ix, :]
						for iy in range(0, 1):
							this_angle = abs(angle(ev, sel_evecs[iy, :]))
							lg_angles_anis[ix-1].append(this_angle)		
							nsub_asph_eval[i_lg, i_sub_asph[i_lg], 8+ix] = this_angle
					
					if i_lg == 0:
						nsub_asph_eval[i_lg, i_sub_asph[i_lg], 8] = this_lg.LG1.m
						median_over_simu[i_simu, i_lg, 0] += 1.0
						median_over_simu[i_simu, i_lg, 1] += this_lg.LG1.m 
						median_over_simu[i_simu, i_lg, 2] += nsub_asph_eval[i_lg, i_sub_asph[i_lg], 9] 
						median_over_simu[i_simu, i_lg, 3] += nsub_asph_eval[i_lg, i_sub_asph[i_lg], 10] 
						median_over_simu[i_simu, i_lg, 4] += nsub_asph_eval[i_lg, i_sub_asph[i_lg], 11] 
						median_over_simu[i_simu, i_lg, 5] += a_on_c
						median_over_simu[i_simu, i_lg, 6] += min_mmax
						median_over_simu[i_simu, i_lg, 7] += min_mz0
						median_over_simu[i_simu, i_lg, 8] += min_tacc
					else:
						nsub_asph_eval[i_lg, i_sub_asph[i_lg], 8] = this_lg.LG2.m
						median_over_simu[i_simu, i_lg, 0] += 1.0
						median_over_simu[i_simu, i_lg, 1] += this_lg.LG2.m 
						median_over_simu[i_simu, i_lg, 2] += nsub_asph_eval[i_lg, i_sub_asph[i_lg], 9] 
						median_over_simu[i_simu, i_lg, 3] += nsub_asph_eval[i_lg, i_sub_asph[i_lg], 10] 
						median_over_simu[i_simu, i_lg, 4] += nsub_asph_eval[i_lg, i_sub_asph[i_lg], 11] 
						median_over_simu[i_simu, i_lg, 5] += a_on_c
						median_over_simu[i_simu, i_lg, 6] += min_mmax
						median_over_simu[i_simu, i_lg, 7] += min_mz0
						median_over_simu[i_simu, i_lg, 8] += min_tacc

#median_over_simu = np.zeros((simu_end, 2, 5))  # 10 simulations, 2 LGs, 5 mean values = mass, + angles
							
					i_sub_asph[i_lg] += 1
							
							#print lg_angles_anis
				except:
			#		# Dummy value
					lg_perc_anis[i_lg].append(200.0)
			#		print 'Skipping step ', i_sub, ' / ', main_run	
	
			# clean where the distribution is > 0
			#perc_asph[i_simu, i_lg, 1] = np.median(lg_perc_anis[i_lg])
			#perc_asph[i_simu, i_lg, 0] = np.percentile(lg_perc_anis[i_lg], 10)
			#perc_asph[i_simu, i_lg, 2] = np.percentile(lg_perc_anis[i_lg], 90)
			#print 'Asph: ', i_simu, i_lg, perc_asph[i_simu, i_lg, :]


	# TODO Scatterplot of the subhalos in the inertia tensor frame of reference

	if save_pkl == True:
		f_anis_pkl = open(anis_pkl, 'w')
		f_medians = open(medians_pkl, 'w')
		f_angles_pkl = open(angles_pkl, 'w')
		f_nsub_asph_pkl = open(nsub_asph_pkl, 'w')

		print 'Saving anisotropies to file ', anis_pkl
		pickle.dump(lg_perc_anis, f_anis_pkl)
		pickle.dump(lg_angles_anis, f_angles_pkl)
		pickle.dump(nsub_asph_eval, f_nsub_asph_pkl)
		pickle.dump(median_over_simu, f_medians)
	#print median_over_simu/median_over_simu[:, 0, 0]
			


if do_satellite_anisotropy_plots == True:

	fout_asph_eval = 'output/asph_eval_'+this_step+'.png'	
	fout_anis_all = 'output/hist_percentiles_satellite_anisotropy_'+this_step+'.png'	
	fout_angles_all = 'output/hist_angles_anisotropy_'+this_step+'.png'	
	fout_anis_rand = 'output/satellite_anisotropy_rand_'+this_step+'.png'	
	fout_medians = 'output/medians_'+this_step+'.png'	

	f_nsub_asph_pkl = open(nsub_asph_pkl, 'r')
	f_medians = open(medians_pkl, 'r')
	nsub_asph_eval = pickle.load(f_nsub_asph_pkl)
	medians = pickle.load(f_medians)

	xs = np.zeros((10))
	ys = np.zeros((10))
	use_lg = 0

	for isim in range(0, 10):
		this_n = medians[isim, 0, 0]
		xs[isim] = medians[isim, use_lg, 1] / this_n
		ys[isim] = medians[isim, use_lg, 4] / this_n
			
	#plt.xscale('log')
	#plt.yscale('log')
	plt.scatter(xs, ys)
	plt.show()
	plt.clf()
	plt.cla()

	n_sub_min = 5
	n_sub_max = 140
	n_sub_max1 = 130
	n_sub_max2 = 80
	y_min = 0.0
	y_max = 1.0
	
	'''
	x_subs = np.zeros((n_sub_max - n_sub_min))
	random_subs = np.zeros((3, n_sub_max - n_sub_min))

	for i_sub in range(n_sub_min, n_sub_max):
		rand_evals = random_table_triaxialities(i_sub, 10000, True)
		value_median = np.median(rand_evals[0, :])
		value_perc25 = np.percentile(rand_evals[0, :], 5)
		value_perc75 = np.percentile(rand_evals[0, :], 95)

		x_subs[i_sub-n_sub_min] = i_sub
		random_subs[0, i_sub-n_sub_min] = value_perc25
		random_subs[1, i_sub-n_sub_min] = value_median
		random_subs[2, i_sub-n_sub_min] = value_perc75
		#print value_perc25, value_median, value_perc75

	fig, (ax0, ax1) = plt.subplots(1, 2, sharey=True, figsize=(8,4))
	ax0.axis([n_sub_min, n_sub_max1, y_min, y_max])
	ax1.axis([n_sub_min, n_sub_max2, y_min, y_max])

	ax0.set_xlabel('Nsub')
	ax1.set_xlabel('Nsub')
	ax0.set_ylabel('c/a')

	ax1.set_title('MW')
	ax1.plot(x_subs, random_subs[1, :])
	ax1.fill_between(x_subs, random_subs[0, :], random_subs[2, :], facecolor='azure')
	ax1.scatter(nsub_asph_eval[1, :, 0], nsub_asph_eval[1, :, 1], c='red')

	ax0.set_title('M31')
	ax0.plot(x_subs, random_subs[1, :])
	ax0.fill_between(x_subs, random_subs[0, :], random_subs[2, :], facecolor='yellow')
	ax0.scatter(nsub_asph_eval[0, :, 0], nsub_asph_eval[0, :, 1], c='red')

	plt.tight_layout()
	plt.savefig(fout_anis_rand)
	plt.clf()
	plt.cla()
	'''

	
	'''
		PLOT HISTOGRAMS OF THE MOST MASSIVE SATELLITES
	'''
	n_bins = 40
	f_anis_pkl = open(anis_pkl, 'r')
	lg_perc_anis = pickle.load(f_anis_pkl)

	fig, (ax0, ax1) = plt.subplots(1, 2, sharey=True, figsize=(8,4))
	plt.rc({'text.usetex': True})
	ax0.axis([0, 100, 0, 20])
	ax0.set_xlabel('Percentile')
	ax0.set_ylabel('N')
	ax0.set_title('MW')
	ax0.plot([-1, 101], [5, 5])
	ax0.hist(lg_perc_anis[1], n_bins)

	ax1.axis([0, 100, 0, 20])
	ax1.plot([-1, 101], [5, 5])
	ax1.set_xlabel('Percentile')
	ax1.set_ylabel('N')
	ax1.set_title('M31')
	ax1.hist(lg_perc_anis[0], n_bins)
	
	plt.tight_layout()
	plt.savefig(fout_anis_all)
	plt.clf()
	plt.cla()


	'''
		asphericity versus eigenvalues
	'''
	#ax1.scatter(nsub_asph_eval[1, :, 0], nsub_asph_eval[1, :, 1], c='red')
	#fig, (ax0, ax1) = plt.subplots(1, 2, sharey=True, figsize=(8,4))
	fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(8,4))
	plt.rc({'text.usetex': True})
	ax0.set_title('MW')
	ax0.axis([0.0, 1.0, 1.e+12, 1.e+13])
	#ax0.axis([5.e+11, 6.e+12, 1.e+9, 1.e+12])
	#ax0.axis([5.e+11, 6.e+12, 0, 14])
	#ax0.axis([5.e+11, 6.e+12, 0, 14])
	#x_ev_mw = nsub_asph_eval[0, :, 1]; ax0.set_xlabel('a/c')
	#x_ev_mw = nsub_asph_eval[0, :, 9] + nsub_asph_eval[0, :, 8]; ax0.set_xlabel('$M_{LG}$')
	#x_ev_mw = nsub_asph_eval[0, :, 9]/nsub_asph_eval[0, :, 8]; ax0.set_xlabel('$M_{ratio}$')
	#x_ev_mw = nsub_asph_eval[0, :, 3] + nsub_asph_eval[0, :, 2] + nsub_asph_eval[0, :, 3]; ax0.set_xlabel('$M_{ratio}$')
	x_ev_mw = nsub_asph_eval[0, :, 2] - nsub_asph_eval[0, :, 3]; ax0.set_xlabel('$M_{ratio}$')
	y_ev_mw = nsub_asph_eval[0, :, 8] + nsub_asph_eval[1, :, 8]; ax0.set_ylabel('$M_{sub}$')
	#print y_ev_mw
	#y_ev_mw = nsub_asph_eval[0, :, 3]; ax0.set_ylabel('l2')
	#x_ev_mw = nsub_asph_eval[0, :, 0]; ax0.set_xlabel('N')
	#x_ev_mw = nsub_asph_eval[0, :, 0]; ax0.set_xlabel('N')
	#y_ev_mw = nsub_asph_eval[0, :, 2]; ax0.set_ylabel('l1')
	#ax0.set_xscale('log')
	ax0.set_yscale('log')
	ax0.scatter(x_ev_mw, y_ev_mw)

	#ax1.axis([0, 100, 0, 20])
	#ax1.plot([-1, 101], [5, 5])
	ax1.set_xlabel('l1')
	ax1.set_ylabel('a/c')
	ax1.set_title('M31')
	x_ev_m31 = nsub_asph_eval[1, :, 3]
	y_ev_m31 = nsub_asph_eval[1, :, 3]
	ax1.scatter(x_ev_m31, y_ev_m31) 
	
	plt.tight_layout()
	plt.savefig(fout_asph_eval)
	plt.clf()
	plt.cla()



	'''
		PLOT ANGLES BETWEEN PLANE AND EIGENVALUES
	'''
	#lg_angles_anis[ix-1].append(this_angle)		
	# Plot Nsub differences histograms
	n_bins = 20
	f_angles_pkl = open(angles_pkl, 'r')
	#pickle.dump(lg_angles_anis, f_angles_pkl)
	lg_angles_anis = pickle.load(f_angles_pkl)

	'''
	print lg_angles_anis[0]

	fig, (ax0, ax1, ax2) = plt.subplots(1, 3, sharey=True, figsize=(12,4))
	plt.rc({'text.usetex': True})
	#ax0.axis([0, 1, 0, 1])
	ax0.set_ylabel('N')
	ax0.set_xlabel('|cos|')
	ax0.hist(lg_angles_anis[0], n_bins)

	ax1.set_ylabel('N')
	ax1.set_xlabel('|cos|')
	ax1.hist(lg_angles_anis[1], n_bins)
	
	ax2.set_ylabel('N')
	ax2.set_xlabel('|cos|')
	ax2.hist(lg_angles_anis[2], n_bins)

	plt.tight_layout()
	plt.savefig(fout_angles_all)
	plt.clf()
	plt.cla()

	fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12,4))
	plt.rc({'text.usetex': True})
	plt.rc('font', family='serif')
	ax1.set_xlabel('$\lambda _{1}$')
	ax1.set_ylabel('$|cos|$')
	ax1.scatter(lg_massmax_sat[0], lg_acctime_sat[0], c='blue')
	ax1.scatter(lg_massmax_sat[1], lg_acctime_sat[1], c='red')

	ax2.set_xlabel('$\lambda _{2}$')
	ax2.set_ylabel('$|cos|$')
	ax2.scatter(lg_massz0_sat[0], lg_radmin_sat[0], c='blue')
	ax2.scatter(lg_massz0_sat[1], lg_radmin_sat[1], c='red')

	ax3.set_xlabel('$\lambda _{3}$')
	ax3.set_ylabel('$|cos|$')
	ax3.scatter(lg_massz0_sat[0], lg_acctime_sat[0], c='blue')
	ax3.scatter(lg_massz0_sat[1], lg_acctime_sat[1], c='red')

	plt.tight_layout()
	plt.savefig(fout_massz0_massmax_tacc_radmin)
	plt.clf()
	plt.cla()

	'''

'''
	ONLY LOOK AT SUBHALO STATISTICS for mass, mass at accretion, mass at z=0 etc.

'''
if do_subs_stats == True:

	# Store informations on 
	lg_massmax_sat = [[] for i in range(0, 2)]
	lg_massz0_sat = [[] for i in range(0, 2)]
	lg_acctime_sat = [[] for i in range(0, 2)]
	lg_radmin_sat = [[] for i in range(0, 2)]

	for i_simu in range(simu_init, simu_end):	
		main_run = simuruns[i_simu]

		for i_lg in range(0, 2):		
			for i_sub in range(true_sub_init, true_sub_end):
				mass_max0 = 0.0
				subrun = '%02d' % i_sub
				lg_fname = 'saved/lg_' + main_run + '_' + subrun + '.pkl'
				sub_fname='saved/sub_stats_'+main_run+'_'+subrun+'_mains.pkl'

				try:
				#if do_subs_stats == True:
					print 'Loading pkl file: ', sub_fname
					f_lg = open(lg_fname, 'r')
					f_sub = open(sub_fname, 'r')

					# Stat: (0 = mz0), (1=mmax), (2=n cross), (3=first cross), (4=dist rvir), (5=r_min/rvir), (6=m_rmin), (7=rvir)
					lg_sats = pickle.load(f_sub)
					#print main_run, i_sub, i_lg, len(sats)

					sats = lg_sats[i_lg]
					nsats = len(sats)
					nselect = 0	

					for isat in range(0, nsats):
						this_sat = sats[isat]
						this_mz0 = this_sat[0]
						this_mmax = this_sat[1]
						this_tacc = this_sat[3]
						this_rmin = this_sat[5]
						this_rvir = this_sat[7]
						
						if mass_max0 < this_mmax:
							mass_max0 = this_mmax
							time_acc = this_tacc
							mass_mz0 = this_mz0
							rad_min = this_rmin

					#print '%d) %.3e %.3e %.3f %.3f' % (i_lg, mass_max0, mass_mz0, rad_min, time_acc)

					lg_massmax_sat[i_lg].append(mass_max0)
					lg_massz0_sat[i_lg].append(mass_mz0)
					lg_radmin_sat[i_lg].append(rad_min)
					lg_acctime_sat[i_lg].append(time_acc)
				except:
					Gesu = 'Maiale'

	fout_massz0_massmax_tacc_radmin = 'output/massz0_tacc_massmax_tacc_massmax_radmin.png'	
	fout_hist_acctime = 'output/hist_mass_acctime.png'	
	fout_histmass_max = 'output/hist_mass_max.png'	
	fout_histmass_z0 = 'output/hist_mass_z0.png'	
		
	fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12,4))
	plt.rc({'text.usetex': True})
	plt.rc('font', family='serif')
	ax1.set_xlabel('$M_{\odot}$(z=infall) / $h$')
	ax1.set_ylabel('$T_{acc}$')
	ax1.set_xscale('log')
	ax1.scatter(lg_massmax_sat[0], lg_acctime_sat[0], c='blue')
	ax1.scatter(lg_massmax_sat[1], lg_acctime_sat[1], c='red')

	ax2.set_xlabel('$M_{\odot}$(z=0) / $h$')
	ax2.set_ylabel('$R_{min}$')
	ax2.set_xscale('log')
	ax2.scatter(lg_massz0_sat[0], lg_radmin_sat[0], c='blue')
	ax2.scatter(lg_massz0_sat[1], lg_radmin_sat[1], c='red')

	ax3.set_xlabel('$M_{\odot}$(z=0) / $h$')
	ax3.set_ylabel('$T_{acc}$')
	ax3.set_xscale('log')
	ax3.scatter(lg_massz0_sat[0], lg_acctime_sat[0], c='blue')
	ax3.scatter(lg_massz0_sat[1], lg_acctime_sat[1], c='red')

	plt.tight_layout()
	plt.savefig(fout_massz0_massmax_tacc_radmin)
	plt.clf()
	plt.cla()

	'''
		Max Mass OF LARGEST SATELLITE
	'''
	n_bins = 20
	plt.rc({'text.usetex': True})
	fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(8,4))
	ax1.set_xlabel('$M_{\odot}$ / $h$')
	ax1.set_ylabel('N')
	ax1.axis([1.e+9, 1.e+12, 0, 20])
	ax1.set_title('Max MW sub at accretion time')
	ax1.set_xscale('log')
	ax1.hist(lg_massmax_sat[0], bins=np.logspace(np.log10(1.e+9), np.log10(5.e+11), n_bins))

	plt.rc({'text.usetex': True})
	ax2.axis([1.e+9, 1.e+12, 0, 20])
	ax2.set_xlabel('$M_{\odot}$ / $h$')
	ax2.set_ylabel('N')
	ax2.set_title('Max M31 sub at accretion time')
	ax2.set_xscale('log')
	ax2.hist(lg_massmax_sat[1], bins=np.logspace(np.log10(1.e+9), np.log10(5.e+11), n_bins))
	plt.tight_layout()
	plt.savefig(fout_histmass_max)
	plt.clf()
	plt.cla()

	'''
		z=0 mass OF LARGEST SATELLITE
	'''
	n_bins = 20
	plt.rc({'text.usetex': True})
	fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(8,4))
	ax1.set_xlabel('$M_{\odot}$ / $h$')
	ax1.set_ylabel('N')
	ax1.axis([1.e+9, 1.e+12, 0, 20])
	ax1.set_title('Max MW sub at z=0')
	ax1.set_xscale('log')
	ax1.hist(lg_massz0_sat[0], bins=np.logspace(np.log10(1.e+9), np.log10(5.e+11), n_bins))

	plt.rc({'text.usetex': True})
	ax2.axis([1.e+9, 1.e+12, 0, 20])
	ax2.set_xlabel('$M_{\odot}$ / $h$')
	ax2.set_ylabel('N')
	ax2.set_title('Max M31 sub at z=0')
	ax2.set_xscale('log')
	ax2.hist(lg_massz0_sat[1], bins=np.logspace(np.log10(1.e+9), np.log10(5.e+11), n_bins))
	plt.tight_layout()
	plt.savefig(fout_histmass_z0)
	plt.clf()
	plt.cla()

	'''
		ACCRETION TIME OF LARGEST SATELLITE
	'''
	n_bins = 20
	plt.rc({'text.usetex': True})
	fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(8,4))
	ax1.set_xlabel('$T_{acc}$')
	ax1.set_ylabel('N')
	#ax1.axis([1.e+9, 1.e+12, 0, 20])
	ax1.set_title('MW Accretion time')
	ax1.hist(lg_acctime_sat[0], bins=n_bins) #=np.logspace(np.log10(1.e+9), np.log10(5.e+11), n_bins))

	plt.rc({'text.usetex': True})
	#ax2.axis([1.e+9, 1.e+12, 0, 20])
	#ax2.set_xlabel('$M_{\odot}$ / $h$')
	ax2.set_xlabel('$T_{acc}$')
	ax2.set_ylabel('N')
	ax2.set_title('M31 Accretion time')
	ax2.hist(lg_acctime_sat[1], bins=n_bins) #np.logspace(np.log10(1.e+9), np.log10(5.e+11), n_bins))
	plt.tight_layout()
	plt.savefig(fout_hist_acctime)
	print fout_hist_acctime
	plt.clf()
	plt.cla()





#print lg_perc_anis[1]0
