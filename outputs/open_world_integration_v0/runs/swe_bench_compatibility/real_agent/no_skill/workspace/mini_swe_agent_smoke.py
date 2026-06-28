
from __future__ import annotations

import json
import sys
from pathlib import Path

from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models.test_models import DeterministicModel, make_output


trajectory_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])
prompt_path = Path(sys.argv[3])
workspace = trajectory_path.parent
task_text = prompt_path.read_text(encoding="utf-8")

model = DeterministicModel(
    outputs=[
        make_output(
            "I will complete the open-world integration smoke task.",
            [{"command": "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"}],
            cost=0.0,
        )
    ]
)
env = LocalEnvironment(cwd=str(workspace), timeout=10)
agent = DefaultAgent(
    model,
    env,
    system_template="You are a mini-SWE-agent smoke-test agent.",
    instance_template="Task: {{task}}",
    step_limit=2,
    cost_limit=1,
    output_path=trajectory_path,
)
result = agent.run(task_text)
result_path.write_text(json.dumps({"status": "completed", "result": result}, indent=2), encoding="utf-8")
print(json.dumps({"mini_swe_agent_smoke": "executed", "result": result}, sort_keys=True))
