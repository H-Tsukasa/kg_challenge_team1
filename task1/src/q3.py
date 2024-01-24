##キッチンに入った後行ったアクションは何か？（キッチンに入っていなければ空）
##キッチンに入った直後のアクション？
##キッチンに入った以降のアクション？


##キッチンに入った直後のアクションと仮定


# アクティビティ内のevent取得
import re
import json
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
    print(f"{episode['id']}")

    total_action_after_kitchen = []
    for activity in episode["activities"]:
        activity_name = (activity + "_scene" + str(episode["scene"])).strip()
        print(f"activity_name: {activity}")
        sparql.setQuery(
            f"""
        PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
        PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
        select DISTINCT * where {{
            ex:{activity_name} :hasEvent ?event .
            ?event (:place | :from) ?nowplace .
            ?nowplace a ?objectType .
            ?event :action ?action.
        }}
                        """
        )
        # sparqlの結果取得
        results = sparql.query().convert()["results"]["bindings"]

        # 結果をまとめる
        results_summarized = []
        for result in results:
            event = result["event"]
            place = result["objectType"]
            action = result["action"]
            # イベント番号の取得
            event_num = event_num_pattern.match(
                event["value"].replace(url_instance, "")
            ).groups()[0]
            results_summarized.append(
                (
                    int(event_num),
                    place["value"].replace(url_ontlogy, ""),
                    action["value"].replace(url_action, "").upper(),
                )
            )
        # eventの番号でソート
        results_sorted = sorted(results_summarized, key=lambda x: x[0])

        # kitchenに入ったかのフラグ
        kitchen_flag = 0

        # キッチンに入った後のアクションの取得
        action_after_kitchen = []
        for result in results_sorted:
            print(f"\tevent_num: {result[0]}, place: {result[1]}, action: {result[2]}")

            if (kitchen_flag == 0) and ("Kitchen" in result[1]):
                kitchen_flag = 1

            if kitchen_flag:
                total_action_after_kitchen.append(result[2])
                action_after_kitchen.append(result[2])

        # print("")
        # print("actions after the kitchen (no Duplicate)")
        # print(list(dict.fromkeys(action_after_kitchen)))

        # print("actions after the kitchen (Duplicate)")
        # print(action_after_kitchen)

    print("--------------------")

    print("action after the kitchen")
    print(total_action_after_kitchen)
    answers = list(dict.fromkeys(total_action_after_kitchen))

    # 解答形式への変換
    jsonify_answers(
        result_path="./result",
        answers=answers,
        senario=episode["id"],
        question_id="q3",
    )
