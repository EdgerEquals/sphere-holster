# ssm-sim-gateway: MCP gateway to the open simulation stack (issue #10)

Locked by Danny on 2026-10-19 (round 3, Kimi's pick), sequenced after the ledger: every gateway smoke run is written
to the ledger as a `gateway_run` record.

## What's here
| File | What |
|---|---|
| `ssm_mcp_server.py` | Thin stdlib MCP server (stdio JSON-RPC). Tools: `list_sim_tools`, `fenics_poisson_smoke`, `openfoam_cavity_smoke`. Each one copies `sim/<tool>` into `/tmp` and runs the existing smoke test there. |
| `Dockerfile.fenics`, `Dockerfile.openfoam` | Built on the same digest-pinned DOLFINx 0.11.0 and OpenFOAM v2512 images as `sim-stack.yml`, with a non-root user (uid 10001). |
| `docker-compose.yml` | The hardened services: `network_mode: none`, read-only root filesystem, non-root user, `cap_drop: ALL`, `no-new-privileges`, tmpfs `/tmp` as the only writable path, and `sim/` mounted read-only. |
| `mcp_smoke_client.py` | Plain Python MCP client used by CI. No LLM is involved. |
| `../.cursor/mcp.json` | Cursor client config (servers `ssm-fenics` and `ssm-openfoam`) with the same hardening flags. |

CI: `.github/workflows/mcp-gateway.yml` runs on dispatch and on pushes to `gateway/**`. It builds both images, starts
each one on demand and calls `tools/list` plus one solver tool. It uploads `gateway-run-<id>`, which `ledger.yml`
ingests.

## Local use (Cursor)
```bash
docker compose -f gateway/docker-compose.yml build   # once; needs network at build time only
```
Then enable `ssm-fenics` / `ssm-openfoam` in Cursor's MCP settings. The containers start per session with no network.

## Upstream servers (researched 2026-10-19)
- **dolfinx-mcp** (github.com/ekstanley/ccFenics-plugin, MIT; announced on the FEniCS Discourse 2026-02-24).
  - FastMCP server with 38 tools, including `run_custom_code`, which executes arbitrary Python. Its docs say Docker
    isolation is the only boundary for that tool.
  - Its Dockerfile builds on the unpinned `dolfinx/dolfinx:stable` and installs unpinned pip packages.
  - CI tries it as an **experimental, non-blocking** step: pinned commit `cedb5f8`, base swapped to our pinned image,
    `tools/list` only.
  - It is not the default gateway because the arbitrary-code tool would widen what a model can run.
- **openfoam-mcp-server** (github.com/webworn/openfoam-mcp-server).
  - A C++ server for "CFD education with Socratic questioning".
  - Its own docs mark heat transfer as "in development" and list partial OpenFOAM 12 compatibility.
  - It is not built here. The thin wrapper around our own tested `sim/openfoam` case is used instead.
