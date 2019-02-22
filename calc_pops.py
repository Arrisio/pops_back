import os
import re
import string
from ast import literal_eval as make_tuple
from io import BytesIO

import pandas as pd
import requests

import scipy.spatial as spatial
import pickle
# from shapely.geometry import Point, Polygon
# import geopandas as gpd

DEFAULT_RADIUS = 1


def set_auto_width_excel_cols(worksheet, indent=4):
    for i, column in enumerate(worksheet.iter_cols()):
        worksheet.column_dimensions[
            string.ascii_uppercase[i]].width = indent + max(
                [len(str(cell.value)) for cell in column])


def load_data():
    all_buildings_df = pd.read_pickle(os.path.join('data', 'data.pkl'))
    all_buildings_geodata = None
    all_buildings_geodata = gpd.read_file(
        os.path.join('data', 'building_gpd.shp'))

    # all_buildings_point_tree = spatial.cKDTree(
    # all_buildings_df['pos'].tolist())
    with open(os.path.join('data', 'cKDTree.pkl'), 'rb') as fh:
        all_buildings_point_tree = pickle.load(fh)

    return all_buildings_df, all_buildings_point_tree, all_buildings_geodata


(ALL_BUILDINGS_DF, ALL_BUILDINGS_POINT_TREE,
 ALL_BUILDINGS_GEOSERIES) = load_data()


def prepare_radius(in_radious=None):
    if isinstance(in_radious, str) and in_radious != '':
        return float(in_radious.replace(',', '.')) / 111
    else:
        return (in_radious or DEFAULT_RADIUS) / 111


def get_1st_yandex_geoobject_data(request_result):
    request_result = request_result['response']['GeoObjectCollection'].get(
        'featureMember')

    if request_result:
        first_object = request_result[0].get('GeoObject')
        verified_address = first_object.get('metaDataProperty').get(
            'GeocoderMetaData').get('Address').get('formated')
        coord_str = first_object.get('Point').get('pos')
        coord = make_tuple(coord_str.replace(' ', ', '))

        return coord, verified_address


def get_coord_by_addr(input_address,
                      url='https://geocode-maps.yandex.ru/1.x/'):
    rest_params = {'format': 'json', 'geocode': input_address}

    return get_1st_yandex_geoobject_data(
        request_result=requests.get(url, params=rest_params).json())


def string_with_coords2Polygon(coords_string):
    latitudes = map(float, coords_string.split(',')[::2])
    longtitudes = map(float, coords_string.split(',')[1::2])

    return Polygon(zip(latitudes, longtitudes))


class PopsDataObj():
    def __init__(self, inp_address=None, inp_radius=None, inp_area=None):
        self.inp_address = inp_address
        self.inp_radius = inp_radius
        self.inp_area = inp_area

    def compile_data(self, inp_address=None, inp_radius=None, inp_area=None):
        self.inp_address = inp_address or self.inp_address or 'area'
        self.inp_radius = inp_radius or self.inp_radius or DEFAULT_RADIUS
        self.radius = prepare_radius(self.inp_radius)
        self.inp_area = inp_area or self.inp_area

        if self.inp_area:
            buildings_idx = ALL_BUILDINGS_GEOSERIES.geometry.within(
                string_with_coords2Polygon(self.inp_area)).values
            self.nearest_buildings = ALL_BUILDINGS_DF.loc[buildings_idx].copy()

        elif self.inp_address:
            self.radius = prepare_radius(self.inp_radius)
            try:
                (self.address_coord,
                 self.verified_address) = get_coord_by_addr(self.inp_address)
            except TypeError as e:
                raise ValueError(
                    f"Can't get yandex data by your address \n{e}")

            buildings_idx = ALL_BUILDINGS_POINT_TREE.query_ball_point(
                self.address_coord, self.radius)
            self.nearest_buildings = ALL_BUILDINGS_DF.iloc[buildings_idx].copy(
            )
        else:
            raise ValueError(
                f"didn't enter naither address, no area to calc population")

        self.pops_in_radius = self.nearest_buildings.pops.sum()

    def compile_xls(self, xls_output, filename=None):
        self.filename = filename or re.sub('[\W]+', '_',
                                           self.inp_address) + '.xlsx'

        self.xls_output = xls_output or self.xls_output
        if not isinstance(self.xls_output, BytesIO):
            self.xls_output = os.path.join(self.xls_output, self.filename)

        self.writer = pd.ExcelWriter(self.xls_output, engine='openpyxl')

        pd.DataFrame(
            data=[
                self.inp_address,
                self.inp_radius,
                # round(self.pops_in_radius), self.address_coord
                round(self.pops_in_radius)
            ],
            # index=['Адрес', 'Радиус (км.) ', 'Население', 'Координаты'],
            index=['Адрес', 'Радиус (км.) ', 'Население'],
        ).to_excel(
            self.writer, sheet_name='Статистика')

        # ОБщая статистика по возрастам
        weeman = (self.nearest_buildings[[
            column for column in self.nearest_buildings.columns
            if 'weeman_' in column
        ]].sum().round(0))
        men = (self.nearest_buildings[[
            column for column in self.nearest_buildings.columns
            if 'men_' in column
        ]].sum().round(0))
        idx = men.index.str.replace('men_', '')

        self.nearest_buildings_summary = pd.DataFrame(
            data={
                'Женщины': weeman.values,
                'Мужчины': men.values
            }, index=idx)
        self.nearest_buildings_summary.to_excel(
            self.writer, sheet_name='Статистика', startcol=6)
        set_auto_width_excel_cols(worksheet=self.writer.sheets['Статистика'])

        # Детальная ифнормация'
        # self.nearest_buildings.sort_values('address', inplace=True)
        self.nearest_buildings.to_excel(
            self.writer, sheet_name='Детальная ифнормация')
        self.writer.close()

        # go back to the beginning of the stream
        if isinstance(self.xls_output, BytesIO):
            self.xls_output.seek(0)


def main():
    # inp_address = input('Введите адрес(если пусто => Выход): ')
    # if not inp_address:
    #     exit('Счастливо!')
    inp_address = 'Бутырская 6'
    inp_radius = input('Введите радиус (default 1km): ')

    pops_data = PopsDataObj()
    pops_data.compile_data(inp_address=inp_address, inp_radius=inp_radius)
    print('You coords: {}'.format(pops_data.address_coord))
    print(
        f'Pops in radius {pops_data.inp_radius}km: {pops_data.pops_in_radius}')

    pops_data.compile_xls(xls_output=os.path.join(os.path.curdir, 'results'))
    pops_data.writer.save()
    print(f'Результат записан в файл {pops_data.xls_output}')


if __name__ == '__main__':
    while True:
        main()
