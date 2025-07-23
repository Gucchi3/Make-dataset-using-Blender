import bpy
import os
import math
import random
from mathutils import Vector
import json
from bpy_extras.object_utils import world_to_camera_view
 
# -----------------------------------------------------------------
#  設定
# -----------------------------------------------------------------

# 1. オブジェクト名
GATE_NAME = "DroneGate"

# 2. 画像・JSONの保存先フォルダ
OUTPUT_FOLDER_IMGS = r"C:\Users\nnykb\Desktop\gate_controller_8\train\dataset"
OUTPUT_FOLDER_JSONS = r"C:\Users\nnykb\Desktop\gate_controller_8\train\jsons"

# 3. ゲートの移動範囲
X_START = 0.3; X_END = -0.3; X_STEPS = 9
Y_START = 0.3; Y_END = -0.3; Y_STEPS = 9
Z_POS = 0.0

# 4. ゲートのサイズ範囲
MIN_SCALE = 2; MAX_SCALE = 6.5; SCALE_STEPS = 9

# 5. ゲートを傾ける角度の範囲設定
# ---  x 角度範囲 ---
X_MIN_ANGLE_DEG = -15
X_MAX_ANGLE_DEG =15
X_ANGLE_STEPS = 5

# --- y ---
Y_MIN_ANGLE_DEG = -60.0
Y_MAX_ANGLE_DEG = 60.0
Y_ANGLE_STEPS = 9

# --- z 角度範囲 ---
Z_MIN_ANGLE_DEG = -15
Z_MAX_ANGLE_DEG = 15
Z_ANGLE_STEPS = 5

# 6. 太陽の強さの範囲 
SUN_STRENGTH_MIN = 0.1
SUN_STRENGTH_MAX = 5

# ゲートの元となる頂点座標（ローカル座標）
F1 = [-0.0378, 0.0378, 0.002]
F2 = [0.0378, 0.0378, 0.002]
F3 = [0.0378, -0.0378, 0.002]
F4 = [-0.0378, -0.0378, 0.002]
BASE_CORNERS = [Vector(p) for p in [F1, F2, F3, F4]]

# -----------------------------------------------------------------
# ★★★ プログラム本体 ★★★
# -----------------------------------------------------------------

def get_pixel_coords(scene, camera, obj, local_points):
    """
    オブジェクトのローカル座標点を、透視投影を考慮して
    最終的なレンダリング画像のピクセル座標に変換する。
    """
    # depsgraph（依存グラフ）を取得して、オブジェクトの最終的な状態を評価
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    # 評価後のオブジェクトを取得
    evaluated_obj = obj.evaluated_get(depsgraph)
    
    # 評価後のワールド行列を使用
    mat_world = evaluated_obj.matrix_world

    render = scene.render
    render_width = render.resolution_x
    render_height = render.resolution_y
    
    pixel_coords = []
    for point in local_points:
        # ワールド座標に変換
        world_coord = mat_world @ point
        
        # 透視投影を考慮してカメラビュー座標に変換
        # この関数が遠近感を正しく処理してくれます
        camera_coord = world_to_camera_view(scene, camera, world_coord)
        
        # 画面外の座標も計算はされるが、AIの学習上は問題ないことが多い
        # (必要なら is_visible チェックなどを追加)
        
        # ピクセル座標に変換 (Y座標は上下反転)
        px = camera_coord.x * render_width
        py = (1.0 - camera_coord.y) * render_height
        
        pixel_coords.append((px, py))
        
    return pixel_coords

# (★★★ 修正 ★★★) 引数に sun_light を追加
def process_and_save(scene, camera, gate, sun_light, image_counter):
    bpy.context.view_layer.update()
    
    filename_base = f"{image_counter:06d}"
    img_filepath = os.path.join(OUTPUT_FOLDER_IMGS, filename_base + ".png")
    json_filepath = os.path.join(OUTPUT_FOLDER_JSONS, filename_base + ".json")
    
    scene.render.filepath = img_filepath
    pixel_coords = get_pixel_coords(scene, camera, gate, BASE_CORNERS)

    print("-" * 50)
    print(f"画像 No.{image_counter:06d} のパラメータを出力:")
    rot_x_deg = math.degrees(gate.rotation_euler.x)
    rot_y_deg = math.degrees(gate.rotation_euler.y)
    rot_z_deg = math.degrees(gate.rotation_euler.z)
    print(f"  - 回転角度 (X, Y, Z): ({rot_x_deg:8.2f}, {rot_y_deg:8.2f}, {rot_z_deg:8.2f}) 度")
    print(f"  - 座標 (X, Y, Z):     ({gate.location.x:8.2f}, {gate.location.y:8.2f}, {gate.location.z:8.2f})")
    print(f"  - スケール:           {gate.scale.x:8.2f}")
    # (★★★ 追加 ★★★) 太陽の強さを表示
    if sun_light: print(f"  - 太陽の強さ:       {sun_light.data.energy:.2f}")
    print("  - アノテーション座標 (x, y):")
    print(f"    - Point 1: ({pixel_coords[0][0]:.2f}, {pixel_coords[0][1]:.2f})")
    print(f"    - Point 2: ({pixel_coords[1][0]:.2f}, {pixel_coords[1][1]:.2f})")
    print(f"    - Point 3: ({pixel_coords[2][0]:.2f}, {pixel_coords[2][1]:.2f})")
    print(f"    - Point 4: ({pixel_coords[3][0]:.2f}, {pixel_coords[3][1]:.2f})")

    shapes = []
    for i, (px, py) in enumerate(pixel_coords):
        shapes.append({
            "label": str(i + 1), "points": [[px, py]], "group_id": None,
            "description": "", "shape_type": "point", "flags": {}, "mask": None
        })

    image_path = f"..\\dataset\\{filename_base}.png"
    converted_data = {
        "shapes": shapes, "imagePath": image_path, "imageData": None,
        "imageHeight": scene.render.resolution_y, "imageWidth": scene.render.resolution_x
    }
    
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, indent=4)
        
    bpy.ops.render.render(write_still=True)
    
    print(f"  -> 保存完了: {filename_base}.png / .json")
    return image_counter + 1

# -----------------------------------------------------------------
# ★★★ メイン処理 ★★★
# -----------------------------------------------------------------
def main():
    scene = bpy.context.scene
    gate = bpy.data.objects.get(GATE_NAME)
    camera = scene.camera

    # (★★★ 追加 ★★★) 太陽(Sun)ライトを探す
    sun_light = None
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and obj.data.type == 'SUN':
            sun_light = obj
            break
            
    if not sun_light:
        print("警告: シーンに太陽(Sun)ライトが見つかりません。")

    if not gate: print(f"エラー: オブジェクト '{GATE_NAME}' がありません。"); return
    if not camera: print(f"エラー: カメラがありません。"); return
        
    if not os.path.exists(OUTPUT_FOLDER_IMGS): os.makedirs(OUTPUT_FOLDER_IMGS)
    if not os.path.exists(OUTPUT_FOLDER_JSONS): os.makedirs(OUTPUT_FOLDER_JSONS)
        
    print("データセット生成を開始します...")
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    image_counter = 0

    # =================================================================
    #  Z軸回転 + Y軸回転
    # =================================================================
    print("\n---  Z-Y回転  ---")
    for az_step in range(Z_ANGLE_STEPS):
        z_ratio = az_step / (Z_ANGLE_STEPS - 1) if Z_ANGLE_STEPS > 1 else 0.5
        current_z_angle_rad = math.radians(Z_MIN_ANGLE_DEG + (Z_MAX_ANGLE_DEG - Z_MIN_ANGLE_DEG) * z_ratio)
        for ay_step in range(Y_ANGLE_STEPS):
            y_ratio = ay_step / (Y_ANGLE_STEPS - 1) if Y_ANGLE_STEPS > 1 else 0.5
            current_y_angle_rad = math.radians(Y_MIN_ANGLE_DEG + (Y_MAX_ANGLE_DEG - Y_MIN_ANGLE_DEG) * y_ratio)
            gate.rotation_euler = (0.0, current_y_angle_rad, current_z_angle_rad)
            for s_step in range(SCALE_STEPS):
                s_ratio = s_step / (SCALE_STEPS - 1) if SCALE_STEPS > 1 else 0.5
                gate.scale.xyz = MIN_SCALE + (MAX_SCALE - MIN_SCALE) * s_ratio
                for y_step in range(Y_STEPS):
                    y_pos_ratio = y_step / (Y_STEPS - 1) if Y_STEPS > 1 else 0.5
                    current_y = Y_START + (Y_END - Y_START) * y_pos_ratio
                    for x_step in range(X_STEPS):
                        x_pos_ratio = x_step / (X_STEPS - 1) if X_STEPS > 1 else 0.5
                        current_x = X_START + (X_END - X_START) * x_pos_ratio
                        gate.location = (current_x, current_y, Z_POS)
                        
                        # (★★★ 追加 ★★★) 太陽の強さをランダムに設定
                        if sun_light:
                            random_strength = random.uniform(SUN_STRENGTH_MIN, SUN_STRENGTH_MAX)
                            sun_light.data.energy = random_strength
                            
                        # (★★★ 修正 ★★★) 引数に sun_light を追加
                        image_counter = process_and_save(scene, camera, gate, sun_light, image_counter)

    # =================================================================
    #  Z軸回転 + X軸回転
    # =================================================================
    print("\n---  Z-X回転パターン---")
    for az_step in range(Z_ANGLE_STEPS):
        z_ratio = az_step / (Z_ANGLE_STEPS - 1) if Z_ANGLE_STEPS > 1 else 0.5
        current_z_angle_rad = math.radians(Z_MIN_ANGLE_DEG + (Z_MAX_ANGLE_DEG - Z_MIN_ANGLE_DEG) * z_ratio)
        for ax_step in range(X_ANGLE_STEPS):
            x_ratio = ax_step / (X_ANGLE_STEPS - 1) if X_ANGLE_STEPS > 1 else 0.5
            current_x_angle_deg = X_MIN_ANGLE_DEG + (X_MAX_ANGLE_DEG - X_MIN_ANGLE_DEG) * x_ratio
            if current_x_angle_deg == 0.0: continue
            current_x_angle_rad = math.radians(current_x_angle_deg)
            gate.rotation_euler = (current_x_angle_rad, 0.0, current_z_angle_rad)
            for s_step in range(SCALE_STEPS):
                s_ratio = s_step / (SCALE_STEPS - 1) if SCALE_STEPS > 1 else 0.5
                gate.scale.xyz = MIN_SCALE + (MAX_SCALE - MIN_SCALE) * s_ratio
                for y_step in range(Y_STEPS):
                    y_pos_ratio = y_step / (Y_STEPS - 1) if Y_STEPS > 1 else 0.5
                    current_y = Y_START + (Y_END - Y_START) * y_pos_ratio
                    for x_step in range(X_STEPS):
                        x_pos_ratio = x_step / (X_STEPS - 1) if X_STEPS > 1 else 0.5
                        current_x = X_START + (X_END - X_START) * x_pos_ratio
                        gate.location = (current_x, current_y, Z_POS)
                        
                        # (★★★ 追加 ★★★) 太陽の強さをランダムに設定
                        if sun_light:
                            random_strength = random.uniform(SUN_STRENGTH_MIN, SUN_STRENGTH_MAX)
                            sun_light.data.energy = random_strength
                        
                        # (★★★ 修正 ★★★) 引数に sun_light を追加
                        image_counter = process_and_save(scene, camera, gate, sun_light, image_counter)



    print("-" * 50)
    print(f"完了！合計 {image_counter} 枚のデータを生成しました。")
    print(f"画像保存先: {OUTPUT_FOLDER_IMGS}")
    print(f"JSON保存先: {OUTPUT_FOLDER_JSONS}")

if __name__ == "__main__":
    main()
