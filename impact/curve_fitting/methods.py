"""
Methods for curve fitting
"""

from .core import CurveFitObject
import numpy as np

keys = ['name', 'guess', 'min', 'max', 'vary']
curve_fit_dict = {}

"""
Generalized logistic
"""
def generalized_logistic(t, A, k, C, Q, K, nu):
    return A + ( (K - A) / (np.power((C + Q * np.exp(-k * t)), (1 / nu))))
curve_fit_dict['productionEquation_generalized_logistic'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 50, lambda data: 0.001, 1000, True])),
     dict(zip(keys, ['C', 1, None, None, True])),
     dict(zip(keys, ['Q', 0.01, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 1, None, None, True]))],
    generalized_logistic,
)
curve_fit_dict['growthEquation_generalized_logistic'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 0.5, lambda data: 0.001, 1, True])),
     dict(zip(keys, ['C', 1, None, None, True])),
     dict(zip(keys, ['Q', 0.01, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 1, None, None, True]))],
    generalized_logistic
)

curve_fit_dict['growthEquation_generalized_logistic_2'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     # starting titer
     dict(zip(keys, ['k', 1, 0, 2, True])),  # Growth fit_params
     dict(zip(keys, ['C', 1, None, None, False])),
     dict(zip(keys, ['Q', 0.5, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 0.5, None, None, True]))],
    generalized_logistic,
    method='leastsq'
)

"""
janoschek
"""
def janoschek(t, B, k, L, delta): return L - (L - B) * np.exp(-k * np.power(t, delta))
curve_fit_dict['janoschek'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 0.5, lambda data: 0.001, 200, True])),
     dict(zip(keys, ['delta', 1, -100, 100, True])),
     dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
    janoschek,
    method='nelder'
)

"""
5-param Richard's
http://www.pisces-conservation.com/growthhelp/index.html?richards_curve.htm
"""
def richard_5(t, B, k, L, t_m, T): return B + L / np.power(1 + T * np.exp(-k * (t - t_m)), (1 / T))
curve_fit_dict['richard_5'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 0.5, 0.001, None, True])),
     dict(zip(keys, ['t_m', 10, None, None, True])),
     dict(zip(keys, ['T', 1, None, None, True])),
     dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
    richard_5,
    # method='slsqp'
)

"""
Gompertz growth equation
http://www.ncbi.nlm.nih.gov/pmc/articles/PMC184525/pdf/aem00087-0379.pdf
"""
def gompertz(t, A, growth_rate, lam):
    return A * np.exp(-np.exp(growth_rate * np.e / A * (lam - t)))
curve_fit_dict['gompertz'] = CurveFitObject(
    [dict(zip(keys, ['A', np.max, lambda data: 0.975 * np.max(data), lambda data: 1.025 * np.max(data), True])),
     dict(zip(keys, ['growth_rate', 1, 0, 5, True])),
     dict(zip(keys, ['lam', 0, 0, lambda data:np.min(data)*0.95, True]))],
    gompertz,
    method='slsqp'
)
