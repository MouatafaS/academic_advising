# db_tickets.py

from extensions import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=True, default='New')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys صحيحة تشير إلى id كل جدول
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    advisor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)

    # علاقة لجلب الرسائل داخل هذه التذكرة
    messages = db.relationship('ChatMessage', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket {self.id} for Student {self.student_id}>"