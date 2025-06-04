import math
from typing import Dict
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy import interpolate
from DKS_math.dimKoef import DimKoef
from app.schemas.schemas import BuildGdh, CurveResponse, Dataset, DataPoint
from scipy.optimize import minimize_scalar

def get_df_by_excel(excel_data, 
                    deg=4, 
                    k_value=1.31, 
                    press_conditonal=0.101325, 
                    temp_conditonal=283
                    ) -> Dict[str, pd.DataFrame]:
    excel = pd.ExcelFile(excel_data)
    dct_df = {}
    for sheet_name in excel.sheet_names:
        dimKoef = DimKoef.create_by_excel(
            excel, 
            sheet_name, 
            k_value=k_value, 
            deg=deg, 
            press_conditonal=press_conditonal, 
            temp_conditonal=temp_conditonal
        )
        df = dimKoef.create_df()
        df['name'] = sheet_name
        df['deg'] = deg
        df_1 = df[['k_rash', 'k_nap', 'kpd', 'k_nap_polin', 'kpd_polin', 
                   'k_rash_lin', 'freq', 'deg', 'name', 'temp', 'R', 'k', 
                   'diam', 'mgth','p_title', 'stepen', 'fnom']]
        df_1 = df_1.fillna(0)
        dct_df[sheet_name] = df_1
    return dct_df

labels = ['polytropic efficiency', 'head coefficient']
kinds = ['points', 'line']
y_col_2 = {
            'polytropic efficiency': ['kpd_polin'],
            'head coefficient': ['k_nap_polin']
            }   
y_col_1 = {
            'kpd', 'k_nap'
            }

def use_pydantic_model(dct_df):
    curves = []
    for key, df in dct_df.items():
        datasets = []
        for kind in kinds:
            if kind == 'points':
                grouped_dfs = [group for _, group in df.groupby('freq')]
                for gr_df in grouped_dfs:
                    for label in labels:
                        for y in y_col_1:
                            dataset = Dataset(label=label, 
                                            title=f"freq={gr_df['freq'].iloc[0]:.0f}",
                                            kind=kind,
                                            data=[DataPoint(x=row['k_rash'], 
                                                            y=row[y]) 
                                                        for _, row in gr_df.iterrows()])                        
                            datasets.append(dataset)
            else:
                for label in labels:
                    for y in y_col_2[label]:
                        dataset = Dataset(label=label, 
                                        title=f"deg={df['deg'][0]}",
                                        kind=kind,
                                        data=[DataPoint(x=row['k_rash_lin'], 
                                                        y=row[y]) 
                                                    for _, row in df.iterrows()])                        
                        datasets.append(dataset)                
        curve = CurveResponse(datasets=datasets, label=df['name'][0])
        curves.append(curve)
    return curves



class BaseGDH:
    
    p_komer = 0.101325
    t_komer = 283

    def __init__(self, p_in, diam, freq_nom, t_in, r_value, kpd, koef_rash, koef_nap, name, k_value = 1.31): 
        self.p_in = p_in
        self.diam = diam
        self.freq_nom = freq_nom
        self.t_in = t_in
        self.r_value = r_value
        self.k_value = k_value
        self.name = name
        self.kpd = kpd 
        self.koef_rash = koef_rash
        self.koef_nap = koef_nap
        self.f_kpd:np.poly1d=None  


    @classmethod
    def read_dict(cls, param):
        r_value = param.r_value
        k_value = param.k_value
        freq_nom = param.eq_compressor_type.eq_compressor_type_freq_nominal.value
        t_in = param.t_in
        diam = param.diam
        p_in = 3
        lst_koef_rash = []
        lst_koef_nap = []
        lst_kpd = []
        for i in range(len(param.eq_compressor_perfomance_curve)):
            koef_rash = param.eq_compressor_perfomance_curve[i].non_dim_rate
            koef_nap = param.eq_compressor_perfomance_curve[i].head
            kpd = param.eq_compressor_perfomance_curve[i].kpd
            lst_koef_rash.append(koef_rash)
            lst_koef_nap.append(koef_nap)
            lst_kpd.append(kpd)
        name = param.name
        return cls(p_in, diam, freq_nom, t_in, r_value, lst_kpd, lst_koef_rash, lst_koef_nap, name, k_value)
    

    @classmethod
    def get_z_val(cls, p_in:float, t_in:float, t_krit=190, p_krit=4.6) -> float: 
        """Расчет коэффициента сверсжимаемости
        Args:
            p_in (float): Давление, МПА
            t_in (float): Температура, К
            t_krit (int, optional): Критич. Температура, К {default = 190}
            p_krit (float, optional): Критич. Давление, МПа {default = 4.6}
        Returns:
            float: Значение сверхсжимаемости Z
        """
        z_val = 1 - 0.427 * p_in / p_krit * (t_in / t_krit)**(-3.688)        
        if type(z_val) == float:
            return 0.1 if z_val < 0 else z_val
        else:
            if type(z_val) == np.ndarray or type(z_val) == np.float64:
                return np.where(z_val < 0 , 0.1, z_val)
            else:
                return z_val
    

    @classmethod
    def get_line_N_p_in(self, u_val:float, z_in:float, r_val:float, t_in:float, koef_rash:float, koef_nap:float, kpd:float, diam:float) -> float:
        return (u_val ** 3) * koef_nap * koef_rash * math.pi * (diam**2) / (4 * z_in * r_val * t_in * kpd) * 10 ** 3        
    

    @classmethod
    def get_volume_rate_from_koef_rash(self, k_rash:float, diam:float, freq:float): 
        return k_rash * math.pi * diam**2 * (diam * math.pi)/4 * freq #обьемный расход из коэффициента расхода
    

    @classmethod
    def get_comp_ratio_from_koef_nap(self, koef_nap:float, freq:float, diam:float, kpd:float, t_in:float, z_in:float, r_val:float, k_value:float): # получение P2/P1 
        u_val = freq * diam * math.pi / 60
        dh =  koef_nap * u_val**2
        m_t =  (k_value - 1) / (k_value * kpd)
        return (dh * m_t / (z_in * r_val * t_in) + 1) ** (1 / m_t)

       
    def get_koef_rash(self, koef_rash:np.array):
        k_rash_min = np.min(koef_rash)
        k_rash_max = np.max(koef_rash)

        res_min = minimize_scalar(lambda x: -self.f_kpd(x), bounds=[k_rash_min, k_rash_max])
        kpd_max = -res_min.fun 
        k_rash_kpd_max = res_min.x 

        kpd_range_left = np.arange(self.f_kpd(k_rash_min), kpd_max+0.025, 0.005)

        if kpd_range_left.size > 3:
            kpd_range_left = np.linspace(self.f_kpd(k_rash_min), kpd_max, 4)

        kpd_range_right = np.arange(kpd_max-0.01, self.f_kpd(k_rash_max), -0.01)

        if kpd_range_right.size > 3:
            kpd_range_right = np.linspace(kpd_max-0.01, self.f_kpd(k_rash_max), 4)

        kpd_range = np.array([
            self.f_kpd(k_rash_min),
            *np.round(kpd_range_left,10)[1:-1],
            kpd_max,
            *np.round(kpd_range_right,10)[1:-1],
            self.f_kpd(k_rash_max)])

        f_left = interpolate.interp1d(
            x=self.f_kpd(np.linspace(k_rash_min, k_rash_kpd_max)),
            y=np.linspace(k_rash_min, k_rash_kpd_max)
            )

        f_right = interpolate.interp1d(
            x=self.f_kpd(np.linspace(k_rash_kpd_max, k_rash_max)),
            y=np.linspace(k_rash_kpd_max, k_rash_max)
            )

        k_koef_rash_range = np.array([
            *f_left(kpd_range[0:kpd_range_left.size]),
            *f_right(kpd_range[kpd_range_left.size:]),
            ])
        return k_koef_rash_range
    

    def get_summry(self):
        c00_kpd = np.polyfit(x=self.koef_rash, y=self.kpd, deg=4)     
        self.f_kpd = np.poly1d(c00_kpd)
        c00_nap = np.polyfit(x=self.koef_rash, y=self.koef_nap, deg=4)
        self.f_nap = np.poly1d(c00_nap) 
        
        koef_rash_ = self.get_koef_rash(self.koef_rash)
        kpd_ = self.f_kpd(koef_rash_)
        koef_nap_ = self.f_nap(koef_rash_)

        freq_base_nom = [1.05, 1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.7]
        freq_base = [x * self.freq_nom for x in freq_base_nom]
        volume_rate_x = self.get_volume_rate_from_koef_rash(koef_rash_, self.diam, np.vstack(freq_base))

        z_in = self.get_z_val(self.p_in, self.t_in)  
        comp_y = self.get_comp_ratio_from_koef_nap(koef_nap_, np.vstack(freq_base), self.diam, kpd_, self.t_in, z_in, self.r_value, self.k_value)
        # power_line = self.get_line_N_p_in(u_val, z_in, self.r_value, self.t_in, koef_rash_, koef_nap_, kpd_, self.diam)

        res = {
            # 'N/pн': power_line,
            'freq_nom_all': freq_base_nom,
            'comp': [comp_ for comp_ in comp_y],
            'volume_rate': [volume_rate_x for volume_rate_x in volume_rate_x]
            }
        res = pd.DataFrame(res)

        grouped_dfs = [group.reset_index(drop=True) for _, group in res.groupby('freq_nom_all')]

        lst_df_2 = []
        lst_buil_gdh_freq = []
        for df in grouped_dfs:
            df_freq = df[['volume_rate', 'comp']].T
            df_freq = pd.DataFrame({**{str(i): df_freq[0].str[i] 
                                for i in range(len(df_freq.loc['comp'][0]))}})
            df_kpd_1 = df_freq.T.stack()
            lst_df_2.append(df_kpd_1)
            datasets_freq = []
            for volume_rate, comp in zip(df_freq.loc['volume_rate'], df_freq.loc['comp']):
                dataset_freq = DataPoint(
                            x=volume_rate, 
                            y=comp
                            ) 
                datasets_freq.append(dataset_freq)

            buil_gdh_freq = BuildGdh(
                label=f"{df['freq_nom_all'][0]}",
                datasets=datasets_freq
                    )
            lst_buil_gdh_freq.append(buil_gdh_freq)

            lst_buil_gdh_kpd = []
            df_kpd_2 = pd.concat(lst_df_2, axis=1) 
            for i, label in zip(range(len(df_kpd_2) // 2), kpd_):
                volume_rate_row = df_kpd_2.iloc[2*i]
                comp_row = df_kpd_2.iloc[2*i+1]

                datasets_kpd = []
                for col in df_kpd_2.columns:
                    volume_rate = volume_rate_row[col]
                    comp = comp_row[col]
                    dataset_kpd = DataPoint(
                            x=volume_rate, 
                            y=comp)            
                    datasets_kpd.append(dataset_kpd)
                
                buil_gdh_kpd = BuildGdh(
                    label=f"{label:.2f}",
                    datasets=datasets_kpd
                    )
                lst_buil_gdh_kpd.append(buil_gdh_kpd)

        return lst_buil_gdh_freq, lst_buil_gdh_kpd
 

    @classmethod
    def get_plot_gdh(self, data1, data2, data3, name):
        # print(data1, data2, data3)
        fig, ax = plt.subplots()

        for f_nom in data1['n/nном'].unique():
            sup_data = data1[data1['n/nном'] == f_nom]
            x = sup_data.iloc[0, 1:].astype(float).values
            y = sup_data.iloc[1, 1:].astype(float).values
            degree = 4  # Степень полинома
            coefficients = np.polyfit(x, y, degree)
            polynomial = np.poly1d(coefficients)   
            x_smooth = np.linspace(x.min(), x.max(), 300)
            y_smooth = polynomial(x_smooth)       
            ax.plot(x_smooth, y_smooth, color = 'black', linestyle='-')      
            if f_nom == 1: 
                ax.plot(x_smooth, y_smooth, linestyle='-', color = 'deepskyblue')
            if f_nom == 1.05: 
                ax.plot(x_smooth, y_smooth, linestyle='-', color = 'red')  
            ax.text(sup_data.iloc[0, 1], sup_data.iloc[1, 1], round(f_nom, 2), ha = 'right', va = 'baseline', fontsize=9)
        
        for i in range(0, len(data2), 2):
            sup_data = data2.iloc[i:i+2]
            x = sup_data.iloc[0, 1:].astype(float).values
            y = sup_data.iloc[1, 1:].astype(float).values
            degree = 4  # Степень полинома
            coefficients = np.polyfit(x, y, degree)
            polynomial = np.poly1d(coefficients)   
            x_smooth = np.linspace(x.min(), x.max(), 300)
            y_smooth = polynomial(x_smooth)         
            ax.plot(x_smooth, y_smooth, color = 'black', linestyle='-')
            end_value = len(sup_data.iloc[0, 1:])
            ax.text(sup_data.iloc[0, end_value], sup_data.iloc[1, end_value], round(data2['kpd'][i], 2), ha = 'left', va = 'bottom', fontsize=9)
            
        if data3.empty:
            pass
        else: 
            for power_l in data3['N/pн'].unique():
                sup_data = data3[data3['N/pн'] == power_l]
                ax.plot(sup_data.iloc[0, 1:], sup_data.iloc[0, 1:], color = 'black', linestyle='--', linewidth=1)
                end_value = len(sup_data.iloc[0, 1:])
                ax.text(sup_data.iloc[0, end_value], sup_data.iloc[1, end_value], round(power_l, 2), ha = 'left', va = 'top', fontsize=9)
        
        plt.title(f"{name}", fontsize=10)
        ax.set_xlabel('Q, м\u00b3/мин', fontsize=10, loc='right')
        ax.set_ylabel(r'$\epsilon$', fontsize=10, rotation=0, loc='top')
        ax.set_axisbelow(True)
        ax.grid(color='lightgray', linestyle='dashed')
        return plt
    


if __name__=='__main__':
    # f_path = 'media\Оцифрованные СПЧ.xlsx'
    # res = get_df_by_excel(f_path)
    # print([
    #     (type(row['kpd']),type(row['k_rash']),type(row['k_nap']))
    # for _, row in res[0].iterrows()])
    pass

