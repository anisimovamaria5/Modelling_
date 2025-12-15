import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from scipy.optimize import minimize, Bounds, NonlinearConstraint
from app_name.DKS_math.confGDH import *
import warnings
from autograd import value_and_grad
import autograd.numpy as anp
warnings.filterwarnings("ignore")


class PressInSolver:

    def __init__(self, conf:ConfGDH, bound_dict:Dict[str,Tuple[np.ndarray,np.ndarray,float]]) -> None:
        self.conf = conf
        self.bound_dict = bound_dict


    def func_z(self, x, mode:Mode):
        p_in = x[0]
        freqs = x[1:1+len(self.conf.stage_list)]
        curr_mode = mode.clone()
        curr_mode.p_in = p_in    
        df_res = self.conf.get_summry_without_bound(curr_mode, freqs)
        target = df_res[-1]['p_in']
        return target


    def get_p_out_constr(self, x, mode:Mode) -> List[NonlinearConstraint]:
        p_in = x[0]
        freqs = x[1:]
        cur_mode = mode.clone()
        cur_mode.p_in = p_in
        res = self.conf.get_summry_without_bound(cur_mode, freqs)[-1]['p_out']
        return res


    def get_bound_dict_constr(self, x, mode:Mode, num_stage) -> List[NonlinearConstraint]:
        p_in = x[0]
        freqs = x[1:]
        param_names = ['p_out_diff', 'freq_dimm', 'power', 'comp', 'udal']
        
        cur_mode = mode.clone()
        cur_mode.p_in = p_in
        stage_results = self.conf.get_summry_without_bound(cur_mode, freqs)[num_stage]
        
        return [stage_results[key] for key in param_names]

    
    def minimize(self, mode:Mode):
        num_stages = len(self.conf.stage_list)
        param_names = ['p_out_diff', 'freq_dimm', 'power', 'comp', 'udal']
        bounds_array_staged = np.array([
            [
                [getattr(stage.bounds, name).max_value, getattr(stage.bounds, name).min_value]
                for name in param_names
            ]
            for stage in self.bound_dict
        ]   
        )
        upper_bounds = [self.conf.stage_list[i][0].freq_nom * bounds_array_staged[-1][1, 0] for i in range(num_stages)]
        lower_bounds = [self.conf.stage_list[i][0].freq_nom * bounds_array_staged[-1][1, 1] for i in range(num_stages)]
        p_in_lb = 0  
        p_in_ub = mode.p_target 
        bounds = Bounds([p_in_lb] + [-np.inf]*num_stages, [p_in_ub] + [np.inf]*num_stages)
        constraints = [
                *[NonlinearConstraint(
                            fun=lambda x, ns=num_stage: self.get_bound_dict_constr(x, mode, ns),
                            lb=bounds_array_staged[num_stage][:, 1].tolist(), 
                            ub=bounds_array_staged[num_stage][:, 0].tolist()
                            ) for num_stage in range(num_stages)],
                NonlinearConstraint(
                            fun=lambda x: self.get_p_out_constr(x, mode),
                            lb=mode.p_target, 
                            ub=bounds_array_staged[-1][0,0]
                            )    
            ]
        p_in_0 = (p_in_lb + p_in_ub) / 2
        freq_b = [(lb + ub) / 2 for lb, ub in zip(lower_bounds, upper_bounds)]

        x0 = np.array([p_in_0, *freq_b])
        res = minimize(self.func_z, 
                        x0=x0,
                        args=(mode),
                        method='SLSQP',
                        bounds=bounds, 
                        constraints=constraints,
                        )
        return res
   

bound_dict = {
    'power':(
        np.array([16000, 16000]),
        np.array([7000, 7000]),
        200),
    'comp':(
        np.array([3.0, 3.0]),
        np.array([1, 1]),
        0.01),
    'udal':(
        np.array([100, 100]),
        np.array([0, 0]),
        1.0),    
    'freq_dimm':(
        np.array([1.05, 1.05]),    
        np.array([0.7, 0.7]),
        0.01),
    'p_out':(
        np.array([4.5, 7.5]),    
        np.array([0.1, 0.1]),
        0.1),
    'target':(
        np.array([10, 10]),    
        np.array([-10, -10]),
        0.1),
}

