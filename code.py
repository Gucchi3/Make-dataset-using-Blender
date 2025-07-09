import bpy
import os
import math
import numpy as np
import random

import json
#160x160 -- 0.36 x 0.36m
# -----------------------------------------------------------------
# ★★★ 設定項目 ★★★
# -----------------------------------------------------------------

# 1. オブジェクト名
GATE_NAME = "DroneGate"

# 2. 画像の保存先フォルダ
OUTPUT_FOLDER = r"C:\Users\nnykb\Desktop\gate_sim\imgs" # ← パスを書き換える！

# 3. ゲートの移動範囲
X_START = 0.42; X_END = -0.42; X_STEPS = 7
Y_START = 0.42;   Y_END = -0.42;  Y_STEPS = 7
Z_POS = 0.0

# 4. ゲートのサイズ範囲
MIN_SCALE = 2.5; MAX_SCALE = 10; SCALE_STEPS = 7

# 5. 【NEW】ゲートを傾ける角度の範囲設定
# --- 上下（おじぎ）方向の回転（X軸） ---
X_MIN_ANGLE_DEG = -75.0
X_MAX_ANGLE_DEG = 75.0
X_ANGLE_STEPS = 7

# --- 左右（首振り）方向の回転（Y軸） ---
Y_MIN_ANGLE_DEG = -75.0
Y_MAX_ANGLE_DEG = 75.0
Y_ANGLE_STEPS = 7

F1 =[ -0.0366, 0.0366, 0.0]
F2 =[ 0.0366, 0.0366, 0.0]
F3 =[ 0.0366, -0.0366, 0.0]
F4 =[ -0.0366, -0.0366, 0.0]
F = np.array([F1, F2, F3, F4])

divide_rate =0.5

#color_top = 0.9
#color_bottom= 0.1

# -----------------------------------------------------------------
# ★★★ プログラム本体 ★★★
# -----------------------------------------------------------------

scene = bpy.context.scene
gate = bpy.data.objects.get(GATE_NAME)

if not gate:
    print(f"エラー: オブジェクト名 '{GATE_NAME}' が見つかりません。")
else:
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    print("データセット生成を開始します...")
    
    gate_material = gate.active_material
    base_color_input = None # 事前に変数を定義
    
    if gate_material and gate_material.use_nodes:
        principled_node = None
        for node in gate_material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled_node = node
                break
        
        if principled_node:
            base_color_input = principled_node.inputs.get("Base Color")
        else:
            print("エラー: マテリアルにプリンシプルBSDFノードが見つかりません。")
    
    else:
        print("エラー: ゲートにマテリアルが設定されていないか、ノードを使用していません。")
        
    if base_color_input is None:
        print("色の設定ができないため、処理を中断します。")
        exit()

    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    image_counter = 0
    


    # 【ループ1】Y軸（左右）の角度を変えるための繰り返し
    for ay_step in range(Y_ANGLE_STEPS):
        y_ratio = ay_step / (Y_ANGLE_STEPS - 1) if Y_ANGLE_STEPS > 1 else 0
        current_y_angle_deg = Y_MIN_ANGLE_DEG + (Y_MAX_ANGLE_DEG - Y_MIN_ANGLE_DEG) * y_ratio
        current_y_angle_rad = math.radians(current_y_angle_deg)
        
        # X軸の回転は0に固定
        current_x_angle_rad = 0.0
        current_x_angle_deg = 0.0
        
        # Y軸回転のみ設定
        gate.rotation_euler = (current_x_angle_rad, current_y_angle_rad, 0)

        # 【ループ3】サイズを変えるための繰り返し
        for s_step in range(SCALE_STEPS):
            s_ratio = s_step / (SCALE_STEPS - 1) if SCALE_STEPS > 1 else 0
            current_scale = MIN_SCALE + (MAX_SCALE - MIN_SCALE) * s_ratio
            gate.scale = (current_scale, current_scale, current_scale)

            # 【ループ4】Y方向（縦）に動かすための繰り返し
            for y_step in range(Y_STEPS):
                y_pos_ratio = y_step / (Y_STEPS - 1) if Y_STEPS > 1 else 0
                current_y = Y_START + (Y_END - Y_START) * y_pos_ratio

                # 【ループ5】X方向（横）に動かすための繰り返し
                for x_step in range(X_STEPS):
                    x_pos_ratio = x_step / (X_STEPS - 1) if X_STEPS > 1 else 0
                    current_x = X_START + (X_END - X_START) * x_pos_ratio
                    gate.location = (current_x, current_y, Z_POS)
                    
                    #random_gray_value = random.uniform(color_bottom, color_top)
                    #new_color = (random_gray_value, random_gray_value, random_gray_value, 1.0)
                    #base_color_input.default_value = new_color
                    
                    

                    print(fr"current_y_angle_deg:{current_y_angle_deg}")
                    print(fr"current_x_angle_deg:{current_x_angle_deg}")
                    print(fr"scale:{current_scale}")
                    print(fr"current_y:{current_y}")
                    print(fr"current_x:{current_x}")

                    Xr = np.array([[1, 0, 0],
                                     [0, math.cos(current_x_angle_rad), 0],
                                     [0, math.sin(current_x_angle_rad), 1]])
    
                    Yr = np.array([[math.cos(current_y_angle_rad), 0, 0],
                                     [0, 1, 0],
                                     [math.sin(current_y_angle_rad), 0, 1]])
    
                    NF1 = np.dot(Yr, F[0,:])
                    NF2 = np.dot(Yr, F[1,:])
                    NF3 = np.dot(Yr, F[2,:])
                    NF4 = np.dot(Yr, F[3,:])
    
                    NF1 = np.dot(Xr, NF1)
                    NF2 = np.dot(Xr, NF2)
                    NF3 = np.dot(Xr, NF3)
                    NF4 = np.dot(Xr, NF4)
    
                    NF1 = NF1 * current_scale
                    NF2 = NF2 * current_scale
                    NF3 = NF3 * current_scale
                    NF4 = NF4 * current_scale
    
                    NF1[1] += current_y
                    NF2[1] += current_y
                    NF3[1] += current_y
                    NF4[1] += current_y
    
                    NF1[0] += current_x
                    NF2[0] += current_x
                    NF3[0] += current_x
                    NF4[0] += current_x
    
                    NF = np.array([NF1, NF2, NF3, NF4])
                    FN = []
    
                    print(fr"NF1:{NF1}")
                    print(fr"NF2:{NF2}")
                    print(fr"NF3:{NF3}")
                    print(fr"NF4:{NF4}")
    
#                    for row in NF:
#                        if row[2] == 0.0:
#                            NR = [row[0], row[1]]
#                            FN.append(NR)
#                        elif row[2] < 0.0:
#                            iz = row[2] * -1
#                            val0 = row[0] / (1 + iz)
#                            val1 = row[1] 
#                            NR = [val0, val1]
#                            FN.append(NR)
#                        else:
#                            val0 = row[0] / (1 - row[2])
#                            val1 = row[1] 
#                            NR = [val0, val1]
#                            FN.append(NR)
    
                   # print(fr"FN:{FN}")
                    LNF_normalized = NF / divide_rate
                    LNF_normalized_2d = LNF_normalized[:, :2]
                    
                    LNF_pixels = np.zeros_like(LNF_normalized_2d)
                    LNF_pixels[:, 0] = LNF_normalized_2d[:, 0] * 80 + 80
                    LNF_pixels[:, 1] = -LNF_normalized_2d[:, 1] * 80 + 80
                    print(fr"LNF{LNF_pixels}")
                    #LNF_pixels = np.clip(LNF_pixels, 0, 159).astype(int)
                    #print("--- 整数化し、0-159の範囲に収めた座標 ---")
                    #print(LNF_pixels)
     
                    
                    
                    
                 
                    
                    
                    
                    

                    # ファイル名に両方の角度ステップも加える
                    # ay_stepはX軸回転時は無関係になるが、ファイル名の命名規則を統一するため残す
                    ax_step_for_filename = -1 # Y軸回転ループを示すために-1などにする（任意）
                    filename = f"{image_counter:06d}.png"
                    json_filename = fr"C:\Users\nnykb\Desktop\gate_sim\jsons\{image_counter:06}.json"
                    filepath = os.path.join(OUTPUT_FOLDER, filename)
                    scene.render.filepath = filepath
                    
                    x1 = LNF_pixels[0,0]
                    y1 = LNF_pixels[0,1]
                    x2 = LNF_pixels[1,0]
                    y2 = LNF_pixels[1,1]
                    x3 = LNF_pixels[2,0]
                    y3 = LNF_pixels[2,1]
                    x4 = LNF_pixels[3,0]
                    y4 = LNF_pixels[3,1]
                    
                    data = {
                        "x1":x1,
                        "y1":y1,
                        "x2":x2,
                        "y2":y2,
                        "x3":x3,
                        "y3":y3,
                        "x4":x4,
                        "y4":y4,
                        }
                        
                    with open(json_filename, 'w', encoding='utf-8') as f:
                         json.dump(data, f, indent=4, ensure_ascii=False)
                    

                    bpy.ops.render.render(write_still=True)
                    
                    # print(f"保存しました: {filename}")
                    image_counter += 1


    
    # 【ループ2】X軸（上下）の角度を変えるための繰り返し
    for ax_step in range(X_ANGLE_STEPS):
        x_ratio = ax_step / (X_ANGLE_STEPS - 1) if X_ANGLE_STEPS > 1 else 0
        current_x_angle_deg = X_MIN_ANGLE_DEG + (X_MAX_ANGLE_DEG - X_MIN_ANGLE_DEG) * x_ratio
        
        # 変更点③: 角度0度はY軸ループで既に生成済みなのでスキップする
        if current_x_angle_deg == 0.0:
            #print("aaaaaaaaaaaaaaaaaaaaa")
            continue
            
        current_x_angle_rad = math.radians(current_x_angle_deg)
        
        # Y軸の回転は0に固定
        current_y_angle_rad = 0.0

        # X軸回転のみ設定
        gate.rotation_euler = (current_x_angle_rad, current_y_angle_rad, 0)
        
        # 【ループ3】サイズを変えるための繰り返し
        for s_step in range(SCALE_STEPS):
            s_ratio = s_step / (SCALE_STEPS - 1) if SCALE_STEPS > 1 else 0
            current_scale = MIN_SCALE + (MAX_SCALE - MIN_SCALE) * s_ratio
            gate.scale = (current_scale, current_scale, current_scale)

            # 【ループ4】Y方向（縦）に動かすための繰り返し
            for y_step in range(Y_STEPS):
                y_pos_ratio = y_step / (Y_STEPS - 1) if Y_STEPS > 1 else 0
                current_y = Y_START + (Y_END - Y_START) * y_pos_ratio

                # 【ループ5】X方向（横）に動かすための繰り返し
                for x_step in range(X_STEPS):
                    x_pos_ratio = x_step / (X_STEPS - 1) if X_STEPS > 1 else 0
                    current_x = X_START + (X_END - X_START) * x_pos_ratio
                    gate.location = (current_x, current_y, Z_POS)
                    
                    # change the gate color
                    #random_gray_value = random.uniform(color_bottom, color_top)
                    #new_color = (random_gray_value, random_gray_value, random_gray_value, 1.0)
                    #base_color_input.default_value = new_color

                    print(fr"current_y_angle_deg:{current_y_angle_deg}")
                    print(fr"current_x_angle_deg:{current_x_angle_deg}")
                    print(fr"scale:{current_scale}")
                    print(fr"current_y:{current_y}")
                    print(fr"current_x:{current_x}")

                    Xr = np.array([[1, 0, 0],
                                     [0, math.cos(current_x_angle_rad), 0],
                                     [0, math.sin(current_x_angle_rad), 1]])
    
                    Yr = np.array([[math.cos(current_y_angle_rad), 0, 0],
                                     [0, 1, 0],
                                     [math.sin(current_y_angle_rad), 0, 1]])
    
                    NF1 = np.dot(Yr, F[0,:])
                    NF2 = np.dot(Yr, F[1,:])
                    NF3 = np.dot(Yr, F[2,:])
                    NF4 = np.dot(Yr, F[3,:])
    
                    NF1 = np.dot(Xr, NF1)
                    NF2 = np.dot(Xr, NF2)
                    NF3 = np.dot(Xr, NF3)
                    NF4 = np.dot(Xr, NF4)
    
                    NF1 = NF1 * current_scale
                    NF2 = NF2 * current_scale
                    NF3 = NF3 * current_scale
                    NF4 = NF4 * current_scale
    
                    NF1[1] += current_y
                    NF2[1] += current_y
                    NF3[1] += current_y
                    NF4[1] += current_y
    
                    NF1[0] += current_x
                    NF2[0] += current_x
                    NF3[0] += current_x
                    NF4[0] += current_x
    
                    NF = np.array([NF1, NF2, NF3, NF4])
                    FN = []
    
                    print(fr"NF1:{NF1}")
                    print(fr"NF2:{NF2}")
                    print(fr"NF3:{NF3}")
                    print(fr"NF4:{NF4}")
                    
#                    x_rate = current_x / divide_rate
#                    y_rate = current_y / divide_rate
#    
#                    for row in NF:
#                        if row[2] == 0.0:
#                          FN.append(NR)
#                        elif row[2] < 0.0:
#                            iz = row[2] * -1
#                            val0 = row[0]
#                            val1 = row[1] / (1 + iz)
#                            NR = [val0, val1]
#                            FN.append(NR)
#                        else:
#                            val0 = row[0]
#                            val1 = row[1] / (1 - row[2])
#                            NR = [val0, val1]
#                            FN.append(NR)
#                            
#                    FN = np.array(FN)
#                    FN[:,0] += x_rate
#                    FN[:,1] += y_rate
#    
#                    print(fr"FN:{FN}")
                   
                    
                    LNF_normalized = NF / divide_rate
                    LNF_normalized_2d = LNF_normalized[:, :2]
                    
                    LNF_pixels = np.zeros_like(LNF_normalized_2d)
                    LNF_pixels[:, 0] = LNF_normalized_2d[:, 0] * 80 + 80
                    LNF_pixels[:, 1] = -LNF_normalized_2d[:, 1] * 80 + 80
                    print(fr"LNF{LNF_pixels}")
                    #LNF_pixels = np.clip(LNF_pixels, 0, 159).astype(int)
                    #print("--- 0-159の範囲に収めた座標 ---")
                    #print(LNF_pixels)
                    
                    
                    
                            
                    
                   

                    # ファイル名に両方の角度ステップも加える
                    ay_step_for_filename = -1 # X軸回転ループを示すために-1などにする（任意）
                    filename = f"{image_counter:06}.png"
                    json_filename = fr"C:\Users\nnykb\Desktop\gate_sim\jsons\{image_counter:06}.json"
                    filepath = os.path.join(OUTPUT_FOLDER, filename)
                    scene.render.filepath = filepath
                    
                    x1 = LNF_pixels[0,0]
                    y1 = LNF_pixels[0,1]
                    x2 = LNF_pixels[1,0]
                    y2 = LNF_pixels[1,1]
                    x3 = LNF_pixels[2,0]
                    y3 = LNF_pixels[2,1]
                    x4 = LNF_pixels[3,0]
                    y4 = LNF_pixels[3,1]
                    
                    data = {
                        "x1":x1,
                        "y1":y1,
                        "x2":x2,
                        "y2":y2,
                        "x3":x3,
                        "y3":y3,
                        "x4":x4,
                        "y4":y4,
                        }
                        
                    with open(json_filename, 'w', encoding='utf-8') as f:
                         json.dump(data, f, indent=4, ensure_ascii=False)
                    
                    bpy.ops.render.render(write_still=True)
                    image_counter += 1


    print("-----------------------------------------")
    print(f"完了yep!合計 {image_counter} 枚の画像を生成しました。")
    print(f"保存先フォルダ: {OUTPUT_FOLDER}")