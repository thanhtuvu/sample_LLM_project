
import json
import re

AGENTIC_INSTRUCTIONS = '''
Your task is to answer questions from course participants. But you operate in a loop. 
Based on the context given initially, you decide whether or not you need to request for more context. 
If a next iteration needed, use 'search' to refine your query. Then you will get more relevant context to support your answer to the question at hand.
If the answer is not found in the enriched context, just simply respond "I don't know". 

You must respond with ONLY valid JSON — no prose, no markdown fences as follows:
    1. When you need to gather more information, response should be: 
        {"action": "search", "text": "your refined query here"}
    2. When you are confident to answer given all context provided, response should be: 
        {"action": "answer", "text": "your final answer here"}
'''.strip()

PROMPT_TEMPLATE = '''
Question: 
{query}

Context: 
{context}
'''.strip()

class AgenticRAGBase_HW1:

    def __init__(
        self
        ,llm_client
        ,index
        ,index_name = "homework_1_lessons"
        ,model = 'claude-haiku-4-5-20251001'
        ,instructions=AGENTIC_INSTRUCTIONS
        ,prompt_template=PROMPT_TEMPLATE
        ,search_size_return = 3
        ,max_iteration = 3
        
    ):
        self.llm_client = llm_client
        self.index = index
        self.index_name = index_name
        self.model = model
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.search_size_return = search_size_return
        self.max_iteration = max_iteration
        

    def search(self, query):
        fields =  ["content"]
        results = self.index.search(
            index=self.index_name,
            body={
                "size": self.search_size_return
                ,"query": {
                    "bool": {
                        "must":  {"multi_match": {"query": query, "fields": fields}}
                    }
                }
            }
        )
        return [hit["_source"] for hit in results["hits"]["hits"]]
    
    def build_context(self, search_results_dict):
        lines = []
        for item in search_results_dict:
            content = item['content']
            lines.append('C: ' + content)
            lines.append('')

        return '\n'.join(lines).strip()
    

    def build_prompt(self, query, search_results_dict):
        context = self.build_context(search_results_dict)

        return self.prompt_template.format(
            query=query
            ,context=context
        )

    def llm_json(self, prompt):
        raw = self.llm_client.messages.create(
            model = self.model
            ,system = self.instructions
            ,messages=[{"role": "user", "content": prompt}]
            ,max_tokens=1000
            ,temperature=0
        )
        response = raw.content[0].text
        response = re.sub(r"```json|```", "", response).strip()

        try:
            return json.loads(response) #turning the string of json into json
        except json.JSONDecodeError: 
            return {"action":"answer", "text": response}
        

    def rag(self, query):

        iter = 0
        search_count = 1
        accumulated_search_result = []

        init_search_result = self.search(query)
        accumulated_search_result.extend(init_search_result)

        while iter < self.max_iteration:
            iter += 1
            constructed_prompt = self.build_prompt(query, accumulated_search_result)
            llm_response = self.llm_json(constructed_prompt)

            action = llm_response.get('action')

            if action == "search":
                llm_query = llm_response.get('text')
                next_search_result = self.search(llm_query)
                accumulated_search_result.extend(next_search_result)
                search_count +=1

            else: 
                llm_answer = llm_response.get('text')
                return llm_answer, search_count
            
        
        constructed_prompt = self.build_prompt(query, accumulated_search_result)
        
        FORCED_ANSWER_INSTRUCTIONS = '''
        You have reached the maximum number of search iterations.
        Based solely on the context provided, give your best answer to the question.
        If the answer is not in the context, respond with "I don't know."
        You must respond with ONLY valid JSON:
        {"action": "answer", "text": "your final answer here"}
        '''.strip()

        #This is to remove the response of llm query still in search when the loop was forced to stop and the last action was "search" (it never hit the else)
        raw = self.llm_client.messages.create(
            model = self.model
            ,system = FORCED_ANSWER_INSTRUCTIONS
            ,messages=[{"role": "user", "content": constructed_prompt}]
            ,max_tokens=1000
            ,temperature=0
        )
        final_response = raw.content[0].text
        final_response = re.sub(r"```json|```", "", final_response).strip()
        
        try:
            return json.loads(final_response).get("text", "I don't know"), search_count
        except json.JSONDecodeError: 
            return {"action":"answer", "text": final_response}, search_count

        
