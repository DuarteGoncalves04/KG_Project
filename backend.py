import requests
import spacy
import json
import re
import os


class KnowledgeEngine:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), ".config", "keys.json")) as f:
            keys = json.load(f)

        self.kg_endpoint = keys["KG_ENDPOINT"]
        self.openrouter_url = keys["OPENROUTER_API_URL"]
        self.openrouter_apikey = keys["OPENROUTER_API_KEY"]
        self.openrouter_model = keys["OPENROUTER_API_MODEL"]
        #self.nlp = spacy.load("en_core_web_sm")

        self.relation_map = {
            "director": "P57",
            "star": "P161", "cast": "P161", "actor": "P161",
            "release": "P577", "date": "P577", "year": "P577"
        }

    def getCombinedResponse(self,prompt):
        response = {
            "kg_results": None, 
            "llm_response": None, 
            "combined": None
        }

        entityInfo = self.extractEntities(prompt)
        if entityInfo:
            kg_results = self.queryKG(entityInfo["entity"], entityInfo["relation"])
            if kg_results:
                buildLLMPrompt = self.buildLLMPrompt(kg_results, prompt)
                response["kg_results"] = kg_results
                response["llm_response"] = self.getLLMResponse(buildLLMPrompt)
                response["combined"] ={
                    "source": "KG+LLM",
                    "facts": kg_results,
                    "analysis": response["llm_response"]
                }
                return response
        
        # If no entity info is found, fallback to LLM only
        response["llm_response"] = self.getLLMResponse(prompt)
        response["combined"] = {
            "source": "LLM-only",
            "response": response["llm_response"]
        }
        return response
    
    def buildLLMPrompt(self, facts, question):
        # Build a prompt for the LLM using the KG results and the original prompt
        fact_list = "\n".join(f"- {fact}" for fact in facts)
        return f"Based on these verified facts:\n{fact_list}\n\nAnswer this question: {question}"
    
    def queryKG(self, entity, relation):
        # Query the knowledge graph for the given entity and relation
        query = f"""
        SELECT ?answer ?answerLabel WHERE {{
            wd:{entity} wdt:{relation} ?answer.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        try:
            response = requests.get(
                self.kg_endpoint,
                params={"query": query, "format": "json"},
                headers={"User-Agent": "KnowledgeEngine/1.0"}
            )
            data = response.json()
            results = data.get("results", {}).get("bindings", [])
            return [item["answerLabel"]["value"] for item in results if "answerLabel" in item]
        except Exception as e:
            print(f"[Querying Knowledge Graph Error]: {e}")
            return []
        
    def getLLMResponse(self, prompt):
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_apikey}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.openrouter_model,
                "messages": [{"role": "user", "content": prompt}]
            }
            response = requests.post(self.openrouter_url, headers=headers, data=json.dumps(data))
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM Processing Error]: {e}")
            return "LLM response failed."
    
    def extractEntities(self, prompt):
        normalized_prompt = prompt.lower()
        clean_prompt = re.sub(r'[^\w\s]', '', normalized_prompt)

        #Pattern Matching
        match = re.search(
            r"(?:who|what)\s+(?:is|are|was|were)\s+(?:the\s+)?(director|star|cast|release date)s?\s+of\s+(.+)", 
            clean_prompt)
        if match:
            relation,entity = match.groups()
            return {
                "entity": self.wikidataLookup(entity.strip()),
                "relation": self.relation_map.get(relation.strip(), "P31")
            }
        
        match = re.search(
            r"(.*?)\s+(directed|stars?|released)\s+(?:by|in|on)?", 
            clean_prompt
        )
        if match:
            entity, verb = match.groups()
            return{
                "entity": self.wikidataLookup(entity.strip()),
                "relation": self.InferVerbRelation(verb.strip())
            }
        
        #LLM Entity Extraction [FAILSAFE]
        return self.LLMEntityExtraction(prompt)
    
    def wikidataLookup(self, search):
        # Perform a search on Wikidata for the given entity
        try:
            response = requests.get(
                "https://www.wikidata.org/w/api.php",
                params = {
                    "action": "wbsearchentities",
                    "search": search,
                    "language": "en",
                    "format": "json"
                }
            ).json()
            if response.get("search"):
                return response["search"][0]["id"]
        except Exception as e:
            print(f"[Wikidata Lookup Error]: {e}")
        return None

    def InferVerbRelation(self, verb):
        for key, prop in self.relation_map.items():
            if key in verb:
                return prop
        return "P31"
    
    def LLMEntityExtraction(self, prompt):
        # Use the LLM to extract entities from the prompt
        try:
            prompt_text = (
                f"Extract a JSON with 'entity' (Wikidata ID or name) and 'relation' (P-code) from:\n'{prompt}'\n"
                "Relations: P57 (director), P161 (cast), P577 (release date)\n"
                "Return JSON only."
            )
            result = self.getLLMResponse(prompt_text)
            return json.loads(result.strip())
        except Exception as e:
            print(f"[LLM Entity Extraction Error] {e}")
            return None
        
