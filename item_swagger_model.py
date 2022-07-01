from marshmallow import Schema, fields  # fields定義出在GET/POST時需填寫的欄位

## Schema ##

class LoginSchema(Schema): 
    # Login時必填帳號及密碼,並透露輸入格式為string
    account = fields.Str(doc="account", example="string", required=True)  
    password = fields.Str(doc="password", example="string", required=True)

class ItemGetSchema(Schema):   
    # 查詢資料時必填帳號以得知要取用誰的購物車db
    account = fields.Str(doc="account", example="string", required=True)
    product_name = fields.Str(doc="product_name", example="string")  

class ItemPostSchema(Schema):  
    # 新增資料時全部都必須填
    account = fields.Str(doc="account", example="string", required=True)
    product_name = fields.Str(doc="product_name", example="string", required=True)  
    price = fields.Str(doc="price", example="int8", required=True)
    number = fields.Str(doc="number", example="int8", required=True)

class ItemIDSchema(Schema):  
    # 用ID查詢資料或刪除資料時只需填入帳號以得知要取用誰的購物車db,ID輸入在URL即可
    account = fields.Str(doc="account", example="string", required=True)
 
class ItemPatchSchema(Schema): 
    # 修改資料時必填帳號以得知要取用誰的購物車db,其他data可不填(只更動有填的)
    account = fields.Str(doc="account", example="string", required=True)
    product_name = fields.Str(doc="product_name", example="string")
    price = fields.Str(doc="price", example="int8")
    number = fields.Str(doc="number", example="int8")


## Response ##

class ItemGetResponse(Schema):
    # 登入、查詢資料時會多顯示data
    datatime = fields.Str(example="1970-01-01T00:00:00.000000")
    your_current_total_price = fields.Str(example="800")
    data = fields.List(fields.Dict())
    message = fields.Str(example="success")

class ItemPostResponse(Schema):
    # 新增、修改或刪除資料不另外顯示data,只回覆success、total和時間
    message = fields.Str(example="success")
    your_current_total_price = fields.Str(example="800")
    datatime = fields.Str(example="1970-01-01T00:00:00.000000")
