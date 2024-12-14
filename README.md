# llm-function-calling

Here we build an assistant for customers who want to inquire, purchase products of a company. The assistant has access to the following tools, which allows the assistant to access external applications.

- `get_items`, `purchase_item`: Connect to product catalog stored in database via API, for retrieving item list and making a purchase respectively
- `rag_pipeline_func`: Connect to document store with Retrieval Augmented Generation (RAG) to obtain information from unstructured texts e.g. company’s brochures
