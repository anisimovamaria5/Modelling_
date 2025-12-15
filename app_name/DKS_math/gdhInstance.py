"""Модуль ГДХ
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from app_name.DKS_math.baseFormulas import BaseFormulas
from app_name.DKS_math.mode import Mode
from typing import Tuple

class GdhInstance(BaseFormulas):

    @classmethod
    def create_by_csv(cls, csv_path_str) -> "GdhInstance":
        df = pd.read_csv(csv_path_str)
        diam = df['diam'].to_numpy()
        koef_rash = df['k_rash'].to_numpy()
        koef_nap = df['k_nap'].to_numpy()
        kpd = df['kpd'].to_numpy()
        freq_nom = df['fnom'].to_numpy()
        t_in = df['temp'].to_numpy()
        r_value = df['R'].to_numpy()
        k_value = df['k'].to_numpy()
        mgth = df['mgth'].to_numpy()
        stepen = df['stepen'].to_numpy()
        p_title = df['p_title'].to_numpy()
        return cls(diam[0], koef_nap, koef_rash, kpd, freq_nom[0], t_in[0], r_value[0], k_value[0], mgth[0], stepen[0], p_title[0], deg=4, name=csv_path_str)
    
    @classmethod
    def read_dict(cls, param, deg):
        deg = cls.deg if deg is None else deg
        r_value = param.r_value
        k_value = param.k_value
        freq_nom = param.eq_compressor_type.eq_compressor_type_freq_nominal.value
        t_in = param.t_in
        diam = param.diam
        p_out_nom = param.eq_compressor_type.eq_compressor_type_pressure_out.value
        comp_nom = param.eq_compressor_type.eq_compressor_type_comp_ratio.value
        power_nom = param.eq_compressor_type.eq_compressor_type_power.value
        range_param = range(len(param.eq_compressor_perfomance_curve))
        lst_koef_rash = [param.eq_compressor_perfomance_curve[i].non_dim_rate 
                         for i in range_param]
        lst_koef_nap = [param.eq_compressor_perfomance_curve[i].head 
                        for i in range_param]
        lst_kpd = [param.eq_compressor_perfomance_curve[i].kpd 
                   for i in range_param]        
        name = param.name
        return cls(diam, freq_nom, t_in, r_value, np.array(lst_kpd), np.array(lst_koef_rash), np.array(lst_koef_nap), name, p_out_nom, comp_nom, power_nom, k_value, deg=deg)


    def __init__(self, diam, freq_nom, t_in, r_value, kpd, koef_rash, koef_nap, name, p_out_nom, comp_nom, power_nom, k_value, deg): 
        self.diam = diam
        self.koef_nap = koef_nap
        self.koef_rash = koef_rash 
        self.kpd = kpd 
        self.freq_nom = freq_nom
        self.t_in = t_in
        self.r_value = r_value
        self.k_value = k_value
        self.f_nap_poly1d = np.poly1d(np.polyfit(koef_rash, koef_nap, deg))
        self.f_kpd_poly1d = np.poly1d(np.polyfit(koef_rash, kpd, deg))
        self.power_nom = power_nom
        self.comp_nom = comp_nom
        self.p_out_nom = p_out_nom
        self.name = name
        self._diam_cubed = np.pi**2 * diam**3 
    
    def get_kpd(self, k_rash): return self.f_kpd_poly1d(k_rash)
    def get_nap(self, k_rash): return self.f_nap_poly1d(k_rash)
    
    
    def get_freq_bound(self, volume_rate_arr) -> Tuple[float,float]:
        koef_rash_bound_arr = np.array([self.koef_rash.max(), self.koef_rash.min()])
        freq_bound_arr = 4 * volume_rate_arr / (self._diam_cubed * koef_rash_bound_arr)
        return freq_bound_arr
    

    def get_summry_stage(self, mode:Mode, freq:float|np.ndarray, t_in=None, r_value=None, k_value=None) -> pd.Series:
        t_in = self.t_in if t_in is None else t_in
        r_value = self.r_value if r_value is None else r_value
        k_value = self.k_value if k_value is None else k_value

        volume_rate = mode.get_volume_rate
        u_val = self.get_u_val(self.diam, freq)
        koef_rash_ = self.get_koef_rash_from_volume_rate(self.diam, u_val, volume_rate)
        koef_nap_ = self.get_nap(koef_rash_)
        kpd_ = self.get_kpd(koef_rash_)
        dh = self.get_dh(koef_nap_, u_val)
        power = self.get_power(mode.q_rate, dh, kpd_, r_value, mode.press_conditonal, mode.temp_conditonal)
        comp = self.get_comp_ratio(mode.p_in, dh, r_value, t_in, k_value, kpd_)
        p_out = mode.p_in * comp
        res = {
            'q_rate': mode.q_rate,
            'p_in': mode.p_in,
            'p_target': mode.p_target,
            'power': power,
            'comp': comp,
            'volume_rate': volume_rate,
            'udal': (koef_rash_ - self.koef_rash.min()) / (self.koef_rash.max() - self.koef_rash.min()) * 100,
            'freq': np.round(freq).astype(int),
            'freq_dimm': freq / self.freq_nom,
            'p_in_result': mode.p_in,
            'p_out': p_out,
            'p_out_diff': p_out,
            'title': self.name,
            'target': abs(p_out - mode.p_target),
        }
        return res
      

    def __repr__(self) -> str:
        return f'{self.name}'
    
    
    def __format__(self, format_spec: str) -> str:
        return f'{self.power_nom:.0f}-{self.p_out_nom:.0f} {self.comp_nom}'
    

    def show_gdh(self):
        fig, ax = plt.subplots(figsize=(9, 5)) 
        ax.scatter(self.koef_rash, self.koef_nap, c='b')
        x2 = np.linspace(np.min(self.koef_rash), np.max(self.koef_rash), 100)
        ax.plot(x2, self.f_nap_poly1d(x2), c='b')
        ax2 = ax.twinx()
        ax2.scatter(self.koef_rash, self.kpd, c='r')
        ax2.plot(x2, self.f_kpd_poly1d(x2), c='r')
        return ax, ax2
    

