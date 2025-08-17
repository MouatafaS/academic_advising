# ==============================================================================
# app.py - نقطة الدخول الرئيسية للتطبيق (Main Entry Point)
# ==============================================================================

import json as standard_json
from flask import Flask, render_template, request
from datetime import timedelta
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import emit

# ⭐ 1. استيراد الإضافات من ملف extensions.py
from extensions import db, mail, socketio

# استيراد المسارات (Blueprints)
from auth_routes import auth_bp
from doctor_routes import doctor_bp
from student_routes import student_bp

# ==============================================================================
# 2. تعريف الثوابت
# ==============================================================================
PORT = 5000
DB_FILENAME = 'database.db'

# ==============================================================================
# 3. دالة إنشاء التطبيق (Application Factory)
# ==============================================================================
def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'static/images/'
    app.config['SECRET_KEY'] = 'change_this_to_a_random_secret_key'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=115)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILENAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'moustafasamy490@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_google_app_password'
    app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True

    # ⭐ 2. تهيئة الإضافات مع التطبيق
    db.init_app(app)
    mail.init_app(app)
    socketio.init_app(app) # <--- تهيئة socketio مع التطبيق

    # تسجيل المسارات
    app.register_blueprint(auth_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(student_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    return app

# ==============================================================================
# 4. إنشاء التطبيق وتهيئة الإضافات الإضافية
# ==============================================================================
app = create_app()
migrate = Migrate(app, db, render_as_batch=True)

# فلتر Jinja (يبقى كما هو)
@app.template_filter('fromjson')
def fromjson_filter(value):
    if not value: return None 
    try: return standard_json.loads(value)
    except standard_json.JSONDecodeError: return None

# ==============================================================================
# 5. تعريف أحداث SocketIO العامة
# ==============================================================================
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

# (يمكنك إضافة أي أحداث عامة أخرى هنا)

# ==============================================================================
# 6. تشغيل التطبيق (Run)
# ==============================================================================
if __name__ == "__main__":
    # ⭐ 3. استخدم socketio الذي تم استيراده لتشغيل التطبيق
    socketio.run(app, debug=True, port=PORT, host='0.0.0.0', allow_unsafe_werkzeug=True)