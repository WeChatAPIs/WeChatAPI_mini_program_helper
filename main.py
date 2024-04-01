import requests
import xmltodict
from flask import Flask, request, jsonify

# Flask常规操作
app = Flask(__name__)
# 微信API的地址
WECHAT_API_URL = 'http://127.0.0.1:8888/api/'


@app.route('/WeChatAPI', methods=['POST'])
def chat():
    data = request.json
    print(data)
    pushType = data["pushType"]  #
    # 仅接受群、好友发送的小程序消息，其他消息类型不处理
    # 消息类型详见： https://github.com/kawika-git/wechatAPI/blob/main/doc/处理消息/消息类型.md
    if pushType != 1 or data["data"]['type'] != 49:
        return jsonify({"success": "true"})
    xmlContent = data['data']['content']
    if '@chatroom' in data['data']['from']:
        # 是群消息
        xmlContent = xmlContent.split(":\n")[1]
    # 将xml转成json
    xml_dict = xmltodict.parse(xmlContent)
    miniAppConfig = xml_dict["msg"]["appmsg"]["weappinfo"]
    # 获取小程序的appid
    appid = miniAppConfig['appid']
    if appid is None:
        return jsonify({"success": "true"})
    open_miniapp_json = {"type": 10106, "appid": appid, "bizUserName": miniAppConfig['username']}
    # 获取小程序的页面路径
    if 'pagepath' in miniAppConfig:
        open_miniapp_json['pageUrl'] = miniAppConfig['pagepath']
    # 打开小程序
    requests.post(WECHAT_API_URL, json=open_miniapp_json)
    return jsonify({"success": "true"})


def addCallBackUrl(callBackUrl):
    """
        设置回调地址，当有人发送消息时，微信会就把信息发送到这个接口中

        为了能确保该程序能接收到消息，为了保险起见，会先将之后的回调地址删除掉，再设置新的回调地址
    """
    # 获取所有的回调地址
    resdatalist = requests.post(WECHAT_API_URL, json={"type": 1003, }).json()["data"]["data"]
    # 删除之前的回调地址
    for item in resdatalist:
        requests.post(WECHAT_API_URL, json={"type": 1002, "cookie": item["cookie"], })
    # 设置新的回调地址
    requests.post(WECHAT_API_URL, json={"type": 1001, "protocol": 2, "url": callBackUrl})


if __name__ == '__main__':
    """
    启动python的http服务，并将python的http接口地址设置为微信的回调地址
    但由于python服务器启动后就不会再执行下面的代码，所以需要先将微信的回调地址设置为这个服务的WeChatAPI接口
    设置成功后，再启动python的http服务，这时候微信的所有消息都会发送到这个服务的WeChatAPI接口中
    """
    serverPort = 18000
    # 给微信设置回调地址，当有人给发送消息时，微信会就把信息发送到这个接口中
    addCallBackUrl(f"http://127.0.0.1:{serverPort}/WeChatAPI")
    # 将微信回调地址设置为这个服务的地址
    #
    try:
        print("连接微信成功")
    except Exception as e:
        print("连接微信失败", e)
    app.run(host='0.0.0.0', port=serverPort)
