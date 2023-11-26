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
url_ontology = "http://kgrc4si.home.kg/virtualhome2kg/ontology/"
url_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns"
url_bbox = "https://www.web3d.org/specifications/X3dOntology4.0"
# event番号取得のパターン
event_num_pattern = re.compile(r"event([0-9]*)")
# durationの上限
duration_limit = 20

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
main_answers = []

for i, episode in enumerate(episodes):
    print(f"{episode['id']}")

    main_answers.append({})
    main_answers[i].setdefault("scene", episode["scene"])
    main_answers[i].setdefault("day", episode["title"])

    duration_sum = 0
    break_flag = False
    # それぞれのeventでsparqlを発行
    events = []
    for j, activity in enumerate(episode["activities"]):
        objects = {}
        event_num_target = None
        break_activity_id = None

        activity_name = (activity + "_scene" + str(episode["scene"])).strip()
        print(f"activity_name: {activity_name}")

        # 1. 20秒までのevent番号を取得
        sparql.setQuery(
            f"""
                PREFIX ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
                PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
                PREFIX time: <http://www.w3.org/2006/time#>
                select DISTINCT ?event ?duration where {{
                    ex:{activity_name} :hasEvent ?event .
                    ?event :time ?time.
                    ?time time:numericDuration ?duration.
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
            event_num = event_num_pattern.match(
                event["value"].replace(url_instance, "")
            ).groups()[0]
            results_summarized.append(
                (int(event_num), duration["value"], event["value"])
            )
        results_sorted = sorted(results_summarized, key=lambda x: x[0])
        # 20秒時点のeventnumを取得
        for result in results_sorted:
            duration_sum += float(result[1])
            # 20秒経過した時点のアクティビティ，イベントを取得
            if duration_sum >= duration_limit:
                print(f"{duration_limit}秒経過した時点のアクティビティ：{activity}, {j}")
                print(f"{duration_limit}秒経過した時点のイベント:{result[0]}")
                break_activity_id = j
                events.append(
                    {"first_event": results_sorted[0][2], "last_event": result[2]}
                )
                break_flag = True
                break
        if break_flag:
            break
        # activity内で20秒に満たなかった場合は最初と最後のイベント保存
        else:
            events.append(
                {"first_event": results_sorted[0][2], "last_event": result[2]}
            )

    # 2. 物体，位置，状態の取得
    first_objects = {}
    last_objects = {}
    for j, activity in enumerate(episode["activities"]):
        if j > break_activity_id:
            break
        # 最初のイベント
        sparql.setQuery(
            f"""
                PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
                PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                select DISTINCT ?object ?state_main ?stateType ?pos_x ?pos_y ?pos_z where {{
                <{events[j]["first_event"]}> :situationBeforeEvent ?before_situation .
                ?state_main :partOf ?before_situation;
                                    :state ?stateType ;
                                    :isStateOf ?object ;
                                    :bbox ?shape1 .
                ?shape1 x3do:bboxCenter ?pos1 .
                ?pos1 rdf:first ?pos_x .
                ?pos1 rdf:rest ?pos_y_cl .
                ?pos_y_cl rdf:first ?pos_y .
                ?pos_y_cl rdf:rest ?pos_z_cl .
                ?pos_z_cl rdf:first ?pos_z .

                }}
        """
        )
        # sparqlの結果取得
        results = sparql.query().convert()["results"]["bindings"]

        # 結果をまとめる
        results_summarized = []
        tmp_objects = {}
        for result in results:
            object_name = result["object"]
            state_type = result["stateType"]
            state_main = result["state_main"]
            pos_x = result["pos_x"]
            pos_y = result["pos_y"]
            pos_z = result["pos_z"]
            results_summarized.append(
                {
                    "object_name": object_name["value"].replace(url_instance, ""),
                    "state_type": state_type["value"]
                    .replace(url_ontology, "")
                    .replace(url_bbox, "")
                    .replace(url_type, ""),
                    "pos": [
                        float(pos_x["value"]),
                        float(pos_y["value"]),
                        float(pos_z["value"]),
                    ],
                }
            )
        # とりあえず同じobjectでまとめる
        for result in results_summarized:
            if result["object_name"] in tmp_objects:
                tmp_objects[result["object_name"]]["state"].append(result["state_type"])
            tmp_objects.setdefault(
                result["object_name"],
                {"state": [result["state_type"]], "pos": result["pos"]},
            )
        # 最初のアクティビティならfirstとして追加
        if j == 0:
            first_objects = tmp_objects
        # 新たに追加されたobjectがある場合はfirstに追加
        else:
            for k, v in tmp_objects.items():
                if k not in first_objects:
                    first_objects[k] = v

        # 最後のイベント
        sparql.setQuery(
            f"""
                PREFIX x3do: <https://www.web3d.org/specifications/X3dOntology4.0#>
                PREFIX : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                select DISTINCT ?event ?object ?state_main ?stateType ?pos_x ?pos_y ?pos_z where {{
                <{events[j]["last_event"]}> :situationAfterEvent ?after_situation .
                    ?state_main :partOf ?after_situation;
                                :state ?stateType ;
                                :isStateOf ?object ;
                                :bbox ?shape1 .
                    ?shape1 x3do:bboxCenter ?pos1 .
                    ?pos1 rdf:first ?pos_x .
                    ?pos1 rdf:rest ?pos_y_cl .
                    ?pos_y_cl rdf:first ?pos_y .
                    ?pos_y_cl rdf:rest ?pos_z_cl .
                    ?pos_z_cl rdf:first ?pos_z .
                }}
            """
        )

        # sparqlの結果取得
        results = sparql.query().convert()["results"]["bindings"]

        # 結果をまとめる
        results_summarized = []
        tmp_objects = {}
        for result in results:
            object_name = result["object"]
            state_type = result["stateType"]
            state_main = result["state_main"]
            pos_x = result["pos_x"]
            pos_y = result["pos_y"]
            pos_z = result["pos_z"]
            results_summarized.append(
                {
                    "object_name": object_name["value"].replace(url_instance, ""),
                    "state_type": state_type["value"]
                    .replace(url_ontology, "")
                    .replace(url_bbox, "")
                    .replace(url_type, ""),
                    "pos": [
                        float(pos_x["value"]),
                        float(pos_y["value"]),
                        float(pos_z["value"]),
                    ],
                }
            )

        # とりあえず同じobjectでまとめる
        for result in results_summarized:
            if result["object_name"] in tmp_objects:
                tmp_objects[result["object_name"]]["state"].append(result["state_type"])
            tmp_objects.setdefault(
                result["object_name"],
                {"state": [result["state_type"]], "pos": result["pos"]},
            )

        # 最初のアクティビティならlastとして追加
        if j == 0:
            last_objects = tmp_objects
        # 新たに変更されたもの，追加されたものをlastに追加
        else:
            for k, v in tmp_objects.items():
                last_objects[k] = v

    change_values = []
    try:
        for j, (object_key, first_object) in enumerate(first_objects.items()):
            append_flag = False
            change_values.append({})
            if (not first_object["state"] == last_objects[object_key]["state"]) or (
                not first_object["pos"] == last_objects[object_key]["pos"]
            ):
                change_values[j].setdefault("name", object_key)
                change_values[j]["first"] = {}
                change_values[j]["later"] = {}
                change_values[j]["first"]["state"] = first_object["state"]
                change_values[j]["later"]["state"] = last_objects[object_key]["state"]
                change_values[j]["first"]["pos"] = first_object["pos"]
                change_values[j]["later"]["pos"] = last_objects[object_key]["pos"]
    except KeyError as e:
        # NOTE: situationにおいて，途中で無くなるobjectが一つ存在している
        print(f"KeyError: {e}")

    change_values = list(filter(None, change_values))
    main_answers[i]["changed_objects"] = change_values

# 解答形式への変換
for i in range(len(episodes)):
    answers = []
    for change_object in main_answers[i]["changed_objects"]:
        first_pos = change_object["first"]["pos"]
        later_pos = change_object["later"]["pos"]
        first_state = change_object["first"]["state"]
        later_state = change_object["later"]["state"]
        answers.append(
            {
                "name": change_object["name"],
                "change": {
                    "first": {"pos": first_pos, "state": first_state},
                    "later": {"pos": later_pos, "state": later_state},
                },
            }
        )
    jsonify_answers(
        result_path="./result",
        answers=answers,
        senario=episodes[i]["id"],
        question_id="q8",
    )
