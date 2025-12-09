# 🧭 Calibration Practice App (Scout Mindset Inspired)

This project is a **Streamlit-based probability calibration practice app**, inspired by the calibration exercises from *The Scout Mindset* by **Julia Galef**. It allows users to:

- Answer binary (True/False or A/B) questions  
- Assign a confidence level (55%, 65%, 75%, 85%, 95%)  
- Receive instant feedback on:
  - Overall accuracy
  - Calibration by confidence level
  - A visual calibration curve
  - Brier score (overall probabilistic accuracy)

The goal is to help users improve **epistemic humility and probabilistic reasoning**—core ideas of the scout mindset.

---

## 📸 App Features

- ✅ 40-question multi-round calibration test  
- ✅ Animal facts, historical figures, country populations, and science facts  
- ✅ Radio-button input (no forced defaults)  
- ✅ Confidence-based calibration scoring  
- ✅ Interactive calibration chart  
- ✅ Brier score & overall accuracy  
- ✅ Fully CSV-driven question bank  
- ✅ Easily extensible for new question sets  

---

## 🚀 How to Run the App

### 1. Install dependencies

```bash
pip install streamlit pandas altair
