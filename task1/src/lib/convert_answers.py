import json


def jsonify_answers(result_path="./result", answers=None, senario=None, question_id=None):  # fmt: skip
    if answers is None:
        print("answersに値が入っていません．")
        return
    # jsonファイルへの書き出し
    with open(f"{result_path}/{question_id}/{question_id}_answer_{senario}.json", "w") as f:  # fmt: skip
        dict_answer = {
            "name": "Test Test",
            "senario": senario,
            "answers": answers,
        }
        json.dump(dict_answer, f, indent=4)
