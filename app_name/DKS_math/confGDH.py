"""Модуль компоновки ГДХ"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from app_name.DKS_math.baseFormulas import BaseFormulas
from app_name.DKS_math.gdhInstance import GdhInstance
from app_name.DKS_math.mode import Mode

class ConfGDH(BaseFormulas):

    def __init__(self, stage_list:List[Tuple[GdhInstance,int]], t_in=288, avo_t_in=288, avo_dp=0.06) -> None:
        self.stage_list = stage_list
        self.avo_dp = avo_dp
        self.t_in = t_in
        self.avo_t_in = avo_t_in
        
    def get_freq_bound_all(self, mode:Mode, t_in=None, r_value=None, k_value=None):
        curr_mode = mode.clone()
        curr_mode.t_in = curr_mode.t_in if t_in is None else t_in
        curr_mode.r_value = curr_mode.r_value if r_value is None else r_value
        curr_mode.k_value = curr_mode.k_value if k_value is None else k_value
        curr_mode.p_in = mode.p_in
        res = []

        for ind, (stage, cnt_gpa) in enumerate(self.stage_list):
            if isinstance(mode.q_rate, (int, float)):
                curr_mode.q_rate = mode.q_rate / cnt_gpa
            else: 
                curr_mode.q_rate = mode.q_rate[ind] / cnt_gpa

            volume_rate_arr = curr_mode.get_volume_rate
            if ind == 0:
                freq_bound_arr = self.stage_list[ind][0].get_freq_bound(volume_rate_arr)
            else:
                freq_bound_arr:np.ndarray = self.stage_list[ind][0].get_freq_bound(volume_rate_arr.reshape((*volume_rate_arr.shape, 1))).T 
            
            comp_arr = stage.get_summry_stage(curr_mode, freq_bound_arr)['comp']
            curr_mode.p_in = comp_arr * curr_mode.p_in - self.avo_dp
            res.append(freq_bound_arr)
        return res
    
    
    def get_summry_without_bound(self, mode:Mode, freq:list, t_in=None):
        res = []
        curr_mode = mode.clone()
        curr_mode.t_in =  curr_mode.t_in  if t_in is None else t_in
        for ind, ((stage, cnt_gpa), freq) in enumerate(zip(self.stage_list, freq)):
            if isinstance(mode.q_rate, (int, float)):
                curr_mode.q_rate = mode.q_rate / cnt_gpa
            else:
                curr_mode.q_rate = mode.q_rate[ind] / cnt_gpa

            temp_res = stage.get_summry_stage(curr_mode, freq)
            temp_res['work_gpa'] = self.stage_list[ind][1]
            res.append(temp_res)
            curr_mode.p_in = temp_res['comp'] * curr_mode.p_in - self.avo_dp
           
        return res


    def get_summry_with_bound(self, mode:Mode, freq:np.ndarray, bound_dict:Dict[str,Tuple[np.ndarray,np.ndarray]]):
        df_smmry = self.get_summry_without_bound(mode, freq)
        curr_mode = mode.clone()
        curr_mode.p_target = mode.p_target
        res = {'target':[],'out':[]}

        for ind, (stage, cnt_gpa) in enumerate(self.stage_list): 
            res['target'].append(df_smmry['p_out'][ind] - curr_mode.p_target)

            for name in bound_dict.keys():  
                y_i = []
                y = df_smmry[name]
                for i in y:
                    if i <= float(bound_dict[name][1][ind]):
                        y_i.append((float(bound_dict[name][1][ind]) - i) / bound_dict[name][2])
                    elif i >= float(bound_dict[name][0][ind]):
                        y_i.append((i - float(bound_dict[name][0][ind])) / bound_dict[name][2]) 
                    elif float(bound_dict[name][1][ind]) < i < float(bound_dict[name][0][ind]):
                        y_i.append(0)  
                    else:
                        y_i.append(0)
                res[name] = y_i 

        res_out_array = np.array([
            value
        for key, value in res.items() if key in bound_dict.keys()])
        res['out'] = np.nan_to_num(res_out_array.mean(axis=0, where=res_out_array!=0))        
        
        df_smmry.columns = [f'{key}_s' for key in df_smmry.columns]
        
        res2 =  pd.concat([
            pd.DataFrame(data=np.array(list(res.values())).T, columns=res.keys()).T,
            df_smmry.T],
            axis=0).T
        
        res2['target'] = res2['out'].fillna(0) + res2['power_s'] / 7000 + abs(res['target']) #FIXME 7000 убрать
        return res2 
    

    def get_freq_dop(self, mode:Mode, freq_bounds:np.array, t_in=None, r_value=None, k_value=None):
        curr_mode = mode.clone()
        curr_mode.t_in = curr_mode.t_in if t_in is None else t_in
        curr_mode.r_value = curr_mode.r_value if r_value is None else r_value
        curr_mode.k_value = curr_mode.k_value if k_value is None else k_value
        curr_mode.q_rate = mode.q_rate / self.stage_list[0][1]

        curr_mode.p_in = np.array([
            self.stage_list[0][0].get_summry_stage(curr_mode, freq)['p_out_diff'] - self.avo_dp
        for freq in np.linspace(freq_bounds[0][0], freq_bounds[0][1], 50)]) 

        curr_mode.q_rate = mode.q_rate / self.stage_list[1][1]
        volume_rate_arr = curr_mode.get_volume_rate
        freq_dop:np.ndarray = self.stage_list[1][0].get_freq_bound(volume_rate_arr.reshape((*volume_rate_arr.shape, 1))).T
        return freq_dop
    

    def __repr__(self) -> str:
        return " ".join([
            f'{stage} X {cnt}'
        for stage, cnt in self.stage_list
        ])

