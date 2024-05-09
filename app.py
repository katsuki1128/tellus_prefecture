# app.py
import tellus_traveler
import pprint
import geopandas as gpd
import pandas as pd
import folium
import matplotlib.pyplot as plt
import rioxarray
from flask import Flask, render_template, request, url_for, jsonify
import os

app = Flask(__name__)

tellus_traveler.api_token = "FgIaEvBKbokfCq1JMFFNslFDxBRdYwiI"

# 都道府県コードと名称の辞書
pref_codes = {
    "01": "北海道",
    "02": "青森県",
    "03": "岩手県",
    "04": "宮城県",
    "05": "秋田県",
    "06": "山形県",
    "07": "福島県",
    "08": "茨城県",
    "09": "栃木県",
    "10": "群馬県",
    "11": "埼玉県",
    "12": "千葉県",
    "13": "東京都",
    "14": "神奈川県",
    "15": "新潟県",
    "16": "富山県",
    "17": "石川県",
    "18": "福井県",
    "19": "山梨県",
    "20": "長野県",
    "21": "岐阜県",
    "22": "静岡県",
    "23": "愛知県",
    "24": "三重県",
    "25": "滋賀県",
    "26": "京都府",
    "27": "大阪府",
    "28": "兵庫県",
    "29": "奈良県",
    "30": "和歌山県",
    "31": "鳥取県",
    "32": "島根県",
    "33": "岡山県",
    "34": "広島県",
    "35": "山口県",
    "36": "徳島県",
    "37": "香川県",
    "38": "愛媛県",
    "39": "高知県",
    "40": "福岡県",
    "41": "佐賀県",
    "42": "長崎県",
    "43": "熊本県",
    "44": "大分県",
    "45": "宮崎県",
    "46": "鹿児島県",
    "47": "沖縄県",
}


# 都道府県から市町村リストを取得するための関数
def get_city_names(pref_code):
    try:
        prefecture_gdf = gpd.read_file(
            f"/vsizip//vsicurl/https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2023/N03-20230101_{pref_code}_GML.zip/N03-23_{pref_code}_230101.geojson"
        )
        city_names = sorted(prefecture_gdf["N03_004"].unique())
        pprint.pprint(city_names)
        return city_names, prefecture_gdf
    except Exception as e:
        return [], None


def update_city_names(selected_prefecture):
    city_names, prefecture_gdf = get_city_names(selected_prefecture)
    return city_names, prefecture_gdf


@app.route("/update_prefecture/<pref_code>")
def update_prefecture(pref_code):
    city_names, prefecture_gdf = get_city_names(pref_code)
    if city_names:
        geo_json = prefecture_gdf.to_json() if prefecture_gdf is not None else None
        return jsonify({"city_names": city_names, "geo_data": geo_json})
    else:
        return jsonify(
            {"error": f"Could not retrieve cities for prefecture {pref_code}"}
        )


# AVNIR-2 データセットの取得
datasets = tellus_traveler.datasets()
avnir2_dataset = next(dataset for dataset in datasets if "AVNIR-2" in dataset["name"])


@app.route("/", methods=["GET", "POST"])
def home():
    map_html = None
    error_message = None
    selected_city = None
    selected_prefecture = None
    selected_tellus_name = None
    city_names = []
    tellus_names = []
    output_image_path = None

    if request.method == "POST":
        selected_prefecture = request.form.get("prefecture")
        selected_city = request.form.get("city_name")

        selected_tellus_name = request.form.get("tellus_name")
        action = request.form.get("action")

        city_names, prefecture_gdf = update_city_names(selected_prefecture)
        # city_names = get_city_names(selected_prefecture)

        try:
            # GeoDataFrameの取得
            # prefecture_gdf = gpd.read_file(
            #     f"/vsizip//vsicurl/https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2023/N03-20230101_{selected_prefecture}_GML.zip/N03-23_{selected_prefecture}_230101.geojson"
            # )
            city_gdf = prefecture_gdf[prefecture_gdf["N03_004"] == selected_city]

            if city_gdf.empty:
                raise ValueError(f"City '{selected_city}' は見つかりません")

            city_bbox = city_gdf.total_bounds

            # 自治体のAVNIR-2シーンを検索
            search = tellus_traveler.search(
                datasets=[avnir2_dataset["id"]],
                bbox=city_bbox,
                start_datetime="2011-04-01T00:00:00Z",
                end_datetime="2012-05-01T00:00:00Z",
            )
            pprint.pp(search.total())

            scenes = list(search.scenes())
            # pprint.pp(scenes)
            # pprint.pp(scenes[1].__geo_interface__)

            # 地図を作成し、HTMLに保存する
            search_results_gdf = gpd.GeoDataFrame.from_features(scenes, crs="EPSG:4326")

            # "tellus:name" 列の値を pprint で表示
            tellus_names = search_results_gdf["tellus:name"].tolist()
            pprint.pprint(tellus_names)

            if action == "get_map":
                map = search_results_gdf.explore("tellus:name")
                folium.Rectangle(
                    bounds=[(city_bbox[1], city_bbox[0]), (city_bbox[3], city_bbox[2])]
                ).add_to(map)
                map.save("static/map.html")
                map_html = url_for("static", filename="map.html")

            elif action == "get_image" and selected_tellus_name:
                # 適切なシーンを選択
                matching_scene = next(
                    (
                        scene
                        for scene in scenes
                        if scene["tellus:name"] == selected_tellus_name
                    ),
                    None,
                )
                pprint("matching_scene", matching_scene)

                if matching_scene is None:
                    raise ValueError(
                        f"No scene found for 'tellus:name' {selected_tellus_name}"
                    )

                files = matching_scene.files()
                # thumbs = scene.thumbnails()
                target_file = next(file for file in files if "webcog" in file["name"])
                data = rioxarray.open_rasterio(target_file.url(), masked=True)
                clipped_data = data.rio.clip_box(*city_bbox)

                # 画像を表示
                fig, ax = plt.subplots(figsize=(11, 11))
                clipped_data.sel(band=[1, 2, 3]).astype("uint8").plot.imshow(ax=ax)
                city_gdf.plot(ax=ax, color="none")
                ax.set_title(f"True Color\n{matching_scene['tellus:name']}")
                output_image_path = "static/output_image.png"
                plt.savefig(output_image_path, format="png", dpi=300)
                plt.close(fig)

        except Exception as e:
            error_message = str(e)

    return render_template(
        "index.html",
        pref_codes=pref_codes,
        city_names=city_names,
        selected_city=selected_city,
        selected_prefecture=selected_prefecture,
        tellus_names=tellus_names,
        selected_tellus_name=selected_tellus_name,
        map_html=map_html,
        error_message=error_message,
        output_image_path=output_image_path,
    )


if __name__ == "__main__":
    app.run(debug=True)
