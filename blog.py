from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Girişi Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:

            return f(*args, **kwargs)
        else:
            flash("Bu sayfaya erişmek için kullanıcı girişi yapmanız gerekmektedir!","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kullanici kayit formu
class RegisterForm(Form):

    name = StringField("Adınız:",validators=[validators.length(min= 4,max=20)])
    username = StringField("Kullanıcı adınız:",validators=[validators.length(min=4,max=30,message="Kullanıcı adınız fazla uzun.")])
    email = StringField("E-posta adresiniz:",validators=[validators.email("Lütfen geçerli bir e-posta adresi giriniz.")])
    password = PasswordField("Parolanız:",validators=[
        validators.DataRequired("Lütfen parolanizi giriniz."),
        validators.EqualTo(fieldname="confirmPassword",message="Parolanız uyuşmuyor...")
    ])
    confirmPassword = PasswordField("Parolanizi doğrulayiniz:")

#Kullanici giriş formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı:")
    password = PasswordField("Parola:")

app = Flask(__name__)

#Makale Oluşturma Formu
class AddArticle(Form):
    title = StringField("Makale Adı", validators=[validators.length(min = 5,max =100,message="Lütfen makale adınızın 4-100 karakter arasında olmasına dikkat ediniz!")])
    content = TextAreaField("Makalenin İçeriği", validators=[validators.length(min=10,message="Lütfen makalenize 10 karakterden fazla karakter girin!")])
#Makale Güncelleme
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update_article(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where author = %s and id = %s"

        result = cursor.execute(sorgu,(session["username"],id))
        if result == 0:
            flash("Böyle bir makale yok veya buna yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = AddArticle()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else:
        # Post request
        form = AddArticle(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles set title = %s , content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makaleniz güncellenmiştir.","success")

        return redirect(url_for("dashboard"))

#Secret Key
app.secret_key = "GizliAnahtar"

#App Config
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "arefnueblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#Ana Sayfa
@app.route("/")
def index():

    return render_template("index.html")

#Hakkimizda
@app.route("/about")
def about():

    return render_template("about.html")

#Makaleler
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles "

    result = cursor.execute(sorgu,)

    if result > 0 :
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

# Makale Detay

@app.route("/article/<string:id>")
def article(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if (result > 0):

        article = cursor.fetchone()

        return render_template("article.html",article = article)

    else:
        return render_template("article.html")
#Makale Arama
@app.route("/search", methods = ["GET","POST"])
def search():
    if request.method == "GET":

        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)
            

# Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete_article(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if (result > 0):

        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya buna yetkiniz yok.","danger")
        return redirect(url_for("index"))
#Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()

        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")


#Kayıt Ol
@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,username,email,password))

        mysql.connection.commit()

        cursor.close()
        flash("Tebrikler! Başarıyla kayıt oldunuz...", category = "success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

#Giriş Yap
@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":

        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * from users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if sha256_crypt.verify(password_entered,real_password):
                flash("Tebrikler!\nBaşarıyla giriş yaptınız...","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz...","danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)
#Çıkış Yap
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Makale oluştur
@app.route("/addarticle" , methods = ["GET","POST"])
def addarticle():
    form = AddArticle(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Makale başarıyla eklenmiştir.","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)

if __name__ == "__main__":

    app.run(debug=True)
