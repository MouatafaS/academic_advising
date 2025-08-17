# extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_socketio import SocketIO
from sqlalchemy import MetaData

# ==============================================================================
# 1. تعريف اصطلاح التسمية (Naming Convention) لحل مشكلة أسماء القيود
# ==============================================================================
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# إنشاء كائن MetaData مع اصطلاح التسمية الذي عرفناه
metadata = MetaData(naming_convention=convention)

# ==============================================================================
# 2. تهيئة الإضافات مع تمرير الـ MetaData إلى SQLAlchemy
# ==============================================================================

# ✅ قاعدة البيانات مع تطبيق قواعد التسمية
db = SQLAlchemy(metadata=metadata)

# ✅ باقي الإضافات
mail = Mail()
socketio = SocketIO()