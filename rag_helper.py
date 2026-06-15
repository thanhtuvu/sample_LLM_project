
INSTRUCTIONS = '''
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
'''.strip()

PROMPT_TEMPLATE = '''
Question: 
{question}

Context: 
{relevant_document}
'''.strip()

class RAGBase:

    def __init__(
        self
        ,index
        ,llm_client
        ,instructions=INSTRUCTIONS
        ,prompt_template=PROMPT_TEMPLATE
        ,search_size_return = 3
    ):
        
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.search_size_return = search_size_return

    def search(self, query,  boost_dict={}):
        fields =  [f"{k}^{v}" for k, v in boost_dict.items()]  or ["question", "answer", "section"]
        results = self.index.search(
            index="zoomcamp"
            ,body={
                "size": self.search_size_return
                ,"query": {
                    "bool": {
                        "must":  {"multi_match": {"query": query, "fields": fields}}, #multi_match means "search this query across multiple fields at once."
                    }
                }
            }
        )

        return [hit["_source"] for hit in results["hits"]["hits"]]
    
    def build_context(self, search_results_dict):
        lines = []
        for item in search_results_dict:
            section = item['section']
            question = item['question']
            answer = item['answer']
            lines.append(section)
            lines.append('Q: ' + question)
            lines.append('A: ' + answer)
            lines.append('')

        return  '\n'.join(lines).strip()
    

    def build_prompt(self, query, search_results_dict):
        relevant_document = self.build_context(search_results_dict)

        return self.prompt_template.format(
            question=query
            ,relevant_document=relevant_document
        )

    def llm(self, prompt):
        response = self.llm_client.messages.create(
            model = "claude-haiku-4-5-20251001" #claude-sonnet-4-6
            ,system = self.instructions
            ,messages=[{"role": "user", "content": prompt}]
            ,max_tokens=20000
            ,temperature=0
        )

        return response.content[0].text

    #the final method rag: orchestrate the process in order
    def rag(self, query, boost_dict ={}):
        search_results_dict = self.search(query,  boost_dict)
        constructed_prompt = self.build_prompt(query, search_results_dict)
        llm_response = self.llm(constructed_prompt)
        
        return llm_response
        
