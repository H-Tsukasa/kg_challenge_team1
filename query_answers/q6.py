# アクティビティ内のevent取得
from SPARQLWrapper import SPARQLWrapper
from lib.episodes_loader import load_episodes_from_json
from lib.convert_answers import jsonify_answers

sparql = SPARQLWrapper(
    endpoint="https://morita.it.aoyama.ac.jp/homekg/sparql", returnFormat="json"
)
# 削除するurlの定義
url_instance = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
url_ontology = "http://kgrc4si.home.kg/virtualhome2kg/ontology/"
url_action = "http://kgrc4si.home.kg/virtualhome2kg/ontology/action/"

# CSVファイルからエピソードデータを読み込む
# episodes = load_episodes_from_csv('Episodes.csv')
# jsonファイルからエピソードデータを読み込む
episodes = load_episodes_from_json("./data/Episodes.json")
"""
jsonファイルの場合，読み込まれるデータは以下の通り

id: エピソードのid 本番ではSenarioに該当
title: Day1など 本番では Morning Ritualsなど
scene: sceneのidのみが入る
activities: アクティビティの配列

"""

# 各エピソードで繰り返し
for i, episode in enumerate(episodes):
    print(f"episode {i}")

    duration_sum = 0
    should_break = False  # 各エピソードのループを抜けるためのフラグ

    # 各アクティビティで繰り返し
    for activity in episode["activities"]:
        activity_name = (activity + "_scene" + str(episode["scene"])).strip()

        sparql.setQuery(
            f"""
                PREFIX ex: <{url_instance}>
                PREFIX : <{url_ontology}>
                PREFIX time: <http://www.w3.org/2006/time#>
                select DISTINCT ?event ?action ?numericDuration where {{
                    ex:{activity_name} :hasEvent ?event .
                    ?event :action ?action .
                    ?event :time ?time.
                    ?time time:numericDuration ?numericDuration.
                }}
            """
        )

        events = sparql.query().convert()["results"]["bindings"]

        # イベントのループ
        for event in events:
            action = event["action"]["value"].replace(url_action, "")
            duration = float(event["numericDuration"]["value"])

            duration_sum += duration

            # duration_sumが10以上の場合は、actionを表示し、ループを抜ける
            if duration_sum > 10:
                print(f"\tduration exceeded 10, action: {action}")
                should_break = True  # 外側のループを抜けるためにフラグをセット
                break

        # 外側のループを終了するためのチェック
        if should_break:
            break

    # 解答形式への変換
    jsonify_answers(
        result_path="./result",
        answers=[action.upper()],
        senario=episode["id"],
        question_id="q6",
    )
