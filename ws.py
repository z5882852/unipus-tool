import ssl
import time
import json
import websocket


def ws_connect(uuid, token, tutorial_id, t=20):
    """
    与服务器建立websocket连接，用来刷课程时长

    :param uuid: str 用户id，也就是open_id
    :param token: str  X-Annotator-Auth-Token的值
    :param tutorial_id: str 课程id（在course中的get_courses_index获取）
    :param t: int 发送数据的周期(s)
    """
    url = f"wss://ucontent.unipus.cn/unipusio/?uuid={uuid}&token={token}&EIO=3&transport=websocket"
    ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
    try:
        ws.connect(url)
        print("websocket连接成功!\n")
    except Exception as e:
        raise Exception("连接异常：", e)
    
    # 鉴权
    mes = f"40/userActivities?uuid={uuid}&token={token},"
    print(f"->| {mes}\n")
    ws.send(mes)
    response = ws.recv()
    print(f"<-| {response}\n")

    data = [
        "start",
        {
            "module": "u1g2",
            "moduleGroup": tutorial_id,
            "client": "U校园pc",
            "url": f"https://ucontent.unipus.cn/_pc_default/pc.html?cid=&appid=#/{tutorial_id}/courseware/u1/u1g1/u1g2/__main",
            "tag1": "u1",
            "tag2": "u1g1",
        },
    ]
    mes = "42/userActivities,0" + json.dumps(data, ensure_ascii=False)
    # 心跳包, 刷时长
    while True:  # 连接上，循环用于一直向服务器发送消息
        try:
            print(f"->| {mes}\n")
            ws.send(mes)
            response = ws.recv()
            print(f"<-| {response}\n")
            time.sleep(t)
        except KeyboardInterrupt:
            break