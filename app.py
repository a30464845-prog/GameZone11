from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = "gaming_secret_123_super_secure"

# --- Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Yahan se aap apna Username aur Password change kar sakte hain
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123" 

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None
# -------------------

DATA_FILE = "database.json"
UPLOAD_FOLDER = "static/images"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route("/")
def home():
    all_items = load_data()
    return render_template("index.html", items=all_items, show_form=False, active_tab="all")

@app.route("/category/<cat_type>")
def category(cat_type):
    all_items = load_data()
    if cat_type != "all":
        all_items = [item for item in all_items if item.get("type") == cat_type]
    return render_template("index.html", items=all_items, show_form=False, active_tab=cat_type)

# --- Login aur Logout Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user = User(username)
            login_user(user)
            flash("Successfully Login!", "success")
            return redirect(url_for("home"))
        else:
            flash("Ghalat Username ya Password!", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Aap logout ho gaye hain.", "success")
    return redirect(url_for("home"))
# -------------------------------

@app.route("/add", methods=["GET", "POST"])
@login_required 
def add_item():
    if request.method == "POST":
        title = request.form.get("title")
        item_type = request.form.get("type")
        genre = request.form.get("genre")
        size = request.form.get("size")
        link = request.form.get("link")
        description = request.form.get("description")

        image_filename = ""
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "":
                ext = file.filename.split(".")[-1]
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        all_items = load_data()
        new_id = len(all_items) + 1
        
        new_item = {
            "id": new_id,
            "title": title,
            "type": item_type,
            "genre": genre,
            "size": size,
            "link": link,
            "description": description,
            "image": image_filename
        }
        
        all_items.append(new_item)
        save_data(all_items)
        flash(f"{title} successfully add ho gaya!", "success")
        return redirect(url_for("category", cat_type=item_type))

    return render_template("index.html", items=load_data(), show_form=True, active_tab="add")

@app.route("/delete/<int:item_id>")
@login_required
def delete_item(item_id):
    all_items = load_data()
    item_to_delete = next((item for item in all_items if item["id"] == item_id), None)
    
    if item_to_delete:
        if item_to_delete.get("image"):
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], item_to_delete["image"])
            if os.path.exists(img_path):
                os.remove(img_path)
        
        all_items = [item for item in all_items if item["id"] != item_id]
        
        for i, item in enumerate(all_items, start=1):
            item["id"] = i
            
        save_data(all_items)
        flash("Item delete ho gaya!", "success")
        return redirect(url_for("category", cat_type=item_to_delete.get("type", "all")))

    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)