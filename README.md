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

Here is the English translation, tailored for a crisp, professional product feature or software specification presentation:

---

## ✨ Key Features

* **🤖 Smart Adaptive DoE Matrix Generation:**
* **2 Control Factors:** Automatically triggers a **$3^2$ full factorial grid design** (9 experimental runs), strictly securing safe operational boundaries.
* **3–4 Control Factors:** Automatically switches to a **Box-Behnken Design (BBD)**, significantly cutting down experimental costs.


* **⚡ Ultra-Lean Process Optimization:** Automatically removes replicated center points to minimize execution steps and material consumption.
* **📈 Continuous Space Gradient Prediction:** Breaks through traditional discrete-level limitations to precisely predict fine-tuned parameters (e.g., power at `74.28%`).
* **🎯 Intelligent Multi-Objective Desirability Engine:** Automatically identifies responses based on naming conventions:
* Terms with "depth" or "efficiency" default to **Larger-the-Better**.
* Terms with "roughness" or "HAZ" default to **Smaller-the-Better**.
* Terms with "angle" default to **Nominal-the-Best**.


* **📊 3D Response Surface Visualization:** Automatically fits multivariate quadratic equations and renders intuitive 3D response surface plots.
