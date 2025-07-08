# Simple script to read out tracked target from RFbeam K-LD7
#
#**************************************************************************
# RFbeam Microwave GmbH
#**************************************************************************
#
# Author:   RFbeam Microwave GmbH
# Date:     20.09.2019
# Python Version: 3.7.4
#
# Notes:    Enter the corresponding COM Port and make sure all modules
#           are installed before executing.
#           MODIFIED: Runs continuously and saves data to CSV on exit.
#
#--------------------------------------------------------------------------
# Rev 1.0   | 15.10.2019    | - Initial version                           |   FN
# Rev 2.1   | 08.07.2025    | - Fixed sequence error, added finally block |   AI
#**************************************************************************
import time
import serial
import matplotlib.pyplot as plt
import numpy as np
import math
import csv # 데이터 저장을 위해 csv 모듈 추가

# --- 설정 변수 ---
COM_Port = 'COM10' # 사용하는 COM 포트 번호로 변경하세요.
DATA_FILENAME = 'measured_data.csv' # 저장될 파일 이름

# --- 데이터 저장을 위한 리스트 초기화 ---
measured_data_list = []
# CSV 파일의 헤더(첫 번째 줄)를 정의합니다.
csv_header = ['Timestamp', 'Distance_cm', 'Speed_kmh', 'Angle_deg', 'Magnitude', 'x_cm', 'y_cm']

# --- 시리얼 객체 생성 ---
# create serial object with corresponding COM Port and open it
# com_obj 변수가 try 블록 밖에서도 인식되도록 None으로 초기화
com_obj = None
try:
    com_obj=serial.Serial(COM_Port, timeout=2) # 2초 타임아웃 설정
    com_obj.baudrate=115200
    com_obj.parity=serial.PARITY_EVEN
    com_obj.stopbits=serial.STOPBITS_ONE
    com_obj.bytesize=serial.EIGHTBITS

    # --- 센서 초기화 및 설정 ---
    # connect to sensor and set baudrate
    payloadlength = (4).to_bytes(4, byteorder='little')
    value = (3).to_bytes(4, byteorder='little')
    header = bytes("INIT", 'utf-8')
    cmd_init = header+payloadlength+value
    com_obj.write(cmd_init)

    # get response
    response_init = com_obj.read(9)
    if not response_init or response_init[8] != 0:
        print('Error during initialisation for K-LD7. Check connection.')
        exit() # 초기화 실패 시 프로그램 종료

    # delay 75ms
    time.sleep(0.075)

    # change to higher baudrate
    com_obj.baudrate = 2E6

    # change max speed to 25km/h
    value = (1).to_bytes(4, byteorder='little')
    header = bytes("RSPI", 'utf-8')
    cmd_frame = header+payloadlength+value
    com_obj.write(cmd_frame)
    response_init = com_obj.read(9)
    if not response_init or response_init[8] != 0:
        print('Error: Speed command not acknowledged')

    # change max range to 10m
    value = (1).to_bytes(4, byteorder='little')
    header = bytes("RRAI", 'utf-8')
    cmd_frame = header+payloadlength+value
    com_obj.write(cmd_frame)
    response_init = com_obj.read(9)
    if not response_init or response_init[8] != 0:
        print('Error: Range command not acknowledged')

    # --- 그래프 창 생성 ---
    fig = plt.figure(figsize=(10,5))
    plt.ion()
    plt.show()

    # plot speed/distance
    sub1 = fig.add_subplot(121)
    point_sub1, = sub1.plot(0,0,'o',markersize=10,markerfacecolor='b',markeredgecolor='k')
    plt.grid(True)
    plt.axis([-25, 25, 0, 1000])
    plt.title('Distance / Speed')
    plt.xlabel('Speed [km/h]')
    plt.ylabel('Distance [cm]')

    # plot distance/distance
    sub2 = fig.add_subplot(122)
    point_sub2, = sub2.plot(0,0,'o',markersize=10,markerfacecolor='b',markeredgecolor='k')
    plt.grid(True)
    plt.axis([-500, 500, 0, 1000])
    plt.title('Distance / Distance \n (Green: Receding, Red: Approaching)')
    plt.xlabel('Distance [cm]')
    plt.ylabel('Distance [cm]')

    # --- 메인 루프: 데이터 수집 및 시각화 ---
    print("Starting data acquisition... Press Ctrl+C to stop and save data.")
    while True:
        # request next frame data
        TDAT = (8).to_bytes(4, byteorder='little')
        header = bytes("GNFD", 'utf-8')
        cmd_frame = header+payloadlength+TDAT
        com_obj.write(cmd_frame)

        # get acknowledge
        resp_frame = com_obj.read(9)
        if not resp_frame or resp_frame[8] != 0:
            print('Warning: Command not acknowledged')
            continue # 다음 루프로 넘어감

        # get data
        resp_frame = com_obj.read(8)

        # check if target detected
        target_detected = 0
        if resp_frame and resp_frame[4] > 1:
            target_detected = 1
            # --- 데이터 파싱 ---
            TDAT_Distance_raw = np.frombuffer(com_obj.read(2), dtype=np.uint16)
            TDAT_Speed_raw = np.frombuffer(com_obj.read(2), dtype=np.int16)
            TDAT_Angle_raw = np.frombuffer(com_obj.read(2), dtype=np.int16)
            TDAT_Magnitude_raw = np.frombuffer(com_obj.read(2), dtype=np.uint16)

            # 배열에서 값 추출 및 변환
            TDAT_Distance = float(TDAT_Distance_raw[0])
            TDAT_Speed = float(TDAT_Speed_raw[0]) / 100
            TDAT_Angle_deg = float(TDAT_Angle_raw[0]) / 100
            TDAT_Angle_rad = math.radians(TDAT_Angle_deg)
            TDAT_Magnitude = float(TDAT_Magnitude_raw[0])

            distance_x = -(TDAT_Distance * math.sin(TDAT_Angle_rad))
            distance_y = TDAT_Distance * math.cos(TDAT_Angle_rad)

            # --- 데이터 저장 리스트에 추가 ---
            current_time = time.time()
            data_row = [current_time, TDAT_Distance, TDAT_Speed, TDAT_Angle_deg, TDAT_Magnitude, distance_x, distance_y]
            measured_data_list.append(data_row)

        if target_detected:
            # --- 그래프 업데이트 ---
            # ❗❗ 오류 수정: 변수를 리스트로 감싸서 전달합니다. ❗❗
            point_sub1.set_xdata([TDAT_Speed])
            point_sub1.set_ydata([TDAT_Distance])

            point_sub2.set_xdata([distance_x])
            point_sub2.set_ydata([distance_y])

            if TDAT_Speed > 0 :
                point_sub2.set_markerfacecolor('g') # 후퇴: 초록색
            else:
                point_sub2.set_markerfacecolor('r') # 접근: 빨간색

        # draw figures
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.01) # CPU 부하 감소 및 GUI 이벤트 처리 시간 확보

except KeyboardInterrupt:
    # --- Ctrl+C를 누르면 여기로 이동 ---
    print(f"\nLoop terminated by user. Saving {len(measured_data_list)} data points to {DATA_FILENAME}...")
    # --- 데이터 파일로 저장 ---
    try:
        with open(DATA_FILENAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csv_header) # 헤더 작성
            writer.writerows(measured_data_list) # 모든 데이터 작성
        print("Data saved successfully.")
    except Exception as e:
        print(f"Error saving data: {e}")

except serial.SerialException as e:
    print(f"Serial port error: {e}")

finally:
    # --- 어떤 상황에서든 마지막에 항상 실행 ---
    if com_obj and com_obj.is_open:
        # --- 센서 연결 종료 ---
        print("Disconnecting from sensor...")
        payloadlength = (0).to_bytes(4, byteorder='little')
        header = bytes("GBYE", 'utf-8')
        cmd_frame = header+payloadlength
        com_obj.write(cmd_frame)

        # get response
        com_obj.read(9)

        # close connection to COM port
        com_obj.close()
        print("Connection closed.")