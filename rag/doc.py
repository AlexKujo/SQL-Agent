from langchain.schema import Document
from typing import List, Dict


def create_documents_from_schema(schema_data: List[Dict]) -> List[Document]:
    documents = []

    for table_info in schema_data:
        doc = Document(
            page_content=table_info["table_schema"],
            metadata={
                "table_name": table_info["table_name"],
                "columns": table_info["columns_names"],
                "source": "database_schema",
            },
        )

        documents.append(doc)
    return documents
