# 🏛️ Aesop-IR-Engine  
*A Python Information Retrieval (IR) System for Aesop's Fables*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 🔍 Overview  
A modular IR system implementing classic retrieval models to search through Aesop's Fables. Supports Boolean, Vector Space, and Signature-Based models with precision/recall evaluation.  

## ✨ Features  
- **Multiple Retrieval Models**:  
  - Boolean (Linear, Inverted Index, Signature-Based)  
  - Vector Space (TF-IDF)  
  - *Fuzzy Set (Planned)*  
- **Text Processing**:  
  - Porter Stemmer  
  - Stopword filtering (Crouch's frequency-based method)  
- **CLI Interface**: Interactive menu for indexing, searching, and evaluation.  
- **Metrics**: Precision, Recall, and query execution time.  

## 🛠️ Setup  
1. Clone the repo:  
   ```bash
   git clone https://github.com/enayat-hussain/aesop-ir-engine.git
   cd aesop-ir-engine