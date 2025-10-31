import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from flask import Flask, render_template, request, jsonify
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.optimize import linprog
import joblib
import os

sns.set(style="whitegrid", context="notebook", font_scale=1.1)

app = Flask(__name__)

gb_model = None
trained_data = None

def load_or_train_models():
    global gb_model, trained_data
    
    model_path = 'gb_model.joblib'
    csv_path = 'dairy_cattle_dataset.csv'
    
    if os.path.exists(model_path) and os.path.exists(csv_path):
        try:
            gb_model = joblib.load(model_path)
            df = pd.read_csv(csv_path)
            feature_cols = [
                "MaizeBran_kg", "Cottonseed_kg", "BrewersGrain_kg", "GrassSilage_kg",
                "NEL_MJkg", "CP_pct", "Lysine_pct"
            ]
            y = df["MilkYield_L"].copy()
            trained_data = {
                'mean_yield': float(y.mean()),
                'std_yield': float(y.std()),
                'mean_days': float(df['DaysInMilk'].mean()),
                'feature_cols': feature_cols
            }
            return True
        except:
            pass
    
    if not os.path.exists(csv_path):
        generate_sample_data(csv_path)
    
    df = pd.read_csv(csv_path)
    
    feature_cols = [
        "MaizeBran_kg", "Cottonseed_kg", "BrewersGrain_kg", "GrassSilage_kg",
        "NEL_MJkg", "CP_pct", "Lysine_pct"
    ]
    
    X = df[feature_cols].copy()
    y = df["MilkYield_L"].copy()
    
    gb_model = GradientBoostingRegressor(
        n_estimators=200, 
        learning_rate=0.05, 
        max_depth=4, 
        random_state=42
    )
    gb_model.fit(X, y)
    
    joblib.dump(gb_model, model_path)
    
    trained_data = {
        'mean_yield': float(y.mean()),
        'std_yield': float(y.std()),
        'mean_days': float(df['DaysInMilk'].mean()),
        'feature_cols': feature_cols
    }
    
    return True

def generate_sample_data(csv_path):
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'CowID': [f'C{i+1:04d}' for i in range(n_samples)],
        'Parity': np.random.randint(1, 6, n_samples),
        'DaysInMilk': np.random.randint(30, 350, n_samples),
        'BCS': np.random.uniform(2.5, 4.0, n_samples),
        'Temp_C': np.random.uniform(20, 35, n_samples),
        'MaizeBran_kg': np.random.uniform(2.0, 5.0, n_samples),
        'Cottonseed_kg': np.random.uniform(1.0, 2.0, n_samples),
        'BrewersGrain_kg': np.random.uniform(0.5, 4.0, n_samples),
        'GrassSilage_kg': np.random.uniform(1.0, 5.0, n_samples),
        'NEL_MJkg': np.random.uniform(5.8, 6.2, n_samples),
        'CP_pct': np.random.uniform(13.0, 14.5, n_samples),
        'Lysine_pct': np.random.uniform(0.58, 0.68, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    feed_quality = (df['NEL_MJkg'] - 5.8) / 0.4
    protein_quality = (df['CP_pct'] - 13.0) / 1.5
    
    milk_base = 10 + df['DaysInMilk'] * 0.02
    milk_feed = (df['MaizeBran_kg'] * 0.8 + df['Cottonseed_kg'] * 1.2 + 
                 df['BrewersGrain_kg'] * 1.5 + df['GrassSilage_kg'] * 0.6)
    milk_quality = feed_quality * 2 + protein_quality * 1.5
    
    df['MilkYield_L'] = milk_base + milk_feed + milk_quality + np.random.normal(0, 1.5, n_samples)
    df['MilkYield_L'] = np.clip(df['MilkYield_L'], 8, 25)
    
    df['MilkFat_pct'] = np.random.uniform(3.0, 4.0, n_samples)
    df['MilkProt_pct'] = np.random.uniform(3.0, 3.5, n_samples)
    
    total_dm = (df['MaizeBran_kg'] + df['Cottonseed_kg'] + 
                df['BrewersGrain_kg'] + df['GrassSilage_kg'])
    df['FCE_LperkgDM'] = df['MilkYield_L'] / total_dm
    
    df.to_csv(csv_path, index=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        maize = float(data.get('maize_bran', 0))
        cotton = float(data.get('cottonseed', 0))
        brewers = float(data.get('brewers_grain', 0))
        silage = float(data.get('grass_silage', 0))
        nel = float(data.get('nel', 0))
        cp = float(data.get('cp', 0))
        lysine = float(data.get('lysine', 0))
        days_in_milk = float(data.get('days_in_milk', 150))
        
        features = np.array([[maize, cotton, brewers, silage, nel, cp, lysine]])
        
        if gb_model is None:
            load_or_train_models()
        
        if gb_model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 500
        
        milk_yield_pred = gb_model.predict(features)[0]
        
        total_dm = maize + cotton + brewers + silage
        fce = milk_yield_pred / total_dm if total_dm > 0 else 0
        
        return jsonify({
            'success': True,
            'milk_yield': float(milk_yield_pred),
            'feed_efficiency': float(fce),
            'total_dm': float(total_dm)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/optimize', methods=['POST'])
def optimize():
    try:
        data = request.json
        target_milk = float(data.get('target_milk', 15))
        max_cost = float(data.get('max_cost', 10000))
        
        prices = {
            'maize_bran': 570,
            'cottonseed': 3000,
            'brewers_grain': 528,
            'grass_silage': 550
        }
        
        maintenance_req = {
            'ME': 7.0,
            'CP': 191.0,
            'Ca': 10.0,
            'P': 7.0
        }
        
        production_req_per_liter = {
            'ME': 0.62,
            'CP': 45.0,
            'Ca': 1.605,
            'P': 0.99
        }
        
        feed_composition = {
            'maize_bran': {'ME': 2.8, 'CP': 90.0, 'Ca': 0.5, 'P': 3.0, 'min': 1.0, 'max': 6.0},
            'cottonseed': {'ME': 3.2, 'CP': 230.0, 'Ca': 2.0, 'P': 11.0, 'min': 0.5, 'max': 3.0},
            'brewers_grain': {'ME': 2.6, 'CP': 250.0, 'Ca': 1.5, 'P': 5.0, 'min': 0.5, 'max': 4.0},
            'grass_silage': {'ME': 2.2, 'CP': 80.0, 'Ca': 5.0, 'P': 3.0, 'min': 2.0, 'max': 8.0}
        }
        
        c = np.array([prices['maize_bran'], prices['cottonseed'], 
                     prices['brewers_grain'], prices['grass_silage'], 0])
        
        A_ub = []
        b_ub = []
        
        A_ub.append([
            -feed_composition['maize_bran']['ME'],
            -feed_composition['cottonseed']['ME'],
            -feed_composition['brewers_grain']['ME'],
            -feed_composition['grass_silage']['ME'],
            production_req_per_liter['ME']
        ])
        b_ub.append(-maintenance_req['ME'])
        
        A_ub.append([
            -feed_composition['maize_bran']['CP'],
            -feed_composition['cottonseed']['CP'],
            -feed_composition['brewers_grain']['CP'],
            -feed_composition['grass_silage']['CP'],
            production_req_per_liter['CP']
        ])
        b_ub.append(-maintenance_req['CP'])
        
        A_ub.append([
            -feed_composition['maize_bran']['Ca'],
            -feed_composition['cottonseed']['Ca'],
            -feed_composition['brewers_grain']['Ca'],
            -feed_composition['grass_silage']['Ca'],
            production_req_per_liter['Ca']
        ])
        b_ub.append(-maintenance_req['Ca'])
        
        A_ub.append([
            -feed_composition['maize_bran']['P'],
            -feed_composition['cottonseed']['P'],
            -feed_composition['brewers_grain']['P'],
            -feed_composition['grass_silage']['P'],
            production_req_per_liter['P']
        ])
        b_ub.append(-maintenance_req['P'])
        
        A_ub.append([-1, 0, 0, 0, 0])
        b_ub.append(-feed_composition['maize_bran']['min'])
        A_ub.append([0, -1, 0, 0, 0])
        b_ub.append(-feed_composition['cottonseed']['min'])
        A_ub.append([0, 0, -1, 0, 0])
        b_ub.append(-feed_composition['brewers_grain']['min'])
        A_ub.append([0, 0, 0, -1, 0])
        b_ub.append(-feed_composition['grass_silage']['min'])
        
        A_ub.append([1, 0, 0, 0, 0])
        b_ub.append(feed_composition['maize_bran']['max'])
        A_ub.append([0, 1, 0, 0, 0])
        b_ub.append(feed_composition['cottonseed']['max'])
        A_ub.append([0, 0, 1, 0, 0])
        b_ub.append(feed_composition['brewers_grain']['max'])
        A_ub.append([0, 0, 0, 1, 0])
        b_ub.append(feed_composition['grass_silage']['max'])
        
        A_ub.append([1, 1, 1, 1, 0])
        b_ub.append(8.25)
        
        A_ub.append([0, 0, 0, 0, 1])
        b_ub.append(target_milk + 5)
        A_ub.append([0, 0, 0, 0, -1])
        b_ub.append(-max(target_milk - 2, 10))
        
        A_ub = np.array(A_ub)
        b_ub = np.array(b_ub)
        
        result = linprog(c, A_ub=A_ub, b_ub=b_ub,
                        bounds=[(1, 6), (0.5, 3), (0.5, 4), (2, 8), (max(target_milk - 2, 10), target_milk + 5)],
                        method='highs')
        
        if result.success:
            maize_kg, cotton_kg, brewers_kg, silage_kg, milk_yield = result.x
            
            total_cost = (maize_kg * prices['maize_bran'] + 
                         cotton_kg * prices['cottonseed'] + 
                         brewers_kg * prices['brewers_grain'] + 
                         silage_kg * prices['grass_silage'])
            
            fce = milk_yield / (maize_kg + cotton_kg + brewers_kg + silage_kg) if (maize_kg + cotton_kg + brewers_kg + silage_kg) > 0 else 0
            
            nutrients = {}
            for nutrient in ['ME', 'CP', 'Ca', 'P']:
                total_req = maintenance_req[nutrient] + milk_yield * production_req_per_liter[nutrient]
                total_provided = (maize_kg * feed_composition['maize_bran'][nutrient] +
                                cotton_kg * feed_composition['cottonseed'][nutrient] +
                                brewers_kg * feed_composition['brewers_grain'][nutrient] +
                                silage_kg * feed_composition['grass_silage'][nutrient])
                nutrients[nutrient] = {
                    'required': float(total_req),
                    'provided': float(total_provided),
                    'balance': float(total_provided - total_req)
                }
            
            return jsonify({
                'success': True,
                'feeds': {
                    'maize_bran': float(maize_kg),
                    'cottonseed': float(cotton_kg),
                    'brewers_grain': float(brewers_kg),
                    'grass_silage': float(silage_kg)
                },
                'milk_yield': float(milk_yield),
                'total_cost': float(total_cost),
                'cost_per_liter': float(total_cost / milk_yield),
                'feed_efficiency': float(fce),
                'nutrients': nutrients
            })
        else:
            return jsonify({'success': False, 'error': 'Optimization failed. Try adjusting target milk yield.'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    load_or_train_models()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    load_or_train_models()

