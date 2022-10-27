import numpy as np
import inspect
from napari.types import  PointsData

from .._stress import lebedev_info_SPB as lebedev_info

def _sigmoid(array: np.ndarray, center:float, amplitude:float, slope:float, offset:float):
    """
    Sigmoidal fit function
    https://stackoverflow.com/questions/55725139/fit-sigmoid-function-s-shape-curve-to-data-using-python
    """
    return amplitude / (1 + np.exp(-slope*(array-center))) + offset

def _gaussian(array: np.ndarray, center:float, sigma:float, amplitude:float):
    """
    Gaussian normal fit function
    https://en.wikipedia.org/wiki/Normal_distribution
    """
    return amplitude/np.sqrt((2*np.pi*sigma**2)) * np.exp(-(array - center)**2 / (2*sigma**2))

def _detect_maxima(array: np.ndarray, center: float = None):
    """
    Function to find the maximum's index of data with a single peak.
    """
    return np.argmax(array)

def _detect_max_gradient(array: np.ndarray, center: float = None):
    """
    Function to find the location of the steepest gradient for sigmoidal data
    """
    return np.argmax(np.diff(array))

def _function_args_to_list(function: callable) -> list:

    sig = inspect.signature(function)
    return list(sig.parameters.keys())

def Least_Squares_Harmonic_Fit(fit_degree: int,
                               points_ellipse_coords: tuple,
                               input_points: np.ndarray,
                               expansion_type='cartesian') -> np.ndarray:
    """
    Perform least squares harmonic fit on input points.

    Parameters
    ----------

    fit_degree: int
    points_ellipse_coords: tuple
        Input points in elliptical coordinates - required least squares
        fit to find ellipsoid major/minor axes
    input_points:
        Values to be expanded on the surface. Can be cartesian point coordinates
        (x/y/z) or radii for a radial expansion.
    expansion_type: str
        Type of expansion to be performed. Default is 'cartesian'.

    Returns
    -------
    coefficients: np.ndarray
        Numpy array holding spherical harmonics expansion coefficients. The size
        on the type of expansion (cartesian or radial).
    """

    U, V = points_ellipse_coords[0], points_ellipse_coords[1]

    All_Y_mn_pt_in = []

    for n in range(fit_degree + 1):
        for m in range(-1*n, n+1):
            Y_mn_coors_in = []
            Y_mn_coors_in = lebedev_info.Eval_SPH_Basis(m, n, U, V)
            All_Y_mn_pt_in.append(Y_mn_coors_in)

    if expansion_type == 'cartesian':
        All_Y_mn_pt_in_mat = np.hstack(( All_Y_mn_pt_in ))
        coefficients_x1 = np.linalg.lstsq(All_Y_mn_pt_in_mat, input_points[:, 0])[0]
        coefficients_x2 = np.linalg.lstsq(All_Y_mn_pt_in_mat, input_points[:, 1])[0]
        coefficients_x3 = np.linalg.lstsq(All_Y_mn_pt_in_mat, input_points[:, 2])[0]

        return np.vstack([coefficients_x1, coefficients_x2, coefficients_x3]).transpose()

    if expansion_type == 'radial':
        coefficients_r = np.linalg.lstsq(All_Y_mn_pt_in_mat, input_points)[0]
        return coefficients_r
        

