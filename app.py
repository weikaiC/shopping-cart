import flask
from flask_restful import Api
from item import Items, Item, Login  # 引用item.py的class物件
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin  # swagger網頁中會用到的擴充功能
from flask_apispec.extension import FlaskApiSpec
from flask_jwt_extended import JWTManager  # 產生token以管理權限

## Flask設定
app = flask.Flask(__name__)
## Flask restful設定
api = Api(app)

app.config["DEBUG"] = True    # 設定跑app時,存檔時會自動rerun一次,就不用先ctrl+c再rerun
app.config["JWT_SECRET_KEY"] = "I_am_key"     # 設定私鑰 

## 建立swagger網頁
app.config.update({    
   'APISPEC_SPEC': APISpec(
       title=' Shopping Mall',   # 網頁標題名稱
       version='v1',
       plugins=[MarshmallowPlugin()],    # 套用擴充功能
       openapi_version='2.0.0'
   ),
   'APISPEC_SWAGGER_URL': '/swagger/',      # URL格式
   'APISPEC_SWAGGER_UI_URL': '/swagger-ui/'      # UI介面的URL格式
})
docs = FlaskApiSpec(app)    # 設定檔寫入swagger文件

## 定義URL(router)
api.add_resource(Items, "/查詢商品")    # 在POSTMAN上輸入"IP/items"時會觸發Items這個class的功能(包含查詢、新增資料)
docs.register(Items)    

api.add_resource(Item, "/item/<int:id>")   # 在POSTMAN上輸入"IP/item/id"時會觸發Item這個class的功能(包含查詢、更新及刪除資料)
docs.register(Item)    

api.add_resource(Login, "/登入")   # 觸發Login這個class的功能
docs.register(Login)    

## 執行主程式
if __name__ == '__main__':    # py3預設的名字為main,此行是確保py3是由name執行
    jwt = JWTManager().init_app(app)
    app.run(host='127.0.0.1', port=10001)


### 開啟瀏覽器查詢"127.0.0.1:10001/swagger-ui"即可進到視覺化SWAGGER網頁 ###
### 或是用POSTMAN輸入指令和form data以執行功能 ###