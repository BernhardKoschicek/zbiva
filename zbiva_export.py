from collections import defaultdict
from typing import Any

import pandas as pd

from api import get_type_tree_thanados
from database.bodies import fetch_data_from_table
from model.citation import Citation
from model.literature import Literature
from model.place import Place

from database.grave import get_grave_citation_from_database, \
    get_graves_from_database
from database.site import (
    get_place_citation_from_database, get_places_from_database)
from database.literature import get_literature_from_database


def sort_places_by_country(places_: list[Place]) -> dict[str, Any]:
    countries = defaultdict(list)
    for place_ in places_:
        countries[place_.admin_country].append(place_)
    return countries


def get_place_literature(
        lit: list[Literature],
        cit: list[Citation]) -> list[Literature]:
    place_citation_lit_ids = {c.origin_literature_id for c in cit}
    return [l for l in lit if l.id_ in place_citation_lit_ids]


def get_thanados_types() -> dict[str, int]:
    type_tree = get_type_tree_thanados()['typeTree']
    result = {}

    def recurse_subs(entry_id: str) -> None:
        entry = type_tree.get(str(entry_id))
        if not entry:
            return

        result[entry['description']] = entry['id']

        subs = entry.get('subs', [])
        for sub_id in subs:
            recurse_subs(sub_id)

    recurse_subs('237367')  # This is the OpenAtlas ID of Zbiva types
    del result[None]
    return result


def get_admin_hierarchy() -> dict[str, Any]:
    hierarchy = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(set))))

    for p in places:
        hierarchy[p.admin_country][p.admin_region][p.admin_area][
            p.admin_unit].add(p.admin_settlement)

    return hierarchy

def default_to_regular(d: defaultdict[str, Any]) -> dict[str, dict[str, Any]]:
    if isinstance(d, defaultdict):
        d = {k: default_to_regular(v) for k, v in d.items()}
    return d

if __name__ == "__main__":
    # types_names = get_type_names_from_database()
    literature = get_literature_from_database()
    thanados_types = get_thanados_types()

    #########
    # Sites #
    #########
    places = get_places_from_database()
    for place in places:
        place.get_citations(get_place_citation_from_database())
        place.map_types(thanados_types)

    # Sort sites by country
    sorted_places_by_country = sort_places_by_country(places)

    place_csv_dict = []
    slovenia_sites = sorted_places_by_country['slovenija']
    for site in slovenia_sites:
        place_csv_dict.append(site.get_csv_data())

    sites_df = pd.DataFrame(place_csv_dict)
    sites_df.to_csv('csv/sites.csv', index=False)

    # If we want to import admin units, this is where to begin
    #admin_hierarchy = get_admin_hierarchy()
    #print(default_to_regular(admin_hierarchy['slovenija'][None]))

    ##########
    # Graves #
    ##########
    graves = get_graves_from_database()
    for grave in graves:
        grave.get_citations(get_grave_citation_from_database())
        grave.map_types(thanados_types)
        grave.map_value_types()

    slovenia_site_ids = {site.id_ for site in slovenia_sites}
    slovenia_graves = []
    grave_csv_dict = []
    for grave in graves:
        if grave.site_id in slovenia_site_ids:
            slovenia_graves.append(graves)
            grave_csv_dict.append(grave.get_csv_data())

    grave_df = pd.DataFrame(grave_csv_dict)
    grave_df.to_csv('csv/graves.csv', index=False)


    ##########
    # Bodies #
    ##########





    ##############################
    # Export all entities as csv #
    ##############################

    place_df = sites_df.append(grave_df, ignore_index=True)
    place_df.to_csv('csv/places.csv', index=False)




    # Todo: include literature for sites, graves, bodies, artifacts
    #place_literature = get_place_literature(literature, citations)

    lit_csv_dict = [lit.get_csv_data() for lit in literature]
    lit_df = pd.DataFrame(lit_csv_dict)
    lit_df.to_csv('csv/literature.csv', index=False)
    # print(len(sorted_places_by_type['NVR02']))
    # print(json.dumps(data, ensure_ascii=False).encode('utf8'))




def test_which_other_types_exist() -> None:
    # Get overview of some types:
    location_precision = set()
    plot_number = set()
    data_quality = set()
    archaeological_quality = set()
    special_finds = set()
    primary_chronology = set()
    certainty_of_chronology = set()
    chronology_description = set()
    location_description = set()
    author_of_site = set()
    for place_ in sorted_places_by_country['slovenija']:
        location_precision.add(place_.location_precision)
        plot_number.add(place_.plot_number)
        data_quality.add(place_.data_quality)
        archaeological_quality.add(place_.archaeological_quality)
        special_finds.add(place_.special_finds)
        primary_chronology.add(place_.primary_chronology)
        certainty_of_chronology.add(place_.certainty_of_chronology)
        chronology_description.add(place_.chronology_description)
        location_description.add(place_.location_description)
        author_of_site.add(place_.author_of_site)

    print(location_precision)
    print(plot_number)
    print(data_quality)
    print(archaeological_quality)
    print(special_finds)
    print(primary_chronology)
    print(certainty_of_chronology)
    print(chronology_description)
    print(location_description)
    print(author_of_site)
