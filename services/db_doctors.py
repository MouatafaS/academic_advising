# db_doctors.py

from extensions import db
from datetime import datetime

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ismadmin = db.Column(db.Boolean, default=False)
    isadmin = db.Column(db.Boolean, default=False)
    
    # تصحيح: تم جعل الحقول الأساسية إجبارية (nullable=True)
    name = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    
    # تصحيح: تغيير اسم العمود وتشفير كلمة المرور
    password = db.Column(db.String(128), nullable=True)
    
    certificates = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(255))

    # --- العلاقات ---
    students_advised = db.relationship('Student', backref='advisor', lazy='dynamic', foreign_keys='Student.advisor_id')
    time_slots = db.relationship('TimeSlot', backref='doctor', lazy='dynamic')
    tickets = db.relationship('Ticket', backref='assigned_advisor', lazy='dynamic', foreign_keys='Ticket.advisor_id')
    
    # علاقة لنموذج Advising القديم



    def __repr__(self):
        return f"<Doctor(id={self.id}, name='{self.name}')>"
    @classmethod
    def update(self, id, name, username, password):
        query = self.query.filter_by(id=id).first()
        query.name = name
        query.username = username
        query.password = password
        db.session.commit()

    @classmethod
    def getUser(self, id):
        query = self.query.filter_by(id=id).first()
        return query

    @classmethod
    def update_dr_name(self, id, name):
        query = self.query.get(id)
        query.name = name
        db.session.commit()

    @classmethod
    def update_dr_username(self, id, username):
        query = self.query.get(id)
        query.username = username
        db.session.commit()
        
    @classmethod
    def update_dr_password(self, id, password):
        query = self.query.get(id)
        query.password = password
        db.session.commit()
    
    @classmethod
    def update_dr_certificates(self, id, certificates):
        query = self.query.get(id)
        query.certificates = certificates
        db.session.commit()

    @classmethod
    def getByUsername(self, username):
        query = self.query.filter_by(username=username).first()
        return query

    @classmethod
    def getByemail(self, name):
        query = self.query.filter_by(name=name).first()
        email = query.email
        return email

    @classmethod
    def get(self, id):
        query = self.query.get(id)
        return query

    @classmethod
    def getschedual(self, name):
        query = self.query.filter_by(name=name).first()
        time_slots = query.time_slots
        return time_slots

    @classmethod
    def getDOCTORSTUDENT(self, username):
        # 1. تحقق من وجود الدكتور أولاً لتجنب الأخطاء
        doctor = self.query.filter_by(username=username).first()
        
        # إذا لم يتم العثور على الدكتور، أرجع قائمة فارغة
        if not doctor:
            return []

        # 2. نفّذ الاستعلام باستخدام .all() للحصول على قائمة
        students_list = doctor.students_advised.all()
        return students_list

    @classmethod
    def get_schedule(self, username):
        query = self.query.filter_by(username=username).first()
        schedule = query.time_slots
        return schedule

    @classmethod
    def getDOCTORid(self, username):
        query = self.query.filter_by(username=username).first()
        id = query.id
        return id



    @classmethod
    def get_email(self, username):
        query = self.query.filter_by(username=username).first()
        email = query.email
        return email

    @classmethod
    def getname(self, username):
        query = self.query.filter_by(username=username).first()
        name = query.name
        return name

    @classmethod
    def get_dr_password(self, username):
        query = self.query.filter_by(username=username).first()
        password = query.password
        return password

    @classmethod
    def get_dr_certificates(self, username):
        query = self.query.filter_by(username=username).first()
        certificates = query.certificates
        return certificates

    @classmethod
    def get_id_bymail(self, email):
        query = self.query.filter_by(email=email).first()
        dr_id = query.id
        return dr_id

    @classmethod
    def get_name_bymail(self, id):
        query = self.query.filter_by(id=id).first()
        dr_name = query.name
        return dr_name

    @classmethod
    def get_usrname_bymail(self, email):
        query = self.query.filter_by(email=email).first()
        dr_name = query.students_advised
        return dr_name

    @classmethod
    def get_cetificates_bymail(self, email):
        query = self.query.filter_by(email=email).first()
        certificates = query.certificates
        return certificates

    @classmethod
    def get_prifile_pic_bymail(self, email):
        query = self.query.filter_by(email=email).first()
        profile_pic = query.profile_pic
        return profile_pic

    @classmethod
    def getUserId(self, username):
        email = self.query.filter_by(username=username).first().email
        return email

    @classmethod
    def get_message_by_id(self, id):
        email = self.query.filter_by(id=id).first().email
        return email