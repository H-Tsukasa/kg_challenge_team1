# アクティビティ内のevent取得
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

# event番号取得のパターン
event_num_pattern = re.compile(r"event([0-9]*)")

# jsonファイルからエピソードデータを読み込む
# episodes = load_episodes_from_json("./data/Episodes.json")
episodes = load_episodes_from_json("https://github.com/KnowledgeGraphJapan/KGRC-RDF/tree/kgrc4si/CompleteData/Episodes")
print(episodes)
"""
jsonファイルの場合，読み込まれるデータは以下の通り

id: エピソードのid 本番ではSenarioに該当
title: Day1など 本番では Morning Ritualsなど
scene: sceneのidのみが入る
activities: アクティビティの配列

"""

# episodeごとに繰り返し

for i, episode in enumerate(episodes):
    pre_entry_actions = []
    tmp_room = None
    tmp_action = None
    break_flag = 0

    print(f"{episode['id']}")

    # それぞれのeventでsparqlを発行
    for activity in episode["activities"]:
        activity_name = (activity + "_scene" + str(episode["scene"])).strip()
        sparql.setQuery(
            f"""
            PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
            PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            select DISTINCT * where {{
                ex:{activity_name} :hasEvent ?event .
                ?event (:place | :from) ?now_place.
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
            place = result["now_place"]
            action = result["action"]
            # イベント番号の取得
            event_num = event_num_pattern.match(
                event["value"].replace(url_instance, "")
            ).groups()[0]
            results_summarized.append(
                (
                    int(event_num),
                    place["value"].replace(url_instance, ""),
                    action["value"].replace(url_action, ""),
                )
            )

        # eventの番号でソート
        results_sorted = sorted(results_summarized, key=lambda x: x[0])
        for result in results_sorted:
            print(f"\tevent_num: {result[0]}, place: {result[1]}, action: {result[2]}")
            # 部屋が切り替わった場合
            if not tmp_room == result[1] and tmp_action is not None:
                # キッチンなら直前のアクションを保存
                if "kitchen" in result[1]:
                    pre_entry_actions.append(tmp_action.upper())
                    break_flag = 1
                    break
            tmp_room = result[1]
            tmp_action = result[2]
        print("")
        if break_flag:
            break

    print("--------------------")
    # 解答形式への変換
    jsonify_answers(
        result_path="./result_task1",
        answers=pre_entry_actions,
        senario=episode["id"],
        question_id="q4",
    )
