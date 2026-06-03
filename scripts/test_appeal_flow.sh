#!/usr/bin/env bash
# ============================================================
# 企业诉求模块端到端测试脚本
# 覆盖：提交 → 受理 → 分派部门 → 部门反馈 → 审核 → 企业评价
# ============================================================

BASE="http://localhost:8001"
PASS=0
FAIL=0

# ── 工具函数 ─────────────────────────────────────────────────

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
NC="\033[0m"

ok()   { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL+1)); }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
sep()  { echo -e "${YELLOW}──────────────────────────────────────────${NC}"; }

# 发请求并返回响应体
post() { curl -s -X POST "$BASE$1" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$2"; }
get()  { curl -s -X GET  "$BASE$1" -H "Authorization: Bearer $TOKEN"; }

# 从 JSON 中提取字段值
jget() { echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d$2)" 2>/dev/null; }

assert_code() {
  local resp="$1" expected="$2" label="$3"
  local code; code=$(jget "$resp" "['code']")
  if [ "$code" = "$expected" ]; then
    ok "$label (code=$code)"
  else
    fail "$label (期望 code=$expected，实际 code=$code)"
    echo "    响应: $resp"
  fi
}

assert_field() {
  local resp="$1" path="$2" expected="$3" label="$4"
  local val; val=$(jget "$resp" "$path")
  if [ "$val" = "$expected" ]; then
    ok "$label ($val)"
  else
    fail "$label (期望 $expected，实际 $val)"
  fi
}

# ============================================================
sep
info "【准备】检查服务健康状态"
sep
HEALTH=$(curl -s "$BASE/api/common/health")
assert_code "$HEALTH" "0" "服务健康检查"

# ============================================================
sep
info "【Step 5-1】企业端 mock 登录"
sep
ENT_RESP=$(curl -s -X POST "$BASE/api/auth/enterprise/mock-login" \
  -H "Content-Type: application/json" \
  -d '{
    "enterpriseName": "威海测试科技有限公司",
    "creditCode": "91371000TEST000001",
    "legalPersonName": "李四",
    "legalPersonIdNo": "370000199001010011",
    "legalPersonMobile": "13900000001"
  }')
assert_code "$ENT_RESP" "0" "企业端 mock 登录"
ENT_TOKEN=$(jget "$ENT_RESP" "['data']['accessToken']")
info "企业端 Token: ${ENT_TOKEN:0:40}..."

# ============================================================
sep
info "【Step 5-2】提交诉求"
sep
TOKEN="$ENT_TOKEN"
SUBMIT_RESP=$(post "/api/enterprise/appeals" '{
  "title": "申请惠企政策咨询",
  "content": "希望了解2026年最新中小企业扶持政策，包括融资担保、税收优惠等方面",
  "contactName": "李四",
  "contactPhone": "13900000001",
  "regionCode": "371000",
  "regionName": "威海市",
  "urgencyLevel": "NORMAL"
}')
assert_code "$SUBMIT_RESP" "0" "提交诉求"
APPEAL_ID=$(jget "$SUBMIT_RESP" "['data']['id']")
APPEAL_NO=$(jget "$SUBMIT_RESP" "['data']['appealNo']")
assert_field "$SUBMIT_RESP" "['data']['status']" "PENDING_ACCEPT" "初始状态为 PENDING_ACCEPT"
info "诉求 ID: $APPEAL_ID，编号: $APPEAL_NO"

# ============================================================
sep
info "【Step 5-3】查询我的诉求列表"
sep
LIST_RESP=$(get "/api/enterprise/appeals?pageNo=1&pageSize=10")
assert_code "$LIST_RESP" "0" "企业端诉求列表"
TOTAL=$(jget "$LIST_RESP" "['data']['total']")
info "企业诉求总数: $TOTAL"
[ "$TOTAL" -ge 1 ] && ok "列表有数据 (total=$TOTAL)" || fail "列表为空"

# ============================================================
sep
info "【Step 5-4】查询诉求详情（企业端）"
sep
DETAIL_RESP=$(get "/api/enterprise/appeals/$APPEAL_ID")
assert_code "$DETAIL_RESP" "0" "企业端诉求详情"
assert_field "$DETAIL_RESP" "['data']['appealNo']" "$APPEAL_NO" "详情 appealNo 一致"

# ============================================================
sep
info "【Step 6-1】管理端 mock 登录"
sep
ADMIN_RESP=$(curl -s -X POST "$BASE/api/auth/admin/mock-login" \
  -H "Content-Type: application/json" \
  -d '{
    "platformUserId": "admin_u001",
    "username": "zhangmin",
    "realName": "张敏",
    "departmentId": "center_dept_001",
    "departmentName": "企业服务中心",
    "regionCode": "371000",
    "regionName": "威海市",
    "roleCodes": ["CENTER_ADMIN"],
    "dataScope": "ALL"
  }')
assert_code "$ADMIN_RESP" "0" "管理端 mock 登录"
ADMIN_TOKEN=$(jget "$ADMIN_RESP" "['data']['accessToken']")
info "管理端 Token: ${ADMIN_TOKEN:0:40}..."

# ============================================================
sep
info "【Step 6-2】管理端查询待受理列表"
sep
TOKEN="$ADMIN_TOKEN"
ALIST_RESP=$(get "/api/admin/appeals?status=PENDING_ACCEPT&pageNo=1&pageSize=10")
assert_code "$ALIST_RESP" "0" "管理端诉求列表"
ATOTAL=$(jget "$ALIST_RESP" "['data']['total']")
info "待受理诉求数: $ATOTAL"

# ============================================================
sep
info "【Step 6-3】管理端受理诉求"
sep
ACCEPT_RESP=$(post "/api/admin/appeals/$APPEAL_ID/accept" '{
  "appealTypeCode": "POLICY_CONSULT",
  "appealTypeName": "政策咨询",
  "replyDeadline": "2026-06-30T18:00:00",
  "opinion": "诉求内容清晰，予以受理"
}')
assert_code "$ACCEPT_RESP" "0" "受理诉求"
assert_field "$ACCEPT_RESP" "['data']['status']" "ACCEPTED" "受理后状态为 ACCEPTED"
assert_field "$ACCEPT_RESP" "['data']['appealTypeCode']" "POLICY_CONSULT" "诉求类型写入正确"

# ============================================================
sep
info "【Step 6-4】重复受理应被拒绝（状态校验）"
sep
DUP_ACCEPT=$(post "/api/admin/appeals/$APPEAL_ID/accept" '{
  "appealTypeCode": "POLICY_CONSULT",
  "appealTypeName": "政策咨询",
  "opinion": "重复受理测试"
}')
DUP_CODE=$(jget "$DUP_ACCEPT" "['code']")
[ "$DUP_CODE" = "40901" ] && ok "重复受理被正确拦截 (code=40901)" || fail "重复受理未被拦截 (code=$DUP_CODE)"

# ============================================================
sep
info "【Step 7-1】分派责任部门"
sep
ASSIGN_RESP=$(post "/api/admin/appeals/$APPEAL_ID/assign" '{
  "assignedDeptId": "dept_econ_001",
  "assignedDeptName": "经济发展局",
  "deadline": "2026-06-20T18:00:00",
  "assignOpinion": "请协助解答惠企政策相关问题"
}')
assert_code "$ASSIGN_RESP" "0" "分派部门"
assert_field "$ASSIGN_RESP" "['data']['status']" "DEPT_HANDLING" "分派后状态为 DEPT_HANDLING"
assert_field "$ASSIGN_RESP" "['data']['responsibleDeptId']" "dept_econ_001" "责任部门 ID 写入正确"

# ============================================================
sep
info "【Step 7-2】部门反馈"
sep
DEPT_REPLY_RESP=$(post "/api/admin/appeals/$APPEAL_ID/department-reply" '{
  "replyContent": "根据2026年威海市中小企业扶持政策，具体优惠如下：1.融资担保贷款利率不超过4.5%；2.高新技术企业所得税减按15%征收；3.设备购置可申请一次性扣除。"
}')
assert_code "$DEPT_REPLY_RESP" "0" "部门反馈"
assert_field "$DEPT_REPLY_RESP" "['data']['status']" "CENTER_REVIEWING" "部门反馈后状态为 CENTER_REVIEWING"

# ============================================================
sep
info "【Step 7-3】企服中心审核部门反馈（通过）"
sep
REVIEW_RESP=$(post "/api/admin/appeals/$APPEAL_ID/review-reply" '{
  "pass": true,
  "opinion": "部门答复内容完整，审核通过"
}')
assert_code "$REVIEW_RESP" "0" "审核通过"
REVIEW_STATUS=$(jget "$REVIEW_RESP" "['data']['status']")
[ "$REVIEW_STATUS" = "PENDING_EVALUATION" ] || [ "$REVIEW_STATUS" = "REPLIED" ] \
  && ok "审核通过后状态为 $REVIEW_STATUS" \
  || fail "审核通过后状态异常: $REVIEW_STATUS"

# ============================================================
sep
info "【Step 7-4】管理端查看诉求完整详情"
sep
FULL_DETAIL=$(get "/api/admin/appeals/$APPEAL_ID")
assert_code "$FULL_DETAIL" "0" "管理端诉求详情"
REC_COUNT=$(echo "$FULL_DETAIL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['records']))" 2>/dev/null || echo 0)
info "办理记录条数: $REC_COUNT"
[ "$REC_COUNT" -ge 4 ] && ok "办理记录完整 (共 $REC_COUNT 条)" || fail "办理记录条数不足，期望≥4条，实际 $REC_COUNT 条"
ASSIGN_COUNT=$(echo "$FULL_DETAIL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['data']['assignments']))" 2>/dev/null || echo 0)
[ "$ASSIGN_COUNT" -ge 1 ] && ok "分派记录存在 (共 $ASSIGN_COUNT 条)" || fail "分派记录为空"

# ============================================================
sep
info "【Step 7-5】审核退回流程（另开一条诉求验证）"
sep
TOKEN="$ENT_TOKEN"
SUBMIT2_RESP=$(post "/api/enterprise/appeals" '{
  "title": "营业执照变更咨询",
  "content": "公司名称变更后需要办理哪些手续？",
  "contactName": "李四",
  "contactPhone": "13900000001",
  "regionCode": "371000",
  "regionName": "威海市"
}')
assert_code "$SUBMIT2_RESP" "0" "提交第2条诉求"
APPEAL2_ID=$(jget "$SUBMIT2_RESP" "['data']['id']")

TOKEN="$ADMIN_TOKEN"
# 受理
post "/api/admin/appeals/$APPEAL2_ID/accept" '{"appealTypeCode":"BIZ_CONSULT","appealTypeName":"业务咨询","opinion":"受理"}' > /dev/null
# 分派
post "/api/admin/appeals/$APPEAL2_ID/assign" '{"assignedDeptId":"dept_mkt_001","assignedDeptName":"市场监管局","assignOpinion":"请协助"}' > /dev/null
# 部门反馈
post "/api/admin/appeals/$APPEAL2_ID/department-reply" '{"replyContent":"需要提交变更申请表及相关材料"}' > /dev/null
# 审核退回
REJECT_REVIEW=$(post "/api/admin/appeals/$APPEAL2_ID/review-reply" '{
  "pass": false,
  "opinion": "答复内容不够详细，请补充具体材料清单"
}')
assert_code "$REJECT_REVIEW" "0" "审核退回请求成功"
assert_field "$REJECT_REVIEW" "['data']['status']" "REVIEW_REJECTED" "审核退回后状态为 REVIEW_REJECTED"

# 重新分派（REVIEW_REJECTED 允许再次分派）
REASSIGN=$(post "/api/admin/appeals/$APPEAL2_ID/assign" '{"assignedDeptId":"dept_mkt_001","assignedDeptName":"市场监管局","assignOpinion":"请补充详细材料清单"}')
assert_code "$REASSIGN" "0" "审核退回后重新分派"
assert_field "$REASSIGN" "['data']['status']" "DEPT_HANDLING" "重新分派后状态为 DEPT_HANDLING"

# ============================================================
sep
info "【Step 8-1】企业评价诉求（第1条，状态：$REVIEW_STATUS）"
sep
TOKEN="$ENT_TOKEN"
EVAL_RESP=$(post "/api/enterprise/appeals/$APPEAL_ID/evaluation" '{
  "satisfaction": "SATISFIED",
  "score": 5,
  "resolvedFlag": 1,
  "comment": "回复及时，内容详实，非常满意！"
}')
assert_code "$EVAL_RESP" "0" "企业评价"
assert_field "$EVAL_RESP" "['data']['status']" "EVALUATED" "评价后状态为 EVALUATED"

# ============================================================
sep
info "【Step 8-2】重复评价应被拒绝"
sep
DUP_EVAL=$(post "/api/enterprise/appeals/$APPEAL_ID/evaluation" '{
  "satisfaction": "UNSATISFIED",
  "score": 1,
  "comment": "重复评价测试"
}')
DUP_EVAL_CODE=$(jget "$DUP_EVAL" "['code']")
[ "$DUP_EVAL_CODE" = "40901" ] && ok "重复评价被正确拦截 (code=40901)" || fail "重复评价未被拦截 (code=$DUP_EVAL_CODE)"

# ============================================================
sep
info "【Step 8-3】企业端查看诉求详情（含评价信息）"
sep
FINAL_DETAIL=$(get "/api/enterprise/appeals/$APPEAL_ID")
assert_code "$FINAL_DETAIL" "0" "企业端查看最终详情"
EVAL_SATISFACTION=$(jget "$FINAL_DETAIL" "['data']['evaluation']['satisfaction']")
EVAL_SCORE=$(jget "$FINAL_DETAIL" "['data']['evaluation']['score']")
[ "$EVAL_SATISFACTION" = "SATISFIED" ] && ok "评价满意度正确: $EVAL_SATISFACTION" || fail "评价满意度异常: $EVAL_SATISFACTION"
[ "$EVAL_SCORE" = "5" ]               && ok "评价星级正确: $EVAL_SCORE 星"       || fail "评价星级异常: $EVAL_SCORE"

# ============================================================
sep
info "【Step 8-4】管理端不满意回访记录（用第1条演示）"
sep
TOKEN="$ADMIN_TOKEN"
FOLLOWUP_RESP=$(post "/api/admin/appeals/$APPEAL_ID/followup" '{
  "responsibleDeptId": "dept_econ_001",
  "responsibleDeptName": "经济发展局",
  "followupMethod": "PHONE",
  "followupContent": "电话联系企业，了解诉求办理满意情况",
  "followupResult": "企业表示满意，无进一步诉求"
}')
assert_code "$FOLLOWUP_RESP" "0" "不满意回访记录"

# ============================================================
sep
info "【Step 8-5】验证退回补充流程"
sep
TOKEN="$ENT_TOKEN"
SUBMIT3_RESP=$(post "/api/enterprise/appeals" '{
  "title": "土地使用权转让咨询",
  "content": "工业用地转让需要哪些审批流程？",
  "contactName": "李四",
  "contactPhone": "13900000001",
  "regionCode": "371000",
  "regionName": "威海市"
}')
APPEAL3_ID=$(jget "$SUBMIT3_RESP" "['data']['id']")
assert_code "$SUBMIT3_RESP" "0" "提交第3条诉求"

TOKEN="$ADMIN_TOKEN"
RETURN_RESP=$(post "/api/admin/appeals/$APPEAL3_ID/return-supplement" '{
  "opinion": "请补充相关土地证明材料"
}')
assert_code "$RETURN_RESP" "0" "退回补充"
assert_field "$RETURN_RESP" "['data']['status']" "NEED_SUPPLEMENT" "退回后状态为 NEED_SUPPLEMENT"

TOKEN="$ENT_TOKEN"
SUPP_RESP=$(post "/api/enterprise/appeals/$APPEAL3_ID/supplement" '{
  "content": "已补充土地使用权证书扫描件及测量报告"
}')
assert_code "$SUPP_RESP" "0" "企业补充材料"
assert_field "$SUPP_RESP" "['data']['status']" "PENDING_ACCEPT" "补充后状态回到 PENDING_ACCEPT"

# ============================================================
sep
info "【Step 8-6】验证不予受理流程"
sep
TOKEN="$ENT_TOKEN"
SUBMIT4_RESP=$(post "/api/enterprise/appeals" '{
  "title": "道路交通事故赔偿投诉",
  "content": "请帮我处理交通事故赔偿问题",
  "contactName": "李四",
  "contactPhone": "13900000001",
  "regionCode": "371000",
  "regionName": "威海市"
}')
APPEAL4_ID=$(jget "$SUBMIT4_RESP" "['data']['id']")
assert_code "$SUBMIT4_RESP" "0" "提交第4条诉求（不在受理范围）"

TOKEN="$ADMIN_TOKEN"
REJECT_RESP=$(post "/api/admin/appeals/$APPEAL4_ID/reject" '{
  "reasonCode": "OUT_OF_SCOPE",
  "reasonName": "不属于受理范围",
  "opinion": "该事项属于交通事故纠纷，不在企服中心受理范围，建议向交警部门反映"
}')
assert_code "$REJECT_RESP" "0" "不予受理"
assert_field "$REJECT_RESP" "['data']['status']" "REJECTED" "不予受理后状态为 REJECTED"

# ============================================================
sep
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           测试完成 — 汇总结果             ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  通过 (PASS): $(printf '%2d' $PASS)                          ║${NC}"
if [ "$FAIL" -gt 0 ]; then
echo -e "${RED}║  失败 (FAIL): $(printf '%2d' $FAIL)                          ║${NC}"
else
echo -e "${GREEN}║  失败 (FAIL):  0                          ║${NC}"
fi
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
