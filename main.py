import pyotp
import mysql.connector
from load_json import key_and_pass

#認証関数
def verify(key, code):
    #引数としてキーとコードを受け取り認証
    totp = pyotp.TOTP(key)
    return totp.verify(code)

if __name__=="__main__":
    my_json = key_and_pass("./oauth.json","./pass.json")
    while True:
        #tagの認証システム:まだなにも決まっていないのでinput関数を使う
        tag = input("tag_idを入力してください")
        connect = mysql.connector.connect(
            host=my_json.sql_json['host'],
            user=my_json.sql_json['user'],
            password=my_json.sql_json['pass'],
            database=my_json.sql_json['db']
        )

        # 接続確認
        if connect.is_connected():
            print("MySQLサーバーに接続成功!")
            #tag_idにあったstudent_id...を取得
            try:
                with connect.cursor() as cursor:
                    sql = "SELECT student_id, s_key FROM users WHERE tag_id = %s"
                    cursor.execute(sql, (tag,))
                    result = cursor.fetchall()
                if not cursor.rowcount:
                    print("tag_idがありません")
                    continue
            except Exception as e:
                print(str(e))
            finally:
                connect.commit()
                connect.close()
            id = result[0][0]
            key = result[0][1]
            #ユーザーからコードを取得
            code = input("codeを入力してください")
            #認証
            verify_flag = verify(key,code)
            if verify_flag:
                #認証時のプログラムを書く
                print("認証")
            else:
                print("一致しませんでした")
        