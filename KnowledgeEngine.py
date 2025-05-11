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
        response = {
            "triplet": None,
            "kg_results": None, 
            "llm_response": None, 
            "combined": None
        }

        response["triplet"] = self.extractTriplet(prompt)
        if response["triplet"]:
            print(f"[getCombinedResponse - Triplet]: {response['triplet']}")
            response["kg_results"] = self.queryKG(response["triplet"])
            if response["kg_results"]:
                llm_prompt = self.buildLLMPrompt(response["kg_results"], prompt)
                response["llm_response"] = self.getLLMResponse(llm_prompt)
                if response["llm_response"]:
                    response["combined"] = {
                        "source": "KG+LLM",
                        "triplet": response["triplet"],
                        "facts": response["kg_results"],
                        "explanation": response["llm_response"]
                    }
                else:
                    print(f"[getCombinedResponse - LLM Response ERROR]: {response['llm_response']}")
            else:
                print(f"[getCombinedResponse - KG Results ERROR]: {response['kg_results']}")
        else:
            print(f"[getCombinedResponse - Triplet ERROR]: {response['triplet']}")
        return response

    def extractTriplet(self, prompt):
        results = self.llmTripletExtraction(prompt)
        resolved = []
        if results:
            for step in results:
                entity_label = step.get("entity", "")
                relation_label = step.get("relation", "")
                object_label = step.get("object", "")

                if entity_label.startswith("?") or relation_label.startswith("?"):
                    print(f"[Skipped Placeholder Triplet] Entity: {entity_label}, Relation: {relation_label}")
                    continue

                entity_id = self.wikidataLookup(entity_label, type="item") if entity_label else None
                relation_id = self.wikidataLookup(relation_label, type="property") if relation_label else None

                # If both entity and relation are valid, resolve the triplet
                if entity_id and relation_id:
                    resolved.append({"entity": entity_id, "relation": relation_id, "object": object_label})
                else:
                    print(f"[Triplet Resolution Skipped] Entity: {entity_label} ({entity_id}), Relation: {relation_label} ({relation_id})")

        return resolved if resolved else None

    def llmTripletExtraction(self, prompt):
        system_msg = (
            "You are an expert in knowledge graph queries. Given a question, extract a list of stepwise triplets.\n"
            "Each triplet must be a dictionary with keys 'entity', 'relation', and 'object'.\n"
            "Use real-world concepts only like Q42 for Douglas Adams, not variables like '?x'.\n"
            "When choosing the property for tje relation, use the most specific one.\n"
            "Do NOT return placeholders like'?x'.\n"
            "Only return a valid JSON list of dictionaries.\n"
        )

        user_msg = f"Extract entity and relation from: '{prompt}'"

        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_apikey}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.openrouter_model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            }
            response = requests.post(self.openrouter_url, headers=headers, data=json.dumps(data))
            # Sometimes the LLM wraps JSON in markdown
            print(f"[extractTriplet - LLM Response]: {response.text}")
            content = response.json()["choices"][0]["message"]["content"].strip()

            # Remove markdown code block wrapping if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            result = json.loads(content.strip())
            print(f"[extractTriplet - LLM Result]: {result}")
            return result
        except Exception as e:
            print(f"[LLM Triplet Extraction Error]: {e}")
            return None

    def queryKG(self, triplet):
        results = []
        current_entity_id = None

        for i, step in enumerate(triplet):
            entity = step["entity"]
            relation = step["relation"]

            if i == 0:
                current_entity_id = entity
                if not current_entity_id.startswith("Q"):
                    print(f"[Entity Lookup Failed at step {i}] {entity}")
                    return []
            if not relation.startswith("P"):
                print(f"[Relation Invalid at step {i}] {relation}")
                return []

            print(f"[Hop {i}] Entity: {current_entity_id}, Relation: {relation}")

            # Adjusted query for retrieving items related to the entity
            queries = [
                f"SELECT DISTINCT ?itemLabel WHERE {{ wd:{current_entity_id} wdt:{relation} ?item . SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en'. }} }} LIMIT 10",
                f"SELECT DISTINCT ?itemLabel WHERE {{ ?item wdt:{relation} wd:{current_entity_id} . SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en'. }} }} LIMIT 10"
            ]
            try:
                headers = {"Accept": "application/sparql-results+json"}
                response = requests.get(
                    self.sparql_endpoint,
                    params={"query": queries, "format": "json"},
                    headers=headers
                )
                response.raise_for_status()
                bindings = response.json()["results"]["bindings"]
                items = [b["itemLabel"]["value"] for b in bindings if "itemLabel" in b]
                print(f"[KG Query Results - Hop {i}]: {items}")
                results.extend(items)
                if i < len(triplet) - 1:
                    current_entity_id = self.wikidataLookup(items[0], type="item") if items else None
                    if not current_entity_id:
                        print(f"[Entity Resolution Failed at hop {i+1}]")
                        break
            except Exception as e:
                print(f"[SPARQL Error - Hop {i}]: {e}")
                return []

        return results
    
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

    def buildLLMPrompt(self, facts, original_prompt):
        bullet_facts = "\n".join(f"- {fact}" for fact in facts)
        return f"Here are some facts:\n{bullet_facts}\n\nNow answer this question:\n{original_prompt}"

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
            print(f"[LLM Error]: {e}")
            return "LLM failed to respond."