import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import csv
import pandas as pd
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Filepath for storing user data
EXCEL_FILE = 'users.xlsx'

# Initialize a dictionary to store captions loaded from the file
captions = {}


def load_users():
    """Load user data from Excel file."""
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    else:
        # If the file does not exist, create an empty DataFrame
        return pd.DataFrame(columns=['username', 'email', 'password'])


def save_users(users):
    """Save user data to Excel file."""
    users.to_excel(EXCEL_FILE, index=False)


def load_captions():
    """Load image captions from the text file."""
    global captions
    if os.path.exists('captions.txt'):
        with open('captions.txt', mode='r') as infile:
            reader = csv.reader(infile)
            next(reader)  # Skip header row
            for rows in reader:
                image, caption = rows
                if image not in captions:
                    captions[image] = []
                captions[image].append(caption)


# Load captions from file
load_captions()


@app.route('/')
def index():
    if 'username' in session:
        return render_template('upload.html')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Load users from Excel
        users = load_users()

        # Validate user credentials
        if ((users['username'] == username) & (users['password'] == password)).any():
            session['username'] = username
            if username == 'admin' and password == 'admin':
                session['admin'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


def is_valid_email(email):
    """Check if the provided email address is valid."""
    # Regular expression for validating an email
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Validate email format
        if not is_valid_email(email):
            flash('Invalid email address')
            return render_template('register.html', error='Invalid email address')

        # Load users from Excel
        users = load_users()

        # Check if username already exists
        if username in users['username'].values:
            flash('Username already exists')
            return render_template('register.html', error='Username already exists')

        # Add new user to DataFrame
        new_user = pd.DataFrame([[username, email, password]], columns=['username', 'email', 'password'])
        users = pd.concat([users, new_user], ignore_index=True)

        # Save updated DataFrame to Excel
        save_users(users)

        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']

        # Load users from Excel
        users = load_users()

        # Find user by email and username
        user = users[(users['email'] == email) & (users['username'] == username)]

        if not user.empty:
            password = user['password'].values[0]
            flash(f'Password for user "{username}" is: {password}')
        else:
            flash('Email or Username not found')

    return render_template('forgot_password.html')



@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('display_file', filename=filename))

    return render_template('upload.html')


@app.route('/display/<filename>')
def display_file(filename):
    # Select a random caption for the given filename
    caption_list = captions.get(filename, ["No captions found for this image."])
    selected_caption = random.choice(caption_list) if caption_list else "No captions found for this image."
    return render_template('display.html', filename=filename, caption=selected_caption)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    return redirect(url_for('login'))


@app.route('/show_users')
def show_users():
    if 'admin' in session and session['admin']:
        # Load users from Excel
        users = load_users()
        return render_template('show_users.html', users=users.to_dict(orient='records'))
    else:
        flash('You are not authorized to view this page.')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)


