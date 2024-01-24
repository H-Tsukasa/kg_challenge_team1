# kg_challenge_team1
This repository contains the executable code for Team 1's knowledge graph inference held at [International Knowledge Graph Reasoning Challenge 2024](https://ikgrc.org/2024/)
## Challenge details
### task1
Extracts from the [complete knowledge graph](https://github.com/KnowledgeGraphJapan/KGRC-RDF/tree/kgrc4si/CompleteData) suitable for the following tasks.
- Q3: What to do after entering the kitchen?
- Q4: What to do before entering the kitchen?
- Q7: Extraction of relations between things and objects in the initial state and after 10 seconds
- Q8: Extraction of the position and state of the object after 20 seconds.
### task2
Infer missing data from the [missing knowledge graph](https://github.com/KnowledgeGraphJapan/KGRC-RDF/tree/kgrc4si/PartiallyMissingData).

## Related Work
- [GPT4](https://openai.com/research/gpt-4)
- [LLaVA](https://llava-vl.github.io/)
- [Video-LLaVA](https://arxiv.org/abs/2311.10122)
## Environment
### Version
- Ubuntu 22.04.3 LTS
- python 3.10.13
- cuda 11.7

### Main Library
#### task1
```
SPARQLWrapper==2.0.0
torch==2.1.0
torchaudio==0.13.0+cu117
torchvision==0.16.0
```
### Preparations
#### task1
- Install SPARQLWrapper
    ```
    pip install SPQRQLWrapper==2.0.0
    ```
- Execute each code
  ```
  python3 q4.py
  ```
#### task2
- Install Video-LLaVA(reference [here](https://github.com/PKU-YuanGroup/Video-LLaVA))
    ```
    git clone https://github.com/PKU-YuanGroup/Video-LLaVA
    cd Video-LLaVA
    conda create -n videollava python=3.10 -y
    conda activate videollava
    pip install --upgrade pip  # enable PEP 660 support
    pip install -e .
    pip install -e ".[train]"
    pip install flash-attn --no-build-isolation
    pip install decord opencv-python git+https://github.com/facebookresearch/pytorchvideo.git@28fe037d212663c6a24f373b94cc5d478c8c1a1d
    ```
- Execute code
    ```
    python3 prediction_miss_graph.py
    ```
