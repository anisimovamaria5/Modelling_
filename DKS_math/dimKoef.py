"""Модуль получения безразмерных коэффициентов расхода, напора и кпд
"""
import numpy as np
import pandas as pd
from .baseFormulas import BaseFormulas
import warnings
warnings.simplefilter("ignore")

class DimKoef(BaseFormulas):
    
    @classmethod
    def create_by_excel(cls, df, sheet_name, k_value=None, deg=None, press_conditonal=None, temp_conditonal=None):
        press_conditonal = cls.press_conditonal if press_conditonal is None else press_conditonal
        temp_conditonal = cls.temp_conditonal if temp_conditonal is None else temp_conditonal
        deg = cls.deg if deg is None else deg
        k_value = cls.k_value if k_value is None else k_value

        df = pd.read_excel(df, sheet_name=sheet_name)

        del_idx = df[df.iloc[:,0] == '//'].index[0]
        df_1 = df.iloc[:del_idx][~(df.iloc[:,0] == '/')]
        df_2 = df.iloc[del_idx+1:][~(df.iloc[:,0] == '/')]
        q_rate = df_1['V'].to_numpy()
        kpd = df_1['kpd'].to_numpy()
        freq = df_1['f'].to_numpy()
        r_value = df_2[df_2.iloc[:,0] == 'R'].iloc[:,1].values
        t_in = df_2[df_2.iloc[:,0] == 'T'].iloc[:,1].values
        diam = df_2[df_2.iloc[:,0] == 'd'].iloc[:,1].values
        freq_nom = df_2[df_2.iloc[:,0] == 'fnom'].iloc[:,1].values

        if df_1['Pvh'][0] < df_2[df_2.iloc[:,0] == 'P'].iloc[:,1].values:
            p_in = df_1['Pvh'].to_numpy()
            p_out =  df_2[df_2.iloc[:,0] == 'P'].iloc[:,1].values
        else:
            p_out = df_1['Pvh'].to_numpy()
            p_in = df_2[df_2.iloc[:,0] == 'P'].iloc[:,1].values 

        mgth = df_2[df_2.iloc[:,0] == 'mgth'].iloc[:,1].values 
        stepen = df_2[df_2.iloc[:,0] == 'stepen'].iloc[:,1].values 
        p_title = df_2[df_2.iloc[:,0] == 'ptitle'].iloc[:,1].values 
        return cls(q_rate, p_in, kpd, freq, t_in[0], p_out, diam[0], r_value[0], freq_nom[0], mgth[0], stepen[0], p_title[0], k_value = k_value, deg=deg, press_conditonal=press_conditonal, temp_conditonal=temp_conditonal, name=sheet_name)
    
    def __init__(self, q_rate, p_in, kpd, freq, t_in, p_out, diam, r_value, freq_nom, mgth, stepen, p_title, k_value = 1.31, deg=4, press_conditonal=0.101325, temp_conditonal=283, name=None): 
        self.q_rate = q_rate
        self.p_in = p_in
        self.diam = diam
        self.kpd = kpd 
        self.freq = freq
        self.t_in = t_in
        self.r_value = r_value
        self.k_value = k_value
        self.p_out = p_out
        self.freq_nom = freq_nom
        self.mgth = mgth
        self.stepen = stepen
        self.p_title = p_title
        self.name = name
        self.deg = deg
        self.press_conditonal = press_conditonal
        self.temp_conditonal = temp_conditonal


    @classmethod   
    def get_comp_r(cls, p_in:float, p_out:float) -> float: 
        """расчет степени сжатия
        Args:
            p_in (float): Давление на входе, МПа
            p_out (float): Давление на выходе, МПа
        Returns:
            float: Степень сжатия
        """
        comp_r = p_out / p_in
        return comp_r
    
    @classmethod   
    def get_dh(cls, p_in:float, r_value:float, t_in:float, comp:float, k_value:float, kpd:float) -> float: 
        """удельное изменение энтальпии
        Args:
            z_1 (float): Коэффициент сверсжимаемости
            r_value (float): Постоянная Больцмана поделеная на молярную массу
            t_in (float): Температура, K
            comp (float): Степень сжатия
            k_value (float): Коэф-т политропы, б.м.
            kpd (float): Политропный кпд, д.ед
        Returns:
            float: Необходимое для сжатия измение энтальпии, дж/кг
        """
        z_1 = cls.get_z_val(p_in, t_in, t_krit=190, p_krit=4.6)
        dh = z_1 * r_value * t_in * (comp**((k_value - 1) / (k_value * kpd)) -1) * (k_value * kpd) /(k_value - 1)
        return dh 
       
    @classmethod
    def get_koef_nap(cls, dh:float, u_val:float) -> float:     
        """Расчет безразмерного коэффицента напора
        Args:
            dh (float): Изменение энтальпии, Дж
            u_val (float): Угловая скорость, м/мин
        Returns:
            float: Возврощяет коеффициент напора, при заданных условиях и текущей температуре, д.ед
        """
        koef_nap = dh  / u_val**2
        return koef_nap
    
    def get_summry(self): 
        comp = self.get_comp_r(self.p_in, self.p_out)
        u_val = self.get_u_val(self.diam, self.freq)
        dh = self.get_dh(self.p_in, self.r_value, self.t_in, comp, self.k_value, self.kpd)
        volume_rate = self.get_volume_rate_from_press_temp(self.q_rate, self.p_in, self.t_in, self.r_value, self.press_conditonal, self.temp_conditonal)
        koef_rash = self.get_koef_rash_from_volume_rate(self.diam, u_val, volume_rate)
        koef_nap = self.get_koef_nap(dh, u_val)
        return koef_rash, koef_nap
    
    def create_df(self):

        res = []
        koef = self.get_summry()
        res.append(koef)
        k_rash, k_nap = res[0]

        k_rash  = [0 if pd.isna(x) else x for x in k_rash]
        k_nap  = [0 if pd.isna(x) else x for x in k_nap]

        k_rash_np = np.array(k_rash, dtype=np.float64)
        k_nap_np = np.array(k_nap, dtype=np.float64) 
        kpd_np = np.array(self.kpd, dtype=np.float64) 

        min_rash = min(k_rash)
        max_rash = max(k_rash)
        k_rash_lin = np.linspace(min_rash, max_rash, len(k_rash))

        c00_nap = np.polyfit(x=k_rash_np, y=k_nap_np, deg=self.deg)
        f_nap = np.poly1d(c00_nap)
        c00_kpd = np.polyfit(x=k_rash_np, y=kpd_np, deg=self.deg)        
        f_kpd = np.poly1d(c00_kpd)   
        koef_nap_ = f_nap(k_rash_lin)
        kpd_ = f_kpd(k_rash_lin)


        df = pd.DataFrame({'diam': self.diam,
                        'k_rash': k_rash,
                        'k_rash_lin': k_rash_lin,
                        'k_nap': k_nap,
                        'kpd': self.kpd,
                        'k_nap_polin': koef_nap_,
                        'kpd_polin': kpd_,   
                        'freq':self.freq,                     
                        'fnom': self.freq_nom,
                        'temp': self.t_in,
                        'R': self.r_value,
                        'k': self.k_value,
                        'mgth': self.mgth,
                        'stepen': self.stepen,
                        'p_title': self.p_title
                        })
        # filename = f'{self.name}.csv'
        # df.to_csv(f'spch_dimkoef\{filename}', index=False)
        return df

if __name__ == '__main__':
    df = pd.ExcelFile('dbqp3.xlsx')
    for sheet_name in df.sheet_names:
        dimKoef = DimKoef.create_by_excel(df)
        dimKoef.create_csv()

