from flask import Flask, render_template_string, request
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import ssl
import os

app = Flask(__name__)

# Add this right after app is created 
@app.route("/health") 
def health(): 
    return "OK"


# HTML template with status message
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Student Registration</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f9;
            margin: 0;
            padding: 20px;
        }
        h2 {
            color: #2c3e50;
            text-align: center;
        }
        form {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            max-width: 500px;
            margin: auto;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        label {
            font-weight: bold;
            display: block;
            margin-top: 10px;
        }
        input[type="text"], input[type="email"], input[type="number"] {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        input[type="submit"] {
            margin-top: 20px;
            width: 100%;
            padding: 10px;
            background: #3498db;
            color: #fff;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background: #2980b9;
        }
        .receipt {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            max-width: 600px;
            margin: 30px auto;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .receipt strong {
            color: #2c3e50;
        }
        .status {
            margin-top: 10px;
            font-weight: bold;
            color: green;
        }
        .error {
            color: red;
        }
    </style>
    <script>
        function validateForm() {
            let name = document.forms["regForm"]["name"].value;
            let email = document.forms["regForm"]["email"].value;
            let course = document.forms["regForm"]["course"].value;
            let paid = document.forms["regForm"]["paid"].value;

            if (name == "" || email == "" || course == "" || paid == "") {
                alert("Please fill all required fields!");
                return false;
            }
            return true;
        }
    </script>
</head>
<body>
    <h2>Student Registration Form</h2>
    <form name="regForm" method="post" onsubmit="return validateForm()">
        <label>Name:</label>
        <input type="text" name="name" required>

        <label>Contact No:</label>
        <input type="text" name="contact">

        <label>Email:</label>
        <input type="email" name="email" required>

        <label>Course:</label>
        <input type="text" name="course" required>

        <label>Amount Paid:</label>
        <input type="number" name="paid" required>

        <label>Amount Pending:</label>
        <input type="number" name="pending">

        <input type="submit" value="Generate Receipt & Send Email">
    </form>

    {% if receipt %}
    <div class="receipt">
        <h2>Receipt</h2>
        <p><strong>H2RS Bitwave Academy</strong></p>
        <p>{{ name }} successfully registered for course <strong>{{ course }}</strong>.</p>
        <p>Total Fees: Rs{{ total }}</p>
        <p>Received: Rs{{ paid }}</p>
        <p>Pending: Rs{{ pending }}</p>
        <p>Email sent to: <strong>{{ email }}</strong></p>
        <p class="status">{{ status }}</p>
    </div>
    {% endif %}
</body>
</html>
"""

# PDF class
class PDF(FPDF):
    def header(self):
        # Add logo (make sure logo.png is in your project folder)
        #self.image("logo.png", 10, 8, 33)   # x=10, y=8, width=33mm
        self.image(os.path.join(os.path.dirname(__file__), "logo.png"), 10, 8, 33)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "H2RS Bitwave Academy", ln=1, align="C")
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, "Official Invoice", ln=1, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def invoice_body(self, name, course, paid, pending, total):
        self.set_font("Arial", "", 12)

        # Student details section
        self.cell(0, 10, f"Student Name: {name}", ln=1)
        self.cell(0, 10, f"Course: {course}", ln=1)
        self.ln(5)

        # Fees table
        self.set_font("Arial", "B", 12)
        self.cell(60, 10, "Description", 1, 0, "C")
        self.cell(60, 10, "Amount (Rs)", 1, 1, "C")

        self.set_font("Arial", "", 12)
        self.cell(60, 10, "Total Fees", 1, 0)
        self.cell(60, 10, str(total), 1, 1, "R")

        self.cell(60, 10, "Amount Paid", 1, 0)
        self.cell(60, 10, str(paid), 1, 1, "R")

        self.cell(60, 10, "Pending Balance", 1, 0)
        self.cell(60, 10, str(pending), 1, 1, "R")

        self.ln(15)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, "Thank you for registering with H2RS Bitwave Academy!", ln=1, align="C")


# Email function using Hostinger SMTP
def send_email_with_pdf(to_email, pdf_path):
    print("Preparing email...")
    from_email = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.hostinger.com")
    smtp_port = int(os.getenv("SMTP_PORT", 465))

    print(f"Connecting to SMTP server {smtp_server}:{smtp_port} as {from_email}")




    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = "Invoice from H2RS Bitwave Academy"

    body = MIMEText("Please find attached your invoice in PDF format.", "plain")
    msg.attach(body)

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(pdf_path)}"'
    msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            print("Logging in...")
            server.login(from_email, password)
            print("Sending email...")
            server.send_message(msg)
        return "Email sent successfully"
    except Exception as e:
        print(f"Email failed: {e}")
        return f"Failed to send email: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        contact = request.form["contact"]
        email = request.form["email"]
        course = request.form["course"]
        paid = int(request.form["paid"])
        pending = int(request.form["pending"])
        total = paid + pending

        # Generate PDF
        pdf = PDF()
        pdf.add_page()
        pdf.invoice_body(name, course, paid, pending, total)
        pdf_path = f"invoice_{name}.pdf"
        pdf.output(pdf_path)

        # Send email
        status = send_email_with_pdf(email, pdf_path)

        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return render_template_string(template, receipt=True, name=name, course=course,
                                      paid=paid, pending=pending, total=total,
                                      email=email, status=status)
    return render_template_string(template, receipt=False)

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))


