from flask import Flask, render_template, redirect, url_for, flash
import pymysql
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, StringField, PasswordField, SubmitField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
Bootstrap(app)
moment = Moment(app)

app.config['SECRET_KEY'] = "TYHuang"

db_config = {
    'host': 'localhost',
    'user': 'DB_admin',
    'password': 'DB_admin',
    'db': 'DB_PJ'
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def get_db_connection():
    connection = pymysql.connect(**db_config)
    return connection

    
@app.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html')


class QueryForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/query', methods=['GET', 'POST'])
# @login_required
def query():
    query_form = QueryForm()
    record = None
    if query_form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute(query_form.query.data)
        record = cursor.fetchall()
        
        cursor.close()
        conn.close()
        # return redirect(url_for('index'))  # how to redirect
    return render_template('query.html', form=query_form, record=record)


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email=email

    @staticmethod
    @login_manager.user_loader
    def get(user_id):
        # Todo: Write query get user from database
        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute('SELECT * FROM Customer Where CustomerId=%s',(user_id,))
        user_data=cur.fetchone()
        cur.close()
        conn.close()
        print(user_data)
        if user_data:
            return User(id=user_data[0],email=user_data[4])
        return None
    


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    billing_address = StringField('Billing Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Todo: Write query to insert user into database; add logic checking
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        insert_query = """
            INSERT INTO Customer (UserName, Email, Password, BillingAddress) 
            VALUES (%s, %s, %s, %s)
        """
        data = (
            form.username.data, 
            form.email.data, 
            form.password.data, 
            form.billing_address.data
        )
        try:
            cursor.execute(insert_query, data)
            conn.commit()  # commit to make changes persistent in the database
            print("Query executed successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            conn.rollback()  # rollback to the previous state if any error occurred
        print(cursor.fetchall())   
        return redirect(url_for('login'))
    return render_template('signup.html', title='Sign Up', form=form)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Todo: validate user login info
        email=form.email.data
        password=form.password.data
        print(email,password)
        conn=get_db_connection()
        # cur=conn.cursor()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute('SELECT * FROM Customer WHERE Email=%s', (email,))
        user=cur.fetchone()
        print(user)
        cur.close()
        conn.close()
        if user and user['Password']==password:
            user=User(id=user['CustomerID'],email=user['Email'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password")

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class ServiceLocationForm(FlaskForm):
    building=StringField('Building', validators=[DataRequired()])
    unit_number=IntegerField('Unit Number', validators=[DataRequired()])
    takeover_time=DateField('Takeover Time', validators=[DataRequired()])
    square_footage=IntegerField('Square Footage',validators=[DataRequired()])
    number_of_bedrooms= IntegerField('Number of Bedrooms', validators=[DataRequired()])
    number_of_occupants= IntegerField('Number of Occupants', validators=[DataRequired()])
    zcode=StringField('Zip Code',validators=[DataRequired()])
    submit=SubmitField('Add Location')

@app.route('/locations', methods=['GET', 'POST'])
@login_required
def locations():
    # Todo: Write query to get devices from database
    # Todo: Allow user to delete a device
    # Todo: Allow user to add a location by submitting a form
    form=ServiceLocationForm()
    conn=get_db_connection()
    cur=conn.cursor(pymysql.cursors.DictCursor)

    if form.validate_on_submit():
        data=(
            current_user.id,
            form.building.data,
            form.unit_number.data,
            form.takeover_time.data,
            form.square_footage.data,
            form.number_of_bedrooms.data,
            form.number_of_occupants.data,
            form.zcode.data
        )
        cur.execute('INSERT INTO ServiceLocation (CustomerID, Building, UnitNumber, TakeOverTime, SquareFootage, NumberOfBedrooms, NumberOfOccupants, Zcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', data)
        conn.commit()

    cur.execute('Select * from ServiceLocation where CustomerID=%s',(current_user.id,))
    locations=cur.fetchall()
    cur.close()
    conn.close()

   # locations = [{"CustomerID": 1,
   #             "ServiceLocationID": 1,
   #             "Building": "123 Maple St Building", 
   #             "UnitNumber": 5, 
   #             "TakeOverTime": "2021-06-01",
   #             "SquareFootage": 1200,
   #             "NumberOfBedrooms": 2,
   #             "NumberOfOccupants": 4,
   #             "Zcode": '12345'}]
    return render_template('locations.html', form=form, locations=locations)

@app.route('/location/<int:location_id>', methods=['GET', 'POST'])
@login_required
def devices(location_id):
    # Todo: Write query to get all devices from database and show them
    # Todo: Allow user to delete a device
    # Todo: Allow user to add new device by 
    #   1. first selecting from user prestored device type list
    #   2. choose the device model from the prestored model list
    devices = [{"DeviceID": 1,
                "ServiceLocationID": 1,
                "Type": "Refrigerator", 
                "ModelName": "Samsung 1234"}]
    return render_template('devices.html', devices=devices)


@app.route('/energy_consumption_analysis', methods=['GET', 'POST'])
@login_required
def energy_consumption_analysis():
    # Todo: provide several(4-5) analysis options(views) for user to choose
    # Todo: create visualization for each analysis option
    return render_template('analysis.html')



if __name__ == '__main__':
    app.run(debug=True, port=8000)