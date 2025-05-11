import requests

def test_wikidata_search(query):
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "format": "json",
        "type": "item"
    }
    response = requests.get("https://www.wikidata.org/w/api.php", params=params)
    print(response.status_code)
    print(response.json())


search_query = input("Enter your search query: ")
test_wikidata_search(search_query)