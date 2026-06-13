"""Local real-agent backend.

This backend runs a local command-line agent that reads target assets and an
optional skill package from disk, then writes concrete output and trace files.
It does not require WSL2.
"""

BACKEND_TYPE = "local_real_agent"
