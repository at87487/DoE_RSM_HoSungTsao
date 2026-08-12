import os
import sys
import urllib.request
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import gradio as gr
from matplotlib.font_manager import FontProperties
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from scipy.optimize import minimize

# =====================================================================
# 🛠️ 全局字型防爆機制
# =====================================================================
FONT_PATH = "msjh.ttf"
if not os.path.exists(FONT_PATH):
    try:
        url = "https://github.com/DescentOfG/Fonts/raw/master/Microsoft-JhengHei.ttf"
        urllib.request.urlretrieve(url, FONT_PATH)
    except Exception:
        try:
            url = "https://github.com/adobe-fonts/source-han-sans/raw/release/Variable/TTF/SourceHanSansTC-VF.ttf"
            urllib.request.urlretrieve(url, FONT_PATH)
        except Exception:
            pass

GLOBAL_MY_FONT = FontProperties(fname=FONT_PATH) if os.path.exists(FONT_PATH) else None

# ==========================================
# 核心邏輯 1：動態解析輸入
# ==========================================
def parse_inputs(factors_text, responses_text):
    factors = {}
    for item in factors_text.split(";"):
        if ":" in item:
            name, levels_str = item.split(":")
            name = name.strip()
            levels = [float(x.strip()) for x in levels_str.split(",") if x.strip()]
            if name and len(levels) >= 2:
                factors[name] = [min(levels), (min(levels)+max(levels))/2.0, max(levels)]
                
    responses = {}
    for item in responses_text.split(";"):
        if ":" in item:
            name, target_str = item.split(":")
            name = name.strip()
            try:
                target = float(target_str.strip())
                if name: responses[name] = target
            except: pass
    return factors, responses

# ==========================================
# 核心邏輯 2：實驗矩陣生成與動態更新下拉選單
# ==========================================
def generate_matrix_and_update_dropdowns(factors_input, responses_input):
    # 呼叫原本的矩陣生成邏輯
    df, status = generate_adaptive_rsm_matrix(factors_input, responses_input)
    
    if df.empty:
        return df, status, gr.update(choices=[]), gr.update(choices=[])
    
    # 解析出因子的名稱，用來更新前台 UI 的下拉選單
    factors, _ = parse_inputs(factors_input, responses_input)
    var_names = list(factors.keys())
    
    # 預設 X 軸選第一個，Y 軸選第二個（若有）
    default_x = var_names[0]
    default_y = var_names[1] if len(var_names) > 1 else var_names[0]
    
    return df, status, gr.update(choices=var_names, value=default_x), gr.update(choices=var_names, value=default_y)

def generate_adaptive_rsm_matrix(factors_input, responses_input):
    factors, responses = parse_inputs(factors_input, responses_input)
    var_names = list(factors.keys())
    k = len(var_names)
    
    if k < 2:
        return pd.DataFrame(), "❌ 錯誤：請至少輸入 2 個控制因子才能進行 RSM 曲面擬合！"
    if not responses:
        return pd.DataFrame(), "❌ 錯誤：請至少輸入一個結果指標與目標值！"

    design_type = ""
    if k == 2:
        design_type = "3² 全因子九宮格設計"
        bbd_coded = list(itertools.product([-1, 0, 1], repeat=2))
    elif k == 3:
        design_type = "Box-Behnken 減量設計 (BBD)"
        bbd_coded = [
            [-1, -1, 0], [1, -1, 0], [-1, 1, 0], [1, 1, 0],
            [-1, 0, -1], [1, 0, -1], [-1, 0, 1], [1, 0, 1],
            [0, -1, -1], [0, 1, -1], [0, -1, 1], [0, 1, 1],
            [0, 0, 0]
        ]
    elif k == 4:
        design_type = "Box-Behnken 減量設計 (BBD)"
        bbd_coded = []
        for i in range(k):
            for j in range(i+1, k):
                for x1 in [-1, 1]:
                    for x2 in [-1, 1]:
                        row = [0] * k
                        row[i], row[j] = x1, x2
                        bbd_coded.append(row)
        bbd_coded.append([0] * k)
    else:
        return pd.DataFrame(), "❌ 目前系統自適應範圍為 2 ~ 4 個變量。"

    runs = []
    for row in bbd_coded:
        row_data = {}
        for idx, name in enumerate(var_names):
            min_v, mid_v, max_v = factors[name][0], factors[name][1], factors[name][2]
            coded_val = row[idx]
            if coded_val == -1: real_val = min_v
            elif coded_val == 0: real_val = mid_v
            else: real_val = max_v
            row_data[name] = real_val
            
        for r_name in responses.keys():
            row_data[r_name] = 0.0  
        runs.append(row_data)

    df = pd.DataFrame(runs)
    df.insert(0, "實驗編號", [f"RSM-EXP-{i+1:02d}" for i in range(len(df))])
    status = f"✅ 矩陣生成成功！\n採用架構: {design_type}\n變量數: {k} | 結果指標數: {len(responses)} | 總實驗組數: 【{len(df)} 組】"
    return df, status

# =====================================================================
# 核心邏輯 3：整合分析、優化搜尋與 3D 繪圖（支援自訂 X, Y 軸向）
# =====================================================================
def analyze_adaptive_rsm(df, factors_input, responses_input, x_axis_var, y_axis_var):
    factors, response_targets = parse_inputs(factors_input, responses_input)
    var_names = list(factors.keys())
    
    if df is None or df.empty or len(df) < 5:
        return "❌ 錯誤：請先生成矩陣並確實回填有效數據再進行分析！", None

    # 驗證選定的軸向是否存在
    if not x_axis_var or not y_axis_var or x_axis_var not in var_names or y_axis_var not in var_names:
        x_axis_var = var_names[0]
        y_axis_var = var_names[1] if len(var_names) > 1 else var_names[0]

    # 1. 訓練多目標二次曲面模型
    X = df[var_names]
    poly = PolynomialFeatures(degree=2, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    models = {}
    for r_name in response_targets.keys():
        if r_name not in df.columns:
            return f"❌ 錯誤：數據表中找不到結果指標 [{r_name}] 的欄位！", None
        model = LinearRegression()
        model.fit(X_poly, df[r_name])
        models[r_name] = model

    # 2. 連續空間尋優
    def objective_function(x):
        score = 0.0
        x_reshaped = np.array([x])
        x_poly_feat = poly.transform(x_reshaped)
        for r_name, target_val in response_targets.items():
            pred_val = models[r_name].predict(x_poly_feat)[0]
            score += (pred_val - target_val) ** 2
        return score

    bounds = [(factors[name][0], factors[name][2]) for name in var_names]
    initial_guess = [factors[name][1] for name in var_names]
    res = minimize(objective_function, initial_guess, method='L-BFGS-B', bounds=bounds)
    opt_x = res.x

    # 3. 建立報告
    report = "### 🏆 多目標響應曲面優化結果報告\n\n"
    report += "#### 🌟 最佳連續機台參數推薦配方：\n"
    for idx, name in enumerate(var_names):
        report += f"*   **{name}**： `{opt_x[idx]:.3f}`\n"
    
    report += "\n#### 🔮 預期達成之製程指標值：\n"
    opt_poly_feat = poly.transform(np.array([opt_x]))
    for r_name, target_val in response_targets.items():
        pred_val = models[r_name].predict(opt_poly_feat)[0]
        report += f"*   **{r_name}** ➔ 預測值: `{pred_val:.3f}` (設定目標: `{target_val}`)\n"

    # 4. 開始繪製 3D 響應曲面圖（依據 UI 選定的因子當 X, Y 軸）
    fig = plt.figure(figsize=(5 * len(response_targets), 4.5))
    
    x1_line = np.linspace(factors[x_axis_var][0], factors[x_axis_var][2], 30)
    x2_line = np.linspace(factors[y_axis_var][0], factors[y_axis_var][2], 30)
    X1_mesh, X2_mesh = np.meshgrid(x1_line, x2_line)

    for r_idx, r_name in enumerate(response_targets.keys()):
        ax = fig.add_subplot(1, len(response_targets), r_idx + 1, projection='3d')
        
        # 建立高維預測網格
        grid_points = []
        for x1, x2 in zip(np.ravel(X1_mesh), np.ravel(X2_mesh)):
            # 建立一個與變量等長的基礎點，預設全部填最佳解
            pt = list(opt_x)
            # 將使用者選定的變量動態替換為網格線資料
            pt[var_names.index(x_axis_var)] = x1
            pt[var_names.index(y_axis_var)] = x2
            grid_points.append(pt)
            
        Z_pred = models[r_name].predict(poly.transform(grid_points))
        Z_mesh = Z_pred.reshape(X1_mesh.shape)

        surf = ax.plot_surface(X1_mesh, X2_mesh, Z_mesh, cmap='viridis', alpha=0.8, edgecolor='none')
        ax.scatter(df[x_axis_var], df[y_axis_var], df[r_name], color='red', s=35, label='Measured')
        
        # 套用防爆中文字型
        if GLOBAL_MY_FONT:
            ax.set_title(f"RSM 曲面: {r_name}", fontweight='bold', fontproperties=GLOBAL_MY_FONT, fontsize=12)
            ax.set_xlabel(x_axis_var, fontproperties=GLOBAL_MY_FONT, fontsize=10)
            ax.set_ylabel(y_axis_var, fontproperties=GLOBAL_MY_FONT, fontsize=10)
            ax.set_zlabel(r_name, fontproperties=GLOBAL_MY_FONT, fontsize=10)
        else:
            ax.set_title(f"RSM Surface: {r_name}", fontweight='bold')
            ax.set_xlabel(x_axis_var)
            ax.set_ylabel(y_axis_var)
            ax.set_zlabel(r_name)
            
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=8)

    plt.tight_layout()
    return report, fig

# ==========================================
# Gradio 介面佈局
# ==========================================
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), title="自適應 RSM 預測優化系統") as demo:
    gr.Markdown("# 🌋 萬能自適應響應曲面法 (RSM) 優化系統")
    gr.Markdown("自動依變量數切換架構：輸入 **2 個變量**自動生成 **9 組九宮格**；輸入 **3~4 個變量**自動生成 **BBD 減量矩陣**。")
    
    with gr.Row():
        with gr.Column():
            factors_input = gr.Textbox(
                value="加工次數: 4, 12 ; 雷射功率(%): 60, 100 ; 第二外框距離: 0, 14 ; 第二外框次數: 0, 8", 
                label="🛠️ 控制因子與範圍 (參數名稱: 最小值, 最大值 ; 隔開)",
                lines=3
            )
        with gr.Column():
            responses_input = gr.Textbox(
                value="Taper_Angle(°): 0.0 ; 加工深度(µm): 150.0 ; 凹陷: 2.0",
                label="🎯 結果指標與優化目標 (指標名稱: 目標值 ; 隔開)",
                lines=3
            )
            
    with gr.Row():
        btn_gen = gr.Button("⚡ 生成自適應 RSM 實驗矩陣", variant="primary")
        txt_status = gr.Textbox(label="系統配對狀態", interactive=False)
        
    with gr.Row():
        dt_table = gr.Dataframe(interactive=True, label="數據回填表 (請手動修改結果指標欄位為你的實驗量測值)")
        
    # ─── 💡 新增：允許使用者自由切換 3D 圖底座軸向的互動區塊 ───
    with gr.Row():
        gr.Markdown("### 🔍 3D 響應曲面圖觀測軸向微調 (可隨時切換)")
    with gr.Row():
        drop_x = gr.Dropdown(choices=[], label="選擇圖表 X 軸參數", interactive=True)
        drop_y = gr.Dropdown(choices=[], label="選擇圖表 Y 軸參數", interactive=True)

    with gr.Row():
        btn_analyze = gr.Button("📈 啟動二次曲面擬合與連續空間最佳化", variant="secondary")
        
    with gr.Row():
        with gr.Column(scale=1):
            md_report = gr.Markdown("💡 等待數據回填並分析...")
        with gr.Column(scale=1):
            plot_output = gr.Plot(label="3D 響應曲面圖")

    # 點擊生成矩陣時，除了更新表格，也會動態把因子的清單塞進下拉選單中
    btn_gen.click(
        generate_matrix_and_update_dropdowns, 
        [factors_input, responses_input], 
        [dt_table, txt_status, drop_x, drop_y]
    )
    
    # 點擊分析時，連同下拉選單選定的變數名稱一起丟進繪圖引擎
    btn_analyze.click(
        analyze_adaptive_rsm, 
        [dt_table, factors_input, responses_input, drop_x, drop_y], 
        [md_report, plot_output]
    )

if __name__ == "__main__":
    demo.launch(share=True, debug=True)
