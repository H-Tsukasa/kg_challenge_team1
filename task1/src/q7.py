# Q7, 初期状態と10秒後のモノとモノの関係を抽出する

import re
from SPARQLWrapper import SPARQLWrapper
from lib.episodes_loader import load_episodes_from_json
from lib.convert_answers import jsonify_answers

sparql = SPARQLWrapper(
    endpoint="https://morita.it.aoyama.ac.jp/homekg/sparql", returnFormat="json"
)
# 削除するurlの定義
url_instance = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
url_action = "http://kgrc4si.home.kg/virtualhome2kg/ontology/action/"
url_ontlogy = "http://kgrc4si.home.kg/virtualhome2kg/ontology/"
# event番号取得のパターン
event_num_pattern = re.compile(r"event([0-9]*)")
# jsonファイルからエピソードデータを読み込む
episodes = load_episodes_from_json("./data/Episodes.json")
"""
jsonファイルの場合，読み込まれるデータは以下の通り

id: エピソードのid 本番ではSenarioに該当
title: Day1など 本番では Morning Ritualsなど
scene: sceneのidのみが入る
activities: アクティビティの配列

"""

# episodeごとに繰り返し
for i, episode in enumerate(episodes):
    duration_sum = 0
    break_activity_id = None  # 各エピソードにおける10秒経過時点でのアクティビティのID
    break_activity_name = None
    break_event_num = None  # 上記のアクティビティでの10秒経過時点でのイベントのID
    break_flag = False

    print(f"{episode['id']}")

    for j, activity in enumerate(episode["activities"]):
        activity_name = (activity + "_scene" + str(episode["scene"])).strip()
        print(f"    activity:{activity}")
        # 10秒までのevent番号を取得
        sparql.setQuery(
            f"""
            PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
            PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            PREFIX time: <http://www.w3.org/2006/time#>
            select DISTINCT ?event ?duration where {{
                ex:{activity_name} :hasEvent ?event .
                ?event :time ?time .
                ?time time:numericDuration ?duration .
            }}
        """
        )
        # sparqlの結果取得
        results = sparql.query().convert()["results"]["bindings"]

        # 結果をまとめる
        results_summarized = []
        for result in results:
            event = result["event"]
            duration = result["duration"]
            # イベント番号の取得
            event_num = event_num_pattern.match(
                event["value"].replace(url_instance, "")
            ).groups()[0]
            results_summarized.append(
                (
                    int(event_num),
                    duration["value"],
                )
            )
        results_sorted = sorted(results_summarized, key=lambda x: x[0])
        # 10秒経過時点のevent_numを取得
        for result in results_sorted:
            if break_flag:
                break
            duration_sum += float(result[1])
            print(f"    event_num: {result[0]}, duration_sum: {duration_sum}")
            if duration_sum >= 10:
                break_activity_id = j
                break_activity_name = activity
                break_event_num = result[0]
                break_flag = True
                print(f"    10 秒経過した時点のアクティビティ: {break_activity_name}")
                print(f"    10 秒経過した時点のイベント番号: {break_event_num}")
        if break_flag:
            break

    for j, activity in enumerate(episode["activities"]):
        if (j == 0) or (j == break_activity_id):
            activity = activity.strip()

            sparql.setQuery(
                f"""
            PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
            PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            PREFIX time: <http://www.w3.org/2006/time#>
            select DISTINCT ?event ?obj1Type ?obj2Type ?relation where {{
                ex:{activity_name} :hasEvent ?event .
                ?state1 :bbox ?shape1 .
                ?state2 :bbox ?shape2 .
                ?shape1 ?relation ?shape2 .

                ?state1 :isStateOf ?obj1 .
                ?state2 :isStateOf ?obj2 .

                ?obj1 a ?obj1Type .
                ?obj2 a ?obj2Type .
            }}
                            """
            )
            # sparqlの結果取得
            results = sparql.query().convert()["results"]["bindings"]

            # 結果をまとめる
            results_summarized = []
            for result in results:
                event = result["event"]
                obj1 = result["obj1Type"]
                obj2 = result["obj2Type"]
                relation = result["relation"]
                # イベント番号の取得
                event_num = event_num_pattern.match(
                    event["value"].replace(url_instance, "")
                ).groups()[0]
                results_summarized.append(
                    (
                        int(event_num),
                        event["value"].replace(url_instance, ""),
                        obj1["value"].replace(url_ontlogy, ""),
                        obj2["value"].replace(url_ontlogy, ""),
                        relation["value"].replace(url_ontlogy, "").upper(),
                    )
                )
            results_sorted = sorted(results_summarized, key=lambda x: x[0])

            # 初期状態のイベント番号の取得
            from_event_num = results_sorted[0][0]

            # 解答形式への変換
            answers = []
            # 初期状態と10秒経過時点でのモノとモノの関係を出力
            for result in results_sorted:
                if (result[0] == from_event_num) or (result[0] == break_event_num):
                    answers.append(
                        {
                            "obj1": result[2],
                            "obj2": result[3],
                            "relation": result[4],
                        }
                    )

            jsonify_answers(
                result_path="./result",
                answers=answers,
                senario=episode["id"],
                question_id="q7",
            )
