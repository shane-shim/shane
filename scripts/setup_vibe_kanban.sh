#!/usr/bin/env bash
set -euo pipefail

# Setup a GitHub Project as a Kanban board with fields for Status, Sprint, Priority, Size
# Requirements: gh CLI authenticated with a token that has `project` scope
# Usage: GH_OWNER=<org_or_user> REPO=<repo_name> ./scripts/setup_vibe_kanban.sh

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install from https://cli.github.com/" >&2
  exit 1
fi

: "${GH_OWNER:?Set GH_OWNER to your org or username}"
: "${REPO:?Set REPO to your repository name}"

TITLE=${TITLE:-"Vibe Kanban"}

echo "Creating project '$TITLE' for owner '$GH_OWNER'..."
proj_json=$(gh project create --owner "$GH_OWNER" --title "$TITLE" --format json)
proj_number=$(echo "$proj_json" | rg -o '"number":\s*(\d+)' -r '$1')
test -n "$proj_number" || { echo "Failed to get project number" >&2; exit 1; }

echo "Adding fields to project #$proj_number..."
gh project field-create "$proj_number" --owner "$GH_OWNER" \
  --name Status --data-type SINGLE_SELECT \
  --options "Backlog,Ready,In Progress,In Review,Blocked,Done"

gh project field-create "$proj_number" --owner "$GH_OWNER" \
  --name Sprint --data-type ITERATION

gh project field-create "$proj_number" --owner "$GH_OWNER" \
  --name Priority --data-type SINGLE_SELECT \
  --options "P0,P1,P2"

gh project field-create "$proj_number" --owner "$GH_OWNER" \
  --name Size --data-type SINGLE_SELECT \
  --options "S,M,L"

echo "Linking repository $GH_OWNER/$REPO to project..."
gh project link --owner "$GH_OWNER" --project "$proj_number" --repo "$GH_OWNER/$REPO"

cat <<EOM

Done.
- Project number: $proj_number
- Open in browser: gh project view $proj_number --owner $GH_OWNER --web
- Create a Board view grouped by 'Status' from the web UI.

Tip: Use labels Type/Priority/Size described in docs/vibe-kanban.md.
EOM

