from extensions import db
from datetime import datetime

class TimeSlot(db.Model):
    __tablename__ = 'time_slot'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(5), nullable=True)
    end_time = db.Column(db.String(5), nullable=True)
    doctor_username = db.Column(db.String(100), db.ForeignKey('doctor.username'), nullable=True)
    
    available_days = db.relationship('AvailableDay', backref='time_slot', lazy=True)

    def __repr__(self):
        return f"<TimeSlot(id={self.id}, time='{self.start_time}-{self.end_time}', doctor='{self.doctor_username}')>"

    @classmethod
    def save_schedule(cls, doctor_username, schedule_data):
        try:
            # --- بداية التعديل ---
            # الخطوة 1: البحث عن كل المواعيد القديمة للطبيب
            slots_to_delete = cls.query.filter_by(doctor_username=doctor_username).all()
            if slots_to_delete:
                slot_ids = [s.id for s in slots_to_delete]
                
                # الخطوة 2: حذف الأيام المتاحة المرتبطة بها أولاً (السجلات الأبناء)
                AvailableDay.query.filter(AvailableDay.time_slot_id.in_(slot_ids)).delete(synchronize_session=False)
                
                # الخطوة 3: حذف المواعيد الزمنية نفسها (السجلات الآباء)
                cls.query.filter(cls.id.in_(slot_ids)).delete(synchronize_session=False)
            # --- نهاية التعديل ---

            # الآن، نقوم بإضافة الجدول الجديد إلى قاعدة بيانات نظيفة
            for slot in schedule_data:
                time_range = slot['time']
                start_time, end_time = time_range.split(' - ')
                available_days = slot['days']

                # هذا المنطق صحيح ويتجاهل المواعيد التي لا تحتوي على أيام متاحة
                if available_days:
                    new_timeslot = cls(
                        start_time=start_time,
                        end_time=end_time,
                        doctor_username=doctor_username
                    )
                    db.session.add(new_timeslot)
                    db.session.flush() # للحصول على 'id' الموعد الجديد

                    for day in available_days:
                        new_day = AvailableDay(
                            day=day,
                            time_slot_id=new_timeslot.id
                        )
                        db.session.add(new_day)

            # تنفيذ كل التغييرات (الحذف والإضافة) في خطوة واحدة
            db.session.commit()
            return True, "تم حفظ الجدول بنجاح."
            
        except Exception as e:
            db.session.rollback() # التراجع عن كل شيء في حال حدوث خطأ
            return False, str(e)


    @classmethod
    def get_doctor_schedule(cls, doctor_username):
        query = cls.query.filter_by(doctor_username=doctor_username).all()
        schedule = []
        for timeslot in query:
            days = [day.day for day in timeslot.available_days]
            schedule.append({
                'time_range': f"{timeslot.start_time} - {timeslot.end_time}",
                'days': days
            })
        return schedule


class AvailableDay(db.Model):
    __tablename__ = 'available_day'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(3), nullable=True) # 'sun', 'mon', 'tue', etc.
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=True)
    
    def __repr__(self):
        return f"<AvailableDay(day='{self.day}', time_slot_id='{self.time_slot_id}')>"