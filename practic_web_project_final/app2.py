import pandas as pd
from flask import Flask, render_template, request, jsonify, make_response, send_file
from flask import send_from_directory
import os
import pdfkit
from flask import redirect, url_for, flash, session, make_response
from pymongo import MongoClient
#from bson import ObjectId
app = Flask(__name__)

app.secret_key = "your_secret_key"  # Replace with a strong secret key
client = MongoClient('localhost', 27017)
db = client['users']  # Replace with your MongoDB database name
users_collection = db['user']
pdf_collection = db['pdfs']
def calculate_bmr(weight, height, age, gender):
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'female':
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        print('Invalid gender')
        return None
    return bmr

def calculate_calories(bmr, activity_level):
    if activity_level == 'sedentary':
        pal = 1.2
    elif activity_level == 'lightly active':
        pal = 1.375
    elif activity_level == 'moderately active':
        pal = 1.55
    elif activity_level == 'very active':
        pal = 1.725
    elif activity_level == 'extra active':
        pal = 1.9
    else:
        print('Invalid activity level')
        return None
    calories = bmr * pal
    return calories

def generate_food_recommendations(weight, height, age, gender, activity_level, diseases, meal_preference):
    bmr = calculate_bmr(weight, height, age, gender)
    if bmr is not None:
    
        calories = calculate_calories(bmr, activity_level)
        if calories is not None:
         
            df1 = pd.read_csv('final_diseases.csv')
            df2 = pd.read_csv('final_food_items.csv')

            nutritional_components = []

            for disease in diseases:
        
                row = df1.loc[df1['Disease'] == disease]
                if not row.empty:
                    nutritional_components.append(list(row.iloc[:, 1:].values[0]))
                else:
                    print(f"No data found for disease: {disease}")
            final_list = []

            if nutritional_components:
                final_list = nutritional_components[0]
                for components in nutritional_components[1:]:
                    for i, value in enumerate(components):
                        final_list[i] = min(final_list[i], value)

            food_items_dict = {}
            no_food_it=[]
            for i, component_value in enumerate(final_list):
                component_name = df2.columns[i+1]
                food_items = []
                for index, row in df2.iterrows():
                    food_component_value = row[component_name]
                    if float(food_component_value)/ float(component_value) < 0.90 :
            # add this food item to the list
                       # if row['food items']=='Apple':print(component_name)
                      
                        if row['food items'] not in no_food_it:           
                               food_items.append(row['food items'])
                    else: 
                           no_food_it.append(row['food items'])

                food_items_dict[component_name] = food_items
            print(food_items_dict.keys())
            #print("kkkkkkkkkkkkkkk")
            food_i_list = list(food_items_dict.values())
            food_i_list = sum(food_i_list, [])
            unique_list = list(set(food_i_list))
            no_food_it=list(set(no_food_it))
        
            for i in no_food_it:
              if i in unique_list:
                 unique_list.remove(i)

            
            original_calories = 2200
            adjusted_list = []
            adjusted_list.append(calories)
            for value in final_list:
                adjusted_value = value * (calories / original_calories)
                adjusted_list.append(round(adjusted_value, 2))

            df = pd.read_csv('Calorie_value.csv')

            if meal_preference == 'Vegetarian':
                meal_categories = {
                    'Breakfast': ('Breakfast grains', 'Fruits', 'Vegetables', 'Protein', 'Healthy Fats', 'Breads', 'Juice', 'Indian bread', 'Tea & Coffee'),
                    'Lunch': ('Grains', 'Indian bread', 'Vegetables', 'Salads', 'Healthy Fats', 'Soup', 'Dairy'),
                    'Snacks': ('Tea & Coffee', 'Sandwich', 'Nuts & Seeds', 'Fruits', 'Beverages', 'Juice'),
                    'Dinner': ('Grains', 'Indian bread', 'Vegetables', 'Salads', 'Healthy Fats', 'Soup', 'Dairy')
                }
            elif meal_preference == 'Non-Vegetarian':
                meal_categories = {
                    'Breakfast': ('Breakfast grains', 'Fruits', 'Vegetables', 'Non-veg Protein', 'Protein', 'Healthy Fats', 'Breads', 'Juice', 'Indian bread', 'Tea & Coffee'),
                    'Lunch': ('Grains', 'Indian bread', 'Vegetables', 'Salads', 'Healthy Fats', 'Soup', 'Dairy', 'Meat', 'Non-veg Salads', 'Non-veg Soup'),
                    'Snacks': ('Tea & Coffee', 'Sandwich', 'Nuts & Seeds', 'Fruits', 'Beverages', 'Juice', 'Non-veg Sandwich'),
                    'Dinner': ('Grains', 'Indian bread', 'Vegetables', 'Salads', 'Healthy Fats', 'Soup', 'Dairy', 'Meat', 'Non-veg Salads', 'Non-veg Soup')
                }
            else:
                print('Invalid meal preference')
                return None
            
            food_items_by_category={category: [] for category in meal_categories.values()}
            for food_item in unique_list:
                category = df.loc[df['food items'] == food_item, 'Category'].values[0] 
                for meal_category, categories in meal_categories.items():
                  if category in categories:
                   food_items_by_category.setdefault(meal_category + ': ' + category, []).append(food_item)           
            
            
            
            g={}
    # print the list of food items for each meal category and category
            for meal_category, categories in meal_categories.items():
        #print(colored(meal_category.title(), 'red', attrs=['bold']))
       
               ll={}
               for category in categories:
                key = meal_category + ': ' + category
                if key in food_items_by_category and food_items_by_category[key]:
                
                  ll[category]=food_items_by_category[key]
               g[meal_category]=ll
           
            #return adjusted_list, food_items_by_category
            return adjusted_list,g

    return None
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/createmeal')
def createmeal():
    return render_template('createmeal.html')

@app.route('/diet-plan')
def diet_plan():
    return render_template('diet-plan.html')

@app.route('/diet-plan/diet-chart')
def diet_chart():
    user_id=session['user_id']
    #print("jjjjjjjjjjjjjjjjjjjjjjjjjjjjihih")
    print(user_id)
    return render_template('dietplan-chart.html',userid=user_id)

@app.route('/get_csv')
def get_csv():
    csv_directory = os.path.dirname('final_food_items.csv')
    filename = 'final_food_items.csv'
    return send_from_directory(csv_directory, filename)

@app.route('/get_csv_calorie')
def get_csv_calorie():
    csv_directory = os.path.dirname('Calorie_value.csv')
    filename = 'Calorie_value.csv'
    return send_from_directory(csv_directory, filename)








@app.route('/submit', methods=['POST'])
def submit():
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    age = int(request.form['age'])
    gender = request.form['gender']
    activity_level = request.form['activityLevel']
    diseases = request.form.getlist('diseases')
    meal_preference = request.form['meal']
    result = generate_food_recommendations(weight, height, age, gender, activity_level, diseases, meal_preference)

    if result is not None:
        adjusted_list,g = result
        user_id=session['user_id']
        return render_template('dietplan-chart.html', adjusted_list=adjusted_list, g=g,userid=user_id)
       # return render_template('result.html', adjusted_list=adjusted_list, g=g)
    else:
        return render_template('error.html')
df2=pd.read_csv('final_food_items.csv')

@app.route('/get_item_data', methods=['GET'])
def get_item_data():
    item = request.args.get('item')
    selected_row = df2[df2['food items'] == item].iloc[0].to_dict()
    return jsonify(selected_row)
# Directory to store PDFs
PDF_FOLDER = 'pdfs'
app.config['PDF_FOLDER'] = PDF_FOLDER

# Auto-incremental ID function
def get_next_sequence(collection_name):
    result = db.counters.find_one_and_update(
        {'_id': collection_name},
        {'$inc': {'seq': 1}},
        return_document=True,
        upsert=True
    )
    return result['seq']

@app.route("/receive_data", methods=["POST"])
def receive_data():
    # Get the JSON data sent from the client
    data = request.json

    # Process the data as needed
    print("Received data from client:")
    print(data)

    # Process the data and modify the HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDFKit in Flask</title>
        <style>
        h1 {
            text-align: center;
        }
        </style>
    </head>
    <body>
        <h1>Your Diet Plan!!!</h1>
    """

    # Iterate over the received data and add it to the HTML content
    for category_data in data:
        category_name = category_data["category"]
        items = category_data["items"]
        html_content += f"<h2>{category_name}</h2>"
        for k, v in items.items():
            html_content += f"<h3>{k}</h3>"
            html_content += "<ul>"
            for item in v:
                html_content += f"<li>{item}</li>"
            html_content += "</ul>"
            html_content += "<br>"

    # Close the HTML content
    html_content += """
        </body>
    </html>
    """

    # Generate PDF from modified HTML content
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdf = pdfkit.from_string(html_content, False, configuration=config)

    # Create directory if it doesn't exist
    if not os.path.exists(app.config['PDF_FOLDER']):
        os.makedirs(app.config['PDF_FOLDER'])

    # Save PDF locally
    pdf_filename = os.path.join(app.config['PDF_FOLDER'], f'{session["user_id"]}.pdf')
    pdf_path = os.path.abspath(pdf_filename)
    with open(pdf_filename, 'wb') as f:
        f.write(pdf)

    # Get the next sequence ID for PDF
    pdf_id = session['user_id']

    # Store PDF path in MongoDB
    pdf_document = {
        "_id": pdf_id,
        "pdf_path": pdf_path
    }
    pdf_collection.insert_one(pdf_document)

    return send_file(pdf_filename, as_attachment=True)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Choose a different one.', 'danger')
        else:
            # Get the next sequence ID for the user
            user_id = get_next_sequence('users')

            # Insert user data with auto-incremental ID
            user_document = {
                "_id": user_id,
                "username": username,
                "password": password
            }
            users_collection.insert_one(user_document)

            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password match
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session['user_id'] = user['_id']
            # Store user ID in session
            flash('Login successful.', 'success')
            return redirect(url_for('home'))  # Redirect to dashboard after login
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('index.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Completely clear the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



@app.route('/home')
def home():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))

    # Render dashboard page
    response = make_response(render_template('home.html'))
    # Prevent caching of the dashboard page
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

from flask import render_template

@app.route('/pdf_display')
def pdf_display():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))

    # Retrieve the user's PDF path from the database
    user_id = session['user_id']
    # Render the pdf_display.html template with the PDF path
    return render_template('pdf_display.html', userid= user_id)

@app.route('/pdfs/<path:filename>')
def download_file(filename):
    return send_from_directory('pdfs', filename, as_attachment=True)
if __name__ == '__main__':
    app.run(debug=True)