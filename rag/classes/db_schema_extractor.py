import json
from os import getenv
from typing import Dict, List

from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase


class DatabaseSchemaExtractor:

    def __init__(self, db_connection) -> None:
        self.db = db_connection

    def get_column_names(self, table_name: str) -> List[str]:
        columns = self.db._inspector.get_columns(table_name)
        columns_names = []

        columns_names = [column.get("name") for column in columns]

        return columns_names

    def get_schema_with_comments(self) -> List[Dict]:
        tables = self.db.get_usable_table_names()
        db_schema = []

        for table in tables:
            info = self._get_table_info(table)
            comment = self._get_table_comment(table)

            table_schema = f"""
            TABLE DESCRIPTION: {comment.get('text','No description')}
            {info}
            """.strip()
            columns_names = self.get_column_names(table)

            db_schema.append(
                {
                    "table_name": table,
                    "columns_names": columns_names,
                    "table_schema": table_schema,
                }
            )

        return db_schema

    def _get_table_info(self, table_name: str) -> str:
        return self.db.get_table_info([table_name], get_col_comments=True)

    def _get_table_comment(self, table_name: str) -> Dict:
        return self.db._inspector.get_table_comment(table_name)


# if __name__ == "__main__":

#     load_dotenv()

#     db = SQLDatabase.from_uri(getenv("SUPABASE_URI"))

#     extractor = DatabaseSchemaExtractor(db)

#     schema = extractor.get_schema_with_comments()

#     with open("full_schema.json", "w", encoding="utf-8") as f:
#         json.dump(schema, f, ensure_ascii=False, indent=2)
