from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError 
from flask_jwt_extended import (jwt_required, create_access_token,get_jwt_identity,JWTManager)
import random
import string
import datetime
import subprocess
import os.path
import argparse  
import shutil

from gen_utils import get_folder

BAR = 'BAR'
PIE = 'PIE'
DIAL = 'DIAL'
LINE = 'LINE'
TYPES = [BAR,PIE,DIAL,LINE]
MAX_DATA = 100
MAX_RANDOMIZER = 15
FOLDER = get_folder(__file__)
JWT_SECRET_KEY = b"EssenceMonkeyApexDoorBallroomTimeMonkeyHardBalloon"

parser = argparse.ArgumentParser(description="Create internal server")
parser.add_argument("--folder",help="Folder in which the .db,.csr and .key files will be",required=True)
parser.add_argument("--duration",help="how long should the script run for in seconds. Not needed but always present",default=None)
parser.add_argument("--name",help="Name of the server, used in the certificate which should be ip address",required=True)
parser.add_argument("--port",help="Specific port to on which the server will recieve connections.",default=5000)

args = parser.parse_args()
arg_dict = vars(args)

# create the app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
# configure the SQLite database, relative to the app instance folder
#ran = ''.join(random.choices(string.ascii_uppercase  + string.ascii_lowercase, k = 6))
if not os.path.exists(os.path.join(FOLDER,arg_dict["folder"])):
    os.mkdir(os.path.join(FOLDER,arg_dict["folder"]))
else:
    shutil.rmtree(os.path.join(FOLDER,arg_dict["folder"]))
    os.mkdir(os.path.join(FOLDER,arg_dict["folder"]))
#time.sleep(2)
app.config["SQLALCHEMY_DATABASE_URI"] = str.format("sqlite:///{0}/{1}/server.db",FOLDER,arg_dict["folder"])
#time.sleep(2)
#DATABASE
# initialize the app with the extension
#db.init_app(app)
db = SQLAlchemy(app)
#time.sleep(2)
jwt = JWTManager(app)

def gen_id(cls):
    #print("entered gen_id")
    generated_id = None
    exists = False
    while generated_id is None or exists:
       # print("attempting to create id")
        generated_id = ''.join(random.choices(string.ascii_uppercase  + string.ascii_lowercase, k = 24))
        if cls.query.filter_by(id=generated_id).first() is not None:
            exists = True
    return generated_id

class User(db.Model):
    __bind__ = None
    id= db.Column(db.String(24), primary_key=True)
    username = db.Column(db.String(80),unique=True,nullable=False)
    email = db.Column(db.String(80))
    password = db.Column(db.String(80),nullable=False)
    admin = db.Column(db.Boolean(),nullable=False)

    def __init__(self,user,passwd,email=None,admin=False):
        self.id = gen_id(User)
        print("exited gen_id in user")
        self.username=user
        self.password = passwd
        self.email = email
        self.admin = admin
        print("created user info in object")

    def to_json(self):
        return {"id":self.id,"username":self.username,"password":"XXX","email":self.email,"admin":"Hidden"}



class ChartData(db.Model):
    __bind__ = None
    id = db.Column(db.String(24), primary_key=True)
    name = db.Column(db.String(80),db.ForeignKey('chart.name'),nullable=False)
    xpoint = db.Column(db.Float())
    ypoint = db.Column(db.Float())
    percentage = db.Column(db.Float())
    percentage_name = db.Column(db.String(80))

    def __init__(self,name,xpoint=None,ypoint=None,percentage=None,percentage_name=None):
        self.id = gen_id(ChartData)
        self.name=name
        self.xpoint = xpoint
        self.ypoint = ypoint
        self.percentage = percentage
        self.percentage_name = percentage_name

    def to_json(self):
        return {"id":self.id,"name":self.name,"xpoint":self.xpoint,"ypoint":self.ypoint,"percetage":self.percentage,"percentage_name":self.percentage_name}

data_in_chart = db.Table('data_in_chart',
                         db.Column('chart',db.String(80),db.ForeignKey('chart.name'),primary_key=True),
                         db.Column('datapoint',db.String(24),db.ForeignKey('chart_data.id'),primary_key=True))

class Chart(db.Model):
    __bind__ = None
    id= db.Column(db.String(24), primary_key=True)
    name= db.Column(db.String(80), unique=True,nullable=False)
    data = db.relationship('ChartData',secondary=data_in_chart,lazy=True)
    type_val = db.Column(db.String(20))
    creation = db.Column(db.DateTime(),nullable=False)
    last_updated = db.Column(db.DateTime(),nullable=False)

    def __init__(self,name,type_val=None,creation=None,last_updated=None):
        self.id = gen_id(Chart)
        self.name=name
        self.type_val = type_val
        self.creation = creation
        self.last_updated = last_updated

    def to_json(self):
        return {"id":self.id,"name":self.name,"type":self.type_val,"creation":self.creation,"last_updated":self.last_updated,"data":[dp.to_json() for dp in self.data]}





@app.route("/login",methods=['POST'])
def login_user():
   user,password = request.get_json()['username'],request.get_json()['password']
   user_obj = User.query.filter_by(username=user).first()
   if user_obj is not None and password == user_obj.password:
       result = {"access_token":create_access_token(identity=user_obj.id)} 
       return jsonify(result),200
   return "Username or Password is incorrect",401
   

@app.route("/charts",methods=['GET'])
@jwt_required()
def get_all_charts():
    all_charts = Chart.query.filter_by().all()
    text_charts = [chart.to_json() for chart in all_charts]
    html_page = '<!DOCTYPE html><html><head><title>Charts</title></head>'+\
    '<body><div><label for="type">Type:</label>'+\
    '<select name="type" id="type"><option value="bar">Bar</option><option value="dial">Dial</option>'+\
    '<option value="line">Line</option><option value="pie">Pie</option><option value="all">All</option></select>'+\
    '<label for="time-opt">Time Option:</label><select name="time-opt" id="time-opt"><option value="creation">Creation</option>'+\
    '<option value="last-updated">Last Updated</option><option value="all">All</option></select>'+\
    '<label for="start">Start time:</label><input type="datetime-local" id="start" name="start">'+\
    '<label for="end">End time:</label><input type="datetime-local" id="end" name="end"><button>Search</button>'+\
    str.format('</div><div id="charts">{0}</div></body></html>',text_charts)
   
    return html_page,200

@app.route("/structure",methods=['GET'])
def get_sitemap():
    print("structure called returning sitemap.xml")
    with open(os.path.join(FOLDER,"sitemap.xml")) as file:
        data = file.read()
        return data,200
    return "Error reading file",500


@app.route("/get_charts",methods=['POST'])
@jwt_required()
def get_selected_charts():
    #do filters TODO
    json_data = request.get_json()

    selected_charts = Chart.query.filter_by().all()
    text_charts = [chart.to_json() for chart in selected_charts]
    return jsonify(text_charts),200

def generate_name(val=None):
    str_end = ''.join(random.choices(string.ascii_uppercase  + string.ascii_lowercase, k = 16))
    if val is None:
        return str_end
    return str.format('{0}_{1}',val,str_end)

def random_time(start_time=None):
    if start_time is None:
        start_time = datetime.datetime.min
    end_time = datetime.datetime.now()
    random_time = random.random() * (end_time - start_time) + start_time
    return random_time

def pie_full(name,data_point):
    cds = ChartData.query.filter_by(name=name).all()
    if cds is None:
        return 0
    total_percentage = 0
    for cd in cds:
        total_percentage += cd.percentage
    if total_percentage == 100:
        return 1
    total_percentage += data_point.percentage
    if total_percentage > 100:
        return -1
    return 0
    

def fill_data(name,data_type,parent):
    
    for i in range(MAX_DATA):
        cd = ChartData(name=name)
        if data_type == BAR or data_type == LINE:
            cd.xpoint = random.random() * 100
            cd.ypoint = random.random() * 100
        elif data_type == PIE or data_type == DIAL:
            cd.percentage = random.random() * 100
            if data_type == PIE:
                if pie_full(name,cd) == 1:
                    continue
                while pie_full(name,cd) != 0:
                    cd.percentage = random.random() * 100    
                cd.percentage_name= generate_name()
        else:
            return 2,"500 Internal server error in creation of data"
        parent.data.append(cd)
        # with chosen values for MAX_RANDOMIZER and MAX_DATA the following line
        # will slowly increase the chance to break out and stop adding data with each
        # data point up until a chance of 92%. The exact probabilities can be seen if you run temp.py.
        # Different values of the MAX values will alter the probabilities.
        if i*random.random()>MAX_RANDOMIZER*random.random(): 
            break
    
            

def fill_tables(n):
    try:
        user = User(user='test-user',passwd='password')
        print(user)
        print(user.to_json())
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        print(e)
        db.session.rollback()
        return "Internal server error while creating user",500
    for i in range(n):
        try:
            type_val = random.choice(TYPES)
            name = generate_name(type_val)
            creation = random_time()
            last_updated = random_time(creation)
            chart = Chart(type_val=type_val,name=name,creation=creation,last_updated=last_updated)
            fill_data(name,type_val,chart)
            db.session.add(chart)
            db.session.commit()
        except IntegrityError:
           db.session.rollback()
           return "Internal server error in creation of charts",500
        # fill data
    return "Good",0

def generate_certificate():
    server_key_output_file = os.path.join(FOLDER,arg_dict["folder"],'server.key')
    server_crt_output_file = os.path.join(FOLDER,arg_dict["folder"],'server.csr') 
    if not os.path.isfile(server_key_output_file) or not os.path.isfile(server_crt_output_file): 
        server_key_org = str.format("{0}.org",server_key_output_file)
        subprocess.run(str.format('openssl genrsa -out {0} 2048',server_key_output_file).split(' '))
        subprocess.run(str.format('openssl req -new -key {0} -subj /CN={2} -out {1}',server_key_output_file,server_crt_output_file,arg_dict["name"]).split(' ')) 
        subprocess.run(str.format('cp {0} {1}',server_key_output_file,server_key_org).split(' '))
        subprocess.run(str.format('openssl rsa -in {0} -out {1}',server_key_org,server_key_output_file).split(' '))
        subprocess.run(str.format('openssl x509 -req -days 365 -in {0} -signkey {1} -out {0}',server_crt_output_file,server_key_output_file).split(' ')) 

def restart_db():
    db.drop_all()
    db.create_all()
#TODO quit after duration
with app.app_context():
    restart_db()
    msg,code = fill_tables(5)
    if code == 0:
        generate_certificate()
        server_key_output_file = os.path.join(FOLDER,arg_dict["folder"],'server.key')
        server_crt_output_file = os.path.join(FOLDER,arg_dict["folder"],'server.csr') 
        context = (server_crt_output_file,server_key_output_file) #certificate and key files
        app.run(debug=True, ssl_context=context,host="0.0.0.0",port=arg_dict["port"])
    else:
        print(msg)
        print(code)
        print("Error creating the server")
        