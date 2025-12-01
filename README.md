## AI-Powered Linux OS – Dev Repo

This repo holds **code, scripts, and tests** for your AI-first Linux OS.  
The actual OS runs inside a **VM** (Oracle VirtualBox first, then QEMU/KVM); this project is the brains, tooling, and documentation.

### High-level phases (mirroring `design.plan.md`)

- **Phase 1 – Oracle VM setup + dev environment**
- **Phase 2 – Core agent skeleton + basic tests**
- **Phase 3 – Local LLM integration**
- **Phase 4 – File management layer (test-driven)**
- **Phase 5 – Screen capture & automation**
- **Phase 6 – Clean UI & AI overlay**
- **Phase 7 – System integration & safety**
- **Phase 8+ – QEMU/KVM and bare metal**

This repo never edits `design.plan.md` – that file is the source-of-truth design.

---

### Quickstart (host machine)

1. Clone this repo.
2. Create a Python virtualenv (Python 3.10+ recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run tests (ULTRA SIMPLE - no VM needed):

```bash
make test
```

**That's it.** 2 seconds, all tests pass, no setup, no VM, no complexity.

Your OS is Python code - test it like Python code.

4. Follow `docs/oracle-vm-setup.md` to create the **Oracle VirtualBox** VM where the OS will actually live.

5. **Speed up VM testing**: Use VirtualBox snapshots! After setting up your VM:
   ```bash
   # Create a snapshot once
   ./scripts/vm-snapshot-helper.sh create
   
   # Restore snapshot for each test run (takes ~10 seconds instead of full reinstall)
   ./scripts/vm-snapshot-helper.sh restore
   ```
   See `docs/speeding-up-testing.md` for details.


# AgentOS
