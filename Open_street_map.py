#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import csv
import codecs
import cerberus
import schema

osm_file = open("pasadena.osm", "r")

#paths
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

#fields
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

#lists and dictionaries functions refer to
street_types = defaultdict(set)
zip_types = defaultdict(set)
street_fixes_list = []
street_fixes = defaultdict(list)
names_dict = defaultdict()


expected_street = ["Street", "Alley", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons"]

mapping_street = { "St": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd.": "Boulevard",
            "Blvd": "Boulevard",
            "Ln": "Lane",
            "Rd": "Road",
            "Rd.": "Road",
            "St.": "Street",
            "Dr": "Drive",
            "Dr.": "Drive"
            }

def audit_street_type(street_types, street_name, elem):
    '''Checks street name for problem characters or if it is already correctly inputted.
    If no issues adds their street type as the key and street name as the value into
    the street_types dictionary.  Takes their element id# and stores it in the street_fixes list'''
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected_street:
            if not street_type[-1].isdigit() and street_type in mapping_street:
                street_types[street_type].add(street_name)
                elem_id = elem.attrib["id"]
                street_fixes_list.append(elem_id)

def is_street_name(elem):
    '''Checks if element's tag is a street name.'''
    return (elem.attrib['k'] == "addr:street")


def audit_street(osmfile):
    '''Iterates through the osm_file, checks if tag is a street name and send it to
    audit_street_type.'''
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'], elem)
    return street_types


def update_name(name, mapping_street):
    '''For the items whose names can be fixed, if the key from mapping_street
    is in the name, it is split there and the first part of the name is paired
    with the value of that key from mapping_street thus creating a full
    and proper name.'''
    for key in mapping_street:
        if key in name:
            new_name = name.split(key)
            name = new_name[0] + mapping_street[key]
            return name

def street_test():
    '''Creates a dictionary called st_types which is iterated over multiples times.
    The first time is done to add the element id# and shorter name to a dictionary
    called street_fixes.
    The second time is done to update the name using update_name and store
    the shorter name and the proper name in a dictionary called names_dict.
    The loop combines these above two dictionaries into the first dictionary
    street_fixes which has the element ID as the key and the shorter name and
    proper name in a set as the values.'''
    osm_file.seek(0)
    st_types = audit_street(osm_file)
    #pprint.pprint(dict(st_types))

    osm_file.seek(0)

    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if is_street_name(tag) and elem.attrib['id'] in street_fixes_list:
                        elem_id = elem.attrib['id']
                        street_fixes[elem_id].append(tag.attrib['v'])

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping_street)
            if better_name != None:
                print name, "=>", better_name
                names_dict[name]=better_name

    for old_name, new_name in names_dict.iteritems():
        for k, v in street_fixes.iteritems():
            if list(v)[0] == old_name:
                street_fixes[k].append(names_dict[list(v)[0]])

    pprint.pprint(dict(street_fixes))


def count_street_types_fixed():
    '''A test to see how clean the data would be if we printed
    a dictionary which counted how many of each zip code there are.'''
    st_types_fixed = defaultdict(int)
    st_types = audit_street(osm_file)

    for st_type, ways in st_types.iteritems():
        for name in ways:
            if st_type in mapping_street:
                st_types_fixed[st_type]+=1

    st_types_fixed = dict(st_types_fixed)
    return st_types_fixed


def audit_zip_type(zip_types, zipcode):
    '''Checks to make sure zip codes don't have problems.'''
    m = street_type_re.search(zipcode)
    if m:
        zip_type = m.group()
        zip_types[zip_type].add(zipcode)

def is_zip(elem):
    '''Checks to make sure it is a zipcode.'''
    return (elem.attrib['k'] == "addr:postcode")


def audit_zip(osmfile):
    '''Iterates through the osm_file, checks if tag is a zipcode and send it to
    audit_zip_type.'''
    osm_file.seek(0)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_zip(tag):
                    audit_zip_type(zip_types, tag.attrib['v'])
    return zip_types


def zip_test():
    '''Creates a dictionary called zip_types which is looped over to print
    the old and new zip codes to ensure output is clean.'''
    zip_types = audit_zip(osm_file)
    pprint.pprint(dict(zip_types))

    for zip_type, zipcode in zip_types.iteritems():
        for zipc in zipcode:
            if "CA" in zipc:
                print zipc, "=>", zip_type


def clean_key (attribute):
    '''Fixing the "key" column: the full tag "k" attribute value if no colon
    is present or the characters after the colon if one is.'''
    if ":" in attribute:
        string = attribute.split(":", 1)
        return string[1]
    else:
        return attribute

def clean_type (attribute):
    '''Fixing the "type" column: either the characters before the colon in the
    tag "k" value or "regular" if a colon is not present.'''
    if ":" in attribute:
        string = attribute.split(":", 1)
        return string[0]
    else:
        return "regular"

def change_name (tag, id_number, name):
    '''Receives tags, id numbers and values from shape_element which are then
    checked against the dictionaries created by the street_test and zip_test
    functions.  The data is matched to see if it needs to be replaced with
    the corrected data or to remain as it is.'''
    if tag.attrib['k'] == "addr:street":
        for k, v in street_fixes.iteritems():
            if id_number == k:
                return list(v)[1]
    elif tag.attrib['k'] == "addr:postcode":
        for k, v in zip_types.iteritems():
            if k in name:
                return k
            elif "90032" in name:
                return "90032"
    return name

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []
    counter = 0

    if element.tag == 'node':
        for attrib in NODE_FIELDS:
            node_attribs[attrib] = element.attrib[attrib]
        for tag in element.iter("tag"):
            k = tag.attrib['k']
            if re.search(PROBLEMCHARS,k):
                break
            tag_dict = {}
            tag_dict["id"] = node_attribs["id"]
            tag_dict["key"] = clean_key(tag.attrib['k'])
            tag_dict["value"] = change_name(tag, tag_dict["id"], tag.attrib['v'])
            tag_dict["type"] = clean_type(tag.attrib['k'])
            tags.append(tag_dict)
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for attrib in WAY_FIELDS:
            way_attribs[attrib] = element.attrib[attrib]
        for node in element.iter("nd"):
            nodes_dict = {}
            nodes_dict["id"] = way_attribs["id"]
            nodes_dict["node_id"] = node.attrib['ref']
            nodes_dict["position"] = counter
            counter +=1
            way_nodes.append(nodes_dict)
        for tag in element.iter("tag"):
            k = tag.attrib['k']
            if re.search(PROBLEMCHARS,k):
                break
            tag_dict = {}
            tag_dict["id"] = way_attribs["id"]
            tag_dict["key"] = clean_key(tag.attrib['k'])
            tag_dict["value"] = change_name(tag, tag_dict["id"], tag.attrib['v'])
            tag_dict["type"] = clean_type(tag.attrib['k'])
            tags.append(tag_dict)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    osm_file.seek(0)
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

street_test()
zip_test()
process_map(osm_file, validate=False)
#count_street_types_fixed()
