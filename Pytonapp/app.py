from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from peewee import *
import os


app = Flask(__name__)


db = SqliteDatabase('data.db')


class Dataset(Model):
    name = CharField()
    value = FloatField()
    category = CharField()
    
    class Meta:
        database = db


db.connect()
db.create_tables([Dataset], safe=True)


def generate_plot(plot_type, data):
    plt.figure(figsize=(10, 6))
    
    if plot_type == 'bar':
        plt.bar(data['category'], data['value'])
        plt.xticks(rotation=45)
    elif plot_type == 'histogram':
        plt.hist(data['value'], bins=10)
    
    plt.tight_layout()
    
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f'data:image/png;base64,{plot_url}'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Nav fails!"
        
        file = request.files['file']
        if file.filename.endswith('.csv'):
           
            df = pd.read_csv(file)
            Dataset.delete().execute() 
            
            for _, row in df.iterrows():
                Dataset.create(
                    name=row['name'],
                    value=row['value'],
                    category=row['category']
                )
            return redirect(url_for('dashboard'))
    return render_template('upload.html')


@app.route('/dashboard')
def dashboard():
  
    all_data = pd.DataFrame([
        {'name': d.name, 'value': d.value, 'category': d.category} 
        for d in Dataset.select()
    ])
    
    if len(all_data) == 0:
        return redirect(url_for('upload'))
    
  
    filtered_query = Dataset.select().where(Dataset.value > 50)
    filtered_data = pd.DataFrame([
        {'name': d.name, 'value': d.value, 'category': d.category} 
        for d in filtered_query
    ])
    
 
    bar_plot = generate_plot('bar', all_data)
    histogram = generate_plot('histogram', filtered_data)
    
   
    stats = {
        'total_count': len(all_data),
        'avg_value': all_data['value'].mean(),
        'max_value': all_data['value'].max()
    }
    
    return render_template('dashboard.html', 
                         bar_plot=bar_plot,
                         histogram=histogram,
                         stats=stats)

if __name__ == '__main__':
    app.run(debug=True)