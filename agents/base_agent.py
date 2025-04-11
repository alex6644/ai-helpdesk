from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings


class BaseKIAgent:
    def __init__(self, data_path: str, rules_path: str, context_query: str, llm_model: str = "gemma3:12b"):
        """
        data_path: Pfad zum Ordner mit den FAQ- oder Kontext-Dokumenten.
        rules_path: Pfad zur Regeldatei (Prompt-Vorgabe) dieses Agenten.
        context_query: Standardmäßige Anfrage an den Index, um relevanten Kontext zu erhalten.
        llm_model: Das zu verwendende Modell (Standard: gemma3:12b)
        """
        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        self.documents = SimpleDirectoryReader(data_path).load_data()
        self.index = VectorStoreIndex.from_documents(self.documents)

        self.llm = Ollama(model=llm_model, request_timeout=60)

        self.query_engine = self.index.as_query_engine(similarity_top_k=2, llm=self.llm)

        with open(rules_path, "r", encoding="utf-8") as f:
            self.rule_prompt = f.read()

        self.context_query = context_query

    def process_email(self, email_text: str) -> str:
        """
        Verarbeitet eine eingehende E-Mail:
          - Holt relevanten Kontext aus den Dokumenten
          - Baut den finalen Prompt (Regeln + Kontext + E-Mail) zusammen
          - Ruft das LLM auf und gibt dessen Antwort zurück
        """
        # Hole relevanten Kontext aus dem Index
        context = self.query_engine.query(self.context_query).response

        # Baue den finalen Prompt zusammen. Hier kannst du weiter verfeinern,
        # z.B. indem du den Kontext als separaten Abschnitt einfügst.
        full_prompt = f"""{self.rule_prompt}


        Kontext:
        {context}
        
        Eingehende E-Mail:
        {email_text}
        """
        # Rufe das LLM auf und liefere dessen Antwort (angenommen als plain Text)
        result = self.llm.complete(full_prompt)
        return result.text
