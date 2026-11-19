#!/usr/bin/env bash
# check-skill.py 的回归测试：在临时副本里注入故障，断言每个故障都能被抓到。
# 用法：bash scripts/test-check-skill.sh
set -u

SRC="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0
FAIL=0
OUT="$TMP/out"

fresh() {
  rm -rf "$TMP/s"
  cp -R "$SRC" "$TMP/s" || exit 1
  cd "$TMP/s" || exit 1
}

run() {
  python3 scripts/check-skill.py --quiet >"$OUT" 2>&1
  echo $?
}

# check <期望退出码> <说明>
check() {
  local want="$1" desc="$2" got
  got="$(run)"
  if [ "$got" = "$want" ]; then
    PASS=$((PASS + 1))
    printf '  ok   %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL %s（期望 %s，实际 %s）\n' "$desc" "$want" "$got"
    sed 's/^/       /' "$OUT"
  fi
}

no_traceback() {
  if grep -q "Traceback" "$OUT"; then
    FAIL=$((FAIL + 1))
    printf '  FAIL %s（出现 Traceback）\n' "$1"
    sed 's/^/       /' "$OUT"
  else
    PASS=$((PASS + 1))
    printf '  ok   %s\n' "$1"
  fi
}

echo "check-skill 回归测试"

fresh
check 0 "干净副本应通过"

fresh
rm -rf templates
check 1 "删除 templates/ 目录应报错"
no_traceback "删除目录不应崩溃"

fresh
printf '\n| a | b |\n|---|---|\n| 只有一列 |\n' >>README.md
check 1 "表格列数不一致应报错"

fresh
printf '\nteam_send 不存在，但 team_spawn 仍可用\n' >>SKILL.md
check 1 "同行夹带未否定的禁用词应报错"

fresh
rm -rf templates
sed -i.bak 's|`templates/standard-dev.md`|`templates/ghost.md`|' SKILL.md
rm -f SKILL.md.bak
check 1 "只改表格为不存在文件应报错"

fresh
printf '\n见 references/does-not-exist.md\n' >>SKILL.md
check 1 "断链应报错"

fresh
printf '\n见 scripts/does-not-exist.sh\n' >>SKILL.md
check 1 "断链 .sh 应报错"

fresh
printf '\n```text\n未闭合的围栏\n' >>README.md
check 1 "围栏未闭合应报错"

fresh
sed -i.bak 's/## DoD/## Done/' templates/quick-task.md
rm -f templates/quick-task.md.bak
check 1 "模板缺 DoD 应报错"

fresh
printf '\xff\xfe\x00broken' >references/bad-utf8.md
check 1 "非 UTF-8 文件应报错而不是崩溃"
no_traceback "非 UTF-8 不应抛 Traceback"

fresh
printf '\n| 表头 | 说明 |\n|---|---|\n| `a \\| b` | 转义竖线 |\n' >>README.md
check 0 "代码里的转义竖线不应误报"

fresh
mkdir -p .team-mode
printf '\nteam_spawn 旧名\n' >.team-mode/state.md
check 0 "隐藏目录（.team-mode）应被跳过"

fresh
printf '\n见 references/DSH-PLATFORM.md\n' >>SKILL.md
check 1 "大小写不符的引用应报错"

fresh
printf '\n把 templates/new-template.md 加进来\n' >>SKILL.md
check 1 "SKILL 提到但未登记的新模板应报错"

fresh
python3 scripts/check-skill.py --quie >"$OUT" 2>&1
code=$?
if [ "$code" = "2" ]; then
  PASS=$((PASS + 1))
  echo "  ok   未知参数应返回 2"
else
  FAIL=$((FAIL + 1))
  echo "  FAIL 未知参数应返回 2（实际 $code）"
fi

echo
if [ "$FAIL" -gt 0 ]; then
  echo "失败：$FAIL 个用例失败，$PASS 个通过"
  exit 1
fi
echo "✅ 全部通过：$PASS 个用例"
