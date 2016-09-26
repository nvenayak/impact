"""
Functions for curve fitting
"""

import numpy as np
from lmfit import Model

class CurveFitObject(object):
    """
    Wrapper for curve fitting objects

    Parameters:
        paramList: List of parameters, with initial guess, max and min values
            Each parameter is a dict with the following form
                {'name': str PARAMETER NAME,

                'guess': float or lambda function

                'max': float or lambda function

                'min': float or lambda function

                'vary' True or False}

        growthEquation: A function to fit with the following form:
            def growthEquation(t, param1, param2, ..): return f(param1,param2,..)

        method: lmfit method (slsqp, leastsq)
    """

    def __init__(self, paramList, growthEquation, method='slsqp'):
        self.paramList = paramList
        self.growthEquation = growthEquation
        self.gmod = Model(growthEquation)
        self.method = method

    def calcFit(self, t, data, method='leastsq', **kwargs):
        # print('befor: ', method)
        if method is None: method = method
        # print('after: ', method)
        for param in self.paramList:
            # print(param)
            # Check if the parameter is a lambda function
            temp = dict()
            for hint in ['guess', 'min', 'max']:
                # print('hint: ',hint,'param[hint]: ',param[hint])
                if type(param[hint]) == type(lambda x: 0):
                    temp[hint] = param[hint](data)
                else:
                    temp[hint] = param[hint]
            self.gmod.set_param_hint(param['name'],
                                     value=temp['guess'],
                                     min=temp['min'],
                                     max=temp['max'],
                                     vary=param['vary'])
            # gmod.print_param_hints()

        try:
            params = self.gmod.make_params()
        except Exception as e:
            # gmod.print_param_hints()
            print(data)
            print(e)

        result = self.gmod.fit(data, params, t=t, method=method, **kwargs)
        return result


curve_fit_dict = {}
# curve_fit_types =


keys = ['name', 'guess', 'min', 'max', 'vary']

def growthEquation_generalized_logistic(t, A, k, C, Q, K, nu): return A + (
    (K - A) / (np.power((C + Q * np.exp(-k * t)), (1 / nu))))


curve_fit_dict['growthEquation_generalized_logistic'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 0.5, lambda data: 0.001, 1, True])),
     dict(zip(keys, ['C', 1, None, None, True])),
     dict(zip(keys, ['Q', 0.01, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 1, None, None, True]))],
    growthEquation_generalized_logistic
)

curve_fit_dict['growthEquation_generalized_logistic_2'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     # starting titer
     dict(zip(keys, ['k', 1, 0, 2, True])),  # Growth fit_params
     dict(zip(keys, ['C', 1, None, None, False])),
     dict(zip(keys, ['Q', 0.5, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 0.5, None, None, True]))],
    growthEquation_generalized_logistic,
    method='leastsq'
)


def productionEquation_generalized_logistic(t, A, k, C, Q, K, nu): return A + (
    (K - A) / (np.power((C + Q * np.exp(-k * t)), (1 / nu))))


curve_fit_dict['productionEquation_generalized_logistic'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 50, lambda data: 0.001, 1000, True])),
     dict(zip(keys, ['C', 1, None, None, True])),
     dict(zip(keys, ['Q', 0.01, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 1, None, None, True]))],
    productionEquation_generalized_logistic,
)


def janoschek(t, B, k, L, delta): return L - (L - B) * np.exp(-k * np.power(t, delta))


curve_fit_dict['janoschek'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 0.5, lambda data: 0.001, 200, True])),
     dict(zip(keys, ['delta', 1, -100, 100, True])),
     dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
    janoschek
)


# 5-param Richard's http://www.pisces-conservation.com/growthhelp/index.html?richards_curve.htm
def richard_5(t, B, k, L, t_m, T): return B + L / np.power(1 + T * np.exp(-k * (t - t_m)), (1 / T))


curve_fit_dict['richard_5'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['k', lambda data: 0.5, 0.001, None, True])),
     dict(zip(keys, ['t_m', 10, None, None, True])),
     dict(zip(keys, ['T', 1, None, None, True])),
     dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
    richard_5
)


# http://www.ncbi.nlm.nih.gov/pmc/articles/PMC184525/pdf/aem00087-0379.pdf
def gompertz(t, A, growth_rate, lam):
    return A * np.exp(-np.exp(growth_rate * np.e / A * (lam - t)))


curve_fit_dict['gompertz'] = CurveFitObject(
    [dict(zip(keys, ['A', np.max, lambda data: 0.975 * np.max(data), lambda data: 1.025 * np.max(data), True])),
     dict(zip(keys, ['growth_rate', 1, 0, 5, True])),
     dict(zip(keys, ['lam', -1, None, None, True]))],
    gompertz,
    method='leastsq'
)

