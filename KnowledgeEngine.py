import requests
import json
import os
import re

class KnowledgeEngine:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), ".config", "keys.json")) as f:
            keys = json.load(f)

        self.sparql_endpoint = keys["SPARQL_ENDPOINT"]
        self.wikidata_api = keys["WIKIDATA_API_URL"]

        self.openrouter_url = keys["OPENROUTER_API_URL"]
        self.openrouter_apikey = keys["OPENROUTER_API_KEY"]
        self.openrouter_model = keys["OPENROUTER_API_MODEL"]


    def getCombinedResponse(self,prompt):
        #Step 1: Extract Entities Themes from LLM
        themes = self.extractThemes(prompt)
        if themes:
            #Step 2: Get Themes IDs from Wikidata
            themes_id = self.getThemesID(themes)

            #Step 3: Get Triplets using SPARQL
            triples = self.getTriples(themes_id)

            #Step 4: Refine Triplets with LLM
            result = self.refineTriples(prompt, triples)
            return result
        else:
            print("[getCombinedResponse - Error]: No themes extracted.")
            return None
            


    def extractThemes(self, prompt):
        system_msg = (
            "Extract a list of up to 15 related high-level topics (themes) from the prompt. "
            "Focus on real-world concepts such as fields (e.g., Artificial Intelligence), "
            "methods (e.g., Convolutional Neural Networks), or technologies (e.g., Deep Learning). "
            "Only return a valid JSON list of strings. No explanations or markdown."
        )
        try:
            payload = {
                "model": self.openrouter_model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ]
            }

            headers = {
                "Authorization": f"Bearer {self.openrouter_apikey}",
                "Content-Type": "application/json"
            }

            response = requests.post(self.openrouter_url, headers=headers, data=json.dumps(payload))
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            themes = json.loads(content)
            print(f"[Extracted Themes]: {themes}")
            return themes
        except Exception as e:
            print(f"[Theme Extraction Error]: {e}")
            return None
    
    def getThemesID(self, themes):
        themes_id = {}
        for theme in themes:
            qid = self.wikidataLookup(theme, type="item")
            if qid:
                themes_id[theme] = qid
                print(f"[getThemesID - Result]: {themes_id}")
            else:
                print(f"[getThemesID - Failed]: {theme}")
        return themes_id
    
    def wikidataLookup(self, search_term, type="item"):
        print(f"[Wikidata Lookup - {type.title()} Search Term]: {search_term}")
        try:
            if re.match(r"^[PQ]\d+$", search_term):
                print(f"[Wikidata Search Result]: {search_term}")
                return search_term

            params = {
                "action": "wbsearchentities",
                "search": search_term,
                "language": "en",
                "format": "json",
                "type": type
            }
            response = requests.get(self.wikidata_api, params=params)
            result = response.json().get("search", [])[0]["id"]
            print(f"[Wikidata Search Result]: {result}")
            return result
        except Exception as e:
            print(f"[Wikidata {type.title()} Lookup Failed]: {e}")
            return None
    
    def getTriples(self, themes_id):
        triples = []
        for theme, id in themes_id.items():
            query = f"""
            SELECT ?propertyLabel ?valueLabel WHERE {{
                wd:{id} ?p ?statement .
                ?statement ?ps ?value .
                ?property wikibase:directClaim ?ps .
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT 10
            """
            try:
                response = requests.get(
                    self.sparql_endpoint,
                    params={"query": query, "format": "json"},
                    headers={"Accept": "application/sparql-results+json"}
                )
                response.raise_for_status()
                results = response.json()["results"]["bindings"]
                for r in results:
                    triple = {
                        "entity": theme,
                        "relation": r["propertyLabel"]["value"],
                        "object": r["valueLabel"]["value"]
                    }
                    triples.append(triple)
            except Exception as e:
                print(f"[SPARQL Query Error]: {e}")
        print(f"[Extracted Triples]: {triples}")
        return triples
    
    def refineTriples(self, prompt, triples):
        system_msg = (
            "You are a helpful assistant. Your task is to summarize the information provided in the triples. "
            "Given the following list of (entity, relation, object) triples, summarize each one in a short and "
            "clear natural language sentence. The Result should be a comment to help in educational purposes, when the user is searching for a specific topic. "
        )
        triplet_text =  "\n".join([f"- ({t['entity']}, {t['relation']}, {t['object']})" for t in triples])
        full_prompt = f"{system_msg}\n\n{triplet_text}\n\nOriginal question: {prompt}"
        try:
            payload = {
                "model": self.openrouter_model,
                "messages":  [{"role": "user", "content": full_prompt}]
            }
            headers = {
                "Authorization": f"Bearer {self.openrouter_apikey}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                self.openrouter_url,
                headers=headers,
                data=json.dumps(payload)
            )
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content)
            print(f"[Refine Triples Result]: {result}")
            return result
        except Exception as e:
            print(f"[Refine Triples Error]: {e}")
            return None
