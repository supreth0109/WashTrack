````markdown
# WashTrack

**Campus laundry, without the guesswork.**

WashTrack is a web-based laundry management system built for hostel campuses. It replaces the usual "Where are my clothes?" problem with a simple system for submitting laundry, tracking its progress, verifying handovers, and reporting issues.

The project has two sides: a **Student Portal** for tracking laundry and a **Staff Portal** for managing orders from intake to delivery.

---

## What it does

### Student Portal

Students can:

- Log in using their registration details
- View their laundry orders
- Track the current status of each order
- Search orders by token or clothing
- Filter orders by status
- See their weekly laundry allowance
- Request a re-wash
- Submit complaints

### Staff Portal

Laundry staff can:

- Create new laundry orders
- Record the student's hostel and room
- Add different clothing types and quantities
- Request ironing for an order
- Move orders through each stage of the process
- Verify the student using a 6-digit OTP
- Complete the handover
- View and resolve complaints

---

## Order lifecycle

```text
Submitted
    ↓
In Wash
    ↓
Ready for Pickup
    ↓
OTP Verification
    ↓
Delivered
````

Each order gets a unique token, making it easier for both students and staff to identify it.

---

## Why OTP?

The final handover is not completed just by changing the order status.

When an order is ready, the student provides their OTP to the staff member. The OTP is checked before the order can be marked as **Delivered**.

This adds a simple verification step between:

```text
Ready for Pickup → Delivered
```

---

## Tech Stack

**Frontend**

* HTML
* JavaScript
* Tailwind CSS
* Font Awesome

**Backend**

* Python
* Python HTTP Server
* REST-style API

**Data**

* JSON

The project currently uses a lightweight JSON-based data store, making it simple to run without setting up a separate database.

---

## Project Structure

```text
WashTrack/
├── index.html
├── server.py
├── data.json
├── washtrack_logo.png
└── README.md
```

---

## Running locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/washtrack.git
cd washtrack
```

### 2. Start the server

```bash
python server.py
```

### 3. Open WashTrack

Go to:

```text
http://localhost:5000
```

That's it. No database server or additional Python packages are required for the current version.

---

## Demo staff account

```text
Email:    staff01@laundry.edu
Password: password123
```

This account is included for demonstration and testing.

---

## Current status

**Academic Project / Working Prototype**

The current version focuses on the core laundry workflow and provides a foundation for adding a more complete backend and database later.

---

## Planned improvements

* Proper database integration
* Secure authentication and password handling
* QR/RFID-based clothing identification
* Student notifications
* Admin dashboard and analytics
* Better role-based access control
* Mobile application
* Production-ready deployment

---

## Author

**Supreth S**

B.Tech CSE — AI & ML

---

> WashTrack was built as a practical solution to make campus laundry easier to track, manage, and verify.

```
```
