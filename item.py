import pymysql
from flask_apispec import MethodResource, marshal_with, doc, use_kwargs   
from flask_jwt_extended import create_access_token, jwt_required  
import item_swagger_model
import msng    # 從同一層資料夾匯入py檔
from datetime import timedelta

## 從localhost連上MySQL
def db_init():
   db = pymysql.connect(
       host='127.0.0.1',
       user='root',
       password='root',
       port=3306,    # 資料庫預設的阜號
       db='shop'   # 資料庫名稱
   )
   cursor = db.cursor(pymysql.cursors.DictCursor)
   return db, cursor

## 使用者登入時自動產生一組token 
def get_access_token(account):
    token = create_access_token(
        identity = {"account": account},
        expires_delta = timedelta(days=1)  # 一天後過期
    )
    return token

## Login時的設置
class Login(MethodResource):
    @doc(description='Please Login First!', tags=['Login'])     # 要顯示在此區塊的描述和大標題
    @use_kwargs(item_swagger_model.LoginSchema, location="form")    # 引用item_swagger_model.py的Schema,建立提供user填寫parameter的欄位
    @marshal_with(item_swagger_model.ItemGetResponse, code=201)     # 引用item_swagger_model.py的Schema,預設Response應該顯示什麼
    def post(self, **kwargs):       # method為post(提交帳號密碼)     # "**kwargs"代表填入的帳號密碼(會自動轉換為字典)
        
        # 連線至cart資料庫並將user輸入的欄位資料轉換為變數
        db, cursor = db_init()
        account, password = kwargs["account"], kwargs["password"]
        
        # 查詢會員表格(cart.member)裡有無此組帳號密碼
        sql = f"SELECT * FROM cart.member WHERE account = '{account}' AND password = '{password}';"   
        cursor.execute(sql)
        item = cursor.fetchall()  
        
        # 登入時直接建立一個此帳號的專屬購物車table(如果他還沒有的話)
        sql2 = f"CREATE TABLE IF NOT EXISTS cart.cart_for_{account} ( id INT NOT NULL AUTO_INCREMENT , account VARCHAR(10) NOT NULL , product_name VARCHAR(20) NOT NULL , price INT(10) NOT NULL , number INT(10) NOT NULL , PRIMARY KEY (id));" 
        cursor.execute(sql2)
        
        # 對於已經登入過的user,保險起見,再次幫他重新計算現在消費total多少
        sql3 = f'SELECT SUM(`price` * `number`) FROM cart.cart_for_{account};'  
        cursor.execute(sql3)
        total = str(cursor.fetchone()['SUM(`price` * `number`)'])
        db.close()
        
        # 如果查到有這組帳密,就提供他專屬的token及成功訊息
        if item != ():
            token = get_access_token(account)
            data = {"message": f"Welcome back {item[0]['account']}",
                    "token": token}
            return msng.success(data,total)      
        return msng.failure({"message":"帳號或密碼輸入錯誤"})


### 定義URL執行"/Items"時可使用的功能
class Items(MethodResource):

   ## 查詢資料
   # 用GET的方法,僅需在parameter輸入account(因為必須先確認要取用哪個會員的表格)和product_name
   # 要有token才能執行!
   # 回傳購物車該產品的所有資訊,同時回報購物車目前total多少
   @doc(description="Your Item", tags=["Item"]) 
   @use_kwargs(item_swagger_model.ItemGetSchema, location="query")    # 僅查詢資料,所以用"query"
   @marshal_with(item_swagger_model.ItemGetResponse, code=201) 
   @jwt_required()        # 需要在postman上的"Authorization"輸入token(login的時候拿到的)才能使用此功能
   def get(self, **kwargs):      #輸入值為account和product_name
       
       # 連線至cart資料庫並將user輸入的欄位資料轉換為變數
       db, cursor = db_init()
       account = kwargs.get("account")       
       product_name = kwargs.get("product_name")  
       
       # 根據指定的product_name查詢該帳戶的專屬cart table,沒指定product_name就整個table列出來
       if product_name is not None:           
           sql = f'SELECT * FROM cart.cart_for_{account} WHERE product_name = "{product_name}";'
       elif product_name is None:
           sql = f'SELECT * FROM cart.cart_for_{account};'   
       cursor.execute(sql)
       items = cursor.fetchall()

       # 怕先前有執行過修改或新增資料的動作,保險起見每次查詢時都再重新計算一次購物車的total金額
       sql2 = f'SELECT SUM(`price` * `number`) FROM cart.cart_for_{account};'  
       cursor.execute(sql2)
       total = str(cursor.fetchone()['SUM(`price` * `number`)'])

       # 確認輸入的account是否有在會員表格(cart.member)裡
       sql3 = f'SELECT * FROM cart.member WHERE account = "{account}";'
       result = cursor.execute(sql3)
       db.close()

       # 回復成功或失敗訊息(account不存在就回報fail)
       if result == 0 :
           return msng.failure({"message": "unknown account"})
       else:
           return msng.success(items,total)  
           

   ## 新增單筆資料
   # 用POST的方法,需在form data輸入一整筆產品的必備資料(product_name、account、price、number)
   # 要有token才能執行!
   # 回傳新增成功或失敗,同時回報購物車目前total多少
   @doc(description="Add More Item!", tags=["Item"])  
   @use_kwargs(item_swagger_model.ItemPostSchema, location="form")     # 要提交form data,所以用"form"
   @marshal_with(item_swagger_model.ItemPostResponse, code=201)
   @jwt_required()  
   def post(self, **kwargs):
       
       # 連線至cart資料庫並將user輸入的欄位資料轉換為變數
       db, cursor = db_init()
       item = {
           'product_name': kwargs.get('product_name'),   
           'account': kwargs.get('account'),  
           'price': kwargs.get('price'),  
           'number': kwargs.get('number')  
       }

       # 將user剛剛輸入的欄位資料新增至他的購物車表格
       sql = """
       INSERT INTO `cart`.`cart_for_{}` (`product_name`,`account`,`price`,`number`)
       VALUES ('{}','{}','{}','{}');
       """.format(item['account'], item['product_name'], item['account'], item['price'], item['number'])
       cursor.execute(sql)
       result = cursor.fetchall()

       # 因為新增了資料,因此必須重新計算一次購物車的total金額
       sql2 = 'SELECT SUM(`price` * `number`) FROM cart.cart_for_{};'.format(item['account'])
       cursor.execute(sql2)
       total = str(cursor.fetchone()['SUM(`price` * `number`)'])
       db.commit()
       db.close()
 
       # 回復成功或失敗訊息(insert不成功就回報fail)
       if result == 0:  
           return msng.failure({"message": "fail"})
       return msng.success(None,total)
 

### 定義URL執行"/Item/{id}"時可使用的功能
class Item(MethodResource):

   ## 查詢單筆資料
   # 用GET的方法,僅需在URL後面加上"/Item/{id}",以及在parameter輸入account(因為必須先確認要取用哪個會員的表格)
   # 要有token才能執行!
   # 回傳這個id的產品資訊,同時回報購物車目前total多少
   @doc(description="Your Item", tags=["Item-by-ID"])  
   @use_kwargs(item_swagger_model.ItemIDSchema, location="query")
   @marshal_with(item_swagger_model.ItemGetResponse, code=201)
   @jwt_required()
   def get(self, id, **kwargs): 

       # 連線至cart資料庫並將user輸入的欄位資料轉換為變數
       db, cursor = db_init()
       account = kwargs.get("account") 

       # 根據指定的id查詢該帳戶的專屬cart table內該項產品的所有資訊
       sql = f"SELECT * FROM cart.cart_for_{account} WHERE id = '{id}';"
       cursor.execute(sql)
       items = cursor.fetchall()

       # 怕先前有執行過修改或新增資料的動作,保險起見每次查詢時都再重新計算一次購物車的total金額
       sql2 = f'SELECT SUM(`price` * `number`) FROM cart.cart_for_{account};'
       cursor.execute(sql2)
       total = str(cursor.fetchone()['SUM(`price` * `number`)'])
       
       # 確認輸入的account是否有在會員表格(cart.member)裡
       sql3 = f'SELECT * FROM cart.member WHERE account = "{account}";'
       result = cursor.execute(sql3)
       db.close()

       # 回復成功或失敗訊息(account不存在就回報fail)
       if result == 0 :
           return msng.failure({"message": "unknown account"})
       else:
           return msng.success(items,total) 
   

   ## 更新單筆資料
   # 用PATCH的方法,需在URL後面加上"/Item/{id}",以及在form data輸入要修改的部分(但account必填!)
   # 要有token才能執行!
   # 回傳更新成功或失敗,同時回報購物車目前total多少
   @doc(description="Update Your Item Data", tags=["Item-by-ID"])  
   @use_kwargs(item_swagger_model.ItemPatchSchema, location="form")
   @marshal_with(item_swagger_model.ItemPostResponse, code=201)
   @jwt_required()  #需要在postman上的"Authorization"登入token(login的時候拿到的)才能使用此功能
   def patch(self, id, **kwargs):

       # 連線至cart資料庫並將user輸入的欄位資料轉換為變數
       db, cursor = db_init()
       item = {
           'product_name': kwargs.get('product_name'),
           'account': kwargs.get('account'),
           'price': kwargs.get('price'),
           'number': kwargs.get('number')
        }

       # 將有輸內容的欄位更新到該會員的購物車表格上
       query = []
       '''{'product_name': None, 'price': None, 'number': None}'''
       for key, value in item.items():
           if value is not None:
               query.append(f"{key} = '{value}'")
       query = ",".join(query)

       sql = """
           UPDATE cart.cart_for_{}
           SET {}
           WHERE id = {};
       """.format(item['account'],query, id)
       result = cursor.execute(sql)
       db.commit()

       # 因為修改了資料,因此必須重新計算一次購物車的total金額
       sql2 = 'SELECT SUM(`price` * `number`) FROM cart.cart_for_{};'.format(item['account'])
       cursor.execute(sql2)
       total = str(cursor.fetchone()['SUM(`price` * `number`)'])
       db.close()

       # 回復成功或失敗訊息(update不成功就回報fail)
       if result == 0:
           return msng.failure({"message": "error"})
       return msng.success(None,total)
   

   ## 刪除單筆資料
   # 用DELETE的方法,僅需在URL後面加上"/Item/{id}",以及在parameter輸入account(因為必須先確認要取用哪個會員的表格)
   # 要有token才能執行!
   # 回傳刪除成功或失敗,同時回報購物車目前total多少
   @doc(description="Don't Want Anymore?", tags=["Item-by-ID"]) 
   @use_kwargs(item_swagger_model.ItemIDSchema, location="query") 
   @marshal_with(item_swagger_model.ItemPostResponse, code=201)
   @jwt_required()   
   def delete(self, id, **kwargs):

       # 連線至cart資料庫並將user輸入的欄位資料轉換為變數
       db, cursor = db_init()
       account = kwargs.get("account") 

       # 根據指定的id,刪除該帳戶專屬cart table內該項產品的所有資訊
       sql = f'DELETE FROM cart.cart_for_{account} WHERE id = {id};'
       result = cursor.execute(sql)
       db.commit()
       
       # 因為刪除了資料,因此必須重新計算一次購物車的total金額
       sql2 = 'SELECT SUM(`price` * `number`) FROM cart.cart_for_{};'.format(account)
       cursor.execute(sql2)
       total = str(cursor.fetchone()['SUM(`price` * `number`)'])
       db.close()

       # 回復成功或失敗訊息(update不成功就回報fail)
       if result == 0:
           return msng.failure({"message": "error"})
       return msng.success(None,total)