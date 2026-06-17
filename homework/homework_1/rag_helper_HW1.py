
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

class RAGBase_HW1:

    def __init__(
        self
        ,llm_client
        ,index
        ,index_name = "homework_1_lessons"
        ,model = 'claude-haiku-4-5-20251001'
        ,instructions=INSTRUCTIONS
        ,prompt_template=PROMPT_TEMPLATE
        ,search_size_return = 3
        
    ):
        self.llm_client = llm_client
        self.index = index
        self.index_name = index_name
        self.model = model
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.search_size_return = search_size_return
        

    def search(self, query,  filter_dict={}):
        fields =  ["content"]
        results = self.index.search(
            index=self.index_name,
            body={
                "size": self.search_size_return
                ,"query": {
                    "bool": {
                        "must":  {"multi_match": {"query": query, "fields": fields}}
                        ,"filter": {"term": filter_dict} if filter_dict else {"match_all": {}} 
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

        return  '\n'.join(lines).strip()
    

    def build_prompt(self, query, search_results_dict):
        relevant_document = self.build_context(search_results_dict)

        return self.prompt_template.format(
            question=query
            ,relevant_document=relevant_document
        )

    def llm(self, prompt):
        response = self.llm_client.messages.create(
            model = self.model
            ,system = self.instructions
            ,messages=[{"role": "user", "content": prompt}]
            ,max_tokens=1000
            ,temperature=0
        )

        return response.content[0].text

    #the final method rag: orchestrate the process in order
    def rag(self, query):
        search_results_dict = self.search(query)
        constructed_prompt = self.build_prompt(query, search_results_dict)
        llm_response = self.llm(constructed_prompt)
        
        return llm_response
        
