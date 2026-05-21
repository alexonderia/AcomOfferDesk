#!/usr/bin/env bash
# Promote integration branch dev → deploy branch test (alexonderia/AcomOfferDesk).
# Runs local gates, verifies green CI on dev, opens/reuses PR, waits for PR checks.
#
# Usage:
#   ./scripts/promote-dev-to-test.sh              # checks + PR + wait for green checks
#   ./scripts/promote-dev-to-test.sh --merge      # same, then merge PR (triggers Deploy to VPS)
#   ./scripts/promote-dev-to-test.sh --dry-run    # print plan only
#
# Env:
#   GITHUB_REPO   default alexonderia/AcomOfferDesk
#   GIT_REMOTE    default upstream
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GITHUB_REPO="${GITHUB_REPO:-alexonderia/AcomOfferDesk}"
GIT_REMOTE="${GIT_REMOTE:-upstream}"
DEV_BRANCH="${DEV_BRANCH:-dev}"
TEST_BRANCH="${TEST_BRANCH:-test}"

DO_MERGE=0
DRY_RUN=0

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --merge) DO_MERGE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage 0 ;;
    *) echo "Unknown option: $1" >&2; usage 1 ;;
  esac
  shift
done

info() { echo "PROMOTE: $*"; }
fail() { echo "PROMOTE: FAIL: $*" >&2; exit 1; }
ok() { echo "PROMOTE: OK: $*"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"
}

risky_diff() {
  git diff "${GIT_REMOTE}/${TEST_BRANCH}...${GIT_REMOTE}/${DEV_BRANCH}" -- \
    docker-compose.yml \
    docker-compose.prod.yml \
    docker-compose.test.yml \
    docker-compose.init.yml \
    .github/workflows/deploy.yml \
    .github/workflows/promotion-to-test.yml \
    infra/keycloak/ \
    backend/app/core/config.py \
    backend/app/services/keycloak_admin.py \
    backend/.env.example \
    2>/dev/null || true
}

if [ ! -f docker-compose.yml ]; then
  fail "run from repository root (docker-compose.yml not found)"
fi

require_cmd git
require_cmd gh

if ! gh auth status -h github.com >/dev/null 2>&1; then
  fail "gh not logged in — run: gh auth login"
fi

info "repo=${GITHUB_REPO} remote=${GIT_REMOTE} ${DEV_BRANCH} → ${TEST_BRANCH}"

if [ "$DRY_RUN" = 1 ]; then
  info "DRY-RUN mode (no PR create / merge)"
fi

info "fetch ${GIT_REMOTE}"
if [ "$DRY_RUN" = 0 ]; then
  git fetch "${GIT_REMOTE}" "${DEV_BRANCH}" "${TEST_BRANCH}"
fi

if ! git rev-parse --verify "${GIT_REMOTE}/${DEV_BRANCH}" >/dev/null 2>&1; then
  fail "missing ${GIT_REMOTE}/${DEV_BRANCH} — fetch first"
fi
if ! git rev-parse --verify "${GIT_REMOTE}/${TEST_BRANCH}" >/dev/null 2>&1; then
  fail "missing ${GIT_REMOTE}/${TEST_BRANCH} — fetch first"
fi

DEV_SHA="$(git rev-parse "${GIT_REMOTE}/${DEV_BRANCH}")"
TEST_SHA="$(git rev-parse "${GIT_REMOTE}/${TEST_BRANCH}")"

if [ "$DEV_SHA" = "$TEST_SHA" ]; then
  ok "${DEV_BRANCH} and ${TEST_BRANCH} already at same commit (${DEV_SHA:0:7}) — nothing to promote"
  exit 0
fi

COMMITS_AHEAD="$(git rev-list --count "${GIT_REMOTE}/${TEST_BRANCH}..${GIT_REMOTE}/${DEV_BRANCH}")"
info "${COMMITS_AHEAD} commit(s) on ${DEV_BRANCH} not in ${TEST_BRANCH}"
git log --oneline "${GIT_REMOTE}/${TEST_BRANCH}..${GIT_REMOTE}/${DEV_BRANCH}" | head -20
if [ "$(git rev-list --count "${GIT_REMOTE}/${TEST_BRANCH}..${GIT_REMOTE}/${DEV_BRANCH}")" -gt 20 ]; then
  info "(truncated — see full log: git log ${GIT_REMOTE}/${TEST_BRANCH}..${GIT_REMOTE}/${DEV_BRANCH})"
fi

DIFF_LINES="$(risky_diff | wc -l | tr -d ' ')"
if [ "${DIFF_LINES}" -gt 0 ]; then
  info "risky-path diff (${DIFF_LINES} lines) — review before merge:"
  risky_diff | head -80
  if [ "${DIFF_LINES}" -gt 80 ]; then
    info "(diff truncated — run: git diff ${GIT_REMOTE}/${TEST_BRANCH}...${GIT_REMOTE}/${DEV_BRANCH} -- <paths>)"
  fi
else
  ok "no changes in risky paths (compose/keycloak/deploy)"
fi

if [ "$DRY_RUN" = 1 ]; then
  info "would run: ./scripts/verify-promotion-to-test.sh"
  info "would check: latest CI workflow on branch ${DEV_BRANCH} = success"
  info "would open/reuse PR: base=${TEST_BRANCH} head=${DEV_BRANCH}"
  info "would wait: PR checks CI + Promotion to test"
  [ "$DO_MERGE" = 1 ] && info "would merge PR into ${TEST_BRANCH}"
  exit 0
fi

info "local promotion checks"
bash scripts/verify-promotion-to-test.sh

info "latest CI on ${GITHUB_REPO} branch ${DEV_BRANCH}"
RUN_HEAD="$(gh run list --repo "${GITHUB_REPO}" --branch "${DEV_BRANCH}" --limit 1 \
  --json headSha --jq '.[0].headSha // empty' 2>/dev/null || true)"
RUN_STATUS="$(gh run list --repo "${GITHUB_REPO}" --branch "${DEV_BRANCH}" --limit 1 \
  --json status --jq '.[0].status // empty' 2>/dev/null || true)"
RUN_CONCLUSION="$(gh run list --repo "${GITHUB_REPO}" --branch "${DEV_BRANCH}" --limit 1 \
  --json conclusion --jq '.[0].conclusion // empty' 2>/dev/null || true)"
RUN_URL="$(gh run list --repo "${GITHUB_REPO}" --branch "${DEV_BRANCH}" --limit 1 \
  --json url --jq '.[0].url // empty' 2>/dev/null || true)"
RUN_WF="$(gh run list --repo "${GITHUB_REPO}" --branch "${DEV_BRANCH}" --limit 1 \
  --json workflowName --jq '.[0].workflowName // empty' 2>/dev/null || true)"

if [ -z "$RUN_STATUS" ]; then
  fail "no GitHub Actions runs on ${DEV_BRANCH} — push ${DEV_BRANCH} and wait for CI"
fi

if [ -n "${RUN_HEAD:-}" ] && [ "${RUN_HEAD}" != "$DEV_SHA" ]; then
  fail "latest CI run is for ${RUN_HEAD:0:7}, but ${GIT_REMOTE}/${DEV_BRANCH} is ${DEV_SHA:0:7} — push ${DEV_BRANCH} and wait for green CI"
fi

if [ "$RUN_STATUS" != "completed" ]; then
  fail "latest CI on ${DEV_BRANCH} still ${RUN_STATUS} — wait, then retry (${RUN_URL:-see Actions tab})"
fi
if [ "$RUN_CONCLUSION" != "success" ]; then
  fail "latest CI on ${DEV_BRANCH} is ${RUN_CONCLUSION} — fix ${DEV_BRANCH} before promoting to ${TEST_BRANCH}"
fi
ok "dev CI green (${RUN_WF:-workflow}${RUN_URL:+ — $RUN_URL})"

EXISTING_PR="$(gh pr list --repo "${GITHUB_REPO}" --base "${TEST_BRANCH}" --head "${DEV_BRANCH}" --state open --json number --jq '.[0].number // empty' 2>/dev/null || true)"

if [ -n "${EXISTING_PR}" ]; then
  PR_NUM="${EXISTING_PR}"
  PR_URL="$(gh pr view "${PR_NUM}" --repo "${GITHUB_REPO}" --json url --jq .url)"
  ok "reusing open PR #${PR_NUM} (${PR_URL})"
else
  info "creating PR base=${TEST_BRANCH} ← head=${DEV_BRANCH}"
  PR_URL="$(gh pr create --repo "${GITHUB_REPO}" --base "${TEST_BRANCH}" --head "${DEV_BRANCH}" \
    --title "Promote ${DEV_BRANCH} → ${TEST_BRANCH}" \
    --body "Automated promotion via scripts/promote-dev-to-test.sh

- Local: verify-promotion-to-test.sh
- Dev CI: success on ${DEV_SHA:0:7}
- Required PR checks: CI, Promotion to test

See docs/operations/branch-merge-policy.md")"
  PR_NUM="$(gh pr view "${PR_URL}" --json number --jq .number)"
  ok "created PR #${PR_NUM} (${PR_URL})"
fi

info "waiting for required PR checks (CI + Promotion to test)…"
if ! gh pr checks "${PR_NUM}" --repo "${GITHUB_REPO}" --watch; then
  fail "PR checks failed or timed out — open PR #${PR_NUM} and fix before merge"
fi

CHECKS_FAIL=0
while IFS=$'\t' read -r name state; do
  [ -z "$name" ] && continue
  case "$state" in
    pass|success|neutral|skipping) ;;
    *)
      echo "  check: ${name} = ${state}" >&2
      CHECKS_FAIL=1
      ;;
  esac
done < <(gh pr checks "${PR_NUM}" --repo "${GITHUB_REPO}" 2>/dev/null || true)

if [ "$CHECKS_FAIL" -ne 0 ]; then
  fail "not all PR checks are green — review PR #${PR_NUM}"
fi
ok "PR #${PR_NUM} checks green"

if [ "$DO_MERGE" = 0 ]; then
  info "ready to merge — run with --merge or: gh pr merge ${PR_NUM} --repo ${GITHUB_REPO} --merge"
  info "after merge: wait for Deploy to VPS on ${TEST_BRANCH}"
  exit 0
fi

info "merging PR #${PR_NUM} into ${TEST_BRANCH}"
gh pr merge "${PR_NUM}" --repo "${GITHUB_REPO}" --merge
ok "merged — watch Deploy to VPS: gh run list --repo ${GITHUB_REPO} --branch ${TEST_BRANCH} --limit 3"
