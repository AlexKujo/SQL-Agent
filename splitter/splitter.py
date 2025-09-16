import re
from typing import List


class Splitter:

    def split_schema(schema_text: str) -> List[str]:
        """
        Разделяет схему БД на отдельные таблицы

        Принимает: большую строку со всеми таблицами
        Возвращает: список строк, каждая = одна таблица
        """

        table_chunks = re.split(r"(?=CREATE TABLE)", schema_text)
        tables = []

        for chunk in table_chunks:
            clean_chunk = chunk.strip()
            if clean_chunk:
                tables.append(clean_chunk)

        return tables


if __name__ == "__main__":
    test_schema = """CREATE TABLE category_name_translation (
	product_category_name TEXT, 
	product_category_name_english TEXT
)

/*
3 rows from category_name_translation table:
product_category_name	product_category_name_english
beleza_saude	health_beauty
informatica_acessorios	computers_accessories
automotivo	auto
*/


CREATE TABLE customers (
	customer_id TEXT NOT NULL, 
	customer_unique_id TEXT NOT NULL, 
	customer_zip_code_prefix BIGINT, 
	customer_city TEXT, 
	customer_state TEXT, 
	CONSTRAINT customers_pkey PRIMARY KEY (customer_id)
)

/*
Column Comments: {'customer_id': 'key to the orders dataset. Each order has a unique customer_id', 'customer_unique_id': 'unique identifier of a customer', 'customer_zip_code_prefix': 'first five digits of customer zip code'}
*/

/*
3 rows from customers table:
customer_id	customer_unique_id	customer_zip_code_prefix	customer_city	customer_state
06b8999e2fba1a1fbc88172c00ba8bc7	861eff4711a542e4b93843c6dd7febb0	14409	franca	SP
18955e83d337fd6b2def6b18a428ac77	290c77bc529b7ac935b93aa66c333dc3	9790	sao bernardo do campo	SP
4e7b3e00288586ebd08712fdd0374a03	060e732b5b29e8181a18229c7b0b2b5e	1151	sao paulo	SP
*/ """

tables = Splitter.split_schema(test_schema)
print(f"Найдено таблиц: {len(tables)}")
print("\n" + "=" * 50 + "\n")

for i, table in enumerate(tables, 1):
    print(f"ТАБЛИЦА {i}:")
    print(table)
    print("\n" + "-" * 30 + "\n")
