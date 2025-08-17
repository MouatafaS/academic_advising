# doctor_routes.py

from flask import Blueprint, render_template, redirect, session, request,url_for,current_app,flash,json,jsonify
import os
from werkzeug.utils import secure_filename
from extensions import socketio
from extensions import db

from services.db_students import *
from services.db_doctors import *
from services.db_schedual import *
from services.db_tickets import *
from services.db_chatmessages import *

# تعريف الـ Blueprint
doctor_bp = Blueprint('doctor', __name__)

# --- المسارات ---
@doctor_bp.route('/user/drinfo', methods=['GET'])
def get_DOCTORS():
    if "username" in session:
        uname = session['username']
        stssusername = Doctor.getDOCTORSTUDENT(uname)
        print('students are:', stssusername)
        return render_template('drinfo.html', stssusername=stssusername)
    else:
        return render_template('wrong page.html')

@doctor_bp.route('/stsusername/<id>/edit', methods=['POST'])
def update_stusername(id):
    if "username" not in session:
        return render_template('wrong page.html')
    student_to_update = Student.query.get(id)
    if not student_to_update:
        return "Student not found", 404
    new_stusername = request.form.get('stusername')
    new_name = request.form.get('name')
    new_password = request.form.get('password')
    if new_stusername:
        student_to_update.stusername = new_stusername
    if new_name:
        student_to_update.name = new_name
    if new_password:
        student_to_update.password = new_password
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating student: {e}")
        return "An error occurred while updating.", 500
    return redirect('/user/drinfo')

@doctor_bp.route('/stuname/<id>/edit', methods=['GET'])
def get_student_name(id):
    name = Student.get(id).name
    return render_template('update_student_name.html', id=id, name=name)

@doctor_bp.route('/stuname/<id>/edit', methods=['POST'])
def update_student_name(id):
    if "username" in session:
        updatedname = request.form.get('name')
        Student.update_name(id, updatedname)
        return redirect('/user/drinfo')
    else:
        return redirect('/users/login')

@doctor_bp.route('/stsusername/<id>/delete', methods=['GET'])
def delete_stusername(id):
    if "username" in session:
        Student.delete(id)
        return redirect('/user/drinfo')
    else:
        return redirect('/users/login')

@doctor_bp.route('/stsusername', methods=['POST'])
def add_stusername():
    if "username" in session:
        username = session['username']
        stusername = request.form.get('stusername')
        name = request.form.get('name')
        password = request.form.get('password')
        advisor_id = Doctor.getDOCTORid(username)
        Student.insert(stusername,name,password,advisor_id)
        return redirect('/user/drinfo')
    else:
        return redirect('/login')

@doctor_bp.route("/show/adv")
def show_advisor_dashboard():
    if "username" not in session:
        return "Please log in to view this page.", 403
    advisor = Doctor.query.filter_by(username=session['username']).first()
    if not advisor:
        return "Advisor not found.", 404

    all_tickets = advisor.tickets.order_by(Ticket.created_at.desc()).all()
    
    # حساب الرسائل غير المقروءة لكل تذكرة
    for ticket in all_tickets:
        ticket.unread_messages = ChatMessage.query.filter_by(
            ticket_id=ticket.id, 
            is_read=False, 
            sender_role='student'
        ).count()

    new_tickets = [t for t in all_tickets if t.status == 'New']
    open_tickets = [t for t in all_tickets if t.status == 'Open']
    closed_tickets = [t for t in all_tickets if t.status == 'Closed']
    
    return render_template(
        'show_adv.html',
        new_tickets=new_tickets,
        open_tickets=open_tickets,
        closed_tickets=closed_tickets
    )

@doctor_bp.route("/dr/data", methods=['GET'])
def get_dr_data():
    if "username" in session:
        dr_username = session['username']
        doctor = Doctor.query.filter_by(username=dr_username).first()
        name = doctor.name
        email = doctor.email
        certificates = doctor.certificates
        doctor_schedule = TimeSlot.get_doctor_schedule(dr_username)
        return render_template('dr-data.html', 
                               doctor=doctor, 
                               dr_username=dr_username, 
                               name=name, 
                               email=email,
                               certificates=certificates,
                               schedule=doctor_schedule)
    else:
        return "You don't have access."

@doctor_bp.route('/dr/save_schedule', methods=['POST'])
def save_schedule():
    if "username" not in session:
        return jsonify(success=False, message="You don't have access."), 403
    dr_username = session['username']
    data = request.json
    success, message = TimeSlot.save_schedule(dr_username, data)
    if success:
        return jsonify(success=True)
    else:
        return jsonify(success=False, message=message), 500

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doctor_bp.route("/dr/data", methods=['POST'])
def update_dr_data():
    if "username" in session:
        dr_username = session['username']
        doctor = Doctor.query.filter_by(username=dr_username).first()
        if not doctor:
            return "Doctor not found", 404
        # ... (باقي كود تحديث بيانات الدكتور)
        db.session.commit()
        flash(json.dumps({'message': 'Your Data updated successfully.', 'role': 'user_action'}), 'success')
        return redirect('/dr/data')
    else:
        return "You don't have access", 403

@doctor_bp.route("/ticket/<int:ticket_id>/data")
def get_ticket_data(ticket_id):
    if "username" not in session:
        return jsonify(error="Not authenticated"), 403
    ticket = Ticket.query.get_or_404(ticket_id)
    messages = ticket.messages.order_by(ChatMessage.timestamp.asc()).all()
    ticket_data = { "id": ticket.id, "subject": ticket.subject, "status": ticket.status }
    messages_data = [{
        "content": msg.content,
        "sender_role": msg.sender_role,
        "timestamp": msg.timestamp.strftime('%I:%M %p'),
        "is_read": msg.is_read
    } for msg in messages]
    return jsonify(ticket=ticket_data, messages=messages_data)

@doctor_bp.route("/ticket/<int:ticket_id>/reply", methods=["POST"])
def post_reply(ticket_id):
    if "username" not in session:
        return jsonify(success=False, message="Not authenticated"), 403
    advisor = Doctor.query.filter_by(username=session['username']).first()
    message_content = request.form.get('message_content')
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify(success=False, message="Ticket not found"), 404
    if ticket.status == 'Closed':
        return jsonify(success=False, message="This ticket is closed and cannot be replied to."), 403
    if message_content and advisor:
        if ticket.status == 'New':
            ticket.status = 'Open'
        new_message = ChatMessage(content=message_content, ticket_id=ticket_id, sender_id=advisor.id, sender_role='doctor')
        db.session.add(new_message)
        db.session.commit()
        message_data = {
            'content': new_message.content,
            'sender_role': new_message.sender_role,
            'timestamp': new_message.timestamp.strftime('%I:%M %p'),
            'ticket_id': new_message.ticket_id
        }
        socketio.emit('new_message', message_data)
        return jsonify(success=True)
    return jsonify(success=False, message="Invalid data"), 400

@doctor_bp.route('/ticket/update-status', methods=['POST'])
def update_ticket_status():
    if "username" not in session:
        return jsonify(success=False, message="Not authenticated"), 403
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    new_status = data.get('new_status')
    if new_status not in ['New', 'Open', 'Closed']:
        return jsonify(success=False, message="Invalid status"), 400
    ticket = Ticket.query.get(ticket_id)
    advisor = Doctor.query.filter_by(username=session['username']).first()
    if ticket and advisor and ticket.advisor_id == advisor.id:
        ticket.status = new_status
        db.session.commit()
        return jsonify(success=True, message=f"Ticket {ticket_id} status updated to {new_status}")
    return jsonify(success=False, message="Ticket not found or access denied"), 404

@doctor_bp.route('/ticket/<int:ticket_id>/mark-as-read', methods=['POST'])
def mark_messages_as_read(ticket_id):
    if "username" not in session:
        return jsonify(success=False), 403
    ChatMessage.query.filter_by(ticket_id=ticket_id, sender_role='student', is_read=False).update({'is_read': True})
    db.session.commit()
    socketio.emit('messages_read', {'ticket_id': ticket_id, 'reader_role': 'doctor'})
    return jsonify(success=True)