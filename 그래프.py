import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 설정 ---
# 데이터가 저장된 CSV 파일 이름
DATA_FILENAME = 'measured_data.csv'

# --- 1. 파일 존재 확인 및 데이터 불러오기 ---
if not os.path.exists(DATA_FILENAME):
    print(f"오류: '{DATA_FILENAME}' 파일을 찾을 수 없습니다.")
    print("데이터 측정 스크립트를 먼저 실행하여 데이터를 저장하세요.")
    exit()

try:
    # pandas를 사용하여 CSV 파일 읽기
    df = pd.read_csv(DATA_FILENAME)
except pd.errors.EmptyDataError:
    print(f"오류: '{DATA_FILENAME}' 파일이 비어있습니다.")
    exit()

# 데이터가 비어있는지 추가로 확인
if df.empty:
    print(f"오류: '{DATA_FILENAME}' 파일에 데이터가 없습니다.")
    exit()

# --- 2. 데이터 준비 ---
# 측정 시작 시간으로부터 몇 초가 지났는지 계산
time_from_start = df['Timestamp'] - df['Timestamp'].iloc[0]
distances = df['Distance_cm']
speeds = df['Speed_kmh']


# --- 3. 그래프 생성 및 시각화 ---
fig, ax1 = plt.subplots(figsize=(12, 6))

# 그래프 제목 설정
ax1.set_title('Distance and Speed Over Time', fontsize=16)

# X축 설정
ax1.set_xlabel('Time (seconds from start)')

# 왼쪽 Y축 (거리)
ax1.set_ylabel('Distance (cm)', color='blue')
ax1.plot(time_from_start, distances, color='blue', alpha=0.8, label='Distance (cm)')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

# 오른쪽 Y축 (속도) - 왼쪽 Y축과 X축을 공유
ax2 = ax1.twinx()
ax2.set_ylabel('Speed (km/h)', color='red')
ax2.plot(time_from_start, speeds, color='red', alpha=0.8, label='Speed (km/h)')
ax2.tick_params(axis='y', labelcolor='red')

# 범례(legend) 표시
# 두 축의 라벨을 모두 가져와서 한 번에 표시
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc='upper right')

# 전체 레이아웃 조정 및 그래프 창 표시
fig.tight_layout()
plt.show()