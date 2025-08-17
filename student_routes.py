# student_routes.py

from flask import Blueprint, render_template, redirect, session, request, flash, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from extensions import db, socketio
from services.db_students import Student
from services.db_doctors import Doctor
from services.db_schedual import TimeSlot
from services.db_chatmessages import ChatMessage
from services.db_tickets import Ticket
from collections import defaultdict

student_bp = Blueprint('student', __name__)

class TicketForm(FlaskForm):
    subject = StringField('الموضوع', validators=[DataRequired()])
    message = TextAreaField('الرسالة', validators=[DataRequired()])
    submit = SubmitField('إرسال')

@student_bp.route('/user', methods=['GET'])
def show_user():
    if 'id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('auth.login_get')) 
    student_id = session['id']
    student = Student.query.get(student_id)
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for('auth.logout'))
    days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    if not student.advisor_id:
        flash("You have not been assigned an academic advisor yet.", "info")
        return render_template('stu-page.html', student_name=student.name, schedule_grid={}, days_of_week=days_of_week)
    advisor = Doctor.query.get(student.advisor_id)
    if not advisor:
        flash("Could not find the assigned advisor's details.", "error")
        return render_template('stu-page.html', student_name=student.name, schedule_grid={}, days_of_week=days_of_week)
    schedule_data = TimeSlot.get_doctor_schedule(advisor.username)
    schedule_grid = defaultdict(lambda: {day: None for day in days_of_week})
    for item in schedule_data:
        time_range = item['time_range']
        available_days = item['days']
        for day_abbr in available_days:
            day_full_name = day_abbr.capitalize()
            if day_full_name in days_of_week:
                 schedule_grid[time_range][day_full_name] = {'available': True}
    schedule_grid = dict(sorted(schedule_grid.items()))
    return render_template('stu-page.html', 
                           advisor_name=advisor.name, 
                           student_name=student.name,
                           schedule_grid=schedule_grid,
                           days_of_week=days_of_week)

@student_bp.route("/student/tickets", methods=['GET', 'POST'])
def student_tickets():
    if "id" not in session:
        flash("الرجاء تسجيل الدخول للوصول لهذه الصفحة.", "warning")
        return redirect(url_for('auth.login_get'))
    form = TicketForm()
    if form.validate_on_submit():
        student_id  =session['id']
        get_student=Student.query.get(student_id)
        advisor_id = get_student.advisor_id
        new_ticket = Ticket(subject=form.subject.data, student_id=session['id'], status='New', advisor_id = advisor_id)
        db.session.add(new_ticket)
        db.session.flush()
        initial_message = ChatMessage(content=form.message.data, ticket_id=new_ticket.id, sender_id=session['id'], sender_role='student')
        db.session.add(initial_message)
        db.session.commit()
        flash('تم إرسال تذكرتك بنجاح!', 'success')
        return redirect(url_for('student.student_tickets'))
    all_tickets = Ticket.query.filter_by(student_id=session['id']).order_by(Ticket.created_at.desc()).all()
    open_tickets = [t for t in all_tickets if t.status in ('New', 'Open')]
    closed_tickets = [t for t in all_tickets if t.status == 'Closed']
    return render_template('student_tickets.html', form=form, open_tickets=open_tickets, closed_tickets=closed_tickets)

@student_bp.route("/student/ticket/<int:ticket_id>/data")
def get_student_ticket_data(ticket_id):
    if "id" not in session:
        return jsonify(error="Not authenticated"), 403
    ticket = Ticket.query.filter_by(id=ticket_id, student_id=session['id']).first_or_404()
    messages = ticket.messages.order_by(ChatMessage.timestamp.asc()).all()
    ticket_data = { "id": ticket.id, "subject": ticket.subject, "status": ticket.status }
    messages_data = [{
        "content": msg.content,
        "sender_role": msg.sender_role,
        "timestamp": msg.timestamp.strftime('%I:%M %p'),
        "is_read": msg.is_read
    } for msg in messages]
    return jsonify(ticket=ticket_data, messages=messages_data)

@student_bp.route("/student/ticket/<int:ticket_id>/reply", methods=["POST"])
def post_student_reply(ticket_id):
    if "id" not in session:
        return jsonify(success=False, message="Not authenticated"), 403
    ticket = Ticket.query.filter_by(id=ticket_id, student_id=session['id']).first()
    message_content = request.form.get('message_content')
    if not ticket:
        return jsonify(success=False, message="Ticket not found"), 404
    if ticket.status == 'Closed':
        return jsonify(success=False, message="This ticket is closed and cannot be replied to."), 403
    if message_content:
        if ticket.status in ('New', 'Closed'):
            ticket.status = 'Open'
        new_message = ChatMessage(content=message_content, ticket_id=ticket_id, sender_id=session['id'], sender_role='student')
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

@student_bp.route('/student_advising', methods=['GET', 'POST']) # <-- الخطوة 1: السماح بـ POST
def student_advising_get():
    if "id" not in session:
        flash("الرجاء تسجيل الدخول للوصول لهذه الصفحة.", "warning")
        return redirect(url_for('auth.login_get'))

    form = TicketForm()

    # الخطوة 2: إضافة منطق معالجة النموذج
    if form.validate_on_submit():
        student_id = session['id']
        get_student = Student.query.get(student_id)
        advisor_id = get_student.advisor_id

        # التأكد من وجود مرشد أكاديمي
        if not advisor_id:
            flash('لا يمكنك إنشاء تذكرة لأنه لم يتم تعيين مرشد أكاديمي لك بعد.', 'warning')
            return redirect(url_for('student.student_advising_get'))

        new_ticket = Ticket(subject=form.subject.data, student_id=student_id, status='New', advisor_id=advisor_id)
        db.session.add(new_ticket)
        db.session.flush() # للحصول على new_ticket.id قبل الـ commit

        initial_message = ChatMessage(content=form.message.data, ticket_id=new_ticket.id, sender_id=student_id, sender_role='student')
        db.session.add(initial_message)
        db.session.commit()

        flash('تم إرسال تذكرتك بنجاح!', 'success')
        return redirect(url_for('student.student_advising_get')) # <-- إعادة التوجيه لنفس الصفحة

    # الكود الحالي لعرض الصفحة (يبقى كما هو)
    get_student_id = session['id']
    all_tickets = Ticket.query.filter_by(student_id=get_student_id).order_by(Ticket.created_at.desc()).all()

    for ticket in all_tickets:
        ticket.unread_messages = ChatMessage.query.filter_by(
            ticket_id=ticket.id, 
            is_read=False, 
            sender_role='doctor'
        ).count()

    new_tickets = [t for t in all_tickets if t.status == 'New']
    Opened_tickets = [t for t in all_tickets if t.status == 'Open']
    Closed_tickets = [t for t in all_tickets if t.status == 'Closed']

    return render_template(
        'student_advising.html',
        form=form,
        new_tickets=new_tickets,
        Opened_tickets=Opened_tickets,
        Closed_tickets=Closed_tickets
    )


@student_bp.route('/student/ticket/<int:ticket_id>/mark-as-read', methods=['POST'])
def student_mark_as_read(ticket_id):
    if "id" not in session:
        return jsonify(success=False), 403
    ChatMessage.query.filter_by(ticket_id=ticket_id, sender_role='doctor', is_read=False).update({'is_read': True})
    db.session.commit()
    socketio.emit('messages_read', {'ticket_id': ticket_id, 'reader_role': 'student'})
    return jsonify(success=True)