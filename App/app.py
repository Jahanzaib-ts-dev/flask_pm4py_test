import os
from flask import Flask, request, redirect, url_for, render_template, flash
import pandas as pd
import pm4py

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        try:
            df = pd.read_csv(filepath, sep=';')
            columns = df.columns.tolist()
            return render_template('index.html', columns=columns, file_path=filepath)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('index'))
    else:
        flash('Invalid file type')
        return redirect(request.url)

@app.route('/process', methods=['POST'])
def process_file():
    case_id = request.form['case_id']
    activity_key = request.form['activity_key']
    timestamp_key = request.form['timestamp_key']
    filepath = request.form['file_path']
    
    try:
        df = pd.read_csv(filepath, sep=';')
        df = pm4py.format_dataframe(df, case_id=case_id, activity_key=activity_key, timestamp_key=timestamp_key)
        
        # Discover BPMN model
        bpmn_model = pm4py.discover_bpmn_inductive(df)
        output_image_path_bpmn = 'static/bpmn_model.png'
        pm4py.save_vis_bpmn(bpmn_model, output_image_path_bpmn)
        
        # Discover Process Tree
        process_tree = pm4py.discover_process_tree_inductive(df)
        output_image_path_tree = 'static/process_tree.png'
        pm4py.view_process_tree(process_tree, filename=output_image_path_tree, format='png', variant='generalized_performance')
        
        # Render template with image URLs
        return render_template('index.html', 
                               image_url_bpmn=url_for('static', filename='bpmn_model.png'),
                               image_url_tree=url_for('static', filename='process_tree.png'),
                               columns=df.columns.tolist(),
                               file_path=filepath)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
