import os
from ultralytics import RTDETR

def train_model():
    # 1. 모델 로드
    model = RTDETR("rtdetr-l.pt")

    # 2. 알려주신 경로 그대로 넣었습니다. (앞에 r이 꼭 있어야 해요!)
    data_path = r"C:\Users\a\Desktop\git\dataset-v1\data.yaml"

    # 3. 학습 시작
    model.train(
        data=data_path,
        epochs=100,
        imgsz=640,
        batch=4,          # 발열 방지용
        optimizer='AdamW',
        lr0=0.0001,
        device=0,
        workers=2,
        project='runs/detect',
        name='road_debris_study'
    )

if __name__ == '__main__':
    train_model()