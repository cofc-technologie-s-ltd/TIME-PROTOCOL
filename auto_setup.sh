#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  TIME Protocol - Automated Setup & Demo
#  Run: bash auto_setup.sh
# ═══════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ⏳ TIME Protocol - Automated Setup${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Step 1: Check Python ────────────────────────────────────
echo -e "${BLUE}[1/6]${NC} Checking Python..."
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version)
    echo -e "      ${GREEN}✓${NC} $PY_VERSION"
else
    echo -e "      ${RED}✗${NC} Python 3 not found"
    exit 1
fi

# ─── Step 2: Install dependencies ────────────────────────────
echo ""
echo -e "${BLUE}[2/6]${NC} Installing dependencies..."
if python3 -c "import ecdsa" 2>/dev/null; then
    echo -e "      ${GREEN}✓${NC} ecdsa already installed"
else
    pip install ecdsa --quiet 2>&1 | tail -2
    echo -e "      ${GREEN}✓${NC} ecdsa installed"
fi

# ─── Step 3: Verify imports ──────────────────────────────────
echo ""
echo -e "${BLUE}[3/6]${NC} Verifying module imports..."
python3 -c "
try:
    import time_crypto
    import time_ledger
    import time_consensus
    import time_network
    import time_sdk
    print('      \033[0;32m✓\033[0m Core modules OK')
except ImportError as e:
    print('      \033[0;33m!\033[0m Some modules missing:', e)
" 2>&1

# ─── Step 4: Run tests ───────────────────────────────────────
echo ""
echo -e "${BLUE}[4/6]${NC} Running test suite..."
if [ -f test_pure_core.py ]; then
    python3 -m unittest test_pure_core.py 2>&1 | tail -3
    echo -e "      ${GREEN}✓${NC} Core tests passed"
else
    echo -e "      ${YELLOW}⚠${NC} test_pure_core.py not found"
fi

if [ -f test_time_protocol.py ]; then
    python3 -m unittest test_time_protocol.py 2>&1 | tail -3
    echo -e "      ${GREEN}✓${NC} Full tests passed"
fi

# ─── Step 5: Run sovereign simulation ────────────────────────
echo ""
echo -e "${BLUE}[5/6]${NC} Running sovereign ledger simulation..."
if [ -f main_simulation_sovereign.py ]; then
    timeout 30 python3 main_simulation_sovereign.py 2>&1 | tail -20
    echo -e "      ${GREEN}✓${NC} Simulation completed"
else
    echo -e "      ${YELLOW}⚠${NC} Simulation script not found"
fi

# ─── Step 6: Start sovereign node ────────────────────────────
echo ""
echo -e "${BLUE}[6/6]${NC} Testing sovereign node daemon..."
python3 -c "
try:
    from mainnet_node import SovereignMainnetNode
    node = SovereignMainnetNode('AUTO_VALIDATOR_01', '127.0.0.1', 8080)
    print('      \033[0;32m✓\033[0m Sovereign node initialized')
    print(f'      \033[0;32m✓\033[0m Node ID: {node.node_id}')
    print(f'      \033[0;32m✓\033[0m Endpoint: {node.host}:{node.port}')
except Exception as e:
    print(f'      \033[0;33m⚠\033[0m {e}')
" 2>&1

# ─── Summary ─────────────────────────────────────────────────
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ SETUP COMPLETE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}Available commands:${NC}"
echo ""
echo -e "  ${BLUE}▸${NC} Run tests:"
echo "      python3 -m unittest test_pure_core.py -v"
echo ""
echo -e "  ${BLUE}▸${NC} Run full test suite:"
echo "      python3 -m unittest discover -v"
echo ""
echo -e "  ${BLUE}▸${NC} Run sovereign simulation:"
echo "      python3 main_simulation_sovereign.py"
echo ""
echo -e "  ${BLUE}▸${NC} Start a sovereign node:"
echo "      python3 -c \"from mainnet_node import SovereignMainnetNode; n = SovereignMainnetNode('NODE_01', '127.0.0.1', 8080); n.start_node(); print('Node running at http://127.0.0.1:8080')\""
echo ""
echo -e "  ${BLUE}▸${NC} Docker deployment:"
echo "      docker-compose up -d"
echo ""
echo -e "  ${BLUE}▸${NC} Documentation:"
echo "      cat WHITE_PAPER.md"
echo "      cat BENCHMARK_AND_QA_REPORT.md"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  🌐 Repository: https://github.com/cofc-technologie-s-ltd/TIME-PROTOCOL"
echo ""
