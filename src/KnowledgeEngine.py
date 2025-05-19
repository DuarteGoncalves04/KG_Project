import requests
import json
import os
import re

class KnowledgeEngine:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "../.config", "keys.json")) as f:
            keys = json.load(f)

        self.sparql_endpoint = keys["SPARQL_ENDPOINT"]
        self.wikidata_api = keys["WIKIDATA_API_URL"]

        self.openrouter_url = keys["OPENROUTER_API_URL"]
        self.openrouter_apikey = keys["OPENROUTER_API_KEY"]
        self.openrouter_model = keys["OPENROUTER_API_MODEL"]


    def getCombinedResponse(self,prompt):
        """
        Get a combined response from the LLM by extracting themes, querying Wikidata, and refining the results.
        Args:
            prompt (str): The input prompt to process.
        Returns:
            dict: A dictionary containing the refined response with facts, questions, and an answer.
        """
        #Step 1: Extract Entities Themes from LLM
        themes = self.extractThemes(prompt)
        if themes:
            #Step 2: Get Themes IDs from Wikidata
            themes_id = self.getThemesID(themes)

            #Step 3: Get Triplets using SPARQL
            triples = self.getTriples(themes_id)

            #Step 4: Refine Triplets with LLM
            return self.refineTriples(prompt, triples)
        else:
            print("[getCombinedResponse - Error]: No themes extracted.")
            return None

    def llmQuery(self, sys_msg, user_msg, json_mode= False):
        """
        Query the LLM with a system message and user message.
        Args:
            sys_msg (str): System message to set the context.
            user_msg (str): User message to query the LLM.
            json_mode (bool): If True, return response in JSON format.
        Returns:
            str: The response from the LLM.
        """
        messages = []
        if sys_msg:
            messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": user_msg})
        payload = {
            "model": self.openrouter_model,
            "messages": messages
        }
        headers = {
            "Authorization": f"Bearer {self.openrouter_apikey}",
            "Content-Type": "application/json"
        }
        if json_mode:
            payload["response_format"] = {"type": "json"}
        
        try:
            response = requests.post(
                self.openrouter_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[LLM Query Error]: {e}")
            return None

    def extractThemes(self, prompt):
        """
        Extract high-level themes from the prompt using the LLM.
        Args:
            prompt (str): The input prompt to process.
        Returns:
            list: A list of extracted themes.
        """
        system_msg = (
            "Extract a list of up to 10 related high-level topics (themes) from the prompt."
            "The first of the list should be the prompted theme."
            "Focus on real-world concepts such as fields (e.g., Artificial Intelligence), "
            "methods (e.g., Convolutional Neural Networks), or technologies (e.g., Deep Learning). "
            "Only return a valid JSON list of strings. No explanations or markdown."
        )
        content = self.llmQuery(system_msg, prompt, json_mode=True)
        if content:
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            themes = json.loads(content)
            print(f"[Extracted Themes]: {themes}")
            return themes
        else:
            print(f"[Theme Extraction Error]: {content}")
            return None
    
    def getThemesID(self, themes):
        """
        Get Wikidata IDs for the extracted themes.
        Args:
            themes (list): A list of themes to look up.
        Returns:
            dict: A dictionary mapping themes to their Wikidata IDs.
        """
        themes_id = {}
        for theme in themes:
            qid = self.wikidataLookup(theme, type="item")
            if qid:
                themes_id[theme] = qid 
            else:
                print(f"[getThemesID - Failed]: {theme}")

        print(f"[getThemesID - Result]: {themes_id}")
        return themes_id
    
    def wikidataLookup(self, search_term, type="item"):
        """
        Look up a term in Wikidata and return its ID.
        Args:
            search_term (str): The term to look up.
            type (str): The type of entity to search for (item [default] or property).
        Returns:
            str: The Wikidata ID of the entity.
        """
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
        """
        Get triples from Wikidata using SPARQL for the given themes.
        Args:
            themes_id (dict): A dictionary mapping themes to their Wikidata IDs.
        Returns:
            list: A list of triples extracted from Wikidata.
        """
        triples = []
        for theme, id in themes_id.items():
            query = f"""
            SELECT DISTINCT ?propertyLabel (SAMPLE(?valueLabel) AS ?valueLabel) (SAMPLE(?valueDescription) AS ?valueDescription) WHERE {{
                wd:{id} ?p ?statement .
                ?statement ?ps ?value .
                ?property wikibase:directClaim ?ps .
                
                OPTIONAL {{
                    ?value schema:description ?valueDescription .
                    FILTER(LANG(?valueDescription) = "en")
                }}
                
                SERVICE wikibase:label {{ 
                    bd:serviceParam wikibase:language "en" .
                    ?property rdfs:label ?propertyLabel .
                    ?value rdfs:label ?valueLabel .
                }}
            }}
            GROUP BY ?propertyLabel
            LIMIT 10
            """
            try:
                response = requests.get(
                    self.sparql_endpoint,
                    params={"query": query, "format": "json"},
                    headers={"Accept": "application/sparql-results+json"},
                    timeout=10
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
        """
        Refine the extracted triples using the LLM to generate a more concise and relevant response.
        Args:
            prompt (str): The original prompt.
            triples (list): A list of extracted triples.
        Returns:
            dict: A dictionary containing the refined response with facts, questions, and an answer.
        """
        system_msg = """You are an educational assistant. For the given triples:
        1. Extract key facts relevant to the original question
        2. Formulate 1-2 thought-provoking questions
        3. Provide a concise summary answer
        
        Return as JSON with these keys: {"facts": [], "questions": [], "answer": ""}"""

        # Format triples for LLM
        triplet_text = "\nTriples:\n" + "\n".join(
            f"- {t['entity']} {t['relation']} {t['object']}" 
            for t in triples
        )
        full_prompt = f"Original question: {prompt}{triplet_text}"

        content = self.llmQuery(system_msg, full_prompt, json_mode=True)
        try:
            # Clean up markdown if present
            if content.startswith("```"):
                content = content.split("```")[1].strip()
                if content.startswith("json"):
                    content = content[4:].strip()

            print(f"[Refined Triples Result]: {content}")
            return json.loads(content)
             
        except Exception as e:
            # Fallback to simple text if JSON parsing fails
            return {
                "facts": [],
                "questions": [],
                "answer": content or "No information could be generated."
            }
