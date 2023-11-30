from api.auth import UAuth
from api.course import UCourse
from requests import Session

from ws import ws_connect


HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://sso.unipus.cn",
    "Pragma": "no-cache",
    "Referer": "https://sso.unipus.cn/sso/login?service=https%3A%2F%2Fu.unipus.cn%2Fuser%2Fcomm%2Flogin%3Fschool_id%3D",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

def choose_course(courses_data):
    """
    选择课程，返回课程ID
    """
    i = 0
    print("=====================")
    for course_data in courses_data:
        class_name = course_data.get("class_name")
        print(f"{i}.{class_name}")
        i += 1
    print("=====================")
    index = int(input("请选择课程: "))
    return courses_data[index].get("tutorial_id")

def choose_units(units_data):
    """
    选择必修或其他
    """
    print("=====================")
    print("0. 必修")
    print("1. 必修和选修")
    print("=====================")
    index = int(input("请选择项目: "))
    # index = 0
    required = True if index == 0 else False
    units = []
    for unit_data in units_data:
        if required and "选修" in unit_data[0]:
            continue
        print(f"已选择单元: {unit_data[0]}")
        units.append(unit_data[1])
    return required, units

if __name__ == '__main__':
    username = ""  # 用户名
    password = ""  # 密码
    # 初始化
    session = Session()
    session.headers = HEADERS

    # 登录
    auth = UAuth(session, username, password)
    data = auth.login()
    if data is None:
        exit()
    
    # 获取用户数据
    open_id = data.get("openid")
    user_info = auth.print_user_info(open_id)
    school_id = user_info["result"]["user"]["schoolId"]
    ticket = data.get("serviceTicket")

    auth.login_ticket("", ticket=ticket)

    # 查询课程
    course = UCourse(session, open_id, school_id)

    course.get_courses(ticket=ticket)
    mes, course_info = course.get_courses()
    if course_info is None:
        exit()

    # 获取 headers中 X-Annotator-Auth-Token
    auth_token = auth.set_token()

    mes, course_data = course.get_courses_index()
    print(mes)
    if course_data is None:
        exit()

    # 选择课程
    tutorial_id = choose_course(course_data)
    course.set_tutorial_id(tutorial_id=tutorial_id)

    # 刷时长
    ws_connect(open_id, auth_token, tutorial_id, 5)

    # 以下为自动答题内容
    # mes, units_data = course.get_units()
    # print(mes)
    # if units_data is None:
    #     exit()
    # required, units = choose_units(units_data)

    # sections_list = course.get_all_sections(units, required)
    # if sections_list == []:
    #     print("无可学习内容！")
    #     exit()
    # for section in sections_list:
    #  course.study_section(section)



    
