from datetime import datetime

def success(data,total):
    if data is None:    
        # 新增、修改或刪除資料不另外顯示data,只回覆success、total和時間
        return {'message': 'success',
                'your current total price':total,
                'datatime': datetime.utcnow().isoformat()
                }, 200
    # 登入、查詢資料時會多顯示data
    return {'message': 'success',
            'data': data,
            'your current total price':total,
            'datatime': datetime.utcnow().isoformat()
            }, 200

def failure(data):
    # 失敗時顯示錯誤訊息及時間
    data["datatime"] = datetime.utcnow().isoformat()
    return data, 500
