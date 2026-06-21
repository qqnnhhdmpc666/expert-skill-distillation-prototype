# Local Environment Discovery

Date: 2026-06-22

## Decision

```text
wsl = present
docker_windows = missing
docker_wsl = present_and_daemon_reachable
harbor_windows = missing
harbor_wsl = present
harbor_smoke = pass_plumbing_only
osv_scanner = not_found
```

此前“Harbor、Docker、WSL 均缺失”的报告不成立。原因是旧 discovery 只检查 Windows PATH，并且受限 shell 未看到真实用户的 WSL 状态。

## Windows discovery

Fresh command:

```powershell
wsl.exe -l -v
wsl.exe --status
uv tool list
Get-Command harbor,docker,wsl,uv,pip,pipx -All -ErrorAction SilentlyContinue
where.exe harbor
where.exe docker
where.exe wsl
```

Observed output:

```text
WSL distribution: Ubuntu-24.04-Codex
WSL state at discovery: Stopped
WSL version: 2
default distribution: Ubuntu-24.04-Codex
default WSL version: 2
uv tools: No tools installed
Windows harbor: not found
Windows docker: not found
Windows pipx: not found
wsl.exe: C:\Windows\System32\wsl.exe
wsl.exe: C:\Users\31552\AppData\Local\Microsoft\WindowsApps\wsl.exe
uv.exe: C:\Users\31552\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe
pip.exe: C:\Users\31552\AppData\Local\Programs\Python\Python313\Scripts\pip.exe
```

## WSL discovery

Fresh command shape:

```powershell
wsl.exe -d Ubuntu-24.04-Codex -- bash -lc "id; command -v harbor; command -v docker; command -v uv; command -v pip; command -v pipx; command -v python3; docker --version; docker info; find /opt/spark -type f -name harbor"
```

Observed output:

```text
identity: uid=0(root) gid=0(root)
docker: /usr/bin/docker
Docker client: 29.1.3
Docker server: 29.1.3
uv: /root/.local/bin/uv
pip: /usr/bin/pip
python3: /usr/bin/python3
pipx: not found
Harbor: /opt/spark/harbor-src-locked/.venv/bin/harbor
Harbor: /opt/spark/spark-skills/.venv/bin/harbor
Harbor version: 0.1.45
OSV-Scanner: not found
```

Relevant directories:

```text
/opt/spark/harbor-src-locked
/opt/spark/harbor-src
/opt/spark/harbor-local-tasks
/opt/spark/harbor-local-smoke-20260622
```

## Corrected runtime discovery

Fresh command:

```powershell
eskill --state-dir .tmp/env-discovery-state qualify-harbor
```

Fresh result:

```text
status: partial
reason_codes: []
wsl_distributions: [Ubuntu-24.04-Codex]
wsl_docker_commands: [Ubuntu-24.04-Codex:/usr/bin/docker]
wsl_harbor_commands:
  - Ubuntu-24.04-Codex:/opt/spark/harbor-src-locked/.venv/bin/harbor
  - Ubuntu-24.04-Codex:/opt/spark/spark-skills/.venv/bin/harbor
artifact: sha256:0c5cecf4ec06b5867e73c2a16bbc7b20841a54af9fabd5d30cef7dd185f0af8a
```

`partial` means runtime discovered, not external evaluation passed.

## Harbor Docker smoke

Exact command:

```powershell
wsl.exe -d Ubuntu-24.04-Codex -- bash -lc "timeout 180s /opt/spark/harbor-src-locked/.venv/bin/harbor run --path /opt/spark/harbor-local-tasks/hello-local --agent oracle --env docker --job-name eskill-harbor-smoke-20260622 --jobs-dir /opt/spark/harbor-local-smoke-20260622 --n-concurrent 1 --max-retries 0"
```

Official Harbor result:

```text
trials: 1
errors: 0
mean reward: 1.0
job id: b735ac7f-0ba7-4e3e-9e47-76d8f50b07b9
trial id: 3001af2d-334c-4adf-bf0c-bfc3ab3909e1
task checksum: 98e93ba290cbfade792566f97c23f5ee99630454e25a066eb707b7b8423ecd6c
agent: oracle 1.0.0
environment: docker
verifier reward: 1.0
exception: none
```

Evidence paths inside WSL:

```text
/opt/spark/harbor-local-smoke-20260622/eskill-harbor-smoke-20260622/result.json
/opt/spark/harbor-local-smoke-20260622/eskill-harbor-smoke-20260622/hello-local__MZKpVGG/result.json
/opt/spark/harbor-local-smoke-20260622/eskill-harbor-smoke-20260622/hello-local__MZKpVGG/verifier/reward.txt
/opt/spark/harbor-local-smoke-20260622/eskill-harbor-smoke-20260622/hello-local__MZKpVGG/verifier/test-stdout.txt
```

## Claim boundary and next action

This proves Harbor executable discovery, Docker daemon access, container execution, oracle execution, verifier execution and artifact persistence. It does not prove AgentHost qualification, Skill effectiveness, benchmark parity or compiler superiority.

Next action: package one public OSV-derived task with deterministic evaluator, then compare native evaluator semantics with a Harbor task adapter before labeling Harbor an external evaluation backend.

