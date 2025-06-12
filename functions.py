#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 16:29:32 2025

@author: cbozonnet
"""
#####################
# all useful functions for envelope stuff!
#####################

import numpy as np
import open3d as o3d
import pymeshfix
import pyvista as pv

def read_from_txt(filepath):
    data = np.loadtxt(filepath) #Load the point cloud from the text file using numpy
    xyz = data[:,:3] # extract point cloud coordinates
    rgb = data[:,3:6]/255 # get point cloud original colors.  Must be rescaled in [0,1] !
    
    # point cloud creation
    pcd = o3d.geometry.PointCloud() # initialize a point cloud object
    pcd.points = o3d.utility.Vector3dVector(xyz) # convert numpy coord to open3d format
    pcd.colors = o3d.utility.Vector3dVector(rgb) # add colors
    return pcd

def o3d_to_pyvista(o3d_mesh):
    """
    Converts an Open3D TriangleMesh to a PyVista PolyData mesh.
    """
    # Extract vertices and triangles
    verts = np.asarray(o3d_mesh.vertices)
    faces = np.asarray(o3d_mesh.triangles)

    # PyVista expects a flattened array for faces:
    # [3, v0, v1, v2, 3, v0, v1, v2, ...]
    faces_pv = np.hstack([np.full((faces.shape[0], 1), 3), faces]).flatten()

    # Create a PyVista PolyData mesh
    mesh_pv = pv.PolyData(verts, faces_pv)

    return mesh_pv

def repair_non_manifold_o3d_mesh(o3d_mesh):
    """
    This function repairs an open3d mesh using PyMeshfix.
    -> extract data from o3d mesh
    -> use PyMeshfix to repair the mesh if non-manifold (= not watertight) 
    -> compute stats (area, volume) and print them
    -> returns an o3d mesh
    """
    
    v = np.asarray(o3d_mesh.vertices) # extract vertices
    f = np.asarray(o3d_mesh.triangles) # extract  faces
    
    # Create PolyData mesh
    f_pv = np.hstack([np.full((f.shape[0], 1), 3), f]).flatten()
    mesh_pv = pv.PolyData(v, f_pv)
    
    if mesh_pv.is_manifold:
        #print("\n ORIGINAL MESH IS MANIFOLD")
        vol = mesh_pv.volume
        area = mesh_pv.area
        print(f"\n Volume [m3]: {vol}")
        print(f"\n Area [m2]: {area}") 
        
        return o3d_mesh, vol, area # nothing to change
    else: 
        #print("\n TRYING TO REPAIR THE MESH")
        # Create Pymesh object
        tin = pymeshfix.PyTMesh()
        tin.load_array(v, f) # load known vertices and faces
        
        # Fill holes (check other mesh cleaning options on pymesh API)
        #print('Before cleaning: There are {:d} boundaries'.format(tin.boundaries()))
        tin.fill_small_boundaries()
        #print('After cleaning: there are {:d} boundaries'.format(tin.boundaries()))
        vclean, fclean = tin.return_arrays() # get new vertices and faces
        
        # Convert faces to PyVista format
        fclean_pv = np.hstack([np.full((fclean.shape[0], 1), 3), fclean]).flatten()

        # Create new PolyData mesh
        mesh_repaired = pv.PolyData(vclean, fclean_pv)
        
        # CHECK IF WATERTIGHT AND COMPUTE STATS
        if mesh_repaired.is_manifold:
            #print("\n REPAIRED MESH IS NOW MANIFOLD")
            vol = mesh_repaired.volume
            area = mesh_repaired.area
            print(f"\n Volume [m3]: {vol}")
            print(f"\n Area [m2]: {area}") 
        else:
            print("\n FAILED TO CREATE A MANIFOLD MESH")
            vol = 0.0 ; area = 0.0
            
        # create new open3d mesh
        o3d_repaired = o3d.geometry.TriangleMesh()

        # Add vertices and triangles
        o3d_repaired.vertices = o3d.utility.Vector3dVector(vclean)
        o3d_repaired.triangles = o3d.utility.Vector3iVector(fclean)

        # Optionally compute normals (for better visualization)
        o3d_repaired.compute_vertex_normals()

        return o3d_repaired, vol, area

def create_alpha_shape(point_cloud, alpha_value):
    alpha_shape = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(point_cloud, alpha_value)
    alpha_shape.compute_vertex_normals()
    return alpha_shape

def check_envelop_accuracy(point_cloud, mesh):
    """
    This function checks how many points of the point cloud 
    are within the surface defined by the mesh.

    Parameters
    ----------
    point_cloud : OPEN3D point cloud type
    mesh : OPEN3D Triangular mesh

    Returns
    -------
    ratio : the amount of point clouds within the mesh

    """
    # create Polyvista mesh from open3d
    mesh_pv = o3d_to_pyvista(mesh)
    
    # get point cloud into Pyvista format
    points_poly = pv.PolyData(np.asarray(point_cloud.points))
    
    # check intersection
    intersect = points_poly.select_enclosed_points(mesh_pv, check_surface = True, progress_bar = False)

    # Compute ratio
    ratio = np.mean(intersect['SelectedPoints'])*100
    
    # split meshes to detect multiple envelope
    sub_meshes = mesh_pv.split_bodies()
    n_mesh = len(sub_meshes)
    
    return ratio, n_mesh
    
def z_project(points,alpha):
    
    # compute projection plane z location
    z_const = 0.0
    points[:,2] = z_const # project point cloud

    # # Create a point cloud object
    cloud = pv.PolyData(points)
    
    # 2d Delaunay with same alpha value
    surf = cloud.delaunay_2d(alpha=alpha)

    # get surface    
    projected_area = surf.area
    
    # get corresponding o3d mesh
    o3d_surf = o3d.geometry.TriangleMesh()

    # Add vertices and triangles
    o3d_surf.vertices = o3d.utility.Vector3dVector(surf.points)
    o3d_surf.triangles = o3d.utility.Vector3iVector(surf.faces.reshape(-1, 4)[:, 1:])

    # Optionally compute normals (for better visualization)
    o3d_surf.compute_vertex_normals()
    
    return o3d_surf, projected_area
    
    
    
    
    