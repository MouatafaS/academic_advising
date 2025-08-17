# db_students.py

from extensions import db
from datetime import datetime

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=True)
    
    # تصحيح: جعل اسم المستخدم فريدًا وإجباريًا
    stusername = db.Column(db.String(80), unique=True, nullable=True)
    
    # تصحيح: تم حذف unique=True من الاسم
    name = db.Column(db.String(100), nullable=True)
    
    # تصحيح: تغيير اسم العمود وتشفير كلمة المرور
    password = db.Column(db.String(128), nullable=True)
    
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # تصحيح: الربط الصحيح مع id المرشد
    advisor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)

    # --- العلاقات ---
    tickets = db.relationship('Ticket', backref='requesting_student', lazy='dynamic', foreign_keys='Ticket.student_id')



    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"

    @classmethod
    def getUsermial(self, id):
        mail = self.query.filter_by(id=id).first().doctor_email
        return mail

    @classmethod
    def insert(self, stusername,name,password,doctor_email):

        stusername = Student(stusername=stusername,name = name,password = password,doctor_email=doctor_email)

        # add to db and commit
        db.session.add(stusername)
        db.session.commit()

    @classmethod
    def get_adv_by_id(self, id):
        query = self.query.filter_by(id=id).first()
        adv = query.isadmin

        return adv



    @classmethod
    def get_nam_by_iid(self, id):
        query = self.query.filter_by(id=id).first()
        adv = query.stusername

        return adv
    @classmethod
    def update(self, id, stusername):
        
        query = self.query.get(id)

        # update values in query
        query.stusername = stusername

        query.date_created = datetime.utcnow()

        # commit the updates
        db.session.commit()

    @classmethod
    def update_name(self, id, name):
        
        query = self.query.get(id)

        # update values in query
        query.name = name

        # commit the updates
        db.session.commit()



    @classmethod
    def delete(self, id):

        query = self.query.get(id)
        db.session.delete(query)
        db.session.commit()

    @classmethod
    def get(self, id):

        query = self.query.get(id)

        return query

    @classmethod
    def getByname(self, name):
        query = self.query.filter_by(name=name).first()
        return query
    
    @classmethod
    def getByUsername(self, username):
        query = self.query.filter_by(username=username).first()
        return query

    @classmethod
    def getUserId(self, name):
        '''
        get id associated with the given username
        '''
        id = self.query.filter_by(name=name).first().id
        return id

    @classmethod
    def getUsersessions(self, id):

        query = self.query.filter_by(id=id).first()
        sessionSS = query.advise

        return sessionSS  
    @classmethod
    def getUser_id_bymail(self, doctor_email):

        query = self.query.filter_by(doctor_email=doctor_email).first()
        stu_id = query.id

        return stu_id

        
        

    @classmethod
    def getUsersessionsid(self, stusername):

        query = self.query.filter_by(stusername=stusername).first()
        id = query.id

        return id
    @classmethod
    def getUsersessions_sts(self, stusername):

        query = self.query.filter_by(stusername=stusername).first()
        sessionSSq = query.advise

        return sessionSSq