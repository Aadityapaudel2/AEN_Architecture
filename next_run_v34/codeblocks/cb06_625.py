# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 26 / CB06.625 Upload dataset
# Intended use: replace/run this CB cell in notebook order.

from pathlib import Path
import os
import subprocess
import sys

try:
    import kagglehub
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "kagglehub"])
    import kagglehub

# Frozen Canon/V21 Runtime-at-Boot dataset.
# KaggleHub specific-version syntax is owner/dataset/versions/N.
RUNTIMEATBOOT_DATASET_HANDLE = "aadityapaudel/runtimeatboot/versions/32"

runtime_root = Path(kagglehub.dataset_download(RUNTIMEATBOOT_DATASET_HANDLE))
print("downloaded runtimeatboot:", runtime_root)
print("runtimeatboot_handle:", RUNTIMEATBOOT_DATASET_HANDLE)

def find_runtime_root(root: Path) -> Path:
    candidates = [
        root,
        root / "runtimeatbootdataset",
        root / "runtimeatboot",
    ]
    for c in candidates:
        if (c / "boot").exists():
            return c
    for boot in root.rglob("boot"):
        if boot.is_dir():
            return boot.parent
    raise FileNotFoundError(f"Could not find runtimeatboot boot/ under {root}")

RUNTIME_AT_BOOT_DATASET_ROOT = str(find_runtime_root(runtime_root))
AENAIMO_RUNTIME_AT_BOOT_DATASET_ROOT = RUNTIME_AT_BOOT_DATASET_ROOT
CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT = Path(RUNTIME_AT_BOOT_DATASET_ROOT)

ATHENA_BOOT_PATH = str(Path(RUNTIME_AT_BOOT_DATASET_ROOT) / "boot" / "athena" / "Athena_epistemic_boot_100_final_hq.ndjson")
ATHENA_BOOT_CERTIFICATION_PATH = str(Path(RUNTIME_AT_BOOT_DATASET_ROOT) / "boot" / "athena" / "Athena_epistemic_boot_100_final_certification_hq.ndjson")

ARTEMIS_BOOT_PATH = str(Path(RUNTIME_AT_BOOT_DATASET_ROOT) / "boot" / "artemis" / "Artemis_problem_proof_boot_100_final_hq.ndjson")
ARTEMIS_BOOT_CERTIFICATION_PATH = str(Path(RUNTIME_AT_BOOT_DATASET_ROOT) / "boot" / "artemis" / "Artemis_problem_proof_boot_100_final_hq_mcq.ndjson")

ARIA_BOOT_PATH = str(Path(RUNTIME_AT_BOOT_DATASET_ROOT) / "boot" / "aria" / "Aria_problem_proof_boot_100_final.ndjson")
ARIA_BOOT_CERTIFICATION_PATH = str(Path(RUNTIME_AT_BOOT_DATASET_ROOT) / "boot" / "aria" / "Aria_problem_proof_boot_100_final_mcq_2q.ndjson")

print("RUNTIME_AT_BOOT_DATASET_ROOT =", RUNTIME_AT_BOOT_DATASET_ROOT)
for p in [
    ATHENA_BOOT_PATH,
    ATHENA_BOOT_CERTIFICATION_PATH,
    ARTEMIS_BOOT_PATH,
    ARTEMIS_BOOT_CERTIFICATION_PATH,
    ARIA_BOOT_PATH,
    ARIA_BOOT_CERTIFICATION_PATH,
]:
    print(p, Path(p).exists())

"""## 06.75 - Dataset Path Override



"""
