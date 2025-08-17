from tkinter.tix import Tree
from flask import Flask, render_template, redirect, session,request,flash, url_for
from datetime import timedelta
from flask_cors import CORS
from functions import *
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory


from services.db_students import *
from services.db_doctors import *
from services.db_schedual import *
from services.db_advising import *
##constants##
PORT = 5000
DB_FILENAME = 'database.db'
INIT_DB = True  # to create db file
# Import smtplib for the actual sending function
import smtplib
from flask_mail import Mail, Message
# Import the email modules we'll need
def create_app():
    UPLOAD_FOLDER = 'static/images/'
    # create flask app
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.secret_key = 'asdfads234egrg'
    app.permanent_session_lifetime = timedelta(minutes=5)


    # create database extension
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+DB_FILENAME
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    

    db.init_app(app)

    # create flask cors extension
    CORS(app)

    return app, db



app = Flask(__name__)
mail= Mail(app)
# to send email gmail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'moustafasamy490@gmail.com'
app.config['MAIL_PASSWORD'] = 'twuhuyqcjijywwqx'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

#to upload image
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_file(imgname):
    return '.' in imgname and \
           imgname.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





# create flask app
app, db = create_app()

# create db file on demand
if INIT_DB:
    db.create_all(app=app)


#routes
#home page
@app.route('/')
@app.route('/home')
def index():

   
    return render_template('Home.html')

# create doctor account
# Get register page
@app.route('/register-doc')
def get_reg_page():
    if not( check_if_isadmin()):
        return "<h1>YOU ARE NOT ADMIN</h1>"
    else:
        return render_template('reg-maindoc.html')

#post regiser informations
@app.route('/register-doc', methods=['POST'])
def post_reg_page():
    if not( check_if_isadmin()):
        return "<h1>YOU ARE NOT ADMIN</h1>"
    else:
        isadmin = True
        ismadmin = True
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_pic = filename

        users=Doctor(ismadmin,isadmin , request.form['name'],request.form['username'],request.form['email'],request.form['password'],request.form['certificates'], profile_pic )
      
        db.session.add(users)
        db.session.commit()
        return redirect('/')


#that is for upload doctor image
@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

#log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

#to log in as doctor
#get login page
@app.route('/login', methods=['GET'])
def login_get():
    if  (checkiflogged()):
        return "you are logged in"
    return render_template("logindoctors.html")

#post login information
@app.route('/login', methods=['POST'])
def login_post():
 if  (checkiflogged()):
    return "you r logged in"
 else:
    username = request.form.get('username')
    password = request.form.get('password')

    # validate
    query = Doctor.getByUsername(username)
    if query == None :
        return "<h1>wrong username</h1>"
    if query.password != password:
        # @TODO return a proper failure message
        return "<h1>wrong password</h1>"

    # save session
    print("LOGIN success")
    session.permanent = True
    session['username'] = username
    
    session["qq"] = True
    if query.ismadmin:
        session["ismadmin"] = True


    if query.isadmin:
        session["isadmin"] = True

    else:

        session["isadmin"] = False
        session["ismadmin"] = False
        session['doctor'] = True

    return redirect('/' )

#that page to show students and add a new student
@app.route('/user/drinfo', methods=['GET'])
def get_DOCTORS():
    if "username" in session:
        uname = session['username']

        stssusername = Doctor.getDOCTORSTUDENT(uname)
        
        return render_template('drinfo.html', stssusername=stssusername)
    else:
        # user is not logged in as a doctor  -->hacking try ----->logout
        return render_template('wrong page.html')


#to edit NICK NAME
@app.route('/stsusername/<id>/edit', methods=['GET'])
def get_stusername(id):
 if "username" in session:
    stusername = Student.get(id).stusername
    return render_template('editjoke.html', id=id, stusername=stusername)
 else:
        # user is not logged in --> redirect to login page
    return render_template('wrong page.html')

@app.route('/stsusername/<id>/edit', methods=['POST'])
def update_stusername(id):
    if "username" in session:
        updatedstusername = request.form.get('stusername')
        Student.update(id, updatedstusername)
        return redirect('/user/drinfo')
    else:
        # user is not logged in --> redirect to login page
        return render_template('wrong page.html')
#TO EDIT OFFICIAL MAIL
@app.route('/stuname/<id>/edit', methods=['GET'])
def get_student_name(id):
    name = Student.get(id).name
    return render_template('update_student_name.html', id=id, name=name)


@app.route('/stuname/<id>/edit', methods=['POST'])
def update_student_name(id):
    if "username" in session:
        updatedname = request.form.get('name')
        Student.update_name(id, updatedname)
        return redirect('/user/drinfo')
    else:
        # user is not logged in --> redirect to login page
        return redirect('/users/login')

#TO DELETE A STUDENT
@app.route('/stsusername/<id>/delete', methods=['GET'])
def delete_stusername(id):
    if "username" in session:
        Student.delete(id)
        return redirect('/user/drinfo')

    else:
        # user is not logged in --> redirect to login page
        return redirect('/users/login')
        

#TO ADD A STUDENT
@app.route('/stsusername', methods=['POST'])
def add_stusername():

    # check if user in session
    if "username" in session:
        username = session['username']
        stusername = request.form.get('stusername')
        name = request.form.get('name')
        password = request.form.get('password')
        
     
        # get  DOCTOR EMAIL TO SEND MESSAGE
        email = Doctor.getUserId(username)

        Student.insert(stusername,name,password,email)
        return redirect('/user/drinfo')
    else:
        # user is not logged in --> redirect to login page
        return redirect('/login')


@app.route('/login-stu', methods=['GET'])
def login_stu():
    
    return render_template("log-stu.html")


@app.route('/login-stu', methods=['POST'])
def login_stu_post():
    name = request.form.get('name')
    password = request.form.get('password')

    # validate
    query = Student.getByname(name)
    if query == None :
        return "<h1>wrong username</h1>"
    if query.password != password:
        # @TODO return a proper failure message
        return "<h1>wrong password</h1>"

    # save session
    print("LOGIN success")
    session.permanent = True
    session['email'] = query.id
    session['name'] = name
    session['id'] = query.id

    


    if  session['name']==True:
        session['name']==True
    else:
        session['name'] = True
        session['id'] = query.id


    
    return redirect('/')





@app.route('/drinfo' , methods = ['GET'])
def drinfo():
    if (session["name"] == True) :
        id = session['id'] 
        user = Student.query.get(id)
        drmail = Student.get_adv_by_iid(id)
        dr_name= Doctor.get_name_bymail(drmail)
        dr_prifile_pic= Doctor.get_prifile_pic_bymail(drmail)
        dr_cetificates= Doctor.get_cetificates_bymail(drmail)
        return render_template('doctor_info.html',dr_name=dr_name,   user=user  , dr_prifile_pic = dr_prifile_pic , dr_cetificates = dr_cetificates)
    else:
        return "False"

@app.route('/user' , methods = ['GET'])
def show_user():
    if (session["name"] == True) :
        id = session['id'] 
        drmail = Student.get_adv_by_iid(id)
        dr_name= Doctor.get_name_bymail(drmail)
        doc_schedual= Doctor.getschedual(dr_name)
        return render_template('stu-page.html',doc_schedual = doc_schedual)
    else:
        return "False"

@app.route("/new/email" ,methods = ['Get'])
def adv():
    if "name" in session:
         id = session['email']
         adv = Student.getUsersessions(id)
         return render_template("past-sessions.html"    ,adv = adv)
    else:
        return redirect('/login')


@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404


@app.route("/new/email" , methods = ["post"])
def indexx():
 if "name" in session:
    id = session['email']
    email = Student.getUsermial(id)
    doctor_id = Doctor.get_id_bymail(email)
    message = request.form.get('message')
    name = Student.get_nam_by_iid(id)
    msg = Message("New session request from  %s " % (name), sender = 'moustafasamy490@gmail.com', recipients = [email])
    msg.body = message 
    mail.send(msg)
    session['name'] = name
    user_id = id
    readed = "no"
    replay = "Not replayed"
    Advising.insert(name , message ,user_id ,doctor_id ,readed , replay)    
    return redirect('/new/email')
 else:
    return redirect('/login')

@app.route("/show/adv")
def show_adv():
    if "username" in session:
        username = session['username']
        doctor_id = Doctor.get_stu_advs(username)
        return render_template('show_adv.html' , doctor_id = doctor_id )
    else :
        return "you ar not loggrd in "

@app.route("/adv/<id>/updatehtml" , methods = ['GET'])
def adv_updatehtml(id):
    if "username" in session:
        readed = Advising.get(id).readed
        return render_template('update.html' , id = id , readed = readed)
    else :
        return "you ar not loggrd in "

@app.route("/adv/<id>/updatehtml" , methods=['POST'])
def adv_update(id):
    if "username" in session:
        updatedadv = request.form.get('readed')
        Advising.update(id, updatedadv)
        return redirect('/show/adv')
    else :
        return "you ar not loggrd in "


@app.route('/adv/<id>/delete', methods=['GET'])
def delete_adv(id):
    if "username" in session:

        if "username" in session:
            Advising.delete(id)
            return redirect('/show/adv')

        else:
        # user is not logged in --> redirect to login page
            return redirect('/users/login')
    else:
        return "you are not loggedin"



@app.route("/adv/<id>/updatereplay" , methods = ['GET'])
def adv_updatereplay(id):
    if "username" in session:
        replay = Advising.get(id).replay
        return render_template('updatereplay.html' , id = id , replay = replay)
    else:
        return"you are not logged in"
@app.route("/adv/<id>/updatereplay" , methods=['POST'])
def adv_updatreplay(id):
    if "username" in session:
        updatedreplay = request.form.get('replay')
        Advising.updatereplay(id, updatedreplay)
        return redirect('/show/adv')
    else:
        return"you are not logged in"
        

@app.route("/dr/data" , methods = ['GET'])
def get_dr_data():
    if "username" in session:

        dr_username = session['username'] 

    #1 - dr name 
        name = Doctor.getname(dr_username)
    #2 - dr User Name
    #3 - dr email
        email = Doctor.get_email(dr_username)
    #4 - dr Password
        password = Doctor.get_dr_password(dr_username)
    #5 - dr certificates
        certificates = Doctor.get_dr_certificates(dr_username)
    #6 - dr profile pic
    #7 - dr schedual
        stssusername = Doctor.get_schedual(dr_username)
        return render_template('dr-data.html', dr_username = dr_username ,   name = name , email = email ,password= password , certificates = certificates , stssusername = stssusername)
    else :
        return"you dont have access"
@app.route("/dr/scadule" , methods = ['GET'])
def schadule():
    if "username" in session: 
        dr_username = session['username'] 
        stssusername = Doctor.get_schedual(dr_username)
        return render_template('schadule.html', stssusername = stssusername)
    else :
        return"you dont have access"

@app.route("/dr/name/update" , methods=['GET'])
def get_update_dr_name():
    if "username" in session:
        dr_username = session['username'] 
        id = Doctor.getDOCTORid(dr_username)
        name = Doctor.get(id).name
        return render_template('update-dr-name.html', name =name , id = id)
    else:
        return"you dont have access"
@app.route("/dr/name/update" , methods=['POST'])
def post_update_dr_name():
    if "username" in session:
        dr_username = session['username'] 
        id = Doctor.getDOCTORid(dr_username)
        updatedname = request.form.get('name')
        Doctor.update_dr_name(id, updatedname)
        return redirect('/dr/data')
    #update dr username
    else:
        return "you dont have access"
@app.route("/dr/username/update" , methods=['GET'])
def get_update_dr_username():
    if "username" in session:
        dr_susername = session['username'] 
        id = Doctor.getDOCTORid(dr_susername)
        username = Doctor.get(id).username
        return render_template('update_dr_username.html', username =username , id = id)
    else:
        return "you dont have access"
@app.route("/dr/username/update" , methods=['POST'])
def post_update_dr_username():
    if "username" in session:
        dr_username = session['username'] 
        id = Doctor.getDOCTORid(dr_username)
        updatedusername = request.form.get('username')
        Doctor.update_dr_username(id, updatedusername)
        return redirect('/dr/data')
        #update dr pass
    else :
        return" you dont have acccess"
@app.route("/dr/password/update" , methods=['GET'])
def get_update_dr_password():
    if "username" in session:
        dr_susername = session['username'] 
        id = Doctor.getDOCTORid(dr_susername)
        password = Doctor.get(id).password
        return render_template('update_dr_password.html', password =password , id = id)
    else:
        return"you cant access"
@app.route("/dr/password/update" , methods=['POST'])
def post_update_dr_password():
    if "username" in session:
        dr_username = session['username'] 
        id = Doctor.getDOCTORid(dr_username)
        updatedusername = request.form.get('password')
        Doctor.update_dr_password(id, updatedusername)
        return redirect('/dr/data')
    else:
        return "you cant access"


@app.route("/dr/certificates/update" , methods=['GET'])
def get_update_dr_certificates():
    if "username" in session:
        dr_username = session['username'] 
        id = Doctor.getDOCTORid(dr_username)
        certificates = Doctor.get(id).certificates
        return render_template('update_dr_certificates.html', certificates =certificates , id = id)
    else:
        return"ypu cant access"
@app.route("/dr/certificates/update" , methods=['POST'])
def post_update_dr_certificates():
    if "username" in session:
        dr_username = session['username'] 
        id = Doctor.getDOCTORid(dr_username)
        certificates = request.form.get('certificates')
        Doctor.update_dr_certificates(id, certificates)
        return redirect('/dr/data')
    else:
        return "you cant access"













@app.route("/dr/schadule/update" , methods=['GET'])
def get_update_dr_schadule():
        doctor_username = session['username'] 
        id = Schedual.getid(doctor_username)
        saturday = Schedual.get(id).saturday
        sunday = Schedual.get(id).sunday
        monday = Schedual.get(id).monday
        tuesday = Schedual.get(id).tuesday
        wednesday = Schedual.get(id).wednesday
        thursday = Schedual.get(id).thursday
        friday = Schedual.get(id).friday
        return render_template('update_schadule.html',saturday = saturday , sunday = sunday , monday = monday,tuesday = tuesday, friday =friday,wednesday = wednesday, thursday = thursday)


@app.route("/dr/schadule/update" , methods=['POST'])
def post_update_dr_schadule():
    if "username" in session:
        doctor_username = session['username'] 
        id = Schedual.getid(doctor_username)
        schadule = Schedual.query.get(id)
        schadule.saturday = request.form.get("saturday")
        schadule.sunday = request.form.get("sunday")
        schadule.monday = request.form.get("monday")
        schadule.tuesday = request.form.get("tuesday")
        schadule.wednesday = request.form.get("wednesday")
        schadule.thursday = request.form.get("thursday")
        schadule.friday = request.form.get("friday")
        db.session.commit()
        return redirect('/dr/scadule')
    else:
        return "you cant access"







#post regiser informations
@app.route('/register/schedual', methods=['POST'])
def post_reg_schedual():
    if "username" in session:
        doctor_username =session['username'] 

        users=Schedual( request.form['saturday'], request.form['sunday'] , request.form['monday'],request.form['tuesday'],request.form['wednesday'],request.form['thursday'],request.form['friday']  , doctor_username)
      
        db.session.add(users)
        db.session.commit()
        return redirect('/dr/scadule')
    else:
        return"you cant access"





if __name__ == "__main__":
    app.run(debug=True, port=PORT, host='0.0.0.0')

