# Team Assignment 3: A Multi-Agent System for Testing and Refactoring

This guide shows how to set up a Python virtual environment with **uv**, install the project's libraries from `requirements.txt`, and run the app from `app/main.py`.

## 1. Install uv

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
or with Homebrew:
```bash
brew install uv
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal, then check that it worked:
```bash
uv --version
```

## 2. Create the virtual environment

From the **project root folder** (the folder that contains `requirements.txt` and `app/`):

```bash
uv venv
```

This creates a `.venv/` folder. To use a specific Python version:
```bash
uv venv --python 3.12
```

## 3. Activate the virtual environment

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```cmd
.venv\Scripts\activate.bat
```

Your terminal prompt should now start with `(.venv)`.

## 4. Install the libraries

```bash
uv pip install -r requirements.txt
```




## 5. Configure AWS Credentials


```bash
aws configure
```

Enter your AWS credentials when prompted:

```text
AWS Access Key ID: YOUR_ACCESS_KEY
AWS Secret Access Key: YOUR_SECRET_KEY
Default region name: us-east-2
Default output format: json
```

## 6. Verify AWS Connection

Run:

```bash
aws sts get-caller-identity
```

Expected output:

```json
{
    "UserId": "AIDAEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/tam2Admin"
}
```

**Note:** Never commit your AWS access keys to GitHub.




## 7. Run the app

From the **project root** (not from inside `app/`):

```bash
python app/main.py
```

If `main.py` imports other modules from the `app` package (for example `from app.agents import ...`), run it as a module instead:
```bash
python -m app.main
```

You can also skip activating the environment and let uv run it for you:
```bash
uv run python app/main.py
```


