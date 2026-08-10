---
title: Adaptive RSM Tool
emoji: 🌋
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

This is a universal Design of Experiments (DoE) and process optimization tool developed with Python and Gradio. Specifically engineered for laser processing, semiconductor manufacturing, and industrial engineering, it leverages Response Surface Methodology (RSM) to help engineers accurately predict and identify high-precision, optimal parameters with minimal experimental runs.

## ✨ 核心特色
- **🤖 智慧自適應 DoE 矩陣生成：**
  - **2 個控制因子：** 自動啟動 **3² 全因子九宮格設計** (9組實驗)，嚴格鎖定安全邊界。
  - **3~4 個控制因子：** 自動切換為 **Box-Behnken 減量設計 (BBD)**，大幅壓縮實驗成本。
- **⚡ 極簡製程優化：** 已自動拔除重複中心點，最大程度減少實驗槍數與材料消耗。
- **📈 連續空間梯度預測：** 打破傳統離散水準限制，能精準預測如 `74.28%` 功率的微調參數。
- **🎯 智慧多目標滿意度引擎：** 自動識別名稱。指標含「深度」或「效率」自動判定為**望大**；含「粗糙度」或「HAZ」判定為**望小**；「角度」判定為**望目**。
- **📊 3D 響應曲面視覺化：** 自動擬合多元二次方程式，並繪製直觀的 3D 響應曲面圖。
