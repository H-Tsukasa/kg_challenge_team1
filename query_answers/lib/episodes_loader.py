import csv
import glob
import json


def load_episodes_from_csv(csv_file_path, print_info=True):
    """
    CSVファイルからエピソード情報を読み込み、それをリストで返す関数。

    :param print_info:
    :param csv_file_path: 読み込むCSVファイルのパス
    :return: 各エピソードの情報を含む辞書のリスト
    """
    episodes_data = []  # エピソードデータを保持するためのリストを初期化
    """
    episodes_dataの中身は以下のようになります:
    [
        {
            'scene': 'scene1',
            'day': 'day1',
            'activities': ['get_out_of_bed1', 'put_slippers_in_closet1' ...]
        },
        {
            'scene': 'scene2',
            'day': 'day2',
            'activities': ['get_out_of_bed2', 'put_slippers_in_closet2' ...]
        },
        ...
    ]
    """

    with open(csv_file_path, mode="r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            scene = row[0]
            day = row[1]
            # activitiesは三列目以降の要素を取得し、小文字に変換
            activities = [activity.lower() for activity in row[2:]]
            activities = list(filter(lambda x: x != "", activities))
            # 辞書を作成してリストに追加
            episodes_data.append({"scene": scene, "day": day, "activities": activities})

    if print_info:
        print(f"Loaded {len(episodes_data)} episodes from {csv_file_path}")
        print(f"First episode: {episodes_data[0]}")
        print(f"Last episode: {episodes_data[-1]}")

    return episodes_data


def load_episodes_from_json(json_file_path, print_info=False):
    # jsonファイルからepisodeを取得
    episodes_data = []  # エピソードデータを保持するためのリストを初期化
    file_names = sorted(glob.glob(f"{json_file_path}/*"))
    for file_name in file_names:
        with open(file_name, mode="r") as json_file:
            json_data = json.load(json_file)["data"]
            episode_id = json_data["id"]
            title = json_data["title"]
            scene = json_data["scene"]
            activities = [activity.lower() for activity in json_data["activities"]]
            activities = list(filter(lambda activity: activity != "", activities))
            episodes_data.append(
                {
                    "id": episode_id,
                    "title": title,
                    "scene": scene,
                    "activities": activities,
                }
            )

    if print_info:
        print(f"Loaded {len(episodes_data)} episodes from {json_file_path}")
        print(f"First episode: {episodes_data[0]}")
        print(f"Last episode: {episodes_data[-1]}")

    return episodes_data


# この関数は他のスクリプトから次のように使用できます:
# episodes = load_episodes_from_csv("./data/Episode.csv")
# episodes = load_episodes_from_json("../data/Episodes.json/")
