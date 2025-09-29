Installing PyTorch and Ultralytics (backend)
=============================================

This file provides recommended installation steps to set up a backend environment
that works with YOLO11 (Ultralytics) and the `marmot-edge` backend.

Requirements
------------
- Python 3.8 - 3.12 (3.11 recommended)
- pip or conda
- If using GPU: NVIDIA drivers + compatible CUDA toolkit. Install `torch` with the
  matching `pytorch-cuda` package (see below).

Recommended installation (CPU-only)
----------------------------------
1. Create & activate virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Upgrade pip and install core packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
# If you prefer headless OpenCV (server), replace opencv-python with opencv-python-headless
# pip install opencv-python-headless
```

Recommended installation (GPU with CUDA)
----------------------------------------
Visit https://pytorch.org/get-started/locally/ and follow the selector to get the
correct `pip` or `conda` command for your OS, CUDA version, and Python version.
Example for Linux/Windows with CUDA 12.1 and pip:

```powershell
pip install "pytorch" "torchvision" --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt --no-deps
npip install ultralytics
n```

Notes and gotchas
------------------
- On Windows CPU-only installations, some `torch` versions have known issues
  (see Ultralytics pyproject). If you encounter odd errors, try a different
  torch wheel (e.g. 2.3.x or 2.2.x) or use the official PyTorch install selector.
- `ultralytics` may download model weights on first load (e.g. `yolo11n.pt`) if
  they are not present locally. You can set `YOLO_MODEL_PATH` environment
  variable to point to a local `.pt` file if you wish to manage weights manually.
- If you keep large `.pt` weights outside git, use `YOLO_MODEL_PATH` or set the
  `ultralytics` settings (weights_dir/runs_dir) as needed.

Verifying installation
----------------------
Run a simple import test in PowerShell:

```powershell
python -c "from ultralytics import YOLO; print('ultralytics OK')"
python -c "import torch; print('torch', torch.__version__, 'cuda_available=', torch.cuda.is_available())"
```

If both commands succeed, your environment is ready to run YOLO-based detection
in `marmot-edge/backend`.
