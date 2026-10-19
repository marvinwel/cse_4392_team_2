
import json

from advisor_tools import generate_degree_plan

result = generate_degree_plan.invoke({
    "student_id": "1002000102",  # Michael Smith
    "start_term": "2027-SP",
    "max_credits_per_term": 15,
    "include_summer": False
})

print(json.dumps(result, indent=2))

