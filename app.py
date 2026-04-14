from flask import Flask, redirect, url_for, request, session, render_template
from authlib.integrations.flask_client import OAuth
from load_json import key_and_pass
import mysql.connector
import pyotp
import qrcode
import base64
import io
import os

#oauth及びsql接続用のパスワード等を書いたjsonを読み込み
my_json = key_and_pass("./oauth.json","./pass.json")

#flaskの設定
app = Flask(__name__)
#session用のシークレットキーの発行
app.secret_key = os.urandom(32)
#oauth用の設定
app.config['GOOGLE_CLIENT_ID'] = my_json.oauth_json['id']
app.config['GOOGLE_CLIENT_SECRET'] = my_json.oauth_json['key']
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

#pyotpのキーとQRを発行する関数
def get_key_qr(id):
    #base32のkeyを作成
    key = pyotp.random_base32()
    totp = pyotp.TOTP(key)
    #QRコードを生成
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2,
    )
    qr.add_data(totp.provisioning_uri(name="shuseki_kanri", issuer_name=id))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img, key

#トップページ
@app.route('/')
def index():
    return render_template('index.html')

#ログイン開始
@app.route('/login', methods=['GET', 'POST'])
def login():
    #トップページから正常に飛ばされているとPOSTメソッドとなるので確認
    if request.method == "POST":
        session['student_id'] =request.form['student_id']
        redirect_uri = url_for('callback', _external=True)
        return google.authorize_redirect(redirect_uri)
    else:
        session.clear()
        return render_template('error.html',error="正常なPOSTメッソドで入っていません.<br><a href='./'>トップページからやり直す.</a>")

#コールバック
@app.route('/callback')
def callback():
    token = google.authorize_access_token()
    student_id = session['student_id']
    session.clear()
    #ユーザー情報を取得
    resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
    user_info = resp.json()
    if student_id in user_info['email']:
        connect = mysql.connector.connect(
            host=my_json.sql_json['host'],
            user=my_json.sql_json['user'],
            password=my_json.sql_json['pass'],
            database=my_json.sql_json['db']
        )

        # 接続確認
        if connect.is_connected():
            print("MySQLサーバーに接続成功!")
            try:#mysqlのサーバーとの
                img, key = get_key_qr(student_id)
                with connect.cursor() as cursor:
                    sql = """
                        UPDATE users 
                        SET mail=%s, s_key=%s, on_flag=1 
                        WHERE student_id=%s AND on_flag=0
                    """
                    cursor.execute(sql, (user_info['email'], key, student_id))
                if cursor.rowcount:
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    img_base64 = base64.b64encode(buf.getvalue()).decode()
                    connect.commit()
                    connect.close()
                    student_id = student_id
                    return render_template("success.html",name=user_info['name'],email=user_info['email'],img_base64=img_base64,student_id=student_id)
                else:
                    return render_template("yet.html")
            except Exception as e:
                return render_template("error.html",error="予期せぬエラーが発生しました.サイト管理者にお問い合わせください<br>エラー内容:"+str(e))
        else:
            return render_template("error.html",error="データーベース接続エラーです.")   
    else:
        return render_template("error.html",erroe="学籍番号とメールが一致しないですがないです.")


if __name__ == '__main__':
    app.run(debug=True)