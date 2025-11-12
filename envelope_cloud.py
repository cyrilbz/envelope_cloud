#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 11:02:49 2025

@author: cbozonnet
"""
########################################################################
#### Computation of point cloud envelopes through alpha shape ##########
####-> mesh, envelope volume, area, projected area, accuracy,... #######
####    WORKS ON .TXT FILES ONLY - MIGHT BE MODIFIED EASILY      #######
########################################################################

########################## Inputs ##############################
# relative or absolute path to the directory containing files to study
directory = './test_data' 
alpha=0.2
minimal_distance = 0.035
output_file_name = 'results.csv' # written in "directory"
plot_results = True # option to plot results using open3d
################################################################

import os
os.environ['XDG_SESSION_TYPE'] = 'x11' # important to get open3d viewer to work on Linux
import open3d as o3d
from functions import (read_from_txt, write_results_to_csv,
                        create_alpha_shape, repair_non_manifold_o3d_mesh,
                        check_envelop_accuracy, z_project)
import numpy as np

#################### Extract all .txt file names #############

# Llist all file in the directory
file_list = os.listdir(directory)

# filter txt files
# file_list_txt = [f for f in file_list if f.endswith('.txt')]

# or provide them directly as a list
file_list_txt = ['Cloud1.txt']

################### Main loop ##################################
for file in file_list_txt:
    file_path = os.path.join(directory, file)
    print(f"FILE: : {file}")
    
    ############### Data extraction ##################
    
    pcd = read_from_txt(file_path) # returns open3d point cloud
    print(f"Original file has {len(pcd.points)} points")
    
    pcd_complete = o3d.geometry.PointCloud(pcd) # save the original point cloud
    
    # Downsample following a given voxel grid 
    pcd = pcd.voxel_down_sample(voxel_size=minimal_distance)
    print(f"After voxel down sampling: {len(pcd.points)} points")
    
    ################## alpha shape ###################
    
    print(f"\n ALPHA VALUE [-] : {alpha}")
    
    # using open3d built-in function
    o3d_alpha = create_alpha_shape(pcd, alpha)
    
    # Print initial stats
    print("Before cleaning:")
    print(f"  Vertices: {len(o3d_alpha.vertices)}")
    print(f"  Triangles: {len(o3d_alpha.triangles)}")
    
    #################### repair  mesh ######################
    
    repaired_o3d_alpha = o3d.geometry.TriangleMesh(o3d_alpha) # copy mesh for safety
    repaired_o3d_alpha, volume, area = repair_non_manifold_o3d_mesh(o3d_alpha)
    
    # Print stats after cleaning
    print("\nAfter cleaning:")
    print(f"  Vertices: {len(repaired_o3d_alpha.vertices)}")
    print(f"  Triangles: {len(repaired_o3d_alpha.triangles)}")
    
    #### Compute accuracy of the envelope regarding original cloud ####
    
    ratio, n_meshes = check_envelop_accuracy(pcd_complete, repaired_o3d_alpha)
    print(f"\n ALPHA SHAPE ACCURACY [%] : {ratio}")
    print(f"\n NUMBER OF MESHES [-] : {n_meshes}")
    
    # #################### 2D projection #####################
    
    # project the reduced point cloud "pcd" (can be changed to "pcd_complete")
    copy_pcd = o3d.geometry.PointCloud(pcd) # copy for safety 
    o3d_surf, projected_area = z_project(np.asarray(copy_pcd.points), alpha)
    print(f"\n PROJECTED AREA ON THE GROUND [m2] : {projected_area}")
    
    # #################### save alpha shape as .obj #######################
    
    # Extract file base name
    base_name = os.path.splitext(file_path)[0]
    
    # output mesh filename
    obj_name = f"{base_name}_alpha_shape_{alpha}.obj"
    
    # write
    o3d.io.write_triangle_mesh(obj_name, repaired_o3d_alpha)  # OBJ format
    
    ################### gather results and save ####################
    
    results = {
        'filename': file_path,
        'alpha': alpha,
        'Envelope volume [m3]': volume,
        'Envelope area [m2]': area,
        'projected_area [m2]': projected_area,
        'Enveloppe accuracy': ratio,
        'Number of envelopes': n_meshes
    }
    
    # write results
    output_path = os.path.join(directory, output_file_name)
    write_results_to_csv(results, output_path)
    
    ############### plots using open3d ###########################
    
    if plot_results:
        print("PLOTTING OPTION ACTIVATED - CLOSE OPEN3D WINDOW TO ANALYZE THE NEXT FILE")
        geoms = [{"name":"Point cloud", "geometry": pcd},
                 {"name":"Repaired Alpha shape", "geometry": repaired_o3d_alpha},
                 {"name":"Projected area", "geometry": o3d_surf}]
        
        o3d.visualization.draw(geoms, show_ui=True)
