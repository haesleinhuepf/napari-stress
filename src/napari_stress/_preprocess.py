# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 17:18:26 2021

@author: johan
"""

from skimage.transform import rescale
from ._surface import fibonacci_sphere
from skimage import filters, measure

import pandas as pd
import numpy as np
import vedo

import tqdm


def preprocessing(image: np.ndarray,
                  vsx: float,
                  vsy: float,
                  vsz: float,
                  res_mode: str = 'high'):
    """
    Preprocesses an input 3D image for further processing. Preprocessing includes
    resampling to isotropic voxels.

    Parameters
    ----------
    image : ndarray
        3/4D image array with intensity values in each pixel
    vsx : float, optional
        pixel size in x-dimension. Default value: vsx = 2.076
    vsx : float, optional
        pixel size in x-dimension. Default value: vsx = 2.076
    vsx : float, optional
        pixel size in x-dimension. Default value: vsx = 3.998

    Returns
    -------
    image : MxNxK array
        binary image

    """
    image_resampled = []
    mask_resampled = []

    # resample every timepoint
    for t in range(image.shape[0]):
        _image_resampled = resample(image[t], vsx=vsx, vsy=vsy, vsz=vsz)
        _mask_resampled = threshold(_image_resampled, threshold=0.2)

        image_resampled.append(_image_resampled)
        mask_resampled.append(_mask_resampled)

    mask_resampled = np.asarray(mask_resampled)
    image_resampled = np.asarray(image_resampled)

    return image_resampled, mask_resampled


def fit_ellipse_4D(binary_image: np.ndarray,
                   n_rays: np.uint16):

    n_frames = binary_image.shape[0]

    # Fit ellipse
    pts = np.zeros([n_rays * n_frames, 4])
    for t in range(n_frames):
        _pts = fit_ellipse(binary_image=binary_image[t])
        pts[t * n_rays : (t + 1) * n_rays, 1:] = _pts
        pts[t * n_rays : (t + 1) * n_rays, 0] = t

    return pts

def fit_ellipse(binary_image: np.ndarray,
                n_samples: np.uint16 = 256) -> list:
    """
    Fit an ellipse to a binary image.

    Parameters
    ----------
    binary_image : np.ndarray
        DESCRIPTION.
    n_samples : np.uint16, optional
        DESCRIPTION. The default is 256.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    if not len(binary_image.shape) == 4:
        binary_image = binary_image[None, :]
    
    # Allocate points
    n_frames = binary_image.shape[0]
    pts = []

    for t in range(n_frames):

        _binary_image = binary_image[t]
        props = measure.regionprops_table(_binary_image,
                                          properties=(['centroid']))
        CoM = [props['centroid-0'][0],
               props['centroid-1'][0],
               props['centroid-2'][0]]
    
        # Create coordinate grid:
        ZZ, YY, XX = np.meshgrid(np.arange(_binary_image.shape[0]),
                                  np.arange(_binary_image.shape[1]),
                                  np.arange(_binary_image.shape[2]), indexing='ij')
    
        # Substract center of mass and mask
        ZZ = (ZZ.astype(float) - CoM[0]) * _binary_image
        YY = (YY.astype(float) - CoM[1]) * _binary_image
        XX = (XX.astype(float) - CoM[2]) * _binary_image
    
        # Concatenate to single (Nx3) coordinate vector
        ZYX = np.vstack([ZZ.ravel(), YY.ravel(), XX.ravel()]).transpose((1, 0))
    
        # Calculate orientation matrix
        S = 1/np.sum(_binary_image) * np.dot(ZYX.conjugate().T, ZYX)
        D, R = np.linalg.eig(S)
    
        # # get angles from rotation matrix: http://planning.cs.uiuc.edu/node103.html
        # alpha = np.arctan(R[1,0]/R[0,0])/np.pi*180
        # beta = np.arctan(-R[2, 0]/np.sqrt(R[2,1]**2 + R[2,2]**2))/np.pi*180
        # gamma = np.arctan(R[2,1]/R[2,2])/np.pi*180
    
        # Now create points on the surface of an ellipse
        props = pd.DataFrame(measure.regionprops_table(_binary_image, properties=(['major_axis_length', 'minor_axis_length'])))
        semiAxesLengths = [props.loc[0].minor_axis_length/2,
                           props.loc[0].major_axis_length/2,
                           props.loc[0].major_axis_length/2]
        _pts = fibonacci_sphere(semiAxesLengths, R.T, CoM, samples=n_samples)
        pts.append(vedo.pointcloud.Points(_pts))

    return pts

def resample(image, vsx, vsy, vsz, res_mode='high'):
    """
    Resamples an image with anistropic voxels of size vsx, vsy and vsz to isotropic
    voxel size of smallest or largest resolution
    """
    # choose final voxel size
    if res_mode == 'high':
        vs = np.min([vsx, vsy, vsz])

    elif res_mode == 'low':
        vs = np.max([vsx, vsy, vsz])

    factor = np.asarray([vsz, vsy, vsx])/vs
    image_rescaled = rescale(image, factor, anti_aliasing=True)

    return image_rescaled

def threshold(image, threshold = 0.2, **kwargs):

    sigma = kwargs.get('sigma', 1)

    # Masking
    image = filters.gaussian(image, sigma=sigma)
    mask = measure.label(image > threshold*image.max())

    return mask

# def fit_curvature():
#     """
#     Find curvature for every point
#     """

#     print('\n---- Curvature-----')
#     curv = []
#     for idx, point in tqdm.tqdm(self.points.iterrows(), desc='Measuring mean curvature', total=len(self.points)):
#         sXYZ, sXq = surface.get_patch(self.points, idx, self.CoM)
#         curv.append(curvature.surf_fit(sXYZ, sXq))

#     self.points['Curvature'] = curv
#     self.points = surface.clean_coordinates(self)

#     # Raise flags for provided data
#     self.has_curv = True
