import pandas as pd
import requests
import scipy.spatial as spatial
import argparse
from ast import literal_eval as make_tuple
import re
import os
import string


def set_auto_width_excel_cols(worksheet, indent=4):
    for i, column in enumerate(worksheet.iter_cols()):
        worksheet.column_dimensions[
            string.ascii_uppercase[i]].width = indent + max(
                [len(str(cell.value)) for cell in column])


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        action="store",
        dest="address",
        help="Address to calc pops",
        default="Москва Бутырская 6",
    )

    parser.add_argument(
        "-r",
        action="store",
        type=float,
        dest="radius",
        help="radius where looking fo  pops",
        default=1,
    )

    return parser.parse_args()


def load_data():
    df = pd.read_pickle("data.pkl")
    point_tree = spatial.cKDTree(df["pos"].tolist())
    return df, point_tree


if __name__ == "__main__":
    params = parse_arguments()
    #    print(params.address)
    (df, point_tree) = load_data()

while True:
    address = input("Введите адрес: ")
    # address = "Москва Лавочкина 50"
    if not address:
        exit("Goodbuy motherfucker")

    radius_km = input("Введите радиус (default 1km): ") or 1
    # radius_km = 1
    if isinstance(radius_km, str):
        radius_km = float(radius_km.replace(",", "."))
    radius_m = radius_km / 111

    url = "https://geocode-maps.yandex.ru/1.x/"
    rest_params = {"format": "json", "geocode": address}

    r = requests.get(url, params=rest_params)
    result = (r.json())["response"]["GeoObjectCollection"]

    coord_str = result.get("featureMember")[0].get("GeoObject").get(
        "Point").get("pos")
    coord = make_tuple(coord_str.replace(" ", ", "))
    print("You coords: {}".format(coord))

    t = point_tree.query_ball_point(coord, radius_m)
    nearest_buildings = df.iloc[t]
    pops_in_radius = nearest_buildings.pops.sum()
    print(f"Pops in radius {radius_km}km: {pops_in_radius}")

    # Write to xlsx
    fpath = os.path.join(os.path.curdir, "results",
                         re.sub("[\W]+", "_", address) + ".xlsx")

    # writer = pd.ExcelWriter(fpath, engine="xlsxwriter")
    writer = pd.ExcelWriter(fpath, engine="openpyxl")
    pd.DataFrame(
        data=[address, radius_km,
              round(pops_in_radius), coord],
        index=["Адрес", "Радиус (км.) ", "Население", "Координаты"],
    ).to_excel(
        writer, sheet_name="Статистика")

    # ОБщая статистика по возрастам
    weeman = (nearest_buildings[[
        column for column in nearest_buildings.columns if "weeman_" in column
    ]].sum().round(0))
    men = (nearest_buildings[[
        column for column in nearest_buildings.columns if "men_" in column
    ]].sum().round(0))
    idx = men.index.str.replace("men_", "")

    nearest_buildings_summary = pd.DataFrame(
        data={
            "Женщины": weeman.values,
            "Мужчины": men.values
        }, index=idx)
    nearest_buildings_summary.to_excel(
        writer, sheet_name="Статистика", startcol=6)
    set_auto_width_excel_cols(worksheet=writer.sheets["Статистика"])

    # Детальная ифнормация"
    nearest_buildings.sort_values("address").to_excel(
        writer, sheet_name="Детальная ифнормация")
    # set_auto_width_excel_cols(worksheet=writer.sheets["Детальная ифнормация"])
    # worksheet = writer.sheets["Детальная ифнормация"]
    # worksheet.set_column("A:A", 16)
    # worksheet.set_column("B:B", 40)
    writer.save()
    print(f"Результат записан в файл {fpath}")
