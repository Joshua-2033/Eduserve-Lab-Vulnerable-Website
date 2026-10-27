"""Initialize an empty local database and seed synthetic lab records."""
import os, sqlite3, sys
from pathlib import Path
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
DB=os.getenv('EDUSERVE_DATABASE',str(ROOT/'instance'/'eduserve.sqlite3'))
PASSWORDS={
 'joshua@karunya.edu.in':os.getenv('LAB_JOSHUA_PASSWORD',''),
 'sabari@karunya.edu.in':os.getenv('LAB_SABARI_PASSWORD',''),
 'nithin@karunya.edu.in':os.getenv('LAB_NITHIN_PASSWORD',''),
 'admin@karunya.edu':os.getenv('LAB_ADMIN_PASSWORD','')}
missing=[email for email,pw in PASSWORDS.items() if len(pw)<12 or pw.startswith('change-this-')]
if missing:
 print('Set unique passwords of at least 12 characters in .env before initialization. Missing/placeholder values for: '+', '.join(missing),file=sys.stderr); sys.exit(2)
secret=os.getenv('FLASK_SECRET_KEY','')
if len(secret) < 32 or secret.startswith('replace-with-'):
 print('Set FLASK_SECRET_KEY to a random value of at least 32 characters in .env before initialization.',file=sys.stderr); sys.exit(2)
Path(DB).parent.mkdir(parents=True,exist_ok=True)
if Path(DB).exists():
 print(f'Database already exists: {DB}\nUse scripts/reset_database.py to recreate it intentionally.',file=sys.stderr); sys.exit(1)
conn=sqlite3.connect(DB); conn.execute('PRAGMA foreign_keys=ON')
conn.executescript((ROOT/'database'/'schema.sql').read_text())
users=[
 ('joshua@karunya.edu.in','student','Joshua Mathew','DSC-23-041'),
 ('sabari@karunya.edu.in','student','Sabari Kumar','DSC-23-057'),
 ('nithin@karunya.edu.in','student','Nithin Raj','DSC-23-063'),
 ('admin@karunya.edu','admin','Eduserve Academic Administrator',None)]
ids={}
for email,role,name,reg in users:
 cur=conn.execute('INSERT INTO users(email,password_hash,role,display_name) VALUES(?,?,?,?)',(email,generate_password_hash(PASSWORDS[email]),role,name)); ids[email]=cur.lastrowid
 if role=='student':
  idx=len([x for x in users[:users.index((email,role,name,reg))] if x[1]=='student'])
  details=[('B.Tech Computer Science and Engineering','Data Science and Cyber Security',4,'+91-90000-10041','Coimbatore, Tamil Nadu','2004-02-14'),('B.Tech Computer Science and Engineering','Data Science and Cyber Security',4,'+91-90000-10057','Coimbatore, Tamil Nadu','2004-06-09'),('B.Tech Information Technology','Computer Science and Technology',4,'+91-90000-10063','Coimbatore, Tamil Nadu','2004-09-21')][idx]
  conn.execute('INSERT INTO student_profiles VALUES(?,?,?,?,?,?,?,?)',(cur.lastrowid,reg,*details))
terms=[('Even Semester 2025–26','2026-01-05','2026-05-15',0),('Odd Semester 2026–27','2026-06-15','2026-11-20',1),('Even Semester 2024–25','2025-01-06','2025-05-16',0)]
term_ids={}
for name,start,end,current in terms:
 cur=conn.execute('INSERT INTO academic_terms(name,starts_on,ends_on,is_current) VALUES(?,?,?,?)',(name,start,end,current));term_ids[name]=cur.lastrowid
courses=[('23DC2046','Agile Software Development','Computer Science',3),('23DC2020','Data Science for Ecosystems','Data Science',3),('23CS3012','Web Application Security','Cyber Security',4),('23CS3031','Database Systems','Computer Science',4),('23CS3044','Computer Networks','Computer Science',3),('23DS3020','Applied Machine Learning','Data Science',4)]
course_ids={}
for code,name,faculty,credits in courses:
 cur=conn.execute('INSERT INTO courses(code,name,faculty,credits) VALUES(?,?,?,?)',(code,name,faculty,credits));course_ids[code]=cur.lastrowid
for email,role,name,reg in users:
 if role!='student': continue
 uid=ids[email]; offset={'joshua@karunya.edu.in':0,'sabari@karunya.edu.in':1,'nithin@karunya.edu.in':2}[email]
 for code,_,_,_ in courses[:5]:
  conn.execute('INSERT INTO enrollments(student_id,course_id,term_id,status) VALUES(?,?,?,?)',(uid,course_ids[code],term_ids['Odd Semester 2026–27'],'enrolled'))
 # Attendance is generated from actual stored row values; newest entries intentionally include U.
 for i in range(18):
  from datetime import date,timedelta
  day=date(2026,10,26)-timedelta(days=i*2)
  statuses=['P','P','A','P','M','P','P','A','P','P','U','P','P','A','P','U','P','P']
  base=statuses[(i+offset*2)%len(statuses)]
  if i<3: base='U'
  h1=base; h2=('P' if base=='P' else ('A' if base=='A' else base)); h3=('-' if i%4==0 else ('P' if (i+offset)%3 else 'A')); h4=('-' if i%5==0 else ('U' if i<2 else ('P' if (i+offset)%4 else 'M')))
  assembly='U' if i<2 else ('P' if (i+offset)%5 else 'A')
  conn.execute('INSERT INTO attendance_records(student_id,term_id,course_id,class_date,assembly_status,hour1,hour2,hour3,hour4,note) VALUES(?,?,?,?,?,?,?,?,?,?)',(uid,term_ids['Odd Semester 2026–27'],course_ids[courses[(i+offset)%len(courses)][0]],day.isoformat(),assembly,h1,h2,h3,h4,''))
 for idx,(code,_,_,_) in enumerate(courses[:5]):
  for kind,day in [('IA1',f'2026-08-{10+idx:02d}'),('IA2',f'2026-09-{12+idx:02d}')]:
   exam=conn.execute('INSERT INTO examinations(term_id,course_id,assessment_type,exam_date,max_marks) VALUES(?,?,?,?,?)',(term_ids['Odd Semester 2026–27'],course_ids[code],kind,day,50)).lastrowid
   marks=round(26+((idx*7+offset*4+(0 if kind=='IA1' else 5))%23),1)
   conn.execute('INSERT INTO assessment_results(student_id,examination_id,marks_obtained,status) VALUES(?,?,?,?)',(uid,exam,marks,'Published'))
# Upcoming end-semester assessments make the schedule page useful during the lab.
for idx,(code,_,_,_) in enumerate(courses[:5]):
 conn.execute('INSERT INTO examinations(term_id,course_id,assessment_type,exam_date,max_marks) VALUES(?,?,?,?,?)',(term_ids['Odd Semester 2026–27'],course_ids[code],'End Semester',f'2026-11-{10+idx:02d}',100))
# A synthetic pre-existing feedback record gives the admin review workflow content.
conn.execute('INSERT INTO feedback_submissions(student_id,category,subject,message,status) VALUES(?,?,?,?,?)',(ids['sabari@karunya.edu.in'],'Course materials','Lab schedule','Please publish the next lab schedule a little earlier.','Received'))
conn.commit(); conn.close()
print(f'Initialized {DB}')
print('Seeded three synthetic student accounts and one administrator. Passwords were read from environment configuration and stored only as hashes.')
