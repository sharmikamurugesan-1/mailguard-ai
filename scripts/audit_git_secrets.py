import subprocess
import re
import sys

def audit_git_history():
    proc = subprocess.run(["git", "log", "-p", "--all"], capture_output=True, text=True, errors="replace")
    diff = proc.stdout

    patterns = [
        (r"kaggle\.json", "kaggle.json reference"),
        (r"KAGGLE_KEY", "KAGGLE_KEY reference"),
        (r"KAGGLE_USERNAME", "KAGGLE_USERNAME reference"),
        (r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]", "api_key assignment"),
        (r"(?i)secret\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]", "secret assignment"),
        (r"(?i)password\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{4,}['\"]", "password assignment"),
        (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{16,}", "bearer token"),
        (r"(?i)ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
        (r"(?i)glpat-[a-zA-Z0-9_\-]{20,}", "GitLab personal access token"),
        (r"(?i)sk-[a-zA-Z0-9]{32,}", "OpenAI API key"),
    ]

    print("=" * 60)
    print("GIT HISTORY CREDENTIALS & SECRETS AUDIT")
    print("=" * 60)
    found_any = False
    for regex, desc in patterns:
        matches = re.findall(regex, diff)
        if matches:
            found_any = True
            print(f"[FLAGGED] {desc} ({regex}): {len(matches)} occurrence(s)")
            for m in matches[:5]:
                print(f"    sample: {m}")
        else:
            print(f"[CLEAN]   {desc}: 0 occurrences")

    print("-" * 60)
    if not found_any:
        print("RESULT: Zero credentials, tokens, or private secrets found across entire git history.")
    else:
        print("RESULT: Potential secrets detected! Review above details.")
    print("=" * 60)

if __name__ == "__main__":
    audit_git_history()
