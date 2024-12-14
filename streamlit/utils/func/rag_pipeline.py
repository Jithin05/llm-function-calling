from haystack import Pipeline, Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import (SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder)
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import AzureOpenAIGenerator
from haystack.utils import Secret
import os

# Embed documents
def embed_documents(documents):
    document_store = InMemoryDocumentStore()

    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component(
        "doc_embedder", SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
    )
    indexing_pipeline.add_component("doc_writer", DocumentWriter(document_store=document_store))

    indexing_pipeline.connect("doc_embedder.documents", "doc_writer.documents")

    indexing_pipeline.run({"doc_embedder": {"documents": documents}})

    return document_store

documents = [
    Document(content="The company was founded in 1985 and has been a leader in the carbon black industry ever since. Our mission is to provide high-quality products while maintaining a commitment to sustainability."),
    Document(content="Q: What is the lead time for orders?\nA: The typical lead time for orders is 4-6 weeks, depending on the quantity and product specifications."),
    Document(content="Issue: Poor dispersion in rubber compounds\nSolution: Ensure proper mixing times and temperatures, and consider using a dispersing agent."),
    Document(content="For customer service inquiries, please contact us at support@example.com or call 1-800-987-6543. Our business hours are Monday to Friday, 9am to 5pm.")
]

document_store = embed_documents(documents)

# Create RAG pipeline
template = """
Answer the questions based on the given context.

Context:
{% for document in documents %}
    {{ document.content }}
{% endfor %}
Question: {{ question }}
Answer:
"""
rag_pipe = Pipeline()
rag_pipe.add_component("embedder", SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"))
rag_pipe.add_component("retriever", InMemoryEmbeddingRetriever(document_store=document_store))
rag_pipe.add_component("prompt_builder", PromptBuilder(template=template))
# Note to llm: We are using OpenAIGenerator, not the OpenAIChatGenerator, because the latter only accepts List[str] as input and cannot accept prompt_builder's str output
rag_pipe.add_component("llm", AzureOpenAIGenerator(
        api_key=Secret.from_token(os.getenv('AZURE_OPENAI_API_KEY')),
		        azure_endpoint=os.getenv('AZURE_OPENAI_API_BASE_URL'),
		        azure_deployment=os.getenv('MODEL_NAME')))

rag_pipe.connect("embedder.embedding", "retriever.query_embedding")
rag_pipe.connect("retriever", "prompt_builder.documents")
rag_pipe.connect("prompt_builder", "llm")

def rag_pipeline_func(query: str):
    result = rag_pipe.run({"embedder": {"text": query}, "prompt_builder": {"question": query}})

    return {"reply": result["llm"]["replies"][0]}
