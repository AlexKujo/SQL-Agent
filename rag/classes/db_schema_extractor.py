from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Dict, Iterable, List, Protocol

from langchain_text_splitters import RecursiveCharacterTextSplitter

import logging

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    DESCRIPTION = "description"
    SCHEMA = "schema"
    COLUMNS = "columns"
    SAMPLES = "samples"
    GENERAL = "general"


@dataclass
class TableSchema:
    table_name: str
    columns_names: List[str]
    raw_table_info: str
    table_comment: str

    @property
    def full_schema(self) -> str:
        return f"TABLE: {self.table_name}\n\nDESCRIPTION: {self.table_comment}\n\n{self.raw_table_info}"


@dataclass
class SchemaChunk:
    table_name: str
    columns_names: List[str]
    content: str
    chunk_type: str
    chunk_order: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "columns_names": self.columns_names,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "chunk_order": self.chunk_order,
        }


class InspectorProtocol(Protocol):
    def get_columns(
        self, table_name: str, schema: str | None = None, **kw: Any
    ) -> List[Any]:
        """
        Return information about columns in table_name.

        Given a string table_name and an optional string schema,
        return column information as a list of .ReflectedColumn.

        :param table_name: string name of the table. For special quoting,
        use .quoted_name.

        :param schema: string schema name; if omitted, uses the default schema
        of the database connection. For special quoting,
        use .quoted_name.

        :param **kw: Additional keyword argument to pass to the dialect
        specific implementation. See the documentation of the dialect in use for more information.

        :return: list of dictionaries, each representing the definition of
        a database column.
        """
        ...

    def get_table_comment(
        self, table_name: str, schema: str | None = None, **kw: Any
    ) -> Any:
        """
        Return information about the table comment for table_name.

        Given a string table_name and an optional string schema,
        return table comment information as a .ReflectedTableComment.

        Raises NotImplementedError for a dialect that does not support comments.

        :param table_name: string name of the table. For special quoting,
        use .quoted_name.

        :param schema: string schema name; if omitted, uses the default schema
        of the database connection. For special quoting,
        use .quoted_name.

        :param **kw: Additional keyword argument to pass to the dialect
        specific implementation. See the documentation of the dialect in use for more information.

        :return: a dictionary, with the table comment.
        """
        ...


class DatabaseConnection(Protocol):
    def get_table_info(
        self, table_names: List[str] | None = None, get_col_comments: bool = False
    ) -> str:
        """
        Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If sample_rows_in_table_info, the specified number of sample rows will be appended to each table description. This can increase performance as demonstrated in the paper.
        """
        ...

    def get_usable_table_names(self) -> Iterable[str]:
        """
        Get names of tables available.
        """
        ...

    @property
    def _inspector(self) -> InspectorProtocol:
        """
        Underlying SQLAlchemy inspector (⚠️ private, may change).
        """
        ...


class DatabaseSchemaExtractor:

    def __init__(self, db_connection: DatabaseConnection) -> None:
        self.db = db_connection

    def extract_schemas(
        self, table_names: List[str] | None = None
    ) -> List[TableSchema]:

        if table_names is None:
            table_names = list(self.db.get_usable_table_names())

        schemas = []

        for table in table_names:
            schema = self._extract_table_schema(table)
            schemas.append(schema)

        return schemas

    def _extract_table_schema(self, table_name: str) -> TableSchema:
        """Извлекает схему конкретной таблицы."""
        table_info = self._get_table_info(table_name)
        column_names = self._get_column_names(table_name)
        table_comment = self._get_table_comment(table_name)

        return TableSchema(
            table_name=table_name,
            columns_names=column_names,
            raw_table_info=table_info,
            table_comment=table_comment,
        )

    def _get_column_names(self, table_name: str) -> List[str]:
        """Получает список названий колонок для таблицы."""
        columns = self.db._inspector.get_columns(table_name)
        return [column.get("name") for column in columns]

    def _get_table_info(self, table_name: str) -> str:
        """Получает информацию о таблице от LangChain SQLDatabase."""
        return self.db.get_table_info([table_name], get_col_comments=True)

    def _get_table_comment(self, table_name: str) -> str:
        """Получает комментарий к таблице."""
        comment_dict = self.db._inspector.get_table_comment(table_name)
        return comment_dict.get("text", "No description")


class SchemaSplitter:

    DEFAULT_CHUNK_SIZE = 800
    DEFAULT_CHUNK_OVERLAP = 0

    def _create_splitter(
        self, chunk_size: int, chunk_overlap: int
    ) -> RecursiveCharacterTextSplitter:
        """Создает настроенный сплиттер."""
        return RecursiveCharacterTextSplitter(
            separators=[
                "\n\n/*\n",  # начало блока комментариев
                "\n*/\n\n/*\n",  # переход между блоками
                "\n*/\n",  # конец блока
                "\n\n",  # абзацы
                "\n",  # переносы строк
                " ",  # пробелы
                "",  # принудительное разбиение по символам
            ],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            keep_separator=True,
        )

    def split_schemas(
        self,
        schemas: List[TableSchema],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> List[SchemaChunk]:
        """Разбивает список схем на чанки."""
        splitter = self._create_splitter(chunk_size, chunk_overlap)

        all_chunks = []
        for schema in schemas:
            chunks = self.split_single_schema(schema, splitter=splitter)
            all_chunks.extend(chunks)
        return all_chunks

    def split_single_schema(
        self, schema: TableSchema, splitter: RecursiveCharacterTextSplitter
    ) -> List[SchemaChunk]:
        """Разбивает одну схему на чанки."""
        chunks = []
        order = 1

        # Добавляем чанк с описанием таблицы
        if schema.table_comment and schema.table_comment != "No description":
            description_chunk = SchemaChunk(
                table_name=schema.table_name,
                columns_names=schema.columns_names,
                content=f"TABLE: {schema.table_name}\n\nDESCRIPTION:\n{schema.table_comment}",
                chunk_type=ChunkType.DESCRIPTION.value,
                chunk_order=order,
            )
            chunks.append(description_chunk)
            order += 1

        # Разбиваем основную информацию на блоки
        blocks = self._split_by_comment_blocks(schema.raw_table_info)

        for block_text, block_type in blocks:
            # Разбиваем каждый блок через сплиттер
            parts = splitter.split_text(block_text)

            for part in parts:
                content = self._format_chunk_content(
                    schema.table_name, part, block_type
                )

                chunk = SchemaChunk(
                    table_name=schema.table_name,
                    columns_names=schema.columns_names,
                    content=content,
                    chunk_type=block_type,
                    chunk_order=order,
                )
                chunks.append(chunk)
                order += 1

        return chunks

    def _split_by_comment_blocks(self, text: str) -> List[tuple]:
        """Разделяет текст на блоки по /* ... */ и остальному содержимому."""
        blocks = []
        parts = re.split(r"(/\*.*?\*/)", text, flags=re.DOTALL)

        for part in parts:
            if not part.strip():
                continue
            block_type = self._detect_block_type(part)
            blocks.append((part.strip(), block_type))

        return blocks

    def _detect_block_type(self, text: str) -> str:
        """Определяет тип блока по содержимому."""
        text_lower = text.lower()

        if "create table" in text_lower:
            return ChunkType.SCHEMA.value
        elif "column comments:" in text_lower:
            return ChunkType.COLUMNS.value
        elif "rows from" in text_lower:
            return ChunkType.SAMPLES.value
        else:
            return ChunkType.GENERAL.value

    def _format_chunk_content(
        self, table_name: str, content: str, chunk_type: str
    ) -> str:
        """Форматирует содержимое чанка в зависимости от типа."""
        content = content.strip()

        if chunk_type == ChunkType.SCHEMA.value:
            return f"TABLE: {table_name}\n\nSCHEMA:\n{content}"
        elif chunk_type == ChunkType.COLUMNS.value:
            return f"TABLE: {table_name}\n\nCOLUMN DESCRIPTIONS:\n{content}"
        elif chunk_type == ChunkType.SAMPLES.value:
            return f"TABLE: {table_name}\n\nSAMPLE DATA:\n{content}"
        else:
            return f"TABLE: {table_name}\n\n{content}"


class DatabaseSchemaProcessor:
    """Фасад для работы с извлечением и чанкингом схем БД."""

    def __init__(self, db_connection):
        self.extractor = DatabaseSchemaExtractor(db_connection)
        self.splitter = SchemaSplitter()

    def get_schema_chunks(self) -> List[Dict[str, Any]]:
        """Удобный метод для получения чанков схем в виде словарей."""
        schemas = self.extractor.extract_schemas()
        chunks = self.splitter.split_schemas(schemas, chunk_size=400)
        return [chunk.to_dict() for chunk in chunks]

    def get_table_chunks(self, table_name: str) -> List[Dict[str, Any]]:
        """Получает чанки для конкретной таблицы."""
        schema = self.extractor.extract_schemas([table_name])
        chunks = self.splitter.split_schemas(schema)
        return [chunk.to_dict() for chunk in chunks]
