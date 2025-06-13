#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 16:29:32 2025

@author: cbozonnet
"""
#####################
# All useful functions for envelope processing!
#####################

import numpy as np
import open3d as o3d
import pymeshfix
import pyvista as pv
import os
import csv
from datetime import datetime

def read_from_txt(filepath):
    """
    Load a point cloud from a text file.

    Parameters
    ----------
    filepath : str
        Path to the text file containing the point cloud data.

    Returns
    -------
    o3d.geometry.PointCloud
        A point cloud object with coordinates and colors.
    """
    data = np.loadtxt(filepath) # Load the point cloud from the text file using numpy
    xyz = data[:,:3] # Extract point cloud coordinates
    rgb = data[:,3:6]/255 # Get point cloud original colors. Must be rescaled in [0,1]!

    # Point cloud creation
    pcd = o3d.geometry.PointCloud() # Initialize a point cloud object
    pcd.points = o3d.utility.Vector3dVector(xyz) # Convert numpy coordinates to open3d format
    pcd.colors = o3d.utility.Vector3dVector(rgb) # Add colors
    return pcd

def o3d_to_pyvista(o3d_mesh):
    """
    Converts an Open3D TriangleMesh to a PyVista PolyData mesh.

    Parameters
    ----------
    o3d_mesh : open3d.geometry.TriangleMesh
        The Open3D mesh to convert.

    Returns
    -------
    pv.PolyData
        The converted mesh in PyVista format.
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
    Repairs a non-manifold Open3D mesh using PyMeshfix.
    Extracts data from the Open3D mesh, uses PyMeshfix to repair the mesh if non-manifold (not watertight),
    computes statistics (area, volume) and returns them along with the repaired Open3D mesh.

    Parameters
    ----------
    o3d_mesh : open3d.geometry.TriangleMesh
        The Open3D mesh to repair.

    Returns
    -------
    tuple
        A tuple containing the repaired Open3D mesh, volume, and area.
    """

    v = np.asarray(o3d_mesh.vertices) # Extract vertices
    f = np.asarray(o3d_mesh.triangles) # Extract faces

    # Create PolyData mesh
    f_pv = np.hstack([np.full((f.shape[0], 1), 3), f]).flatten()
    mesh_pv = pv.PolyData(v, f_pv)

    if mesh_pv.is_manifold:
        vol = mesh_pv.volume
        area = mesh_pv.area
        print(f"\nVolume [m3]: {vol}")
        print(f"\nArea [m2]: {area}")

        return o3d_mesh, vol, area # Nothing to change
    else:
        # Create Pymesh object
        tin = pymeshfix.PyTMesh()
        tin.load_array(v, f) # Load known vertices and faces

        # Fill holes (check other mesh cleaning options on pymesh API)
        tin.fill_small_boundaries()
        vclean, fclean = tin.return_arrays() # Get new vertices and faces

        # Convert faces to PyVista format
        fclean_pv = np.hstack([np.full((fclean.shape[0], 1), 3), fclean]).flatten()

        # Create new PolyData mesh
        mesh_repaired = pv.PolyData(vclean, fclean_pv)

        # CHECK IF WATERTIGHT AND COMPUTE STATS
        if mesh_repaired.is_manifold:
            vol = mesh_repaired.volume
            area = mesh_repaired.area
            print(f"\nVolume [m3]: {vol}")
            print(f"\nArea [m2]: {area}")
        else:
            print("\nFAILED TO CREATE A MANIFOLD MESH")
            vol = 0.0; area = 0.0

        # Create new Open3D mesh
        o3d_repaired = o3d.geometry.TriangleMesh()

        # Add vertices and triangles
        o3d_repaired.vertices = o3d.utility.Vector3dVector(vclean)
        o3d_repaired.triangles = o3d.utility.Vector3iVector(fclean)

        # Optionally compute normals (for better visualization)
        o3d_repaired.compute_vertex_normals()

        return o3d_repaired, vol, area

def create_alpha_shape(point_cloud, alpha_value):
    """
    Creates an alpha shape from a point cloud.

    Parameters
    ----------
    point_cloud : open3d.geometry.PointCloud
        The point cloud from which to create the alpha shape.
    alpha_value : float
        Alpha value for creating the alpha shape.

    Returns
    -------
    open3d.geometry.TriangleMesh
        The triangular mesh representing the alpha shape.
    """
    alpha_shape = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(point_cloud, alpha_value)
    alpha_shape.compute_vertex_normals()
    return alpha_shape

def check_envelop_accuracy(point_cloud, mesh):
    """
    Checks how many points of the point cloud are within the surface defined by the mesh.

    Parameters
    ----------
    point_cloud : open3d.geometry.PointCloud
        The point cloud to check.
    mesh : open3d.geometry.TriangleMesh
        The triangular mesh defining the surface.

    Returns
    -------
    tuple
        A tuple containing the ratio of points within the mesh and the number of sub-meshes.
    """
    # Create PyVista mesh from Open3D
    mesh_pv = o3d_to_pyvista(mesh)

    # Get point cloud into PyVista format
    points_poly = pv.PolyData(np.asarray(point_cloud.points))

    # Check intersection
    intersect = points_poly.select_enclosed_points(mesh_pv, check_surface=True, progress_bar=False)

    # Compute ratio
    ratio = np.mean(intersect['SelectedPoints']) * 100

    # Split meshes to detect multiple envelopes
    sub_meshes = mesh_pv.split_bodies()
    n_mesh = len(sub_meshes)

    return ratio, n_mesh

def z_project(points, alpha):
    """
    Projects points onto a constant z plane and creates a 2D Delaunay surface.

    Parameters
    ----------
    points : numpy.ndarray
        The points to project.
    alpha : float
        Alpha value for Delaunay triangulation.

    Returns
    -------
    tuple
        A tuple containing the Open3D mesh of the projected surface and the projected area.
    """
    # Compute projection plane z location
    z_const = 0.0
    points[:, 2] = z_const # Project point cloud

    # Create a point cloud object
    cloud = pv.PolyData(points)

    # 2D Delaunay with the same alpha value
    surf = cloud.delaunay_2d(alpha=alpha)

    # Get surface
    projected_area = surf.area

    # Get corresponding Open3D mesh
    o3d_surf = o3d.geometry.TriangleMesh()

    # Add vertices and triangles
    o3d_surf.vertices = o3d.utility.Vector3dVector(surf.points)
    o3d_surf.triangles = o3d.utility.Vector3iVector(surf.faces.reshape(-1, 4)[:, 1:])

    # Optionally compute normals (for better visualization)
    o3d_surf.compute_vertex_normals()

    return o3d_surf, projected_area

def write_results_to_csv(results, output_file_name):
    """
    Writes the results dictionary to a CSV file with a timestamp.

    Parameters
    ----------
    results : dict
        A dictionary containing the results to be written to the CSV file.
        Expected keys are 'filename', 'alpha', 'Envelope volume [m3]',
        'Envelope area [m2]', 'projected_area [m2]', 'Enveloppe accuracy', and 'Number of envelopes'.
    output_file_name : str
        The name of the output CSV file.

    Returns
    -------
    None
    """
    # Determine if the file exists to decide whether to write headers
    file_exists = os.path.isfile(output_file_name)

    # Open the file in append mode
    with open(output_file_name, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['date'] + list(results.keys()))

        # Write the header if the file does not exist
        if not file_exists:
            writer.writeheader()

        # Prepare the row to be written
        row = {'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        row.update(results)

        # Write the row
        writer.writerow(row)

    print(f"Results have been written to {output_file_name}")