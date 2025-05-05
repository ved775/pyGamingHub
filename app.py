import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from db import UserDb
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  
app.config["UPLOAD_FOLDER"] = "static/uploads/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

db = UserDb()

@app.route("/")
def home():
    if "user_id" in session:
        # Check if the user role is 'admin'
        if session.get("user_role") == "admin":
            return redirect(url_for("indexadmin"))  
        else:
            return render_template("loginindex.html")  
    else:
        return render_template("index.html")  


@app.route("/games")
def games():
    if "user_id" in session:
        all_game = db.get_game_name()
        return render_template("game.html",game = all_game,db=db)  
    else:
        return render_template("login.html")

@app.route("/score")
def score():
    user_id = session.get("user_id")
    if "user_id" in session:
        scores = db.get_scores_grouped_by_game(user_id)
        return render_template("score.html", scores=scores)
    else:
        return render_template("login.html")

@app.route("/reg", methods=["GET", "POST"])
def reg():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("registration.html", show_popup=True)

        # Insert user into the database
        if db.add_user(name, email, password):
            flash("Registration successful! Please log in.", "success")  
            return redirect(url_for("login"))  
        else:
            flash("Registration failed. Try again.", "danger")

    return render_template("registration.html")

@app.route("/indexadmin")
def indexadmin():
    if "user_id" in session and session["user_role"] == "admin":
        return render_template("indexadmin.html")  # Admin dashboard
    else:
        return redirect(url_for("loginindex"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["username"]
        password = request.form["password"]

        user = db.get_user(email, password)

        if user:
            session["user_id"] = user[0]
            session["user_email"] = user[2]
            session["user_role"] = user[3]

            db.add_audit_record(session["user_id"], session["user_role"])

            flash("Login successful!", "success")

            if session["user_role"] == "admin":
                return redirect(url_for("indexadmin"))
            else:
                return redirect(url_for("loginindex"))
        else:
            flash("Invalid email, password, or account blocked", "danger")
            return render_template("login.html", show_popup=True)

    return render_template("login.html", show_popup=False)


@app.route("/logout")
def logout():
    if "user_id" in session:
        db.update_logout_time(session["user_id"])  

    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))



@app.route("/loginindex")
def loginindex():
    if "user_id" in session:
        return render_template("loginindex.html")  
    else:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))     

@app.route("/users")
def users():
    if "user_id" in session and session.get("user_role") == "admin":
        all_users = db.get_all_users()
        live_users = db.get_live_users()
        return render_template("user.html", users=all_users, live_users=live_users)
    else:
        flash("You must be an admin to view this page.", "warning")
        return redirect(url_for("home"))  
    
@app.route("/profile/<int:user_id>")
def view_profile(user_id):
    if "user_id" in session and session.get("user_role") == "admin":
        user_info = db.get_user_by_id(user_id)
        user_scores = db.get_user_scores(user_id)
        return render_template("profile_admin.html", user=user_info, scores=user_scores)
    else:
        flash("Access denied.", "danger")
        return redirect(url_for("home"))    

@app.route("/usersaudit")
def usersaudit():
    if "user_id" in session and session.get("user_role") == "user":
        all_usersaudit = db.get_all_usersaudit(session["user_id"])
        return render_template("useraudit.html", usersaudit=all_usersaudit)
    else:
        return render_template("login.html")
    
@app.route("/allaudit")
def allaudit():
    if "user_id" in session and session.get("user_role") == "admin":
        all_audit = db.get_all_audit()
        return render_template("all_audit.html", all_audits=all_audit)
    else:
        flash("Log in first.", "warning")
        return redirect(url_for("home"))       

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if "user_id" in session and session.get("user_role") == "admin":
        db.delete_user(user_id)
        flash("User deleted successfully", "success")
    else:
        flash("Unauthorized action!", "danger")
    return redirect(url_for("users"))

@app.route("/block_user/<int:user_id>")
def block_user(user_id):
    if "user_id" in session and session.get("user_role") == "admin":
        db.update_user_status(user_id, "blocked")
        flash("User blocked successfully", "warning")
    else:
        flash("Unauthorized action!", "danger")
    return redirect(url_for("users"))

@app.route("/unblock_user/<int:user_id>")
def unblock_user(user_id):
    if "user_id" in session and session.get("user_role") == "admin":
        db.update_user_status(user_id, "active")
        flash("User unblocked successfully", "success")
    else:
        flash("Unauthorized action!", "danger")
    return redirect(url_for("users"))

@app.route("/add_admin", methods=["GET", "POST"])
def add_admin():
    if "user_id" in session and session.get("user_role") == "admin":
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            role = "admin"

            db.add_admin(name, email, password, role)
            flash("Admin added successfully!", "success")
            return redirect(url_for("users"))
        
        return render_template("addadmin.html")
    else:
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    if request.method == "POST":
        if "profile_pic" in request.files:
            file = request.files["profile_pic"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                db.update_profile_pic(user_id, filename)
                flash("Profile picture updated!", "success")

    user_data = db.get_user_by_id(user_id)
    return render_template("profile.html", user=user_data)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/play/<game_name>')
def play_game(game_name):
    if game_name == 'Enemy spawner':
        subprocess.Popen(["python", "game1.py", str(session["user_id"])])
        return redirect(url_for('games'))
    elif game_name == 'rock paper scissors':
        subprocess.Popen(["python", "game2.py", str(session["user_id"])])
        return redirect(url_for('games'))
    elif game_name == 'doom':
        subprocess.Popen(["python", "./game3/main.py", str(session["user_id"])])
        return redirect(url_for('games'))
    elif game_name == 'flappy bird':
        subprocess.Popen(["python", "./game4/main.py", str(session["user_id"])])
        return redirect(url_for('games'))
    elif game_name == 'car game':
        subprocess.Popen(["python", "./game5/car_game.py", str(session["user_id"])])
        return redirect(url_for('games'))
    else:
        return "Game not found", 404
    
@app.route("/community_user", methods=["GET", "POST"])
def community_user():
    if "user_id" in session:
        db = UserDb()
        if request.method == "POST":
            post_id = request.form['post_id']
            comment_text = request.form['comment_text']
            user_id = session['user_id']
            db.add_comment(post_id, user_id, comment_text)

        posts = db.get_all_posts()
        for post in posts:
            # Update to handle datetime format issue
            if '.' in post.date_posted:
                date_main, microseconds = post.date_posted.split('.')
                post.date_posted = f"{date_main}.{microseconds[:6]}"  # Keep only up to 6 digits of microseconds
            post.date_posted = datetime.strptime(post.date_posted, "%Y-%m-%d %H:%M:%S.%f")

        comments_by_post = {}
        for post in posts:
            comments = db.get_comments_by_post(post.post_id)
            for comment in comments:
                if isinstance(comment.date, str):
                    dt_str = comment.date
                    if '.' in dt_str:
                        date_main, micro = dt_str.split('.')
                        micro = micro[:6]  # Keep only up to 6 digits of microseconds
                        comment.date = datetime.strptime(f"{date_main}.{micro}", "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        comment.date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            comments_by_post[post.post_id] = comments
        return render_template("community_user.html", posts=posts, comments_by_post=comments_by_post)
    return render_template("login.html")
    
@app.route("/community_admin", methods=["GET", "POST"])
def community_admin():
    if "user_id" in session and session.get('user_role') == 'admin':
        if request.method == "POST":
            title = request.form['title']
            content = request.form['content']
            admin_id = session['user_id']
            if db.add_post(title, content, admin_id):
                flash("Post added successfully!", "success")
            else:
                flash("Failed to add post.", "danger")
        return render_template("community_admin.html")
    return redirect("/login")  
    
@app.route("/admin_community", methods=["GET", "POST"])
def admin_community():
    if "user_id" in session and session.get('user_role') == 'admin':
        db = UserDb()
        if request.method == "POST":
            post_id = request.form['post_id']
            comment_text = request.form['comment_text']
            user_id = session['user_id']
            db.add_comment(post_id, user_id, comment_text)

        posts = db.get_all_posts()
        for post in posts:
            # Update to handle datetime format issue
            if '.' in post.date_posted:
                date_main, microseconds = post.date_posted.split('.')
                post.date_posted = f"{date_main}.{microseconds[:6]}"  # Keep only up to 6 digits of microseconds
            post.date_posted = datetime.strptime(post.date_posted, "%Y-%m-%d %H:%M:%S.%f")

        comments_by_post = {}
        for post in posts:
            comments = db.get_comments_by_post(post.post_id)
            for comment in comments:
                if isinstance(comment.date, str):
                    dt_str = comment.date
                    if '.' in dt_str:
                        date_main, micro = dt_str.split('.')
                        micro = micro[:6]  # Keep only up to 6 digits of microseconds
                        comment.date = datetime.strptime(f"{date_main}.{micro}", "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        comment.date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            comments_by_post[post.post_id] = comments
        return render_template("admin_comment.html", posts=posts, comments_by_post=comments_by_post)
    return redirect("/login")    

@app.route("/forget_password", methods= ["GET", "POST"])
def forget_password():
    if request.method == "POST":
        email = request.form["email"]
        mail = db.get_mail(email)
        if mail:
            from_address = "pygamingh@gmail.com"
            to_address = email
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['email'] = email

            # Email content
            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = to_address
            msg['Subject'] = "Your OTP for Password Reset"

            body = f"Hello,\n\nYour OTP for password reset is: {otp}\n\nThank you,\nPyGaming Hub Team"
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_address, "hmygryfkhlmolqvw")
            server.sendmail(from_address, to_address, msg.as_string())
            server.quit()

            #flash("OTP sent to your email.", "success")
            return redirect(url_for('verify_otp'))
        else:
            flash("Email is not register!","danger")      
    return render_template("forgot.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]
        email = request.form["email"]
        if entered_otp == session.get("otp"):
            return redirect(url_for('change_password'))
        else:
            flash("Incorrect OTP. Please try again.", "danger")
    return render_template("otp.html", email=session.get("email"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        new_password = request.form["password"]
        email = request.form["email"]
        db.update_password(email, new_password)
        flash("Password changed successfully. Please login.", "success")
        return redirect(url_for('login'))
    return render_template("change_password.html", email=session.get("email"))

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user_id" in session and session.get("user_role") == "user":
        if request.method == "POST":
            user_id = session["user_id"]  # Assuming the user ID is stored in session
            game_id = request.form["game"]
            content = request.form["message"]

            # Add feedback to the database
            if db.add_feedback(user_id, game_id, content):
                flash("Thank you for your feedback!", "success")
            else:
                flash("Error while submitting your feedback. Please try again.", "danger")

            return redirect(url_for('feedback'))  # Redirect to the feedback page after submission

        return render_template("feedback.html")
    else:
        return render_template("login.html")
 
@app.route("/feedback_admin", methods=["GET", "POST"])
def feedback_admin():
    if "user_id" in session and session.get("user_role") == "admin":
        if request.method == "POST":
            selected_ids = request.form.getlist('feedback_ids')
            db.update_feedback_consideration(selected_ids)
            flash("Selected feedback marked as considered.", "success")
            return redirect(url_for('feedback_admin'))

        feedbacks = db.get_all_feedback()
        return render_template("feedback_admin.html", feedbacks=feedbacks)
    return render_template("login.html")

@app.route("/considered_feedback")
def considered_feedback():
    if "user_id" in session and session.get("user_role") == "admin":
        feedbacks = db.get_considered_feedback()
        return render_template("feedback_admin.html", feedbacks=feedbacks)
    return render_template("login.html")


    
if __name__ == "__main__":
    app.run(debug=True)
