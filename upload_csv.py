import argparse
import math
import os
import pandas as pd
from opensearchpy import OpenSearch, helpers
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def make_client(host: str, port: int, user: str, password: str) -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, password),
        use_ssl=True,
        verify_certs=False,          # local dev (self-signed)
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )


def create_or_recreate_index(client: OpenSearch, index: str, mapping: dict, recreate: bool):
    if recreate and client.indices.exists(index=index):
        client.indices.delete(index=index)

    if not client.indices.exists(index=index):
        client.indices.create(index=index, body=mapping)


def infer_mapping_from_df(df: pd.DataFrame, time_field: str | None):
    props = {}
    for col, dtype in df.dtypes.items():
        if time_field and col == time_field:
            props[col] = {"type": "date"}
            continue

        if pd.api.types.is_integer_dtype(dtype):
            props[col] = {"type": "long"}
        elif pd.api.types.is_float_dtype(dtype):
            props[col] = {"type": "double"}
        elif pd.api.types.is_bool_dtype(dtype):
            props[col] = {"type": "boolean"}
        else:
            # strings: keyword para facetas + text para búsqueda
            props[col] = {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            }

    return {
        "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
        "mappings": {"properties": props},
    }


def sanitize_value(v):
    # Convert any NaN/Inf into None (JSON-safe)
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def sanitize_doc(doc: dict):
    return {k: sanitize_value(v) for k, v in doc.items()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True, help="CSV path")
    p.add_argument("--index", required=True, help="OpenSearch index name")
    p.add_argument("--host", default=os.getenv("OPENSEARCH_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.getenv("OPENSEARCH_PORT", "9200")))
    p.add_argument("--user", default=os.getenv("OPENSEARCH_USERNAME", "admin"))
    p.add_argument("--password", default=os.getenv("OPENSEARCH_ADMIN_PASSWORD"))
    p.add_argument("--time-field", default=None, help="Column name to treat as date (optional)")
    p.add_argument("--batch-size", type=int, default=2000)
    p.add_argument("--recreate", action="store_true", help="Delete and recreate the index before loading")
    args = p.parse_args()

    # Read CSV
    df = pd.read_csv(args.file)

    # Optional: parse datetime if time_field provided
    if args.time_field and args.time_field in df.columns:
        df[args.time_field] = pd.to_datetime(df[args.time_field], errors="coerce") \
            .dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Make missing values JSON-safe at dataframe level
    df = df.where(pd.notnull(df), None)

    # IMPORTANT: for numeric columns that have missing values, pandas can still behave weirdly
    # Force all columns to object to preserve None reliably
    df = df.astype("object")

    client = make_client(args.host, args.port, args.user, args.password)

    mapping = infer_mapping_from_df(df, args.time_field)
    create_or_recreate_index(client, args.index, mapping, args.recreate)

    records = df.to_dict(orient="records")

    actions = (
        {"_index": args.index, "_source": sanitize_doc(rec)}
        for rec in records
    )

    helpers.bulk(
        client,
        actions,
        chunk_size=args.batch_size,
        request_timeout=120,
        raise_on_error=True,
    )

    client.indices.refresh(index=args.index)
    count = client.count(index=args.index)["count"]
    print(f"✅ Uploaded {len(df)} rows to index '{args.index}'. Current count: {count}")


if __name__ == "__main__":
    main()

    
