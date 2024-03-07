import json
import requests
from bs4 import BeautifulSoup
from requests import Session

from decrypt import decrypt


class UCourse:
    def __init__(self, session: Session, open_id, shcool_id):
        self.session = session
        self.open_id = open_id
        self.shcool_id = shcool_id
        self.tutorial_id = ""

    def set_tutorial_id(self, tutorial_id):
        self.tutorial_id = tutorial_id

    def get_courses_index(self):
        """
        获取课程列表
        返回值: dict
        class_name: 课程标题
        course_url: 课程链接
        course_name: 课程名
        tutorialid: 课程id
        """
        url = "https://u.unipus.cn/user/student"
        params = {"school_id": self.shcool_id}
        response = self.session.get(url, params=params, allow_redirects=False)
        if response.status_code != 200:
            raise Exception(f"获取课程失败，status_code:{response.status_code}")
        try:
            html = BeautifulSoup(response.text, "lxml")
            courses_data = html.find_all("div", class_="class-content")
            data = []
            for course_data in courses_data:
                temp = {}
                temp["class_name"] = course_data.find(
                    "span", class_="class-name"
                ).string
                temp["course_url"] = course_data.find("span", class_="hideurl").string
                temp["course_name"] = course_data.find("div", class_="my_course_name").string
                temp["tutorial_id"] = course_data.find(
                    "div", class_="my_course_item ite"
                ).get("tutorialid")
                data.append(temp)
            return f"获取课程成功", data
        except Exception as e:
            raise Exception(f"获取课程失败，Exception:{e}")

    def get_courses(self, ticket=None):
        """
        获取课程详细数据
        """
        url = "https://u.unipus.cn/user/student/myscore/list"
        params = {
            "length": "10",
            "school_id": self.shcool_id,
        }
        if ticket is not None:
            params.update({"ticket": ticket})
        response = self.session.get(url, params=params)
        if ticket is not None:
            return
        if response.status_code != 200:
            raise Exception(f"获取课程失败，status_code:{response.status_code}")
        try:
            return "获取课程成功", response.json()
        except Exception as e:
            raise Exception(f"获取课程失败，Exception:{e}")

    def get_units(self):
        """
        获取指定课程所有单元信息
        """
        url = f"https://ucontent.unipus.cn/course/api/v2/course_progress/{self.tutorial_id}/{self.open_id}/default/"
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f"获取课程单元信息失败，status_code:{response.status_code}")
        data = response.json()
        units_data = data.get("rt", {}).get("units", {})
        units = []
        for unit_name in units_data.keys():
            unit_data = units_data.get(unit_name)
            required = unit_data.get("state").get("required")
            units.append(
                [
                    f"{unit_name.replace('u', 'unit')} {'必修' if required else '选修'}",
                    unit_name,
                ]
            )
        return "获取课程单元信息成功!", units

    def get_unit_sections(self, unit_name, required):
        """
        获取指定单元内所有章节
        unit_name str: 单元民
        required str: 是否为必修
        """
        url = f"https://ucontent.unipus.cn/course/api/v2/course_progress/{self.tutorial_id}/{unit_name}/{self.open_id}/default/"
        response = self.session.get(url)
        if response.status_code != 200:
            return f"获取 {unit_name} 章节信息失败，status_code:{response.status_code}", None
        data = response.json()
        sections_data = data.get("rt", {}).get("leafs", {})
        sections = []
        for section_name in sections_data.keys():
            section_data = sections_data.get(section_name)
            if required and not section_data.get("strategies").get("required"):
                continue
            sections.append([section_name, section_data.get("tab_type")])
        return "获取章节信息成功!", sections

    def get_all_sections(self, unit_name_list, required):
        """
        获取所有章节
        """
        section_list = []
        unit_name_list
        for unit_name in unit_name_list:
            mes, sections = self.get_unit_sections(unit_name, required)
            if sections is None:
                print(mes)
                continue
            section_list += sections
        return section_list

    def get_section_conten(self, section_name):
        """
        获取章节加密内容
        """
        url = f"https://ucontent.unipus.cn/course/api/v3/content/{self.tutorial_id}/{section_name}/default/"
        response = self.session.get(url)
        if response.status_code != 200:
            return f"获取 {section_name} 章节内容失败，status_code:{response.status_code}", None
        data = response.json()
        return "获取成功!", data

    def get_section_summary(self, section_name):
        """
        获取章节统计信息
        """
        url = f"https://ucontent.unipus.cn/course/api/pc/summary/{self.tutorial_id}/{section_name}/default/"
        response = self.session.get(url)
        if response.status_code != 200:
            return f"获取 {section_name} 章节统计信息失败，status_code:{response.status_code}", None
        data = response.json()
        return "获取成功!", data

    def set_answer_data(self, answer_list, qid, tab_type, rules, record_version):
        """
        设置提交请求参数
        """
        i = 0
        answers = {}
        for answer in answer_list:
            answer_content = answer
            answers[str(i)] = {
                "student_answer": answer_content,
                "isDone": True,
                "version": "v2",
                "rule": rules[i],
                "user_answer": {
                    "qid": qid,
                    "rule": rules[i],
                    "answer": {"index": i, "answer": answer_content, "version": "v2"},
                    "content": "",
                    "id": f"{qid}-{i}",
                    "offset": 0,
                },
            }
            i += 1
        data = {
            "enable_mistake": False,
            "version": "default",
            "record_version": record_version,
            "specific_scores": [None for i in rules],
            "answers": answers,
        }
        return data

    def submit_answer(self, section_name, answer_data):
        """
        提交答案
        """
        data = json.dumps(answer_data, separators=(",", ":"))
        url = f"https://ucontent.unipus.cn/course/api/v3/submit/{self.tutorial_id}/{section_name}/"
        response = self.session.post(url, data=data)
        if response.status_code != 200:
            return f"提交 {section_name} 答案失败，status_code:{response.status_code}"
        data = response.json()
        score_avg = data["data"]["submit_info"]["state"]["score_avg"]
        return f"{section_name} 章节准确率为: {score_avg}"

    def study_section(self, section_data):
        """
        学习指定章节（未完成）
        """
        # 获取section数据
        section_name = section_data[0]
        tab_type = section_data[1]
        print(f"正在学习: {section_name}")
        mes, content_data = self.get_section_conten(section_name)
        if content_data is None:
            print(mes)
            return False
        mes, content_summary = self.get_section_summary(section_name)
        if content_summary is None:
            print(mes)
            return False
        
        # content的内容
        content = content_data.get("content")
        publish_version = content_data.get("publish_version")
        k = content_data.get("k")
        data = decrypt(content, k)

        # summary的内容
        summary = (
            content_summary.get("summary", {})
            .get("indexMap", {})
            .get("p_1", {})
            .get("c_1", {})
        )
        if summary == {}:
            return False
        qid = summary.get("qid")
        rules = summary.get("rules")
        questions_num = len(rules)

        if tab_type == "task" and "in" in list(set(rules)):
            # 获取题目和选项
            questions_data = data.get("questions:scoopquestions", {})
            scoop_data= questions_data.get("content", [{}])[0].get("scoop", {})
            if scoop_data is None:
                print("无法题目内容")
                return False
            html_text= scoop_data.get("html", None)
            if html_text is None:
                print(html_text)
                print("无法题目内容")
                return False
            html = BeautifulSoup(html_text, "lxml")
            p_list = html.find_all("p")
            questions_list = []
            for p in p_list:
                t = p.text
                if t.strip().replace(" ", "").replace("&nbsp;", "") == "":
                    continue
                questions_list.append(p.text.replace("\xa0", ""))
            span_list = html.find_all("span", class_="words-color")
            option_list = []
            for span in span_list:
                s = span.text
                if s.strip().replace(" ", "").replace("&nbsp;", "") == "":
                    continue
                option_list.append(span.text.replace("\xa0", ""))
            if option_list == []:
                print("无选项填空题")
                return False
            if len(questions_list) != len(option_list):
                print("题目和选项数目不相同!")
                return False
            
            # 在这里构建提交请求参数
            answer_data = {}
            print(self.submit_answer(section_name, answer_data))
            return True
        print(f"{section_name} 不支持的题型: {tab_type}, {json.dumps(rules)}")
