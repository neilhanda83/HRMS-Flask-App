from flask import Flask, request, jsonify 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, Index
from datetime import datetime
from flask import render_template

app = Flask(__name__)
# Using SQL Alchemy for database access
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://neil:neilhanda@localhost/hrms'
db = SQLAlchemy(app)

class Employees(db.Model):
    """
    Model representing employees.

    Attributes:
        id (int): Primary key.
        name (str): Employee name.
        designation (str): Employee designation.
        department (str): Employee department.
        date_of_joining (Date): Date when the employee joined.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    designation = db.Column(db.String(255))
    department = db.Column(db.String(255))
    date_of_joining = db.Column(db.Date)

class Attendance(db.Model):
    """
    Model representing attendance entries.
    Attributes:
        employee_id (int): Foreign key referencing Employees table.
        date (Date): Date of the attendance entry.
        status (bool): Attendance status (True for 'Present', False for 'Absent').
    Relationships:
        employee (Employees): Relationship with Employees table.
    """
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    status = db.Column(db.Boolean, default=False)  # True for 'Present', False for 'Absent'
    
    # Foreign kkey constraint
    employee = db.relationship('Employees', backref=db.backref('attendances', lazy=True))


@app.route('/')
def hello():
    # return 'Hello, World!'
    """
    Route to display the list of employees on the home page. 
    Also contains link to employee attendance page
    """
    employees = Employees.query.all()
    return render_template('home.html', employees=employees)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    """
    API endpoint to add a new employee.

    Returns:
        json: JSON response indicating success or error.
    """
    try:
        # getting data from request
        data = request.get_json()

        # Create a new employee instance
        new_employee = Employees(
            name=data['name'],
            designation=data['designation'],
            department=data['department'],
            date_of_joining=data['date_of_joining']
        )

        # Add the employee to the database
        db.session.add(new_employee)
        db.session.commit()

        return jsonify({'message': 'Employee added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view_employees', methods=['GET'])
def view_employees():
    """
    API endpoint to view all employees.

    Returns:
        json: JSON response containing the list of all employees.
    """
    employees = Employees.query.all()
    employee_list = [{'name': emp.name, 'designation': emp.designation, 'department': emp.department, 'date_of_joining': str(emp.date_of_joining)} for emp in employees]
    return jsonify(employee_list)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """
    API endpoint to mark attendance for a specific employee on a given date.

    Returns:
        json: JSON response indicating success or error.
    """
    try:
        # Get attendance data from the request
        data = request.get_json()

        # Check if the employee exists
        employee_id = data['employee_id']
        employee = Employees.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        # Check if the attendance entry already exists for the given employee and date
        existing_attendance = Attendance.query.filter_by(employee_id=employee_id, date=data['date']).first()
        if existing_attendance:
            return jsonify({'error': 'Attendance entry already exists for the given employee and date'}), 400

         # Check if the date for marking attendance is after the employee's date of joining- invalid case
        print(data['date'])
        print(employee.date_of_joining)
        if employee.date_of_joining > datetime.strptime(data['date'], '%Y-%m-%d').date():
            return jsonify({'error': 'Attendance cannot be marked before the employee\'s date of joining'}), 400
        
        # Create a new attendance entry
        new_attendance = Attendance(
            employee_id=employee_id,
            date=data['date'],
            status=data['status']
        )

        # Add the attendance entry to the database
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({'message': 'Attendance marked successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/attendance_details/<int:employee_id>', methods=['GET'])
def attendance_details(employee_id):
    """
    API endpoint to retrieve attendance details for a specific employee.

    Returns:
        json: JSON response containing the attendance details.
    """
    try:
        # Check if the employee exists
        employee = Employees.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        # Retrieve attendance details for the specified employee
        attendance_entries = Attendance.query.filter_by(employee_id=employee_id).all()

        if not attendance_entries:
            return jsonify({'message': 'No attendance details found for the specified employee'}), 404

        # Prepare the response data
        attendance_details = [
            {
                'date': entry.date.strftime('%Y-%m-%d'),
                'status': 'Present' if entry.status else 'Absent'
            }
            for entry in attendance_entries
        ]

        return jsonify({'attendance_details': attendance_details}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/employee_report', methods=['GET'])
def employee_report():
    """
    Route to show a simple report displaying the count of employees in each department.

    Returns:
        html: Rendered HTML page with the report.
    """
    # Query the database to get the count of employees in each department
    department_counts = Employees.query.with_entities(Employees.department, db.func.count().label('count')).group_by(Employees.department).all()

    # Render the report template with the department counts
    return render_template('employee_report.html', department_counts=department_counts)

from flask import render_template

@app.route('/employee_details/<int:employee_id>', methods=['GET'])
def employee_details(employee_id):
    """
    Route to display the details of a specific employee, including attendance details.

    Returns:
        html: Rendered HTML page with employee details.
    """
    try:
        # Check if the employee exists
        employee = Employees.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        # Retrieve attendance details for the specified employee
        attendance_entries = Attendance.query.filter_by(employee_id=employee_id).all()

        return render_template('employee_details.html', employee=employee, attendance_entries=attendance_entries)

    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
