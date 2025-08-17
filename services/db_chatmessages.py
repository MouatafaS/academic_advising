# services/db_chatmessages.py

from extensions import db
from datetime import datetime

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # الربط الصحيح مع جدول التذاكر
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)

    # لتحديد هوية المرسل
    sender_id = db.Column(db.Integer, nullable=False)
    sender_role = db.Column(db.String(20), nullable=False) # 'student' أو 'doctor'
    
    # الحقل الجديد لتتبع حالة القراءة
    is_read = db.Column(db.Boolean, default=False, nullable=True)
    
    def __repr__(self):
        return f"<Message by {self.sender_role} {self.sender_id} in Ticket {self.ticket_id}>"