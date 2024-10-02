import tkinter as tk
from tkinter import messagebox
import mysql.connector
from datetime import datetime
from PIL import Image, ImageTk  # For handling images

# Connect to MySQL database
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",  # Replace with your MySQL root password
            database="hospital_db"  # Replace with your database name
        )
    except mysql.connector.Error as e:
        messagebox.showerror("Database Connection Error", str(e))
        return None

# Function to insert a new appointment
def book_appointment():
    name = entry_name.get()
    contact = entry_contact.get()
    doctor = entry_doctor.get()
    date = entry_date.get()
    time = entry_time.get()

    if not (name and contact and doctor and date and time):
        messagebox.showwarning("Input Error", "All fields are required!")
        return

    try:
        # Convert date and time to proper format
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(time, '%H:%M').time()

        db = connect_db()
        if db:
            cursor = db.cursor()

            # Check if there is already an appointment with the same doctor, date, and time
            cursor.execute(
                "SELECT * FROM appointments WHERE doctor_name = %s AND appointment_date = %s AND appointment_time = %s",
                (doctor, date_obj, time_obj)
            )
            existing_appointment = cursor.fetchone()

            if existing_appointment:
                # If there is a conflict, show an error message
                messagebox.showerror("Booking Conflict", f"An appointment is already booked with Dr. {doctor} on {date} at {time}. Please choose a different time.")
                return

            # If no conflict, insert the new appointment
            cursor.execute(
                "INSERT INTO appointments (patient_name, contact, doctor_name, appointment_date, appointment_time) VALUES (%s, %s, %s, %s, %s)",
                (name, contact, doctor, date_obj, time_obj)
            )
            db.commit()
            messagebox.showinfo("Success", "Appointment booked successfully!")
            clear_fields()
            db.close()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Function to view all appointments
def view_appointments():
    try:
        db = connect_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM appointments")
            rows = cursor.fetchall()
            db.close()

            # Show appointments in a new window
            view_window = tk.Toplevel(root)
            view_window.title("View Appointments")
            view_window.configure(bg='#e6f7ff')

            # Use 'Courier' font for proper alignment (monospace font)
            text_area = tk.Text(view_window, width=100, height=20, bg='light blue',fg='black', font=('Courier', 12))
            text_area.pack(pady=10)

            # Properly formatted header using fixed-width spacing
            header = f"{'ID':<5} {'Patient':<20} {'Contact':<15} {'Doctor':<20} {'Date':<12} {'Time':<8}\n"
            text_area.insert(tk.END, header)
            text_area.insert(tk.END, "=" * 80 + "\n")

            for row in rows:
                appointment_id = row[0]
                patient_name = row[1]
                contact = row[2]
                doctor_name = row[3]
                appointment_date = row[4]
                appointment_time = row[5]

                appointment_date_str = appointment_date.strftime('%d-%m-%Y') if isinstance(appointment_date,
                                                                                           datetime) else str(
                    appointment_date)
                appointment_time_str = appointment_time.strftime('%H:%M') if isinstance(appointment_time,
                                                                                        datetime) else str(
                    appointment_time)

                # Ensure each column has a fixed width for alignment
                line = f"{appointment_id:<5} {patient_name:<20} {contact:<15} {doctor_name:<20} {appointment_date_str:<12} {appointment_time_str:<8}\n"
                text_area.insert(tk.END, line)

            text_area.config(state=tk.DISABLED)
    except Exception as e:
        messagebox.showerror("Database Error", str(e))


# Function to clear fields after booking an appointment
def clear_fields():
    entry_name.delete(0, tk.END)
    entry_contact.delete(0, tk.END)
    entry_doctor.delete(0, tk.END)
    entry_date.delete(0, tk.END)
    entry_time.delete(0, tk.END)

# Function to cancel an appointment by ID
def cancel_appointment():
    appointment_id = entry_cancel_id.get()

    if not appointment_id:
        messagebox.showwarning("Input Error", "Please provide an Appointment ID!")
        return

    try:
        db = connect_db()
        if db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
            db.commit()
            if cursor.rowcount > 0:
                messagebox.showinfo("Success", "Appointment canceled successfully!")
            else:
                messagebox.showwarning("Not Found", "No appointment found with that ID!")
            db.close()
            entry_cancel_id.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Function to reschedule an appointment
def reschedule_appointment():
    appointment_id = entry_reschedule_id.get()
    new_date = entry_new_date.get()
    new_time = entry_new_time.get()

    if not (appointment_id and new_date and new_time):
        messagebox.showwarning("Input Error", "All fields are required!")
        return

    try:
        # Convert new date and time to proper format
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
        new_time_obj = datetime.strptime(new_time, '%H:%M').time()

        db = connect_db()
        if db:
            cursor = db.cursor()

            # Fetch the doctor name for the given appointment_id
            cursor.execute("SELECT doctor_name FROM appointments WHERE appointment_id = %s", (appointment_id,))
            result = cursor.fetchone()
            if result:
                doctor_name = result[0]

                # Check if there's already an appointment for the same doctor, date, and time
                cursor.execute(
                    "SELECT * FROM appointments WHERE doctor_name = %s AND appointment_date = %s AND appointment_time = %s AND appointment_id != %s",
                    (doctor_name, new_date_obj, new_time_obj, appointment_id)
                )
                conflict = cursor.fetchone()

                if conflict:
                    # If an appointment already exists for the same date, time, and doctor
                    messagebox.showwarning("Time Slot Unavailable", f"Appointment already booked with Dr. {doctor_name} on {new_date} at {new_time}. Please choose a different time.")
                else:
                    # Proceed with rescheduling
                    cursor.execute(
                        "UPDATE appointments SET appointment_date = %s, appointment_time = %s WHERE appointment_id = %s",
                        (new_date_obj, new_time_obj, appointment_id)
                    )
                    db.commit()
                    if cursor.rowcount > 0:
                        messagebox.showinfo("Success", "Appointment rescheduled successfully!")
                    else:
                        messagebox.showwarning("Not Found", "No appointment found with that ID!")
            else:
                messagebox.showerror("Error", "Appointment ID not found!")

            db.close()
            entry_reschedule_id.delete(0, tk.END)
            entry_new_date.delete(0, tk.END)
            entry_new_time.delete(0, tk.END)

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Main Tkinter window
root = tk.Tk()
root.title("Hospital Appointment Booking System")

# Load background image
try:
    bg_image = Image.open("doctorr.jpg")  # Ensure this file exists in the working directory
    bg_image = bg_image.resize((1920, 1080), Image.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)

    background_label = tk.Label(root, image=bg_photo)
    background_label.place(relwidth=1, relheight=1)
except FileNotFoundError:
    messagebox.showerror("File Not Found", "Background image not found. Please check the file path.")

# Labels and Entry fields for booking
frame = tk.Frame(root, bg='white')
frame.place(relx=0.5, rely=0.5, anchor='center')

tk.Label(frame, text="Patient Name", bg='white', font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=5)
entry_name = tk.Entry(frame, font=('Arial', 12))
entry_name.grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame, text="Contact", bg='white', font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=5)
entry_contact = tk.Entry(frame, font=('Arial', 12))
entry_contact.grid(row=1, column=1, padx=10, pady=5)

tk.Label(frame, text="Doctor Name", bg='white', font=('Arial', 12)).grid(row=2, column=0, padx=10, pady=5)
entry_doctor = tk.Entry(frame, font=('Arial', 12))
entry_doctor.grid(row=2, column=1, padx=10, pady=5)

tk.Label(frame, text="Appointment Date (YYYY-MM-DD)", bg='white', font=('Arial', 12)).grid(row=3, column=0, padx=10, pady=5)
entry_date = tk.Entry(frame, font=('Arial', 12))
entry_date.grid(row=3, column=1, padx=10, pady=5)

tk.Label(frame, text="Appointment Time (HH:MM)", bg='white', font=('Arial', 12)).grid(row=4, column=0, padx=10, pady=5)
entry_time = tk.Entry(frame, font=('Arial', 12))
entry_time.grid(row=4, column=1, padx=10, pady=5)

# Book appointment button
btn_book = tk.Button(frame, text="Book Appointment", command=book_appointment, bg='green', fg='white',
                     font=('Arial', 12))
btn_book.grid(row=5, column=0, columnspan=2, pady=10)

# View appointments button
btn_view = tk.Button(frame, text="View All Appointments", command=view_appointments, bg='blue', fg='white',
                     font=('Arial', 12))
btn_view.grid(row=6, column=0, columnspan=2, pady=10)

# Section to cancel appointment
tk.Label(frame, text="Cancel Appointment by ID", bg='white', font=('Arial', 12)).grid(row=7, column=0, padx=10, pady=5)
entry_cancel_id = tk.Entry(frame, font=('Arial', 12))
entry_cancel_id.grid(row=7, column=1, padx=10, pady=5)

btn_cancel = tk.Button(frame, text="Cancel Appointment", command=cancel_appointment, bg='red', fg='white',
                       font=('Arial', 12))
btn_cancel.grid(row=8, column=0, columnspan=2, pady=10)

# Section to reschedule appointment
tk.Label(frame, text="Reschedule Appointment by ID", bg='white', font=('Arial', 12)).grid(row=9, column=0,
                                                                                             padx=10, pady=5)
entry_reschedule_id = tk.Entry(frame, font=('Arial', 12))
entry_reschedule_id.grid(row=9, column=1, padx=10, pady=5)

tk.Label(frame, text="New Date (YYYY-MM-DD)", bg='white', font=('Arial', 12)).grid(row=10, column=0, padx=10, pady=5)
entry_new_date = tk.Entry(frame, font=('Arial', 12))
entry_new_date.grid(row=10, column=1, padx=10, pady=5)

tk.Label(frame, text="New Time (HH:MM)", bg='white', font=('Arial', 12)).grid(row=11, column=0, padx=10, pady=5)
entry_new_time = tk.Entry(frame, font=('Arial', 12))
entry_new_time.grid(row=11, column=1, padx=10, pady=5)

btn_reschedule = tk.Button(frame, text="Reschedule Appointment", command=reschedule_appointment, bg='orange', fg='white',
                            font=('Arial', 12))
btn_reschedule.grid(row=12, column=0, columnspan=2, pady=10)

# Run the application
root.mainloop()