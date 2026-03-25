import os
from osm_importer.importer import import_road_network, simplify_road_network, simplify_bicycle_network
from osm_importer.overpass import get_bbox
import geopandas as gpd
from shapely.geometry import Polygon

CYCLEWAY_COLUMNS = ['cycleway:both', 'cycleway:left', 'cycleway:right']
HIGHWAY_COLUMNS = ['highway', 'maxspeed', 'lanes', 'name', 'oneway', 'surface']


def handler(event, context):
	"""
	event keys :
	bbox :(if not using poly) list[float]
	poly :(if not using bbox) list [[float,float]]
	elevation: bool
	highway : list[str]
	extended_cycleway: bool
	callID : str

	"""
	print(event)
	bucket_name = os.environ['BUCKET_NAME']

	if 'splitDirection' in (event.keys()):
		split_direction = event['splitDirection']
	else:
		split_direction = False

	if 'extended_cycleway' in event.keys():
		extended_cycleway = event['extended_cycleway']
	else:
		extended_cycleway = False

	add_elevation = event['elevation']

	# get bbox or a polygon
	if 'poly' in (event.keys()):
		poly = event['poly']
		bbox = get_bbox(poly)
	else:
		bbox = event['bbox']
		bbox = (*bbox,)  # list to tuple
		# get requested highway
	highway_list = event['highway']

	cycleway_list = None
	if 'cycleway' in highway_list:
		cycleway_list = [
			'lane',
			'opposite',
			'opposite_lane',
			'track',
			'opposite_track',
			'share_busway',
			'opposite_share_busway',
			'shared_lane',
		]
		if extended_cycleway:
			cycleway_list = []  # all

	columns = HIGHWAY_COLUMNS.copy()
	# if cycleway is requested. add cyclway tags to the request.
	# https://wiki.openstreetmap.org/wiki/Map_features#When_cycleway_is_drawn_as_its_own_way_(see_Bicycle)
	if cycleway_list is not None:
		if extended_cycleway:
			columns += ['cycleway']
		else:
			columns += CYCLEWAY_COLUMNS
			columns += ['cycleway']

	# Start

	links, nodes = import_road_network(bbox, highway_list, cycleway_list, columns)
	links.index = [f'rlink_{i}' for i in links.index]
	links['a'] = links['a'].apply(lambda x: f'rnode_{x}')
	links['b'] = links['b'].apply(lambda x: f'rnode_{x}')
	nodes.index = [f'rnode_{i}' for i in nodes.index]

	if 'poly' in (event.keys()):
		print('restrict links to polygon')
		links = gpd.sjoin(
			links, gpd.GeoDataFrame(geometry=[Polygon(poly)], crs=4326), how='inner', predicate='intersects'
		).drop(columns='index_right')

	if 'cycleway' in links.columns:
		links = simplify_bicycle_network(links, highway_list, extended_cycleway)
	links, nodes = simplify_road_network(links, nodes, add_elevation, split_direction)

	# Outputs
	print('Saving on S3')
	folder = event['callID']
	links.to_file(f's3://{bucket_name}/{folder}/links.geojson', driver='GeoJSON')
	nodes.to_file(f's3://{bucket_name}/{folder}/nodes.geojson', driver='GeoJSON')
	print('Success!')
