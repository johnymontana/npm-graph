# Import NPM package dependencies into Neo4j
# Inspired by graph commons example FIXME: insert link

import requests
from lxml.html import fromstring
from py2neo import Graph
from requests.packages import urllib3
urllib3.disable_warnings()


# connect to Neo4j
graph = Graph()


# keep track of already crawled packages
fetched_packages = set()

def addNode(name, label):
    INSERT_QUERY = "MERGE (a:" + label + " {name: {name}})"
    graph.cypher.execute(INSERT_QUERY, parameters={'name': name})


def addRelationship(fromt, to, label, type):
    INSERT_QUERY =  "MERGE (a:" + label + "{name: {fromt}}) \n" + "MERGE (b:" + label + " {name: {to}}) \n" + "CREATE UNIQUE (a)-[:" + type + "]->(b)"
    graph.cypher.execute(INSERT_QUERY, parameters={'fromt': fromt, 'to': to})


def import_package_dependencies(package_name, max_depth=25, depth=0):
    if package_name in fetched_packages:
        return

    if depth > max_depth:
        return

    fetched_packages.add(package_name)

    url = 'https://www.npmjs.com/package/%s' % package_name
    response = requests.get(url, verify=False)
    doc = fromstring(response.content)

    addNode(package_name, "Package")

    for h3 in doc.cssselect('h3'):
        content = h3.text_content()

        if content.startswith('Dependencies'):
            for dependency in h3.getnext().cssselect('a'):
                dependency_name = dependency.text_content()

                print('>' * depth, dependency_name)

                addRelationship(package_name, dependency_name, "Package", "DEPENDS_ON")
                import_package_dependencies(dependency_name, depth=depth + 1)

def runner():
    for offset in ["0", "36", "72", "108"]:
        for urlf in ['https://www.npmjs.com/browse/star?offset=%s', 'https://www.npmjs.com/browse/depended?offset=%s']:

            url =  urlf % offset
            response = requests.get(url, verify=False)
            doc = fromstring(response.content)

            for name in doc.cssselect('.name'):
                package = name.text_content()
                print ("* " + package)
                if not package in fetched_packages:
                    import_package_dependencies(package)
    

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    
    parser.add_option("--package_name", dest="package_name",
                      help="NPM package that will be fetched")
    
    options, args = parser.parse_args()
    if options.package_name:
        import_package_dependencies(package_name)
    else:
        runner()