"""
Create the advisor's DynamoDB tables (safe to run more than once).

Run from the langchain/ folder:

    python scripts/dynamo_setup.py --seed seed/students.json           # real AWS (us-east-2)
    python scripts/dynamo_setup.py --local --seed seed/students.json   # DynamoDB Local on :8000

--seed writes every student in the file (existing students with the same id are replaced).

Tables
  advisor_students       key: student_id                 one item per student, transcript inside
  advisor_degree_plans   key: student_id + plan_name     one item per saved plan
  advisor_checkpoints    key: PK + SK                    LangGraph DynamoDBSaver (chat state)

Billing
  students / degree_plans use PROVISIONED 5 read + 5 write units each. DynamoDB's
  always-free tier covers 25 read + 25 write units per region in provisioned mode,
  so these two stay free. Checkpoints use ON-DEMAND because each chat turn writes a
  burst of checkpoint data that small provisioned capacity would throttle.

Table names must match advisor_tools.py (same environment variables).
"""

import argparse
import json
import os

import boto3
from botocore.exceptions import ClientError

STUDENTS_TABLE = os.environ.get("STUDENTS_TABLE", "advisor_students")
PLANS_TABLE = os.environ.get("PLANS_TABLE", "advisor_degree_plans")
CHECKPOINT_TABLE = os.environ.get("CHECKPOINT_TABLE", "advisor_checkpoints")

SMALL_PROVISIONED = {"BillingMode": "PROVISIONED",
                     "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}}
ON_DEMAND = {"BillingMode": "PAY_PER_REQUEST"}

TABLES = [
    {"TableName": STUDENTS_TABLE,
     "KeySchema": [{"AttributeName": "student_id", "KeyType": "HASH"}],
     "AttributeDefinitions": [{"AttributeName": "student_id", "AttributeType": "S"}],
     **SMALL_PROVISIONED},
    {"TableName": PLANS_TABLE,
     "KeySchema": [{"AttributeName": "student_id", "KeyType": "HASH"},
                   {"AttributeName": "plan_name", "KeyType": "RANGE"}],
     "AttributeDefinitions": [{"AttributeName": "student_id", "AttributeType": "S"},
                              {"AttributeName": "plan_name", "AttributeType": "S"}],
     **SMALL_PROVISIONED},
    # Key layout required by langgraph-checkpoint-aws DynamoDBSaver
    {"TableName": CHECKPOINT_TABLE,
     "KeySchema": [{"AttributeName": "PK", "KeyType": "HASH"},
                   {"AttributeName": "SK", "KeyType": "RANGE"}],
     "AttributeDefinitions": [{"AttributeName": "PK", "AttributeType": "S"},
                              {"AttributeName": "SK", "AttributeType": "S"}],
     **ON_DEMAND},
]



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="use DynamoDB Local on localhost:8000")
    ap.add_argument("--region", default=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-2")
    ap.add_argument("--seed", metavar="STUDENTS_JSON", help="load students from this JSON file")
    args = ap.parse_args()

    endpoint = "http://localhost:8000" if args.local else None
    client = boto3.client("dynamodb", region_name=args.region, endpoint_url=endpoint)
    where = "DynamoDB Local" if args.local else f"AWS {args.region}"

    for spec in TABLES:
        name = spec["TableName"]
        try:
            client.create_table(**spec)
            print(f"creating {name} in {where} ...")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceInUseException":
                raise
            print(f"exists   {name}")
        client.get_waiter("table_exists").wait(TableName=name)

    try:
        client.update_time_to_live(TableName=CHECKPOINT_TABLE,
                                   TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"})
        print(f"TTL on   {CHECKPOINT_TABLE}.ttl (old chat checkpoints expire automatically)")
    except ClientError as e:
        # Raised when TTL is already enabled; nothing to do.
        print(f"TTL      {CHECKPOINT_TABLE}: {e.response['Error']['Message']}")

    if args.seed:
        with open(args.seed) as f:
            students = json.load(f)
        table = boto3.resource("dynamodb", region_name=args.region, endpoint_url=endpoint).Table(STUDENTS_TABLE)
        with table.batch_writer(overwrite_by_pkeys=["student_id"]) as batch:
            for student in students:
                batch.put_item(Item=student)
        for student in students:
            print(f"seeded   {student['student_id']}  {student['first_name']} {student['last_name']}  "
                  f"{student['program_id']}  ({len(student['transcript'])} courses)")

    print("done")


if __name__ == "__main__":
    main()
