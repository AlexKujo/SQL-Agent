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

        for chunk_info in schema_data:

            content = self._build_document_content(chunk_info)
            metadata = self._build_metadata(chunk_info)

            document = Document(page_content=content, metadata=metadata)

            documents.append(document)

        return documents

    def _build_document_content(self, chunk_info: Dict) -> str:
        # region docstring
        """
        Build the main content for the document from table information.

        Args:
            table_info (Dict): Dictionary containing table schema information

        Returns:
            str: String content for the document
        """
        # endregion
        return chunk_info["table_schema"].strip()

    def _build_metadata(self, chunk_info: Dict) -> Dict:
        # region docstring
        """
        Build metadata dictionary for the document.

        Args:
            chunk_info (Dict): Dictionary containing chunk information

        Returns:
            Dict: Metadata dictionary for search and filtering
        """
        # endregion

        metadata = {
            "table_name": chunk_info["table_name"],
            "columns": chunk_info["columns_names"],
            "source": "database_schema",
        }

        # Add chunk-specific metadata if present (for chunked data)
        if "chunk_type" in chunk_info:
            metadata["chunk_type"] = chunk_info["chunk_type"]

        if "chunk_order" in chunk_info:
            metadata["chunk_order"] = chunk_info["chunk_order"]

        return metadata
