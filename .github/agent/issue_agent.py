import os, subprocess, json, re, textwrap, tempfile
from anthropic import Anthropic
from datetime import datetime

ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO_FULL = os.environ["REPO_FULL"]

def git(cmd):
    subprocess.check_call(cmd, shell=True)

def read_issue():
    # gh CLI ile issue içeriğini al
    out = subprocess.check_output(
        f'gh issue view {ISSUE_NUMBER} --repo {REPO_FULL} --json title,body,labels',
        shell=True
    )
    return json.loads(out)

def ask_model(system, user):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=3000,
        temperature=0.2,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text

def main():
    issue = read_issue()
    title = issue["title"]; body = issue["body"]

    # 1) Branch aç
    branch = "agent/" + re.sub(r"[^a-zA-Z0-9-_]+","-", title.lower())[:40]
    git(f"git checkout -b {branch}")

    # 2) Kod değişiklik planı + patch üret
    system = """Sen bir repo-ajanısın. Sadece gerekli dosyaları değiştir.
- Değişiklikleri küçük, mantıklı adımlarla yap.
- Test veya build komutları başarısızsa düzelt.
- Çıktıyı *sadece unified diff patch* (git apply uyumlu) olarak ver.
"""
    user = f"""Issue Başlığı: {title}

Issue İçeriği:
{body}

Repo kökünde çalışıyorsun. Gerekli minimal değişiklikler için patch üret:
- Dosya ekleme/silme gerekiyorsa diff’e dahil et.
- Gerekliyse README/CHANGELOG güncelle.
- Sonunda kısa bir commit mesajı öner.
"""
    patch = ask_model(system, user)

    # 3) Patch uygula
    with tempfile.NamedTemporaryFile(delete=False, suffix=".patch") as tf:
        tf.write(patch.encode("utf-8"))
        patch_path = tf.name

    git(f"git apply --whitespace=fix {patch_path}")

    # 4) Test (isteğe göre özelleştir)
    try:
        subprocess.check_call("pytest -q", shell=True)
        tests = "✅ Tests passed"
    except subprocess.CalledProcessError:
        tests = "⚠️ Tests failed; continuing to open PR for review"

    # 5) Commit & push
    git('git config user.name "issue-agent[bot]"')
    git('git config user.email "issue-agent@local"')
    git('git add -A')
    git(f'git commit -m "agent: {title}"')
    git(f"git push -u origin {branch}")

    # 6) PR aç
    pr_title = f"[agent] {title}"
    pr_body = f"{tests}\n\nThis PR was generated automatically from issue #{ISSUE_NUMBER}."
    subprocess.check_call(
        f'gh pr create --fill --title "{pr_title}" --body "{pr_body}" --repo {REPO_FULL}',
        shell=True
    )

if __name__ == "__main__":
    main()
