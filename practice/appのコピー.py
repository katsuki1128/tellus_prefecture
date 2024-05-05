# app.py
import tellus_traveler
import pprint
import geopandas as gpd
import folium
import rioxarray
import matplotlib.pyplot as plt
from flask import Flask, render_template

tellus_traveler.api_token = "FgIaEvBKbokfCq1JMFFNslFDxBRdYwiI"

datasets = tellus_traveler.datasets()
# pprint.pp(datasets[0])

avnir2_dataset = next(dataset for dataset in datasets if "AVNIR-2" in dataset["name"])
# pprint.pp(avnir2_dataset)

ibaraki_gdf = gpd.read_file(
    "/vsizip//vsicurl/https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2023/N03-20230101_08_GML.zip/N03-23_08_230101.geojson"
)
tsukuba_gdf = ibaraki_gdf[ibaraki_gdf["N03_004"] == "つくば市"]
tsukuba_bbox = tsukuba_gdf.total_bounds
# pprint.pp(tsukuba_bbox)

search = tellus_traveler.search(
    datasets=[avnir2_dataset["id"]],
    bbox=tsukuba_bbox,
    start_datetime="2011-04-01T00:00:00Z",
    end_datetime="2012-05-01T00:00:00Z",
)
# pprint.pp(search.total())

scenes = list(search.scenes())
# pprint.pp(scenes)

search_results_gdf = gpd.GeoDataFrame.from_features(scenes, crs="EPSG:4326")
map = search_results_gdf.explore("tellus:name")
folium.Rectangle(
    bounds=[(tsukuba_bbox[1], tsukuba_bbox[0]), (tsukuba_bbox[3], tsukuba_bbox[2])]
).add_to(map)
map
map.save("map2.html")

# scene = next(scene for scene in scenes if scene["tellus:name"] == "ALAV2A277442870")
# pprint.pp(scene.properties)

# files = scene.files()
# pprint.pp(files)

# thumbs = scene.thumbnails()
# pprint.pp(thumbs)

# url = thumbs[0].url()
# pprint.pprint(url)

# target_file = next(file for file in files if "webcog" in file["name"])
# data = rioxarray.open_rasterio(target_file.url(), masked=True)
# pprint.pp(data)

# clipped_data = data.rio.clip_box(*tsukuba_bbox)
# pprint.pp(clipped_data)

# fig, ax = plt.subplots(figsize=(11, 11))
# clipped_data.sel(band=[1, 2, 3]).astype("uint8").plot.imshow(ax=ax)
# tsukuba_gdf.plot(ax=ax, color="none")
# ax.set_title(f"Tsukuba True Color\n{scene['tellus:name']}")

# fig, ax = plt.subplots(figsize=(11, 11))
# clipped_data.sel(band=[4, 1, 2]).astype("uint8").plot.imshow(ax=ax)
# tsukuba_gdf.plot(ax=ax, color="none")
# ax.set_title(f"Tsukuba False Color\n{scene['tellus:name']}")

# 画像をファイルに保存する
# plt.savefig("output_image2.png", format="png", dpi=300)
# plt.close(fig)
