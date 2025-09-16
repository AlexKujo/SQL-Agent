from typing import Dict, List

from langchain.schema import Document


class SchemaDocumentBuilder:
    # region docstring

    """
    Builds LangChain Document objects from database schema data.

    This class is responsible for converting structured schema information
    into Document objects suitable for vectorization and RAG retrieval.
    """

    # endregion
    def __init__(self):
        # region docstring

        """
        Initialize the SchemaDocumentBuilder.
        """
        # endregion
        pass

    def create_documents(self, schema_data: List[Dict]) -> List[Document]:
        # region docstring

        """
        Create Document objects from schema data.

        Args:
            schema_data (List[Dict]): List of dictionaries containing table information.
                        Each dict should have: table_name, columns_names, table_schema

        Returns:
            List[Document]: List of Document objects ready for vectorization

        Example:
        schema_data = [
            {
                "table_name": "customers",
                "columns_names": ["customer_id", "customer_city"],
                "table_schema": "CREATE TABLE customers..."
            }
        """
        # endregion
        documents = []

        for table_info in schema_data:

            content = self._build_document_content(table_info)
            metadata = self._build_metadata(table_info)

            document = Document(page_content=content, metadata=metadata)

            documents.append(document)

        return documents

    def _build_document_content(self, table_info: Dict) -> str:
        # region docstring

        """
        Build the main content for the document from table information.

        Args:
            table_info (Dict): Dictionary containing table schema information

        Returns:
            str: String content for the document
        """
        # endregion
        return table_info["table_schema"].strip()

    def _build_metadata(self, table_info: Dict) -> Dict:
        # region docstring

        """
        Build metadata dictionary for the document.


        Args:
            table_info (Dict): Dictionary containing table information

        Returns:
            Dict: Metadata dictionary for search and filtering
        """
        # endregion

        metadata = {
            "table_name": table_info["table_name"],
            "columns": table_info["columns_names"],
            "source": "database_schema",
        }

        return metadata


if __name__ == "__main__":
    # Example schema data (as returned by DatabaseSchemaExtractor)
    sample_schema_data = [
        {
            "table_name": "customers",
            "columns_names": ["customer_id", "customer_unique_id", "customer_city"],
            "table_schema": """
        TABLE DESCRIPTION: This dataset has information about customers and location.
        
CREATE TABLE customers (
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,
    customer_city TEXT,
    CONSTRAINT customers_pkey PRIMARY KEY (customer_id)
)

/*
Column Comments: {'customer_id': 'key to the orders dataset'}
*/
        """,
        }
    ]

    # Create document builder
    builder = SchemaDocumentBuilder()

    # Build documents
    documents = builder.create_documents(sample_schema_data)

    # Print results
    for i, doc in enumerate(documents):
        print(doc.page_content[:1000])
