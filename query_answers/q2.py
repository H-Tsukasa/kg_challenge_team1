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
print(len(episodes))
for i, episode in enumerate(episodes):
    print(f"episode {i}")

    duration_sum = 0
    should_break = False  # 各エピソードのループを抜けるためのフラグ

    action_counts = {}

    # 各アクティビティで繰り返し
    for activity in episode["activities"]:
        activity_name = (activity + "_scene" + str(episode["scene"])).strip()

        sparql.setQuery(
            f"""
        PREFIX ex: <{url_instance}>
        PREFIX : <{url_ontology}>

        SELECT ?action (COUNT(?action) AS ?actionCount) WHERE {{
            ex:{activity_name} :hasEvent ?event .
            ?event :action ?action .
        }}
        GROUP BY ?action
                        """
        )

        events = sparql.query().convert()["results"]["bindings"]

        # 結果を解析して辞書に追加
        for event in events:
            # URL 接頭辞を取り除いたアクション名を取得
            action = event["action"]["value"].replace(url_action, "")
            count = int(event["actionCount"]["value"])

            # 既に辞書にアクションが存在する場合は、カウントを追加します。
            # そうでない場合は、新しいエントリを作成します。
            if action in action_counts:
                action_counts[action] += count
            else:
                action_counts[action] = count

    # カウントでソートする
    action_counts = dict(
        sorted(action_counts.items(), key=lambda item: item[1], reverse=True)
    )

    # すべてのイベントを処理した後で、結果を表示します。
    for action, count in action_counts.items():
        print(f"Action: {action}, \tTotal count: {count}")

    # 解答形式への変換
    answers = []
    for action, count in action_counts.items():
        answers.append({"name": action, "number": count})

    jsonify_answers(
        result_path="./result",
        answers=answers,
        senario=episode["id"],
        question_id="q2",
    )

    print("--------------------")
