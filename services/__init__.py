# __init__.py

from .db_doctors import Doctor
from .db_students import Student
from .db_schedual import TimeSlot

# تصحيح: تم استيراد كل كلاس من ملفه الصحيح
from .db_tickets import Ticket
from .db_chatmessages import ChatMessage

__all__ = [
    'Doctor',
    'Student',
    'TimeSlot',
    'Ticket', # تصحيح: اسم الكلاس مفرد
    'ChatMessage'
]