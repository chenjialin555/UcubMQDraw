#!/usr/bin/env bash
# 合并 docs 现行 Markdown 到项目根目录 总.md（排除 archive/）
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
OUTPUT_FILE="${PROJECT_ROOT}/总.md"

cd "${PROJECT_ROOT}"

echo "正在合并 docs 现行文档（排除 archive/）..."

if [[ ! -d "${DOCS_DIR}" ]]; then
  echo "docs folder not found: ${DOCS_DIR}" >&2
  exit 1
fi

# 排序键：README → 根目录 → details → examples → 其它
# archive/ 故意不合并，避免旧稿污染总.md
sort_key() {
  local rel="$1"
  case "${rel}" in
    README.md)  echo "00_${rel}" ;;
    details/*)  echo "02_${rel}" ;;
    examples/*) echo "03_${rel}" ;;
    *)          echo "01_${rel}" ;;
  esac
}

mapfile -t files < <(
  find "${DOCS_DIR}" -type f -name '*.md' -print \
    | while IFS= read -r f; do
        rel="${f#"${DOCS_DIR}"/}"
        case "${rel}" in
          archive/*) continue ;;
        esac
        printf '%s\t%s\n' "$(sort_key "${rel}")" "${f}"
      done \
    | LC_ALL=C sort \
    | cut -f2-
)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "未找到任何 Markdown 文件。" >&2
  exit 1
fi

now="$(date '+%Y-%m-%d %H:%M:%S')"

{
  echo '# UcubMQDraw 文档合集'
  echo ''
  echo '> 由 merge-docs.sh 自动生成，请勿手工编辑。'
  echo '> 已排除 docs/archive/（旧稿仅查历史，禁止作实现依据）。'
  echo "> 生成时间：${now}"
  echo "> 共 ${#files[@]} 个文件"
  echo ''

  for f in "${files[@]}"; do
    rel="${f#"${DOCS_DIR}"/}"
    echo '---'
    echo ''
    echo "<!-- 来源: docs/${rel} -->"
    echo ''
    awk '{ lines[NR]=$0 } END {
      n=NR
      while (n>0 && lines[n] ~ /^[[:space:]]*$/) n--
      for (i=1; i<=n; i++) print lines[i]
    }' "${f}"
    echo ''
  done
} > "${OUTPUT_FILE}"

echo "Merged ${#files[@]} files -> ${OUTPUT_FILE}"
echo "已生成: ${OUTPUT_FILE}"
exit 0
