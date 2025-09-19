import os, subprocess, json, re, tempfile, sys
from datetime import datetime
from anthropic import Anthropic

ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
REPO_FULL = os.environ["REPO_FULL"]

# ---------- helpers ----------
def git(cmd: str):
    subprocess.check_call(cmd, shell=True)

def sh_out(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True).strip()

def slugify(s: str, max_len: int = 40) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)  # harf/rakam/_/boşluk/-
    s = re.sub(r"\s+", "-", s).strip("-")            # boşluk -> -
    s = re.sub(r"-{2,}", "-", s)                     # çoklu - -> tek -
    return (s[:max_len] or "issue")

def default_branch() -> str:
    # origin HEAD branch tespiti; yoksa main'e düş
    try:
        out = sh_out("git remote show origin | sed -n 's/.*HEAD branch: //p'")
        return out or "main"
    except subprocess.CalledProcessError:
        return "main"

def read_issue():
    # gh CLI ile issue içeriğini al
    out = subprocess.check_output(
        f'gh issue view {ISSUE_NUMBER} --repo {REPO_FULL} --json title,body,labels',
        shell=True
    )
    return json.loads(out)

def ask_model(system_prompt: str, user_prompt: str) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # model adını dilediğin gibi değiştir; aşağıdaki güncel sonnet sürümü
    msg = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=3000,
        temperature=0.2,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    # içerik text parçası döner (patch)
    return msg.content[0].text

def try_run_pytest() -> str:
    # pytest yoksa sessizce atla; varsa çalıştır
    try:
        import importlib
        importlib.import_module("pytest")
    except Exception:
        return "ℹ️ pytest not installed; skipping tests"
    try:
        subprocess.check_call("pytest -q", shell=True)
        return "✅ Tests passed"
    except subprocess.CalledProcessError:
        return "⚠️ Tests failed; continuing to open PR for review"

# ---------- main ----------
def main():
    issue = read_issue()
    title = issue["title"]
    body = issue["body"]

    # 1) benzersiz branch adı
    slug = slugify(title)
    run_attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")
    branch = f"agent/issue-{ISSUE_NUMBER}-{slug}-r{run_attempt}"

    # var ise yeniden oluştur (CI tekrar koşularında çakışmayı önler)
    git(f"git checkout -B {branch}")

    # 2) patch üret
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
- Sonunda kısa bir commit mesajı öner (patch sonunda ayrı bir satırda "COMMIT: ..." olarak).
"""
    patch = ask_model(system, user)

    # 3) patch uygula
    with tempfile.NamedTemporaryFile(delete=False, suffix=".patch") as tf:
        tf.write(patch.encode("utf-8"))
        patch_path = tf.name

    # whitespace düzeltmeleri ile uygula
    git(f"git apply --whitespace=fix {patch_path}")

    # 4) testler (opsiyonel/koşullu)
    tests = try_run_pytest()

    # 5) commit
    git('git config user.name "issue-agent[bot]"')
    git('git config user.email "issue-agent@local"')
    git('git add -A')

    # patch içinde "COMMIT: ..." mesajı varsa onu al; yoksa başlığı kullan
    commit_msg = title
    m = re.search(r"^COMMIT:\s*(.+)$", patch, flags=re.MULTILINE)
    if m:
        commit_msg = m.group(1).strip()
    git(f'git commit -m "agent: {commit_msg}"')

    # 6) push (dayanıklı)
    try:
        git(f"git push -u origin {branch}")
    except subprocess.CalledProcessError:
        # remote aynı adda branch varsa rebase dene, sonra force-with-lease
        try:
            git(f"git fetch origin {branch} || true")
            git(f"git rebase origin/{branch} || true")
            git(f"git push -u origin {branch} --force-with-lease")
        except subprocess.CalledProcessError:
            # son çare: direkt force
            git(f"git push -u origin {branch} --force")

    # 7) PR aç
    base = default_branch()
    pr_title = f"[agent] {title}"
    pr_body = f"{tests}\n\nThis PR was generated automatically from issue #{ISSUE_NUMBER}."

    # gh pr create -> base'i açıkça ver; token olarak GH_TOKEN varsa gh onu kullanır
    subprocess.check_call(
        f'gh pr create --base "{base}" --head "{branch}" --title "{pr_title}" --body "{pr_body}" --repo "{REPO_FULL}"',
        shell=True
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # hata çıktısını görünür kıl
        print(f"[agent] error: {e}", file=sys.stderr)
        raise
