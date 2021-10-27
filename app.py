#!/usr/bin/env python
from io import TextIOWrapper
import csv

from flask import Flask, request, redirect, url_for, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import calendar
import json


app = Flask(__name__)
app.secret_key = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Schema
#_______________________________________________________________________
class Employee(db.Model):
    employee_id = db.Column(db.Integer, primary_key=True)
    job_group_type = db.Column(db.String(10))

    def _init_(self, employee_id, job_group_type):
        self.employee_id = employee_id
        self.job_group_type = job_group_type


class Work_record(db.Model):
    record_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer)
    report_number = db.Column(db.Integer) # uploaded report number
    date = db.Column(db.Date)
    hours_worked = db.Column(db.Integer)

    def _init_(self, employee_id, report_number, date, hours_worked):
        self.employee_id = employee_id
        self.report_number = report_number
        self.date = date
        self.hours_worked = hours_worked


class Job_group(db.Model):
    job_group_type = db.Column(db.String(10), primary_key=True)
    job_pay_scale = db.Column(db.Integer)

    def _init(self, job_group_type, job_pay_scale):
        self.job_group_type = job_group_type
        self.job_pay_scale = job_pay_scale
#_______________________________________________________________________


# Setup
#_______________________________________________________________________
@app.before_first_request
def before_first_request_func():
    db.drop_all()
    db.create_all()
    # initialize job group
    db.session.add(Job_group(job_group_type="A", job_pay_scale=20))
    db.session.add(Job_group(job_group_type="B", job_pay_scale=30))

    db.session.commit()
#_______________________________________________________________________


# endpoint for uploading a file
#_______________________________________________________________________
@app.route('/', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        csv_file = request.files['file']
        # check duplicate file
        file_path = csv_file.headers['content-disposition'].split("filename=")[1]
        report_number = file_path.split(".")[0].split("-")[2]
        found_report_id = Work_record.query.filter_by(report_number=report_number).first()
        if found_report_id:
            flash('Error: same report exist, upload failed!')
            return redirect(url_for("upload_csv"))

        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)

        read_csv(csv_reader, report_number)

        flash('upload successfully!')
        return redirect(url_for('upload_csv'))
    return render_template('report.html')


def read_csv(csv_reader, report_number):
    for row in csv_reader:
        date = datetime.strptime(row[0], '%d/%m/%Y').date()
        hours_worked = row[1]
        employee_id = row[2]
        job_group_type = row[3]

        found_employee = Employee.query.filter_by(employee_id=employee_id).first()
        if not found_employee:
            db.session.add(Employee(employee_id=employee_id, job_group_type=job_group_type))

        db.session.add(Work_record(employee_id=employee_id, report_number=report_number, date=date, hours_worked=hours_worked))
        db.session.commit()
#_______________________________________________________________________


# endpoint for retrieving a payroll report
#_______________________________________________________________________
@app.route('/retrieve', methods=['GET'])
def generate_report():
    report_employee_dict = categorize_report()
    
    report = {}
    report["payrollReport"] = {}
    report_employees = []
    for key, value in report_employee_dict.items():
        report_employees.append(value)
    report_employees = sorted(report_employees, key=lambda k : (k.get('employeeId',0), k.get('payPeriod',0).get('startDate',"")))
    report["payrollReport"]["employeeReports"] = report_employees
    report = json.dumps(report, sort_keys=False, indent=4, separators=(',', ': '))
    return render_template('report.html', title="report", jsonfile=report)


def categorize_report():
    employee_pay_map = generate_employee_pay()
    report_employee_dict = {}
    work_records = Work_record.query.all()
    for record in work_records:
        employee_id = record.employee_id
        hours_worked = record.hours_worked
        start_date = categorize_date(record.date, True)
        end_date = categorize_date(record.date, False)
        employee_pay_scale = employee_pay_map[employee_id]
        report_key = str(employee_id)+";"+start_date
        if report_key in report_employee_dict:
            obj = report_employee_dict.get(report_key)
            obj['amountPaid'] = hours_worked * employee_pay_scale + obj['amountPaid']
        else:
            report_employee_dict[report_key] = {
                    "employeeId" : employee_id,
                    "payPeriod" : {
                        "startDate" : start_date,
                        "endDate" : end_date 
                    },
                    "amountPaid" : hours_worked * employee_pay_scale
                }
    return report_employee_dict


def generate_employee_pay():
    employee_pay_map = {}
    employees = Employee.query.all()
    for employee in employees:
        employee_job_type = employee.job_group_type
        employee_pay_scale = Job_group.query.filter_by(job_group_type=employee_job_type).first().job_pay_scale
        employee_pay_map[employee.employee_id] = employee_pay_scale
    return employee_pay_map


def categorize_date(date, is_start_date):
    result_date = None
    if is_start_date:
        result_date = date.replace(day=1) if date.day <= 15 else date.replace(day=16)
    else:
        result_date = date.replace(day=15) if date.day <= 15 else date.replace(day=calendar.monthrange(date.year, date.month)[1])
    result_date = result_date.strftime("%Y-%m-%d")
    return result_date
#_______________________________________________________________________


if __name__ == '__main__':
    app.run()