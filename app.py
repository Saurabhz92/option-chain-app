import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # हे सर्व्हरवर चालवण्यासाठी आवश्यक आहे
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from flask import Flask, render_template, request

# Flask ॲप सुरू करणे
app = Flask(__name__)

# मुख्य फंक्शन जे चार्ट तयार करेल
def create_plots(df):
    try:
        # कॉल आणि पुट डेटा वेगळा करणे
        calls_df = df[['STRIKE'] + [col for col in df.columns if 'CALLS' in col]]
        puts_df = df[['STRIKE'] + [col for col in df.columns if 'PUTS' in col]]

        # चार्टसाठी एक डिक्शनरी तयार करणे
        charts = {}
        sns.set_style("darkgrid")

        # --- चार्ट १: LTP vs. Strike Price ---
        plt.figure(figsize=(12, 6))
        plt.plot(calls_df['STRIKE'], calls_df['CALLS_LTP'], marker='o', linestyle='-', color='orangered', label='Call LTP')
        plt.plot(puts_df['STRIKE'], puts_df['PUTS_LTP'], marker='o', linestyle='-', color='limegreen', label='Put LTP')
        plt.title('LTP vs. Strike Price', fontsize=16)
        plt.xlabel('Strike Price', fontsize=12)
        plt.ylabel('Last Traded Price (LTP)', fontsize=12)
        plt.legend()
        
        # चार्टला इमेजमध्ये रूपांतरित करणे
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        charts['ltp_chart'] = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()

        # --- चार्ट २: Open Interest vs. Strike Price ---
        plt.figure(figsize=(12, 6))
        plt.bar(calls_df['STRIKE'], calls_df['CALLS_OI'], width=20, color='orangered', label='Call OI (Resistance)')
        plt.bar(puts_df['STRIKE'], puts_df['PUTS_OI'], width=20, color='limegreen', label='Put OI (Support)', alpha=0.8)
        plt.title('Open Interest vs. Strike Price', fontsize=16)
        plt.xlabel('Strike Price', fontsize=12)
        plt.ylabel('Open Interest (OI)', fontsize=12)
        plt.legend()

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        charts['oi_chart'] = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()

        # --- चार्ट ३: Implied Volatility (IV) vs. Strike Price ---
        valid_calls_iv = calls_df[calls_df['CALLS_IV'] > 0]
        valid_puts_iv = puts_df[puts_df['PUTS_IV'] > 0]
        plt.figure(figsize=(12, 6))
        plt.plot(valid_calls_iv['STRIKE'], valid_calls_iv['CALLS_IV'], marker='.', linestyle='-', color='orangered', label='Call IV')
        plt.plot(valid_puts_iv['STRIKE'], valid_puts_iv['PUTS_IV'], marker='.', linestyle='-', color='limegreen', label='Put IV')
        plt.title('Implied Volatility (IV) vs. Strike Price', fontsize=16)
        plt.xlabel('Strike Price', fontsize=12)
        plt.ylabel('Implied Volatility (%)', fontsize=12)
        plt.legend()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        charts['iv_chart'] = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()

        return charts
    except Exception as e:
        print(f"Error creating plots: {e}")
        return None

# वेबपेजसाठी रूट (Route)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # फाईल अपलोड झाली आहे का ते तपासणे
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        
        if file and file.filename.endswith('.csv'):
            try:
                # CSV फाईल वाचणे आणि साफ करणे
                df = pd.read_csv(file, skiprows=1)
                df = df.iloc[:, 1:-1]
                
                new_columns = [
                    'CALLS_OI', 'CALLS_CHNG_IN_OI', 'CALLS_VOLUME', 'CALLS_IV', 'CALLS_LTP', 'CALLS_CHNG',
                    'CALLS_BID_QTY', 'CALLS_BID_PRICE', 'CALLS_ASK_PRICE', 'CALLS_ASK_QTY', 'STRIKE',
                    'PUTS_BID_QTY', 'PUTS_BID_PRICE', 'PUTS_ASK_PRICE', 'PUTS_ASK_QTY', 'PUTS_CHNG',
                    'PUTS_LTP', 'PUTS_IV', 'PUTS_VOLUME', 'PUTS_CHNG_IN_OI', 'PUTS_OI'
                ]
                df.columns = new_columns
                df.replace(['-', ' -'], np.nan, inplace=True)
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col].str.replace(',', '', regex=False), errors='coerce')
                df.dropna(subset=['STRIKE'], inplace=True)
                df.fillna(0, inplace=True)
                
                # चार्ट्स तयार करणे
                charts = create_plots(df)
                return render_template('index.html', charts=charts)
            
            except Exception as e:
                return f"An error occurred: {e}"

    # GET request आल्यास फक्त अपलोड पेज दाखवणे
    return render_template('index.html', charts=None)

# ॲप चालवणे
if __name__ == '__main__':
    app.run(debug=True)