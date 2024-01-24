import os
from rdflib import Graph
import re
import torch
from llava.constants import X_TOKEN_INDEX, DEFAULT_X_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
from llava.mm_utils import tokenizer_X_token, get_model_name_from_path, KeywordsStoppingCriteria
from moviepy.editor import *


def video_clip(start, end, file_path, save_path):
    # file_path = "./videos/Read bedtime story1_1.mp4"    # 編集したい動画のパス
    # start = 40    # 切り出し開始時刻。秒で表現
    # end = 50  # 切り出し終了時刻。同じく秒で表現
    # save_path = "test.mp4"    # 編集後のファイル保存先のパス
    if not os.path.exists(save_path):
        video = VideoFileClip(file_path).subclip(start, end)    # ビデオのカット開始
        video.write_videofile(save_path,fps=29)  


def video_llava(video, prompt):
    disable_torch_init()
    model_path = 'LanguageBind/Video-LLaVA-7B'
    device = 'cuda'
    load_4bit, load_8bit = True, False
    model_name = get_model_name_from_path(model_path)
    tokenizer, model, processor, context_len = load_pretrained_model(model_path, None, model_name, load_8bit, load_4bit, device=device)
    video_processor = processor['video']
    conv_mode = "llava_v1"
    conv = conv_templates[conv_mode].copy()
    roles = conv.roles

    video_tensor = video_processor(video, return_tensors='pt')['pixel_values']
    if type(video_tensor) is list:
        tensor = [video.to(model.device, dtype=torch.float16) for video in video_tensor]
    else:
        tensor = video_tensor.to(model.device, dtype=torch.float16)
    key = ['video']

    print(f"{roles[1]}: {prompt}")
    prompt = DEFAULT_X_TOKEN['VIDEO'] + '\n' + prompt
    conv.append_message(conv.roles[0], prompt)
    conv.append_message(conv.roles[1], None)
    prompt = conv.get_prompt()
    input_ids = tokenizer_X_token(prompt, tokenizer, X_TOKEN_INDEX['VIDEO'], return_tensors='pt').unsqueeze(0).cuda()
    stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
    keywords = [stop_str]
    stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)

    with torch.inference_mode():
        output_ids = model.generate(
            input_ids,
            images=[tensor, key],
            do_sample=True,
            temperature=0.1,
            max_new_tokens=1024,
            use_cache=True,
            stopping_criteria=[stopping_criteria])

    outputs = tokenizer.decode(output_ids[0, input_ids.shape[1]:]).strip()
    print(outputs)
    
    del input_ids
    torch.cuda.empty_cache()
    
    return outputs


place_url = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
object_url = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
action_url = "http://kgrc4si.home.kg/virtualhome2kg/ontology/action/"
event_url = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
from_url = "http://kgrc4si.home.kg/virtualhome2kg/instance/"
to_url = "http://kgrc4si.home.kg/virtualhome2kg/instance/"

event_num_pattern = re.compile(r'event([0-9]*)')
object_id_pattern = re.compile(r'[0-9]+_scene.*')
file_pattern = ".*:"

url_list = [
    action_url,
    event_url,
    object_url,
    object_url,
    place_url,
    from_url,
    to_url
]

key_list = [
    "action",
    "event",
    "object",
    "t_object",
    "place",
    "from",
    "to",
]

activities = []
with open("./data/kg_datas/activitites.txt", "r") as f:
    for line in f.readlines():
        activities.append(line.replace("\n", "")) 

miss_probs = [
    "222",
    "500",
    "550",
    "5515",
    "101010",
    "1000",
    "10100"
]

p_count = 0
o_count = 0
a_count = 0
t_count = 0

# 欠損している箇所を取得
for activity in activities:
    if activity[:-7].replace("_", " ") in ex_activities:
        continue
    # 正解データから欠損部分と正解，デュレーションを取得
    print(activity)
    complete_dicts = []
    with open(f"./answers/{activity}.txt", "r") as f:
        for line in f.readlines():
            result_dict = {
                "event": "",
                "time": "",
                "place": "",
                "action": "",
                "object": "",
                "t_object": ""
            }
            line = line.replace("\n", "")
            split_lines = line.split(",")
            for split_line in split_lines:
                result_dict[re.findall(file_pattern, split_line)[0][:-1]] = re.sub(file_pattern, "", split_line)
            complete_dicts.append(result_dict)
    # 先に動画を保存する
    # pathの作成
    new_dir_path = f"./use_movies/{activity}"
    try:
        os.mkdir(new_dir_path)
    except:
        pass
    # videoの抽出
    activity_name = activity[:-7].replace("_", " ")
    action_perspective = 0
    object_perspective = 1
    place_perspective = 2
    for i, complete_dict in enumerate(complete_dicts):
        event = complete_dict["event"]
        scene = event[-6:]
        duration = complete_dict["time"]
        save_path = f"./use_movies/{activity}/{event}_{action_perspective}.mp4"
        save_path_place = f"./use_movies/{activity}/{event}_{place_perspective}.mp4"
        save_path_object = f"./use_movies/{activity}/{event}_{object_perspective}.mp4"
        video_path = f"./movies5.0.2/{scene}/movies/{activity_name}_{action_perspective}.mp4"
        video_path_place = f"./movies5.0.2/{scene}/movies/{activity_name}_{place_perspective}.mp4"
        video_path_object = f"./movies5.0.2/{scene}/movies/{activity_name}_{object_perspective}.mp4"
        if not i == 0:
            for j in range(0, i):
                prev_duration = complete_dicts[i-(j+1)]["time"]
                if not duration == prev_duration:
                    break
                duration = prev_duration
            video_clip(start=prev_duration, end=duration, file_path=video_path, save_path=save_path)
            video_clip(start=prev_duration, end=duration, file_path=video_path_place, save_path=save_path_place)
            video_clip(start=prev_duration, end=duration, file_path=video_path_object, save_path=save_path_object)
        else:
            video_clip(start=0, end=duration, file_path=video_path, save_path=save_path)
            video_clip(start=0, end=duration, file_path=video_path_place, save_path=save_path_place)
            video_clip(start=0, end=duration, file_path=video_path_object, save_path=save_path_object)
action_perspective = 0
object_perspective = 1
place_perspective = 2
for mis_prob in miss_probs:
    for activity in activities:
        print(activity, "activity")
        if "Legopp" in activity:
            tmp_str = list(activity)
            tmp_str[3] = "O"
            file_activity = "".join(tmp_str)
        else:
            file_activity = activity
        complete_dicts = []
        with open(f"./answers/{activity}.txt", "r") as f:
            for line in f.readlines():
                result_dict = {
                    "event": "",
                    "time": "",
                    "place": "",
                    "action": "",
                    "object": "",
                    "t_object": ""
                }
                line = line.replace("\n", "")
                split_lines = line.split(",")
                for split_line in split_lines:
                    result_dict[re.findall(file_pattern, split_line)[0][:-1]] = re.sub(file_pattern, "", split_line)
                complete_dicts.append(result_dict)
        # pathの作成
        new_dir_path = f"./test_answers/{mis_prob}/{activity}"
        try:
            os.mkdir(new_dir_path)
        except:
            pass
        file_path_miss = f'https://raw.githubusercontent.com/takanori-ugai/IKGRC2024Data/master/Data/{mis_prob}/{file_activity}-{mis_prob}.ttl'
        miss_graph = Graph()
        miss_graph.parse(file_path_miss, format='turtle')

        # SPARQLクエリを定義する
        sparql_query = """
            prefix ex: <http://kgrc4si.home.kg/virtualhome2kg/instance/>
            prefix : <http://kgrc4si.home.kg/virtualhome2kg/ontology/>
            select *
            WHERE {
            {
                ?event :action ?action.
                ?event :mainObject ?object.
                ?event :place ?place.
                OPTIONAL{
                ?event :targetObject ?t_object
                }
            }
            UNION
            {
                ?event :action ?action.
                ?event :mainObject ?object.
                ?event :from ?from.
                ?event :to ?to.
                OPTIONAL{
                ?event :targetObject ?t_object
                }
            }      
            }
        """
        query_result_miss = miss_graph.query(sparql_query)
        result_dicts_miss = []
        tmp_event = None
        for row in query_result_miss:
            result_dict = {
                "event": "",
                "event_num": "",
                "place": "",
                "action": "",
                "object": "",
                "t_object": "",
                "from": "",
                "to": "",
            }
            flag = False
            for i, key in enumerate(key_list):
                if getattr(row, key) is not None:
                    result_dict[key] = getattr(row, key).replace(url_list[i], "")
                if key == "event":
                    if getattr(row, key).replace(url_list[i], "") == tmp_event:
                        flag = True
                    tmp_event = getattr(row, key).replace(url_list[i], "")
                    result_dict["event_num"] = event_num_pattern.match(getattr(row, key).replace(url_list[i], "")).groups()[0]
            if not flag:
                result_dicts_miss.append(result_dict)

        result_dicts_miss = sorted(result_dicts_miss, key=lambda x: int(x["event_num"]))
        for i, result_dict in enumerate(result_dicts_miss):
            try:
                save_path = f'./test_answers/{mis_prob}/{activity}/{complete_dicts[i]["event"]}.txt'
                print(result_dict)
                flag = False
                a_flag = False
                p_flag = False
                o_flag = False
                t_flag = False
                duration = None
                for key in key_list:
                    if "XXX" in result_dict[key]:
                        print(result_dict[key])
                        flag = True
                        duration = complete_dicts[i]["time"]
                        event = complete_dicts[i]["event"]
                        event_num = result_dict["event_num"]

                        if key == "action":
                            a_flag = True
                        if key == "place":
                            p_flag = True
                        if key == "object":
                            o_flag = True
                        if key == "t_object":
                            t_flag = True
                if not os.path.exists(save_path):
                    print(a_flag, p_flag, o_flag, t_flag)
                    with open(save_path, "w") as f:
                        # 場所は完全独立
                        if p_flag:
                            prompt = "Choose below the options the most likely location of this video and just display the name of the location. \n"
                            with open("./kg_datas/place.txt", "r") as f2:
                                places = [line.replace("\n", "") for line in f2.readlines()]
                            for place in places:
                                prompt += "・" + place + "\n"
                            video_path = f"./use_movies/{activity}/{event}_{place_perspective}.mp4"
                            write_string = video_llava(video=video_path, prompt=prompt).replace(" ", "").replace("</s>", "")
                            f.write("place:," + write_string + "\n")
                        # 両方欠けている
                        if a_flag and o_flag:
                            print("視点1の動画からobject抽出，objectから妥当なactionを抽出, actionの候補を絞って動画から推論, actionとplaceを使ってobjectを推論")
                            # objectの抽出 事前に行ったもの
                            with open(f"./rule_mainobject_detection/{activity}/{event}.txt", "r") as f2:
                                objects = [line.replace("\n", "").replace("</s>", "").lower() for line in f2.readlines()]
                            # objectと関係のあるaction抽出
                            print(objects)
                            actions = []
                            for object in objects:
                                with open(f"./actions_from_object/{object}.txt", "r") as f2:
                                    lines = [line.replace("\n", "") for line in f2.readlines()]
                                actions += lines
                            prompt = "From the below sentences select one that adequately describes what the person in the video is doing. \n"
                            import random
                            random.shuffle(actions)
                            for action in actions:
                                prompt += action + ","
                            print(prompt)
                            video_path = f"./use_movies/{activity}/{event}_{object_perspective}.mp4"
                            write_string = video_llava(video=video_path, prompt=prompt).replace("</s>", "")
                            f.write("action:," + write_string + "\n")
                            f.write("object:," + write_string + "\n")
                            # targetObjectがある場合
                            main_object = write_string.replace(".","").split(" ")[-1].lower()
                            if t_flag:
                                prompt = f"From the below sentences select only one that best describes the {main_object} in this video. \n"
                                with open("./kg_datas/t_objects.txt", "r") as f2:
                                    t_objects = [line.replace("\n", "") for line in f2.readlines()]
                                for t_object in t_objects:
                                    prompt += "・" + main_object + " has the most to do with " + t_object + "." + "\n"
                                video_path = f"./use_movies/{activity}/{event}_{object_perspective}.mp4"
                                write_string = video_llava(video=video_path, prompt=prompt).replace("</s>", "")
                                f.write("t_object:," + write_string + "\n")
                                
                        # actionのみが欠けている
                        elif (a_flag) and (not o_flag):
                            print("視点1の動画とobjectを使って予測")
                            print(result_dict["object"])
                            main_object = re.sub(object_id_pattern, "", result_dict["object"])
                            prompt = "From the below sentences select only one that adequately describes what the person in the video is doing. \n"
                            if os.path.exists(f"./actions_from_object/{main_object}.txt"):
                                with open(f"./actions_from_object/{main_object}.txt", "r") as f2:
                                    actions = [line.replace("\n", "") for line in f2.readlines()]
                            else:
                                with open("./kg_datas/objects.txt", "r") as f2:
                                    actions = [line.replace("\n", "") for line in f2.readlines()]
                            for action in actions:
                                prompt += "・" + action + "\n"
                            video_path = f"./use_movies/{activity}/{event}_{object_perspective}.mp4"
                            write_string = video_llava(video=video_path, prompt=prompt).replace("</s>", "")
                            f.write("action:," + write_string + "\n")

                        # objectのみが欠けている
                        elif (o_flag) and (not a_flag):
                            action = result_dict["action"]
                            prompt = "From the below sentences select only one that adequately describes what the person in the video is doing. \n"
                            if os.path.exists(f"./objects_from_action/{action}.txt"):
                                with open(f"./objects_from_action/{action}.txt", "r") as f2:
                                    objects = [line.replace("\n", "") for line in f2.readlines()]
                            else:
                                with open(f"./kg_datas/actions.txt", "r") as f2:
                                    objects = [line.replace("\n", "") for line in f2.readlines()]
                            for object in objects:
                                prompt += "・" + object + "\n"
                            video_path = f"./use_movies/{activity}/{event}_{object_perspective}.mp4"
                            write_string = video_llava(video=video_path, prompt=prompt).replace("</s>", "")
                            f.write("object:," + write_string + "\n")
                            if t_flag:
                                main_object = write_string.replace("</s>", "").replace(".","").split(" ")[-1].lower()
                                prompt = f"From the below sentences select only one that best describes the {main_object} in this video. \n"
                                with open("./kg_datas/t_objects.txt", "r") as f2:
                                    t_objects = [line.replace("\n", "") for line in f2.readlines()]
                                for t_object in t_objects:
                                    prompt += "・" + main_object + " has the most to do with " + t_object + "." + "\n"
                                video_path = f"./use_movies/{activity}/{event}_{object_perspective}.mp4"
                                write_string = video_llava(video=video_path, prompt=prompt).replace("</s>", "")
                                f.write("t_object:," + write_string + "\n")
            except Exception as e:
                print(e)
                with open("./error_activity.txt", "w") as f:
                    f.write(activity + complete_dicts[i]["event"])
                    exit()
