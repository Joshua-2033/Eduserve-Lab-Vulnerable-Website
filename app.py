from __future__ import annotations
import os, sqlite3
from pathlib import Path
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, abort, jsonify
from werkzeug.security import check_password_hash
from config import Config

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
STATUSES = {'P': 'Present', 'A': 'Absent', 'U': 'Unmarked', 'M': 'Medical', '-': 'No class'}

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def lab_vulnerable():
    return app.config.get('LAB_MODE', 'vulnerable') == 'vulnerable'

def current_user():
    if 'user_id' not in session:
        return None
    return get_db().execute('SELECT id,email,role,display_name FROM users WHERE id=? AND active=1', (session['user_id'],)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user['role'] != 'admin':
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

def get_student_profiles():
    return get_db().execute('''SELECT u.id,u.display_name,u.email,p.registration_no,p.programme,p.department,p.year_of_study
      FROM users u JOIN student_profiles p ON p.user_id=u.id ORDER BY u.display_name''').fetchall()

def attendance_summary(records):
    totals = {'present': 0, 'absent': 0, 'unmarked': 0, 'medical': 0, 'total': 0}
    for rec in records:
        for key in ('hour1','hour2','hour3','hour4'):
            code = rec[key]
            if code == '-':
                continue
            totals['total'] += 1
            totals[{'P':'present','A':'absent','U':'unmarked','M':'medical'}[code]] += 1
    denominator = totals['present'] + totals['absent']
    totals['percentage'] = round(100 * totals['present'] / denominator, 1) if denominator else 0.0
    totals['recorded_hours'] = totals['total']
    return totals

@app.context_processor
def inject_globals():
    user = current_user()
    return {'logged_user': user, 'lab_mode': app.config.get('LAB_MODE', 'vulnerable'), 'statuses': STATUSES}

@app.after_request
def add_baseline_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'same-origin')
    return response

@app.route('/')
def index():
    return redirect(url_for('dashboard') if current_user() else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user = get_db().execute('SELECT * FROM users WHERE email=? AND active=1', (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            if not lab_vulnerable():
                session.clear()
            session['user_id'] = user['id']
            flash('Welcome back. You are signed in.', 'success')
            target = request.args.get('next', '')
            if target.startswith('/') and not target.startswith('//'):
                return redirect(target)
            return redirect(url_for('dashboard'))
        flash('The email or password was not recognized.', 'error')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    flash('You have been signed out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user(); db = get_db()
    profile = db.execute('SELECT * FROM student_profiles WHERE user_id=?', (user['id'],)).fetchone()
    term = db.execute('SELECT * FROM academic_terms WHERE is_current=1 LIMIT 1').fetchone()
    records = db.execute('SELECT * FROM attendance_records WHERE student_id=? AND term_id=? ORDER BY class_date DESC', (user['id'],term['id'])).fetchall() if term and user['role']=='student' else []
    summary = attendance_summary(records)
    assembly_records = db.execute('SELECT assembly_status FROM attendance_records WHERE student_id=? AND term_id=?', (user['id'],term['id'])).fetchall() if term and user['role']=='student' else []
    assembly_present = sum(1 for row in assembly_records if row['assembly_status']=='P')
    assembly_absent = sum(1 for row in assembly_records if row['assembly_status']=='A')
    assembly_denominator = assembly_present + assembly_absent
    assembly_summary = {'percentage': round(100 * assembly_present / assembly_denominator, 1) if assembly_denominator else 0.0}
    course_count = db.execute('SELECT COUNT(*) n FROM enrollments WHERE student_id=? AND status="enrolled"', (user['id'],)).fetchone()['n'] if user['role']=='student' else 0
    results_count = db.execute('SELECT COUNT(*) n FROM assessment_results WHERE student_id=? AND status="Published"', (user['id'],)).fetchone()['n'] if user['role']=='student' else 0
    outstanding_count = db.execute('SELECT COUNT(*) n FROM assessment_results WHERE student_id=? AND status="Pending"', (user['id'],)).fetchone()['n'] if user['role']=='student' else 0
    return render_template('dashboard.html', user=user, profile=profile, summary=summary, assembly_summary=assembly_summary,
                           term=term, course_count=course_count, results_count=results_count, outstanding_count=outstanding_count)

@app.route('/profile')
@login_required
def profile():
    user = current_user(); db = get_db()
    target_id = request.args.get('student_id', type=int) or user['id']
    if not lab_vulnerable() and user['role'] != 'admin' and target_id != user['id']:
        abort(403)
    row = db.execute('SELECT u.id,u.display_name,u.email,p.* FROM users u JOIN student_profiles p ON p.user_id=u.id WHERE u.id=?', (target_id,)).fetchone()
    if not row: abort(404)
    return render_template('profile.html', profile=row)

@app.route('/classes')
@login_required
def classes():
    return render_template('classes/index.html')

@app.route('/classes/timetable')
@login_required
def timetable():
    schedule = [
        {'day':'Monday', 'periods':['Web Application Security', 'Database Systems', '—', 'Agile Software Development']},
        {'day':'Tuesday', 'periods':['Applied Machine Learning', '—', 'Computer Networks', 'Web Application Security']},
        {'day':'Wednesday', 'periods':['Database Systems', 'Data Science for Ecosystems', 'Applied Machine Learning', '—']},
        {'day':'Thursday', 'periods':['—', 'Web Application Security', 'Computer Networks', 'Database Systems']},
        {'day':'Friday', 'periods':['Agile Software Development', 'Applied Machine Learning', '—', 'Data Science for Ecosystems']},
    ]
    return render_template('classes/timetable.html', schedule=schedule)

@app.route('/classes/calendar')
@login_required
def class_calendar():
    user = current_user(); db = get_db()
    terms = db.execute('SELECT * FROM academic_terms ORDER BY starts_on DESC').fetchall()
    term_id = request.args.get('term', type=int)
    if not term_id:
        current = db.execute('SELECT id FROM academic_terms WHERE is_current=1 LIMIT 1').fetchone()
        term_id = current['id'] if current else (terms[0]['id'] if terms else 0)
    records = db.execute('''SELECT a.class_date, a.assembly_status, a.hour1, a.hour2, a.hour3, a.hour4,
                            c.code AS course_code, c.name AS course_name
                            FROM attendance_records a LEFT JOIN courses c ON c.id=a.course_id
                            WHERE a.student_id=? AND a.term_id=? ORDER BY a.class_date''',
                         (user['id'], term_id)).fetchall() if user['role']=='student' else []
    return render_template('classes/calendar.html', records=records, terms=terms, selected_term=term_id)

@app.route('/classes/assembly-attendance')
@login_required
def assembly_attendance():
    user = current_user(); db = get_db()
    terms = db.execute('SELECT * FROM academic_terms ORDER BY starts_on DESC').fetchall()
    term_id = request.args.get('term', type=int)
    if not term_id:
        current = db.execute('SELECT id FROM academic_terms WHERE is_current=1 LIMIT 1').fetchone()
        term_id = current['id'] if current else (terms[0]['id'] if terms else 0)
    records = db.execute('''SELECT class_date, assembly_status FROM attendance_records
                            WHERE student_id=? AND term_id=? ORDER BY class_date DESC''',
                         (user['id'], term_id)).fetchall() if user['role']=='student' else []
    counts = {code: sum(1 for row in records if row['assembly_status']==code) for code in ('P','A','U','M')}
    total = sum(counts.values())
    denom = counts['P'] + counts['A']
    percentage = round(100 * counts['P'] / denom, 1) if denom else 0.0
    summary = {'present':counts['P'], 'absent':counts['A'], 'unmarked':counts['U'],
               'medical':counts['M'], 'total':total, 'percentage':percentage}
    return render_template('classes/assembly_attendance.html', records=records, terms=terms,
                           selected_term=term_id, summary=summary)

@app.route('/classes/attendance')
@login_required
def attendance():
    user = current_user(); db = get_db()
    terms = db.execute('SELECT * FROM academic_terms ORDER BY starts_on DESC').fetchall()
    term_id = request.args.get('term', type=int)
    if not term_id:
        current = db.execute('SELECT id FROM academic_terms WHERE is_current=1 LIMIT 1').fetchone()
        term_id = current['id'] if current else (terms[0]['id'] if terms else 0)
    target_id = request.args.get('student_id', type=int) or user['id']
    if not lab_vulnerable() and user['role'] != 'admin' and target_id != user['id']:
        abort(403)
    records = db.execute('SELECT a.*,c.code course_code,c.name course_name FROM attendance_records a LEFT JOIN courses c ON c.id=a.course_id WHERE a.student_id=? AND a.term_id=? ORDER BY a.class_date DESC', (target_id,term_id)).fetchall()
    summary = attendance_summary(records)
    return render_template('classes/attendance.html', records=records, summary=summary, terms=terms, selected_term=term_id, target_id=target_id)

@app.route('/classes/course-attendance')
@login_required
def course_attendance():
    user = current_user(); db = get_db()
    terms = db.execute('SELECT * FROM academic_terms ORDER BY starts_on DESC').fetchall()
    term_id = request.args.get('term', type=int)
    if not term_id:
        current = db.execute('SELECT id FROM academic_terms WHERE is_current=1 LIMIT 1').fetchone()
        term_id = current['id'] if current else (terms[0]['id'] if terms else 0)
    rows = db.execute('''SELECT c.code, c.name,
             SUM(CASE WHEN a.hour1!='-' THEN 1 ELSE 0 END + CASE WHEN a.hour2!='-' THEN 1 ELSE 0 END +
                 CASE WHEN a.hour3!='-' THEN 1 ELSE 0 END + CASE WHEN a.hour4!='-' THEN 1 ELSE 0 END) AS recorded,
             SUM(CASE WHEN a.hour1='P' THEN 1 ELSE 0 END + CASE WHEN a.hour2='P' THEN 1 ELSE 0 END +
                 CASE WHEN a.hour3='P' THEN 1 ELSE 0 END + CASE WHEN a.hour4='P' THEN 1 ELSE 0 END) AS present,
             SUM(CASE WHEN a.hour1='A' THEN 1 ELSE 0 END + CASE WHEN a.hour2='A' THEN 1 ELSE 0 END +
                 CASE WHEN a.hour3='A' THEN 1 ELSE 0 END + CASE WHEN a.hour4='A' THEN 1 ELSE 0 END) AS absent,
             SUM(CASE WHEN a.hour1='U' THEN 1 ELSE 0 END + CASE WHEN a.hour2='U' THEN 1 ELSE 0 END +
                 CASE WHEN a.hour3='U' THEN 1 ELSE 0 END + CASE WHEN a.hour4='U' THEN 1 ELSE 0 END) AS unmarked,
             SUM(CASE WHEN a.hour1='M' THEN 1 ELSE 0 END + CASE WHEN a.hour2='M' THEN 1 ELSE 0 END +
                 CASE WHEN a.hour3='M' THEN 1 ELSE 0 END + CASE WHEN a.hour4='M' THEN 1 ELSE 0 END) AS medical
             FROM attendance_records a JOIN courses c ON c.id=a.course_id
             WHERE a.student_id=? AND a.term_id=? GROUP BY c.id ORDER BY c.code''',
                       (user['id'], term_id)).fetchall() if user['role']=='student' else []
    enriched=[]
    for row in rows:
        item=dict(row); denom=item['present']+item['absent']
        item['percentage']=round(100*item['present']/denom,1) if denom else 0.0
        enriched.append(item)
    return render_template('classes/course_attendance.html', rows=enriched, terms=terms, selected_term=term_id)

@app.route('/classes/online-feedback', methods=['GET','POST'])
@login_required
def online_class_feedback():
    return feedback()

@app.route('/classes/feedback', methods=['GET','POST'])
@login_required
def feedback():
    db = get_db(); user = current_user()
    if request.method == 'POST':
        category = request.form.get('category','').strip()
        subject = request.form.get('subject','').strip()
        message = request.form.get('message','').strip()
        if category not in {'Teaching','Course materials','Timetable','Facilities','Other'} or not subject or not message or len(subject)>120 or len(message)>3000:
            flash('Please check the category, subject, and message. Messages are limited to 3,000 characters.', 'error')
        else:
            db.execute('INSERT INTO feedback_submissions(student_id,category,subject,message) VALUES(?,?,?,?)', (user['id'],category,subject,message)); db.commit()
            flash('Your feedback has been submitted.', 'success')
            return redirect(url_for('feedback'))
    history = db.execute('SELECT * FROM feedback_submissions WHERE student_id=? ORDER BY created_at DESC,id DESC', (user['id'],)).fetchall()
    return render_template('feedback/index.html', history=history)

@app.route('/examinations')
@login_required
def examinations():
    return render_template('examinations/index.html')

@app.route('/examinations/upcoming')
@login_required
def upcoming():
    rows = get_db().execute('SELECT e.*,c.code,c.name,t.name term_name FROM examinations e JOIN courses c ON c.id=e.course_id JOIN academic_terms t ON t.id=e.term_id WHERE e.exam_date>=date("now") ORDER BY e.exam_date').fetchall()
    return render_template('examinations/upcoming.html', exams=rows)

@app.route('/results')
@login_required
def results():
    user = current_user(); kind = request.args.get('type','IA1')
    if kind not in ('IA1','IA2'): kind='IA1'
    rows = get_db().execute('''SELECT e.assessment_type,e.exam_date,e.max_marks,c.code,c.name,r.marks_obtained,r.status
       FROM assessment_results r JOIN examinations e ON e.id=r.examination_id JOIN courses c ON c.id=e.course_id
       WHERE r.student_id=? AND e.assessment_type=? ORDER BY e.exam_date,c.code''', (user['id'],kind)).fetchall()
    return render_template('examinations/results.html', rows=rows, kind=kind)

@app.route('/fees')
@login_required
def fees(): return render_template('academic/info.html', title='Fees', intro='Fee information for this fictional training account.', items=['Tuition statement: available from Academic Support','Payment status: synthetic demonstration record','No payment is processed by this lab.'])
@app.route('/leave')
@login_required
def leave(): return render_template('academic/info.html', title='Leave', intro='Review the leave workflow for the current academic term.', items=['No pending leave requests','Requests are not submitted to any real institution.'])
@app.route('/hostel')
@login_required
def hostel(): return render_template('academic/info.html', title='Hostel', intro='Accommodation information for this fictional account.', items=['Hostel allocation: Demo Residence','Contact Academic Support for lab questions.'])

@app.route('/course-registration', methods=['GET','POST'])
@login_required
def course_registration():
    user=current_user(); db=get_db()
    if user['role']!='student': abort(403)
    if request.method=='POST':
        course_id=request.form.get('course_id',type=int); term_id=request.form.get('term_id',type=int)
        course=db.execute('SELECT id FROM courses WHERE id=?',(course_id,)).fetchone()
        term=db.execute('SELECT * FROM academic_terms WHERE id=?',(term_id,)).fetchone()
        if not course or not term:
            flash('Select a valid course and term.','error')
        elif not lab_vulnerable() and (term['is_current'] != 1):
            flash('Registration is only available for the current term.','error')
        else:
            try:
                db.execute('INSERT INTO enrollments(student_id,course_id,term_id,status) VALUES(?,?,?,"enrolled")',(user['id'],course_id,term_id)); db.commit()
                flash('Course registration saved.','success')
            except sqlite3.IntegrityError:
                flash('This course is already registered for that term.','error')
        return redirect(url_for('course_registration'))
    courses=db.execute('SELECT * FROM courses ORDER BY code').fetchall(); terms=db.execute('SELECT * FROM academic_terms ORDER BY starts_on DESC').fetchall()
    enrolled=db.execute('SELECT e.*,c.code,c.name,t.name term_name FROM enrollments e JOIN courses c ON c.id=e.course_id JOIN academic_terms t ON t.id=e.term_id WHERE e.student_id=? ORDER BY t.starts_on DESC,c.code',(user['id'],)).fetchall()
    return render_template('academic/registration.html', courses=courses,terms=terms,enrolled=enrolled)

@app.route('/search')
@login_required
def search():
    q=request.args.get('q','').strip()
    if len(q)>100: q=q[:100]
    db=get_db()
    if lab_vulnerable():
        sql = "SELECT id,code,name,faculty FROM courses WHERE name LIKE '%" + q + "%' OR code LIKE '%" + q + "%' ORDER BY code"
        try: rows=db.execute(sql).fetchall()
        except sqlite3.Error: rows=[]
    else:
        rows=db.execute('SELECT id,code,name,faculty FROM courses WHERE name LIKE ? OR code LIKE ? ORDER BY code', (f'%{q}%',f'%{q}%')).fetchall()
    return render_template('search.html', q=q, rows=rows)

@app.route('/student/<int:student_id>/results')
@login_required
def student_results(student_id):
    user=current_user()
    if not lab_vulnerable() and user['role']!='admin' and student_id!=user['id']: abort(403)
    rows=get_db().execute('''SELECT e.assessment_type,e.exam_date,e.max_marks,c.code,c.name,r.marks_obtained,r.status
      FROM assessment_results r JOIN examinations e ON e.id=r.examination_id JOIN courses c ON c.id=e.course_id
      WHERE r.student_id=? ORDER BY e.exam_date,c.code''',(student_id,)).fetchall()
    if not rows and not get_db().execute('SELECT id FROM users WHERE id=? AND role="student"',(student_id,)).fetchone(): abort(404)
    return render_template('examinations/student_results.html', rows=rows, student_id=student_id)

@app.route('/admin/feedback')
@login_required
def admin_feedback():
    user=current_user()
    if not lab_vulnerable() and user['role']!='admin': abort(403)
    rows=get_db().execute('SELECT f.*,u.display_name,u.email FROM feedback_submissions f JOIN users u ON u.id=f.student_id ORDER BY f.created_at DESC,f.id DESC').fetchall()
    return render_template('admin/feedback.html', rows=rows)

@app.route('/admin')
@login_required
@admin_required
def admin_home():
    db=get_db(); users=db.execute('SELECT id,email,display_name,role FROM users ORDER BY role,email').fetchall()
    return render_template('admin/index.html', users=users)

@app.route('/admin/feedback/<int:feedback_id>/status', methods=['POST'])
@login_required
@admin_required
def update_feedback_status(feedback_id):
    status=request.form.get('status','')
    if status not in {'Received','Under review','Resolved'}: abort(400)
    db=get_db(); cur=db.execute('UPDATE feedback_submissions SET status=? WHERE id=?',(status,feedback_id)); db.commit()
    if cur.rowcount==0: abort(404)
    flash('Feedback status updated.','success'); return redirect(url_for('admin_feedback'))

@app.route('/contact-administration')
@login_required
def contact_administration():
    return render_template('academic/info.html', title='Contact Administration', intro='Independent training environment contact details.', items=['Eduserve Academic Administrator','admin@karunya.edu'])

@app.route('/health')
def health():
    return jsonify({'status':'ok','application':'Eduserve Independent Cybersecurity Lab'})

@app.errorhandler(403)
def forbidden(_e): return render_template('errors/error.html', code=403, message='You do not have permission to access this page.'),403
@app.errorhandler(404)
def not_found(_e): return render_template('errors/error.html', code=404, message='The requested page could not be found.'),404
@app.errorhandler(500)
def internal_error(_e):
    get_db().rollback()
    return render_template('errors/error.html', code=500, message='The application encountered an unexpected error.'),500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT','5000')), debug=False)
