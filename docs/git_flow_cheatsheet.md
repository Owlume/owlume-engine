🦉 Owlume — Protected-Branch Solo Workflow (VS Code + PowerShell)
🌱 1️⃣ Create a new feature branch

VS Code:

Run Task → Create: Feature Branch

Or press Ctrl + Shift + P → “Run Task” → Create: Feature Branch

Enter:

feat/update-readme


(creates & switches branch)

🧩 2️⃣ Work normally — edit → commit → push
git add -A
git commit -m "docs: improved README wording"
git push -u origin feat/update-readme


✅ Push success → GitHub prints a PR link:

https://github.com/Owlume/owlume-engine/pull/new/feat/update-readme

🔄 3️⃣ Open Pull Request (PR) on GitHub

Click the link above.

Base = main ← Compare = feat/update-readme

Fill title & summary → Create pull request

Review → Merge (Squash and merge)

(If you can’t self-approve, set “Approvals required = 0” temporarily, merge, then restore to 1.)

🧹 4️⃣ Clean up locally
git checkout main
git pull
git branch -d feat/update-readme


Output should show:

Fast-forward … 
Deleted branch feat/update-readme

🔐 5️⃣ Protection Settings (one-time)

Branch rule: main

✅ Require PR before merge

✅ Include admins (default on for orgs)

☐ Allow force pushes – off

☐ Allow deletions – off

🧠 6️⃣ Repeat for every new change

Each new task = one branch, one PR, one merge.

Task Type	Branch Prefix Example
Docs / content	docs/clarity-metric-update
Feature / code	feat/empathy-overlay
Fix	fix/ui-render-bug
Chore / config	chore/update-schema-validation
🪶 Optional Hotkey

Bind Ctrl + Alt + B to instantly run “Create: Feature Branch.”
(Add in .vscode/keybindings.json if you want it later.)

Result:
✅ Main always safe
✅ History clean
✅ Future collaborators plug in effortlessly